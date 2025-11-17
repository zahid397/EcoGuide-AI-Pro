import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger
import shutil

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384  # fixed


# -----------------------------
# TF–IDF Embedder (NO TORCH)
# -----------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)

        # Fit on all CSV text
        print("Fitting TF-IDF vectorizer...")

        texts = []
        for file in os.listdir(DATA_DIR):
            if file.endswith(".csv"):
                df = pd.read_csv(os.path.join(DATA_DIR, file))
                for _, row in df.iterrows():
                    text = f"{row.get('name','')} {row.get('description','')} {row.get('location','')}"
                    texts.append(text)

        if texts:
            self.vectorizer.fit(texts)
            print(f"TF-IDF fitted on {len(texts)} items.")
        else:
            print("⚠️ No data to fit TF-IDF.")

    def encode(self, text):
        try:
            return self.vectorizer.transform([text]).toarray()[0].tolist()
        except:
            return [0.0] * VECTOR_DIM


# -----------------------------
# RAG Engine
# -----------------------------
class RAGEngine:
    def __init__(self):

        # Cleanup old Qdrant DB
        if os.path.exists("qdrant_local"):
            shutil.rmtree("qdrant_local")

        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        self._init_collection()
        self._index_all()
        print("✅ RAG Engine Ready")

    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            ),
        )

    def _index_file(self, file_path, data_type):

        if not os.path.exists(file_path):
            print(f"Missing: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))
            payload["image_url"] = payload.get("image_url", "https://placehold.co/100")

            # cost
            payload["cost"] = payload.get("price", payload.get("price_per_night", 0))
            payload["cost_type"] = payload.get("cost_type", "one_time")

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
            self.client.upsert(COLLECTION, points)
            print(f"Indexed {len(points)} → {data_type}")

    def _index_all(self):

        files = [
            ("hotels.csv", "Hotel"),
            ("activities.csv", "Activity"),
            ("places.csv", "Place"),
            ("food.csv", "Food"),
            ("shopping.csv", "Shopping"),
            ("transport.csv", "Transport"),
            ("nightlife.csv", "Nightlife")
        ]

        for file, dtype in files:
            self._index_file(os.path.join(DATA_DIR, file), dtype)

    def search(self, query, top_k=10, min_eco_score=7.0):

        qvec = self.embedder.encode(query)

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            with_payload=True,
            limit=top_k,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score)
                    )
                ]
            )
        )
        return [r.payload for r in results]
