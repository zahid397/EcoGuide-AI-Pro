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


# ---------------------------
# SAFE EMBEDDER (NO TORCH)
# ---------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)
        self.is_fitted = False

    def fit_on_texts(self, texts: List[str]):
        try:
            self.vectorizer.fit(texts)
            self.is_fitted = True
        except Exception:
            pass

    def encode(self, text: str):
        if not self.is_fitted:
            self.fit_on_texts([text])
        vec = self.vectorizer.transform([text]).toarray()[0]
        return vec.tolist()


# ---------------------------
# RAG ENGINE
# ---------------------------
class RAGEngine:
    client: QdrantClient
    embedder: SafeEmbedder
    vector_size: int = 384

    def __init__(self):
        if not QDRANT_URL:
            raise EnvironmentError("❌ QDRANT_URL is missing.")
        if not QDRANT_API_KEY:
            logger.warning("⚠ QDRANT_API_KEY is missing (required for Qdrant Cloud).")

        try:
            # Cloud-safe client
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                https=True,
                timeout=60,
                prefer_grpc=False
            )

            self.embedder = SafeEmbedder()

            # Check existing collections
            try:
                collections = self.client.get_collections().collections
                existing = [c.name for c in collections]
            except Exception:
                existing = []

            if COLLECTION not in existing:
                self._init_collection()
                self._index_all()

        except Exception as e:
            logger.exception(f"RAGEngine initialization failed: {e}")
            raise


    # ---------------------------
    # INIT COLLECTION
    # ---------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )


    # ---------------------------
    # INDEX CSV FILE
    # ---------------------------
    def _index_file(self, file_path: str, data_type: str):
        if not os.path.exists(file_path):
            logger.warning(f"⚠ Missing: {file_path}")
            return

        try:
            df = pd.read_csv(file_path)
            points = []
            full_texts = []   # For TF-IDF fitting

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                payload["cost"] = (
                    payload.get("price_per_night")
                    or payload.get("price")
                    or payload.get("entry_fee")
                    or 0
                )

                payload["cost_type"] = (
                    "per_night" if "price_per_night" in payload else "one_time"
                )

                if "image_url" not in payload:
                    payload["image_url"] = "https://placehold.co/100x100/grey"

                text = f"{payload.get('name','')} {payload.get('description','')}"
                full_texts.append(text)

            # Fit embedder on entire file text
            if full_texts:
                self.embedder.fit_on_texts(full_texts)

            # Now encode + upload
            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                text = f"{payload.get('name','')} {payload.get('description','')}"
                vector = self.embedder.encode(text)

                points.append(
                    models.PointStruct(
                        id=str(uuid4()),
                        vector=vector,
                        payload=payload,
                    )
                )

            if points:
                self.client.upsert(collection_name=COLLECTION, points=points, wait=True)
                print(f"✔ Indexed {len(points)} entries from {file_path}")

        except Exception as e:
            logger.exception(f"❌ Indexing failed for {file_path}: {e}")


    # ---------------------------
    # INDEX ALL DATA
    # ---------------------------
    def _index_all(self):
        print("🚀 Indexing all CSV data...")
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")
        print("✅ All data indexed!")


    # ---------------------------
    # SEARCH ENGINE
    # ---------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        # Load user feedback
        feedback = {}
        if os.path.exists(FEEDBACK_FILE):
            try:
                df = pd.read_csv(FEEDBACK_FILE)
                if not df.empty:
                    feedback = df.groupby("item_name")["rating"].mean().to_dict()
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
            )

            final = []
            for hit in results:
                payload = hit.payload
                name = payload.get("name", "")
                payload["avg_rating"] = round(feedback.get(name, 4.0), 1)
                final.append(payload)

            return final

        except Exception as e:
            logger.exception(f"❌ Qdrant search failed: {e}")
            return []
