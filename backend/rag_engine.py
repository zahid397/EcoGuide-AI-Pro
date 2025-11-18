import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"


class RAGEngine:

    def __init__(self):
        # Local persistent storage
        self.client = QdrantClient(path="qdrant_local")

        # Simple lightweight embedder (NO TORCH)
        self.vectorizer = TfidfVectorizer(max_features=384)

        # Load all CSV text for vectorizer
        all_text = self._load_all_text()
        self.vectorizer.fit(all_text)

        # Rebuild collection ALWAYS (safe)
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
        )

        # Index data
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")


    # -------------------------------------------------------------
    def _load_all_text(self):
        texts = []
        for f in ["hotels.csv", "activities.csv", "places.csv"]:
            path = os.path.join(DATA_DIR, f)
            if not os.path.exists(path):
                continue
            df = pd.read_csv(path)
            for _, r in df.iterrows():
                t = f"{r.get('name','')} {r.get('location','')} {r.get('description','')}"
                texts.append(t)
        return texts


    # -------------------------------------------------------------
    def _embed(self, text):
        try:
            vec = self.vectorizer.transform([text]).toarray()[0]
            # pad if <384
            if len(vec) < 384:
                vec = list(vec) + [0.0] * (384 - len(vec))
            return vec
        except:
            return [0.0] * 384


    # -------------------------------------------------------------
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vec = self._embed(text)

            points.append(models.PointStruct(
                id=str(uuid4()),
                vector=vec,
                payload=payload
            ))

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)


    # -------------------------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):

        qvec = self._embed(query)

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score)
                    )
                ]
            ),
            limit=top_k,
            with_payload=True
        )

        return [hit.payload for hit in results]
