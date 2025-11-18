import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
import numpy as np

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384


# ======================================================
# TF-IDF Embedder (384 FIXED)
# ======================================================
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        self.fitted = False

    def fit_on_all_csv(self, texts):
        self.vectorizer.fit(texts)
        self.fitted = True
        print("✔ TF-IDF fitted on all CSV text")

    def encode(self, text):
        if not self.fitted:
            raise RuntimeError("Embedder not fitted!")

        vec = self.vectorizer.transform([text]).toarray()[0]

        # Always enforce 384-dim
        if len(vec) < VECTOR_DIM:
            vec = np.pad(vec, (0, VECTOR_DIM - len(vec)))
        return vec.tolist()


# ======================================================
# RAG ENGINE — using query_points() for max compatibility
# ======================================================
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # 1) Fit embedder first
        self._fit_embedder()

        # 2) Reset Qdrant collection
        self._init_collection()

        # 3) Index CSV files
        self._index_all()


    # --------------------------------------------------
    def _fit_embedder(self):
        all_texts = []
        for file in [self.csv_hotels, self.csv_activities, self.csv_places]:
            if os.path.exists(file):
                df = pd.read_csv(file)
                for _, row in df.iterrows():
                    t = f"{row.get('name','')} {row.get('location','')} {row.get('description','')}"
                    all_texts.append(t)

        self.embedder.fit_on_all_csv(all_texts)


    # --------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            ),
        )
        print("✔ Qdrant collection recreated")


    # --------------------------------------------------
    def _index_file(self, path, data_type):
        if not os.path.exists(path):
            print(f"⚠ Missing CSV: {path}")
            return

        df = pd.read_csv(path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vec = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"✔ Indexed {len(points)} rows from {path}")


    # --------------------------------------------------
    def _index_all(self):
        print("📦 Indexing CSV files...")
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
        print("✅ Finished indexing")


    # --------------------------------------------------
    # FINAL FIX: search using query_points()
    # --------------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        qvec = self.embedder.encode(query)

        result = self.client.query_points(
            collection_name=COLLECTION,
            query=qvec,
            limit=top_k,
            with_payload=True,
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score)
                    )
                ]
            )
        )

        return [res.payload for res in result.points]
