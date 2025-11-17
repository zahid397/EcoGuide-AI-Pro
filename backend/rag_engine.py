import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from uuid import uuid4
from typing import List, Dict, Any, Optional
from utils.logger import logger
from sklearn.feature_extraction.text import TfidfVectorizer

load_dotenv()

COLLECTION = "eco_travel_v3"

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

FEEDBACK_FILE = "data/feedback.csv"


# ---------------------------------------------------------
# SAFEST EMBEDDER (No torch, No GPU)
# ---------------------------------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)

    def fit(self, texts: List[str]):
        try:
            self.vectorizer.fit(texts)
        except:
            pass

    def encode(self, text: str):
        try:
            vec = self.vectorizer.transform([text]).toarray()
        except:
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()
        return vec[0].tolist()


# ---------------------------------------------------------
class RAGEngine:
    def __init__(self):
        if not QDRANT_URL:
            raise EnvironmentError("QDRANT_URL missing.")

        try:
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                prefer_grpc=False,
                https=True,
                timeout=60
            )

            self.embedder = SafeEmbedder()

            existing = []
            try:
                collections = self.client.get_collections().collections
                existing = [c.name for c in collections]
            except:
                pass

            if COLLECTION not in existing:
                self._init_collection()
                self._index_all()

        except Exception as e:
            logger.exception(f"RAGEngine init failed: {e}")
            raise


    # -----------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            ),
        )


    # -----------------------------------------------------
    def _index_file(self, file_path: str, data_type: str):
        if not os.path.exists(file_path):
            logger.warning(f"Missing file: {file_path}")
            return

        try:
            df = pd.read_csv(file_path)
            points = []

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                payload["cost"] = (
                    payload.get("price_per_night") or
                    payload.get("price") or
                    payload.get("entry_fee") or 0
                )

                payload["cost_type"] = (
                    "per_night" if "price_per_night" in payload else "one_time"
                )

                if "image_url" not in payload:
                    payload["image_url"] = "https://placehold.co/100x100"

                embedding = self.embedder.encode(
                    f"{payload.get('name', '')} {payload.get('description', '')} {payload.get('location', '')}"
                )

                points.append(
                    models.PointStruct(
                        id=str(uuid4()),
                        vector=embedding,
                        payload=payload
                    )
                )

            if points:
                self.client.upsert(
                    collection_name=COLLECTION,
                    points=points,
                    wait=True
                )
                print(f"Indexed: {file_path} → {len(points)} items")

        except Exception as e:
            logger.exception(f"Index error in {file_path}: {e}")


    # -----------------------------------------------------
    def _index_all(self):
        print("Indexing CSV files...")

        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/food.csv", "Food")
        self._index_file("data/places.csv", "Place")
        self._index_file("data/nightlife.csv", "Nightlife")
        self._index_file("data/shopping.csv", "Shopping")
        self._index_file("data/transport.csv", "Transport")

        print("✔ All CSV files indexed.")


    # -----------------------------------------------------
    def search(self, query: str, top_k=15, min_eco_score=7.0):
        try:
            query_vec = self.embedder.encode(query)

            eco_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score)
                    )
                ]
            )

            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=query_vec,
                query_filter=eco_filter,
                with_payload=True,
                limit=top_k
            ) or []

            cleaned = []
            for hit in results:
                p = dict(hit.payload or {})
                cleaned.append(p)

            return cleaned

        except Exception as e:
            logger.exception(f"Search failed: {e}")
            return []
