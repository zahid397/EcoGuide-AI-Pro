import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"


# -------------------------------
# Safe Embedder
# -------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
        except:
            pass

    def encode(self, text):
        try:
            vec = self.vectorizer.transform([text]).toarray()
        except:
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()
        return vec[0].tolist()


# -------------------------------
# RAG Engine
# -------------------------------
class RAGEngine:
    def __init__(self):
        # Local Qdrant (no API needed)
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # Check collection
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
        except:
            names = []

        if COLLECTION not in names:
            self._init_collection()
            self._index_all()

    # ------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )

    # ------------------------------------
    def _index_file(self, path, data_type):
        if not os.path.exists(path):
            logger.error(f"CSV file missing: {path}")
            return

        df = pd.read_csv(path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            text = (
                f"{payload.get('name','')} "
                f"{payload.get('location','')} "
                f"{payload.get('description','')} "
                f"{data_type}"
            )

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
            print(f"Indexed {len(points)} items from {path}")

    # ------------------------------------
    def _index_all(self):
        print("Indexing data sources...")
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")

    # ------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        qv = self.embedder.encode(query)

        eco_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="eco_score",
                    range=models.Range(gte=min_eco_score)
                )
            ]
        )

        hits = self.client.search(
            collection_name=COLLECTION,
            query_vector=qv,
            query_filter=eco_filter,
            limit=top_k,
            with_payload=True
        )

        return [h.payload for h in hits]
