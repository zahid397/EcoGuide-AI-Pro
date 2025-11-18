import os
import pandas as pd
import numpy as np
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
VECTOR_DIM = 384


# ======================================================
# SAFE TF-IDF EMBEDDER (ALWAYS 384-DIM, NO TORCH)
# ======================================================
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM, stop_words="english")
        self.is_fitted = False

    def fit(self, texts):
        if not texts:
            return
        self.vectorizer.fit(texts)
        self.is_fitted = True

    def encode(self, text: str):
        if not self.is_fitted:
            return [0.0] * VECTOR_DIM

        vector = self.vectorizer.transform([text]).toarray()[0]

        # pad to 384 (prevent crash)
        if len(vector) < VECTOR_DIM:
            vector = np.pad(vector, (0, VECTOR_DIM - len(vector)))

        return vector.tolist()


# ======================================================
# RAG ENGINE (FULLY FIXED)
# ======================================================
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # create or recreate collection
        if not self._collection_exists():
            self._init_collection()
            self._index_all()

    def _collection_exists(self):
        names = [c.name for c in self.client.get_collections().collections]
        return COLLECTION in names

    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            ),
        )
        print("✔ Recreated Qdrant collection")

    # ----------------------------------------------------
    # INDEX CSV
    # ----------------------------------------------------
    def _index_all(self):
        print("📦 Indexing CSV data...")
        texts = []

        files = [
            ("data/hotels.csv", "Hotel"),
            ("data/activities.csv", "Activity"),
            ("data/places.csv", "Place"),
        ]

        # First gather all text for embedder training
        for file, dtype in files:
            if os.path.exists(file):
                df = pd.read_csv(file).fillna("")
                for _, r in df.iterrows():
                    txt = f"{r.get('name')} {r.get('location')} {r.get('description')}"
                    texts.append(txt)

        # Fit embedder ONCE
        self.embedder.fit(texts)

        # Now index each file
        for file, dtype in files:
            self._index_file(file, dtype)

        print("✅ Indexing complete")

    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"Missing file: {file_path}")
            return

        df = pd.read_csv(file_path).fillna("")
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            txt = f"{payload.get('name')} {payload.get('location')} {payload.get('description')}"
            vec = self.embedder.encode(txt)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        self.client.upsert(COLLECTION, points)
        print(f"✔ Indexed {len(points)} → {file_path}")

    # ======================================================
    # UNIVERSAL SEARCH (WORKS ON ALL QDRANT VERSIONS)
    # ======================================================
    def search(self, query, top_k=10, min_eco_score=7.0):
        qvec = self.embedder.encode(query)

        try:
            # WORKS EVERYWHERE
            hits = self.client.search(
                collection_name=COLLECTION,
                query_vector=qvec,
                limit=top_k * 5,      # fetch more then filter
                with_payload=True
            )

            # manual eco filtering
            filtered = [
                h.payload for h in hits
                if float(h.payload.get("eco_score", 0)) >= min_eco_score
            ]

            return filtered[:top_k]

        except Exception as e:
            logger.exception(f"RAG search failed: {e}")
            return []
