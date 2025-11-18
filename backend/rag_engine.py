import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384   # fixed dimension


# ================================
# NEVER-BREAK SAFE EMBEDDER
# ================================
class SafeEmbedder:
    def __init__(self):
        try:
            self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        except:
            self.vectorizer = None

        self.fitted = False

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
            self.fitted = True
        except Exception as e:
            logger.error(f"Embedder fit failed: {e}")
            self.fitted = False

    def encode(self, text: str):
        # If embedding model not fitted → always return 384 zeros
        if not self.fitted:
            return [0.0] * VECTOR_DIM

        try:
            vec = self.vectorizer.transform([text]).toarray()[0]    # maybe < 384 dim
            vec = vec.tolist()

            # If vec smaller → pad to 384
            if len(vec) < VECTOR_DIM:
                vec = vec + [0.0] * (VECTOR_DIM - len(vec))

            # If vec bigger → trim to 384
            if len(vec) > VECTOR_DIM:
                vec = vec[:VECTOR_DIM]

            return vec

        except:
            # ANY error → return safe vector
            return [0.0] * VECTOR_DIM



# ================================
# RAG Engine
# ================================
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # Force-fit embedder on all CSV
        self._fit_embedder()

        # Always rebuild collection (fresh)
        self._init_collection()
        self._index_all()


    def _fit_embedder(self):
        all_texts = []

        for file in [self.csv_hotels, self.csv_activities, self.csv_places]:
            if os.path.exists(file):
                df = pd.read_csv(file)
                for _, row in df.iterrows():
                    t = f"{row.get('name','')} {row.get('description','')}"
                    all_texts.append(t)

        if not all_texts:
            all_texts = ["empty data fallback"]

        self.embedder.fit(all_texts)


    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )


    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"Missing CSV: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            txt = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vec = self.embedder.encode(txt)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)


    def _index_all(self):
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")


    def search(self, query, top_k=10, min_eco_score=7.0):
        vec = self.embedder.encode(query)

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=vec,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score)
                    )
                ]
            ),
            limit=top_k
        )

        return [hit.payload for hit in results]
