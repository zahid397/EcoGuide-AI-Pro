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
# SAFE EMBEDDER (Torch/GPU Free)
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
            # First time → train on first text
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()
        return vec[0].tolist()


# ---------------------------------------------------------
class RAGEngine:
    def __init__(self):
        if not QDRANT_URL:
            raise EnvironmentError("❌ QDRANT_URL missing")

        try:
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=60,
                https=True,
                prefer_grpc=False
            )

            self.embedder = SafeEmbedder()

            # Check existing collections
            collections = self.client.get_collections().collections
            existing = [c.name for c in collections]

            if COLLECTION not in existing:
                self._init_collection()
                self._index_all()

        except Exception as e:
            logger.exception(f"Failed to initialize RAGEngine: {e}")
            raise


    # ---------------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            ),
        )
        print("✅ Collection initialized")


    # ---------------------------------------------------------
    def _safe_get(self, row, keys, default=0):
        """Safe getter to avoid missing column errors."""
        for k in keys:
            if k in row and pd.notna(row[k]):
                return row[k]
        return default


    # ---------------------------------------------------------
    def _index_file(self, file_path: str, dtype: str):
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Missing file: {file_path}")
            return

        try:
            df = pd.read_csv(file_path)

            # ensure eco_score exists (default = 7)
            if "eco_score" not in df.columns:
                df["eco_score"] = 7.5

            # ensure price column exists
            if "price" not in df.columns and "price_per_night" not in df.columns:
                df["price"] = 0

            points = []

            for _, row in df.iterrows():
                payload = row.to_dict()

                payload["data_type"] = dtype

                payload["cost"] = self._safe_get(
                    row, ["price_per_night", "price", "entry_fee"], 0
                )

                payload["cost_type"] = (
                    "per_night" if "price_per_night" in row else "one_time"
                )

                if "image_url" not in payload or pd.isna(payload["image_url"]):
                    payload["image_url"] = "https://placehold.co/100x100/grey"

                text = f"{dtype} - {payload.get('name','')} - {payload.get('description','')}"
                embedding = self.embedder.encode(text)

                points.append(
                    models.PointStruct(
                        id=str(uuid4()),
                        vector=embedding,
                        payload=payload
                    )
                )

            if points:
                self.client.upsert(COLLECTION, points, wait=True)
                print(f"✅ Indexed {len(points)} → {file_path}")

        except Exception as e:
            logger.exception(f"❌ Error indexing {file_path}: {e}")


    # ---------------------------------------------------------
    def _index_all(self):

        print("📦 Indexing ALL data files...")

        files = {
            "Hotel": "data/hotels.csv",
            "Activity": "data/activities.csv",
            "Place": "data/places.csv",
            "Food": "data/food.csv",
            "Nightlife": "data/nightlife.csv",
            "Shopping": "data/shopping.csv",
            "Transport": "data/transport.csv",
        }

        for dtype, fpath in files.items():
            self._index_file(fpath, dtype)

        print("🎉 ALL DATA INDEXED SUCCESSFULLY")


    # ---------------------------------------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):

        try:
            qvec = self.embedder.encode(query)

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
                query_vector=qvec,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True
            ) or []

            output = []
            for hit in results:
                p = dict(hit.payload or {})
                p["avg_rating"] = round(p.get("avg_rating", 4.0), 1)
                output.append(p)

            return output

        except Exception as e:
            logger.exception(f"❌ Search failed: {e}")
            return []
