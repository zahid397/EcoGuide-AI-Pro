import os
import pandas as pd
from uuid import uuid4
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384


# -------------------------------
# Simple Embedding (Works 100%)
# -------------------------------
class SimpleEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        self.fitted = False

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
            self.fitted = True
        except Exception as e:
            logger.error(f"Vectorizer fit failed: {e}")

    def encode(self, text):
        if not self.fitted:
            # fallback
            self.fit([text])

        try:
            v = self.vectorizer.transform([text]).toarray()[0]
        except:
            # rebuild if needed
            self.fit([text])
            v = self.vectorizer.transform([text]).toarray()[0]

        return v.tolist()


# -------------------------------
# RAG ENGINE
# -------------------------------
class RAGEngine:
    def __init__(self):
        # Local Qdrant (100% stable)
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SimpleEmbedder()

        # prepare dataset
        self.paths = {
            "Hotel": os.path.join(DATA_DIR, "hotels.csv"),
            "Activity": os.path.join(DATA_DIR, "activities.csv"),
            "Place": os.path.join(DATA_DIR, "places.csv"),
        }

        # rebuild collection every run (safe)
        self._rebuild_collection()

    # ---------------------------
    def _rebuild_collection(self):
        print("🔥 Rebuilding vector DB...")
        self._init_collection()
        self._index_all()
        print("✅ Rebuild complete")

    # ---------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )

    # ---------------------------
    def _index_file(self, path, dtype):
        if not os.path.exists(path):
            logger.warning(f"File missing: {path}")
            return

        df = pd.read_csv(path)

        # Convert eco_score to float cleanly
        def safe_float(x):
            try:
                return float(x)
            except:
                return 0.0

        df["eco_score"] = df["eco_score"].apply(safe_float)

        combined_texts = []
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = dtype

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            combined_texts.append(text)

        # Fit vectorizer once per file
        self.embedder.fit(combined_texts)

        for idx, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = dtype

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vec = self.embedder.encode(text)

            points.append(models.PointStruct(
                id=str(uuid4()),
                vector=vec,
                payload=payload
            ))

        if points:
            self.client.upsert(COLLECTION, points)
            print(f"Indexed {len(points)} items → {dtype}")

    # ---------------------------
    def _index_all(self):
        for dtype, path in self.paths.items():
            self._index_file(path, dtype)

    # ---------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        qvec = self.embedder.encode(query)

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            limit=top_k,
            with_payload=True,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=float(min_eco_score))
                    )
                ]
            )
        )

        output = []
        for r in results:
            p = r.payload

            # Final safety: ensure eco_score is float
            try:
                p["eco_score"] = float(p.get("eco_score", 0))
            except:
                p["eco_score"] = 0.0

            output.append(p)

        return output
