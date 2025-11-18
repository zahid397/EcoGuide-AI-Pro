import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384


# ======================================================
# TF-IDF Embedder (384-dim guaranteed)
# ======================================================
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        self.fitted = False

    def fit_on_all_csv(self, all_texts):
        """Fit vectorizer on all hotel/activity/place descriptions"""
        self.vectorizer.fit(all_texts)
        self.fitted = True
        print("✔️ TF-IDF fitted on full dataset")

    def encode(self, text: str):
        if not self.fitted:
            raise RuntimeError("❌ Embedder not fitted before encode()")

        vec = self.vectorizer.transform([text]).toarray()[0]

        # ENSURE ALWAYS 384-DIM
        if len(vec) != VECTOR_DIM:
            import numpy as np
            vec = np.pad(vec, (0, VECTOR_DIM - len(vec)))

        return vec.tolist()


# ======================================================
# RAG ENGINE
# ======================================================
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # FILES
        self.hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.activities = os.path.join(DATA_DIR, "activities.csv")
        self.places = os.path.join(DATA_DIR, "places.csv")

        # STEP 1 — Fit embedder BEFORE indexing
        self._fit_embedder()

        # STEP 2 — Recreate Qdrant collection
        self._init_collection()

        # STEP 3 — Index all CSV
        self._index_all()

    # --------------------------------------------------
    def _fit_embedder(self):
        texts = []

        for path in [self.hotels, self.activities, self.places]:
            if os.path.exists(path):
                df = pd.read_csv(path)
                for _, row in df.iterrows():
                    txt = f"{row.get('name','')} {row.get('location','')} {row.get('description','')}"
                    texts.append(txt)

        self.embedder.fit_on_all_csv(texts)

    # --------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )
        print("✔️ Qdrant collection recreated (384-dim)")

    # --------------------------------------------------
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            print(f"⚠️ Missing CSV: {file_path}")
            return

        df = pd.read_csv(file_path)
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

        self.client.upsert(collection_name=COLLECTION, points=points)
        print(f"✔️ Indexed {len(points)} → {file_path}")

    # --------------------------------------------------
    def _index_all(self):
        print("📦 Indexing all CSV files...")
        self._index_file(self.hotels, "Hotel")
        self._index_file(self.activities, "Activity")
        self._index_file(self.places, "Place")
        print("✅ Indexing completed.")

    # --------------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        qvec = self.embedder.encode(query)

        result = self.client.search_points(
            collection_name=COLLECTION,
            query_vector=qvec,
            limit=top_k,
            with_payload=True,
            filter=models.Filter(
                must=[models.FieldCondition(
                    key="eco_score",
                    range=models.Range(gte=min_eco_score)
                )]
            )
        )

        return [hit.payload for hit in result]
