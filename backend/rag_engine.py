import os
import shutil
import pandas as pd
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_SIZE = 384


# ------------------------
# EMBEDDER (384-D)
# ------------------------
class SafeEmbedder:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedder loaded (384-d vector).")

    def encode(self, text: str):
        return self.model.encode(text).tolist()


# ------------------------
# RAG ENGINE
# ------------------------
class RAGEngine:
    def __init__(self):

        # --- HARD RESET: delete old DB ---
        if os.path.exists("qdrant_local"):
            print("🧹 Cleaning old Qdrant DB...")
            shutil.rmtree("qdrant_local")

        # fresh local DB
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # recreate empty collection
        self._init_collection()

        # index all supported CSV datasets
        self._index_all()

        print("✅ RAG Engine ready.")


    # recreate collection fresh
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )
        print("Created fresh collection.")


    # index a single CSV
    def _index_file(self, filename, data_type):

        path = os.path.join(DATA_DIR, filename)

        if not os.path.exists(path):
            print(f"⚠️ Skipped missing CSV: {path}")
            return

        df = pd.read_csv(path)
        points = []

        for _, row in df.iterrows():

            payload = row.to_dict()

            # ensure mandatory fields exist
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))
            payload["image_url"] = payload.get("image_url", "https://placehold.co/100")

            # cost field normalization
            payload["cost"] = (
                payload.get("price_per_night")
                or payload.get("price")
                or payload.get("entry_fee")
                or 0
            )
            payload["cost_type"] = payload.get("cost_type", "one_time")

            # text for embedding
            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"

            embedding = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=embedding,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(COLLECTION, points)
            print(f"Indexed {len(points)} items → {filename}")


    # index all CSVs from your data folder
    def _index_all(self):
        print("📦 Indexing all CSV files...")

        files = [
            ("hotels.csv", "Hotel"),
            ("activities.csv", "Activity"),
            ("places.csv", "Place"),
            ("food.csv", "Food"),
            ("nightlife.csv", "Nightlife"),
            ("shopping.csv", "Shopping"),
            ("transport.csv", "Transport"),
        ]

        for file, dtype in files:
            self._index_file(file, dtype)

        print("✅ All CSV indexing done!")


    # semantic search
    def search(self, query: str, top_k=10, min_eco_score=7.0):

        qvec = self.embedder.encode(query)

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
            with_payload=True,
        )

        return [r.payload for r in results]
