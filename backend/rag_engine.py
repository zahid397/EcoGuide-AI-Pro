import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"

# ---------------------------------------------------------
# Safe TF-IDF Embedder (no GPU, no torch, no errors)
# ---------------------------------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)
        self._fitted = False

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
            self._fitted = True
        except Exception as e:
            logger.warning(f"Vectorizer fit failed: {e}")

    def encode(self, text: str):
        if not self._fitted:
            self.fit([text])
        try:
            vec = self.vectorizer.transform([text]).toarray()[0]
        except:
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()[0]
        return vec.tolist()


# ---------------------------------------------------------
# RAG ENGINE (WORKING VERSION)
# ---------------------------------------------------------
class RAGEngine:
    def __init__(self):
        # Local Qdrant — NO API Needed
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # CSV paths
        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # Force rebuild collection every time (so 384 size always matches)
        self._init_collection()
        self._index_all()

    # -----------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            )
        )
        print("✔️ Qdrant collection recreated → 384-dim vectors")

    # -----------------------------------------------------
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"CSV missing: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # Required fields for filtering
            payload["eco_score"] = float(payload.get("eco_score", 0))
            payload["price"] = payload.get("price") or payload.get("price_per_night") or 0

            # Fallback image
            if not payload.get("image_url"):
                payload["image_url"] = "https://placehold.co/100x100/green"

            # Embedding text
            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"

            vector = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"✔️ Indexed {len(points)} items from → {file_path}")

    # -----------------------------------------------------
    def _index_all(self):
        print("📦 Indexing all CSV files...")
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
        print("✅ Indexing complete.")

    # -----------------------------------------------------
    # FIXED SEARCH — uses search_points() (old Qdrant API)
    # -----------------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        vector = self.embedder.encode(query)

        try:
            results = self.client.search_points(
                collection_name=COLLECTION,
                query_vector=vector,
                limit=top_k,
                with_payload=True,
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="eco_score",
                            range=models.Range(gte=min_eco_score)
                        )
                    ]
                )
            )
        except Exception as e:
            print("❌ SEARCH ERROR:", e)
            return []

        output = []
        for hit in results:
            if hasattr(hit, "payload") and hit.payload:
                output.append(hit.payload)

        return output
