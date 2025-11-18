import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"


# ================================================
# Cloud-Safe Embedder (No Torch, No Crash)
# ================================================
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
        self.is_fitted = False
        self.corpus = []

    def fit(self, texts):
        if not texts:
            return
        self.vectorizer.fit(texts)
        self.is_fitted = True
        self.corpus = texts

    def encode(self, text):
        if not self.is_fitted:
            self.fit(self.corpus + [text])
        vec = self.vectorizer.transform([text]).toarray()[0]
        return vec.tolist()


# ================================================
# RAG ENGINE — FINAL WINNER VERSION
# ================================================
class RAGEngine:
    def __init__(self):
        # Local folder for Streamlit Cloud (no Docker needed)
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # Check if collection exists (new version compatible)
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION not in collection_names:
            self._init_collection()
            self._index_all()

    def _init_collection(self):
        self.client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )
        logger.info(f"Collection {COLLECTION} created")

    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return

        df = pd.read_csv(file_path)
        df.fillna("", inplace=True)

        texts = []
        payloads = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # Force eco_score to float
            try:
                payload["eco_score"] = float(payload.get("eco_score", 0))
            except:
                payload["eco_score"] = 0.0

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')} {payload.get('tag','')} {data_type}"
            texts.append(text)
            payloads.append(payload)

        # Fit embedder once
        self.embedder.fit(texts)

        points = []
        for text, payload in zip(texts, payloads):
            vector = self.embedder.encode(text)
            points.append(models.PointStruct(id=str(uuid4()), vector=vector, payload=payload))

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            logger.info(f"Indexed {len(points)} items from {file_path}")

    def _index_all(self):
        logger.info("Starting indexing all CSV files...")
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")
        logger.info("Indexing completed!")

    def search(self, query, top_k=10, min_eco_score=7.0):
        try:
            query_vec = self.embedder.encode(query)

            eco_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=float(min_eco_score))
                    )
                ]
            )

            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=query_vec,
                filter=eco_filter,          # ← Fixed: filter= not query_filter=
                limit=top_k,
                with_payload=True
            )

            return [hit.payload for hit in results]

        except Exception as e:
            logger.exception(f"RAG Search failed: {e}")
            return []   # Never crash — always return empty list
