import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from uuid import uuid4
from typing import List, Dict, Any, Optional
from utils.logger import logger

load_dotenv()
COLLECTION: str = "eco_travel_v3"
QDRANT_URL: Optional[str] = os.getenv("QDRANT_URL")
QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
FEEDBACK_FILE: str = "data/feedback.csv"


class RAGEngine:
    client: QdrantClient
    embedder: SentenceTransformer
    vector_size: int = 384

    def __init__(self) -> None:
        if not QDRANT_URL:
            raise EnvironmentError("QDRANT_URL environment variable not set.")
        if not QDRANT_API_KEY:
            logger.warning("QDRANT_API_KEY is missing. Required for Qdrant Cloud!")

        try:
            # --- Cloud-stable Qdrant Client ---
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=60,
                https=True,
                prefer_grpc=False
            )

            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

            # --- FIX: Replace deprecated has_collection() ---
            try:
                collections = self.client.get_collections().collections
                existing = [c.name for c in collections]
            except Exception:
                existing = []

            if COLLECTION not in existing:
                self._init_collection()
                self._index_all()

        except Exception as e:
            logger.exception(f"Failed to initialize RAGEngine: {e}")
            raise


    def _init_collection(self) -> None:
        """Initializes a new Qdrant collection."""
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )


    def _index_file(self, file_path: str, data_type: str) -> None:
        """Indexes a single CSV file."""
        if not os.path.exists(file_path):
            logger.warning(f"Warning: {file_path} not found. Skipping.")
            return

        try:
            df = pd.read_csv(file_path)
            points: List[models.PointStruct] = []

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                # Normalize pricing fields
                if "price_per_night" in payload:
                    payload["cost"] = payload["price_per_night"]
                    payload["cost_type"] = "per_night"
                elif "price" in payload:
                    payload["cost"] = payload["price"]
                    payload["cost_type"] = "one_time"
                elif "entry_fee" in payload:
                    payload["cost"] = payload["entry_fee"]
                    payload["cost_type"] = "one_time"
                else:
                    payload["cost"] = 0
                    payload["cost_type"] = "free"

                if "image_url" not in payload:
                    payload["image_url"] = (
                        "https://placehold.co/100x100/grey/white?text=Item"
                    )

                embedding = self.embedder.encode(f"{data_type}: {payload}").tolist()

                points.append(
                    models.PointStruct(
                        id=str(uuid4()), vector=embedding, payload=payload
                    )
                )

            if points:
                self.client.upsert(
                    collection_name=COLLECTION, points=points, wait=True
                )
                print(f"Indexed {len(points)} items from {file_path}")

        except Exception as e:
            logger.exception(f"Failed to index file {file_path}: {e}")


    def _index_all(self) -> None:
        """Indexes all CSV data sources."""
        print("Indexing all data sources...")
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")


    def search(
        self, query: str, top_k: int = 10, min_eco_score: float = 7.0
    ) -> List[Dict[str, Any]]:
        """Vector search with eco-filter + feedback weight."""

        feedback_ratings: Dict[str, float] = {}

        if os.path.exists(FEEDBACK_FILE):
            try:
                feedback_df = pd.read_csv(FEEDBACK_FILE)
                if not feedback_df.empty:
                    feedback_ratings = (
                        feedback_df.groupby("item_name")["rating"]
                        .mean()
                        .to_dict()
                    )
            except Exception:
                pass

        try:
            query_vector = self.embedder.encode(query).tolist()

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
            )

            final_items: List[Dict[str, Any]] = []
            for hit in results:
                payload = hit.payload or {}
                item_name = payload.get("name", "")
                payload["avg_rating"] = round(
                    feedback_ratings.get(item_name, 3.0), 1
                )
                final_items.append(payload)

            return final_items

        except Exception as e:
            logger.exception(f"Qdrant search failed: {e}")
            return []
