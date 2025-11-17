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
# SAFE EMBEDDER (No Torch, No GPU)
# ---------------------------------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)

    def fit(self, texts: List[str]):
        try:
            self.vectorizer.fit(texts)
        except Exception:
            pass

    def encode(self, text: str):
        try:
            vec = self.vectorizer.transform([text]).toarray()
        except Exception:
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()
        return vec[0].tolist()


# ---------------------------------------------------------
class RAGEngine:
    client: QdrantClient
    embedder: SafeEmbedder
    vector_size: int = 384

    def __init__(self) -> None:
        if not QDRANT_URL:
            raise EnvironmentError("QDRANT_URL is missing.")
        if not QDRANT_API_KEY:
            logger.warning("QDRANT_API_KEY missing! Required for Qdrant Cloud.")

        try:
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=60,
                https=True,
                prefer_grpc=False,
            )

            self.embedder = SafeEmbedder()

            # Check if collection exists
            try:
                collections = self.client.get_collections().collections
                existing = [c.name for c in collections]
            except Exception:
                existing = []

            if COLLECTION not in existing:
                print("Indexing data sources...")
                self._init_collection()
                self._index_all()

        except Exception as e:
            logger.exception(f"Failed to initialize RAGEngine: {e}")
            raise

    # -----------------------------------------------------
    def _init_collection(self) -> None:
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    # -----------------------------------------------------
    def _index_file(self, file_path: str, data_type: str) -> None:
        if not os.path.exists(file_path):
            logger.warning(f"{file_path} not found.")
            return

        try:
            df = pd.read_csv(file_path)
            points = []

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                # Normalize cost
                payload["cost"] = (
                    payload.get("price_per_night")
                    or payload.get("price")
                    or payload.get("entry_fee")
                    or 0
                )

                payload["cost_type"] = "per_night" if "price_per_night" in payload else "one_time"

                if "image_url" not in payload or not payload["image_url"]:
                    payload["image_url"] = "https://placehold.co/100x100/grey"

                # Create embedding
                text = f"{data_type} - {payload.get('name','')} - {payload.get('description','')}"
                embedding = self.embedder.encode(text)

                points.append(
                    models.PointStruct(
                        id=str(uuid4()),
                        vector=embedding,
                        payload=payload,
                    )
                )

            if points:
                self.client.upsert(
                    collection_name=COLLECTION,
                    points=points,
                    wait=True,
                )
                print(f"Indexed {len(points)} items → {file_path}")

        except Exception as e:
            logger.exception(f"Indexing failed for {file_path}: {e}")

    # -----------------------------------------------------
    def _index_all(self) -> None:
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")

    # -----------------------------------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        feedback_ratings = {}

        if os.path.exists(FEEDBACK_FILE):
            try:
                df = pd.read_csv(FEEDBACK_FILE)
                if not df.empty:
                    feedback_ratings = df.groupby("item_name")["rating"].mean().to_dict()
            except Exception:
                pass

        try:
            query_vector = self.embedder.encode(query)

            eco_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score),
                    )
                ]
            )

            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=query_vector,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True,
            ) or []

            output = []
            for hit in results:
                p = dict(hit.payload or {})
                name = p.get("name", "")
                p["avg_rating"] = round(feedback_ratings.get(name, 4.0), 1)
                output.append(p)

            return output

        except Exception as e:
            logger.exception(f"Qdrant search failed: {e}")
            return []
