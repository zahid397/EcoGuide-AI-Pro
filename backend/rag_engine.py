import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIMENSION = 384


class RAGEngine:
    def __init__(self):
        # Local Qdrant
        self.client = QdrantClient(path="qdrant_local")

        # Load embedder
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # CSV files
        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # Always recreate & reindex for clean data
        print("Recreating collection...")
        self._init_collection()
        self._index_all()
        print("RAGEngine Ready ✔")

    # ------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )

    # ------------------------
    def _index_file(self, path, data_type):
        if not os.path.exists(path):
            logger.error(f"Missing: {path}")
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
                f"{payload.get('description','')}"
            )

            vector = self.embedder.encode(text).tolist()

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload,
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"Indexed {len(points)} → {data_type}")

    # ------------------------
    def _index_all(self):
        print("Indexing all CSV data...")
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
        print("Index complete ✔")

    # ------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        vector = self.embedder.encode(query).tolist()

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score),
                    )
                ]
            ),
            limit=top_k,
        )

        return [hit.payload for hit in results]
