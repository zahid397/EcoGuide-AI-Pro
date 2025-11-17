import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"


# =====================================================
#  SAFE EMBEDDER (Always returns EXACT 384 dims)
# =====================================================
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)
        self.fitted = False

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
            self.fitted = True
        except:
            self.fitted = False

    def encode(self, text):
        try:
            if not self.fitted:
                self.fit([text])

            vec = self.vectorizer.transform([text]).toarray()[0]

            # 🔥 Force vector to exactly 384 dimensions
            if len(vec) < 384:
                vec = list(vec) + [0.0] * (384 - len(vec))
            else:
                vec = vec[:384]

            return vec

        except Exception:
            # Fallback (never crashes)
            return [0.0] * 384


# =====================================================
#  RAG ENGINE
# =====================================================
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")   # Local Qdrant
        self.embedder = SafeEmbedder()

        # Check collection exists
        try:
            colls = self.client.get_collections().collections
            names = [c.name for c in colls]
        except:
            names = []

        if COLLECTION not in names:
            self._init_collection()
            self._index_all()

    # ----------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )

    # ----------------------------------------
    def _index_file(self, path, data_type):
        if not os.path.exists(path):
            logger.error(f"Missing CSV: {path}")
            return

        df = pd.read_csv(path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # ECO SCORE FIX
            try:
                payload["eco_score"] = float(payload.get("eco_score", 0))
            except:
                payload["eco_score"] = 0.0

            # Build embedding text
            text = (
                f"{payload.get('name', '')} "
                f"{payload.get('location', '')} "
                f"{payload.get('description', '')} "
                f"{data_type}"
            )

            emb = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=emb,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"Indexed {len(points)} rows → {path}")

    # ----------------------------------------
    def _index_all(self):
        print("Indexing all CSV files...")

        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")
        self._index_file("data/nightlife.csv", "Nightlife")
        self._index_file("data/shopping.csv", "Shopping")
        self._index_file("data/food.csv", "Food")
        self._index_file("data/transport.csv", "Transport")

    # ----------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        query_vec = self.embedder.encode(query)

        eco_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="eco_score",
                    range=models.Range(gte=min_eco_score)
                )
            ]
        )

        try:
            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=query_vec,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

        output = []
        for r in results:
            payload = r.payload or {}
            output.append(payload)

        return output
