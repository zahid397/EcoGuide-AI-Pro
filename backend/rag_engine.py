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

# IMPORTANT → Cloud Path Fix
DATA_PATH = "/mount/src/ecoguide-ai-pro/data"


# --------------------------------------------------------------------
# SAFE EMBEDDER (NO Torch, NO GPU Needed)
# --------------------------------------------------------------------
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


# --------------------------------------------------------------------
class RAGEngine:
    def __init__(self):
        if not QDRANT_URL:
            raise EnvironmentError("QDRANT_URL is missing!")

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

        # Create + Index if missing
        if COLLECTION not in existing:
            self._init_collection()
            self._index_all()

    # ----------------------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            ),
        )

    # ---------------------------------------------------------------
        def _index_all(self) -> None:
    print("Indexing data sources...")

    base = "/mount/src/ecoguide-ai-pro/data"

    files = [
        ("hotels.csv", "Hotel"),
        ("activities.csv", "Activity"),
        ("places.csv", "Place"),
        ("food.csv", "Food"),
        ("nightlife.csv", "Nightlife"),
        ("shopping.csv", "Shopping"),
        ("transport.csv", "Transport"),
    ]

    loaded_count = 0

    for file, dtype in files:
        path = os.path.join(base, file)

        if os.path.exists(path):
            print(f"Indexing {path}...")
            self._index_file(path, dtype)
            loaded_count += 1
        else:
            print(f"❌ MISSING FILE → {path}")

    print(f"✔ Total datasets indexed: {loaded_count}")

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # cost mapping
            payload["cost"] = (
                payload.get("price_per_night") or
                payload.get("price") or
                payload.get("entry_fee") or 0
            )

            payload["cost_type"] = (
                "per_night" if "price_per_night" in payload else "one_time"
            )

            # Ensure image URL exists
            if "image_url" not in payload or str(payload["image_url"]) == "nan":
                payload["image_url"] = "https://placehold.co/100x100/grey"

            # Create embedding
            text = f"{payload.get('name','')} {payload.get('description','')}"
            vector = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(
                collection_name=COLLECTION,
                points=points,
                wait=True
            )
            print(f"Indexed {len(points)} rows from {file_path}")

    # ----------------------------------------------------------------
    def _index_all(self):
        print("Indexing all CSV files from data/...")

        self._index_file(f"{DATA_PATH}/hotels.csv", "Hotel")
        self._index_file(f"{DATA_PATH}/activities.csv", "Activity")
        self._index_file(f"{DATA_PATH}/places.csv", "Place")

        print("Indexing Completed ✔")

    # ----------------------------------------------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        try:
            vector = self.embedder.encode(query)

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
                query_vector=vector,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True,
            ) or []

            output = []
            for hit in results:
                p = dict(hit.payload or {})
                output.append(p)

            return output

        except Exception as e:
            logger.exception(f"Search failed → {e}")
            return []
