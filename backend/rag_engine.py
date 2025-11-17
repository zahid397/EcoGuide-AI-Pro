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
# SAFE EMBEDDER (TF-IDF based)
# ---------------------------------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)
        self.fitted = False

    def fit(self, texts: List[str]):
        try:
            self.vectorizer.fit(texts)
            self.fitted = True
        except Exception as e:
            logger.exception(f"Embedder fit failed: {e}")

    def encode(self, text: str):
        if not self.fitted:
            # Prevent empty vocabulary error
            self.fit([text])

        try:
            return self.vectorizer.transform([text]).toarray()[0].tolist()
        except:
            return [0.0] * 384


# ---------------------------------------------------------
class RAGEngine:
    def __init__(self):
        if not QDRANT_URL:
            raise EnvironmentError("QDRANT_URL missing")
        if not QDRANT_API_KEY:
            logger.warning("QDRANT_API_KEY missing")

        self.client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=60,
            https=True,
            prefer_grpc=False
        )

        self.embedder = SafeEmbedder()

        # check collection exist
        try:
            existing = [c.name for c in self.client.get_collections().collections]
        except:
            existing = []

        if COLLECTION not in existing:
            self._init_collection()
            self._index_all()


    # ---------------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            ),
        )


    # ---------------------------------------------------------
    def _index_file(self, file_path: str, data_type: str):
        if not os.path.exists(file_path):
            logger.warning(f"{file_path} not found")
            return

        try:
            df = pd.read_csv(file_path)
            texts_for_fit = []

            points = []

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                # standardize cost fields
                payload["cost"] = (
                    payload.get("price_per_night") or
                    payload.get("price") or
                    payload.get("entry_fee") or 0
                )

                payload["cost_type"] = (
                    "per_night" if "price_per_night" in payload else "one_time"
                )

                if "image_url" not in payload:
                    payload["image_url"] = "https://placehold.co/100x100/grey"

                text = f"{data_type} {payload.get('name','')} {payload.get('description','')}"
                texts_for_fit.append(text)

            # FIRST fit the embedder
            self.embedder.fit(texts_for_fit)

            # THEN generate embeddings
            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                text = f"{data_type} {payload.get('name','')} {payload.get('description','')}"
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
                print(f"Indexed {len(points)} items from {file_path}")

        except Exception as e:
            logger.exception(f"Indexing failed for {file_path}: {e}")


    # ---------------------------------------------------------
    def _index_all(self):
        print("Indexing all CSV files...")
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")


    # ---------------------------------------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        try:
            query_vector = self.embedder.encode(query)

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
                query_vector=query_vector,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True
            ) or []

            output = []
            for hit in results:
                p = dict(hit.payload or {})
                p["avg_rating"] = 4.3  # default
                output.append(p)

            return output

        except Exception as e:
            logger.exception(f"Search failed: {e}")
            return []
