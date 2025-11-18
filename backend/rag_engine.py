import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

# ---------------------------------
# CONSTANTS
# ---------------------------------
COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_SIZE = 384   # 🔥 FIXED DIMENSION


# ---------------------------------
# SAFE EMBEDDER (TF-IDF + ZERO-PAD)
# ---------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_SIZE)
        self.fitted = False

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
            self.fitted = True
        except:
            pass

    def encode(self, text: str):
        """Always returns 384-dim vector by padding/trimming."""
        if not self.fitted:
            self.fit([text])

        try:
            vec = self.vectorizer.transform([text]).toarray()[0]
        except:
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()[0]

        # ----- FIX: FORCE EXACT 384 DIM -----
        if len(vec) < VECTOR_SIZE:
            return list(vec) + [0.0] * (VECTOR_SIZE - len(vec))

        if len(vec) > VECTOR_SIZE:
            return list(vec[:VECTOR_SIZE])

        return vec.tolist()


# ---------------------------------
# RAG ENGINE
# ---------------------------------
class RAGEngine:
    def __init__(self):
        # Local Qdrant (no API needed)
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # CSV paths
        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # Always recreate collection when app restarts (cleanest)
        self._init_collection()
        self._index_all()

    # ---------------------------------
    def _init_collection(self):
        """Creates a clean collection with 384-dim vectors."""
        try:
            self.client.recreate_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )
            print("🔥 Qdrant collection created (384-dim, COSINE)")
        except Exception as e:
            logger.error(f"Failed creating Qdrant collection: {e}")

    # ---------------------------------
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"Missing file: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # Ensure eco_score is numeric
            try:
                payload["eco_score"] = float(payload.get("eco_score", 0))
            except:
                payload["eco_score"] = 0.0

            # Convert row to text for embedding
            text = (
                f"{payload.get('name','')} "
                f"{payload.get('location','')} "
                f"{payload.get('description','')} "
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
            print(f"✅ Indexed {len(points)} items from {file_path}")

    # ---------------------------------
    def _index_all(self):
        print("📦 Indexing hotels + activities + places...")
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
        print("🎉 All CSV indexing complete!")

    # ---------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        """Returns structured results reliably — no more empty output."""
        qvec = self.embedder.encode(query)

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score)
                    )
                ]
            ),
            limit=top_k,
            with_payload=True
        )

        output = []
        for hit in results:
            if hit.payload:
                output.append(hit.payload)

        return output
