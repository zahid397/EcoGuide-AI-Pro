import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger


COLLECTION = "eco_travel_v3"


# ---------------------------------------------------------
# SAFE EMBEDDER (Cloud Safe – No Torch)
# ---------------------------------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)
        self.is_fitted = False

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
            self.is_fitted = True
        except:
            pass

    def encode(self, text):
        if not self.is_fitted:
            self.fit([text])

        try:
            vec = self.vectorizer.transform([text]).toarray()[0]
        except:
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()[0]

        return vec.tolist()


# ---------------------------------------------------------
# RAG ENGINE
# ---------------------------------------------------------
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        existing = [c.name for c in self.client.get_collections().collections]

        if COLLECTION not in existing:
            self._init_collection()
            self._index_all()

    # -----------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )

    # -----------------------------------------------------
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"Missing CSV: {file_path}")
            return

        df = pd.read_csv(file_path)
        df.fillna("", inplace=True)

        texts = []
        points = []

        # Build corpus for global TFIDF fit
        for _, row in df.iterrows():
            text = f"{row.get('name','')} {row.get('location','')} {row.get('description','')} {data_type}"
            texts.append(text)

        # Fit once
        self.embedder.fit(texts)

        # Create vectors
        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # Save eco_score as float
            try:
                payload["eco_score"] = float(payload.get("eco_score", 0))
            except:
                payload["eco_score"] = 0

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')} {data_type}"
            emb = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=emb,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"Indexed {len(points)} items from {file_path}")

    # -----------------------------------------------------
    def _index_all(self):
        print("Indexing started...")
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")
        print("Indexing finished!")

    # -----------------------------------------------------
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
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True
            )

            return [hit.payload for hit in (results or [])]

        except Exception as e:
            logger.exception(f"Search failed: {e}")
            return []
