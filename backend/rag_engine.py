import os
import pandas as pd
from uuid import uuid4
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384    # fixed dimension


# ======================================
# SAFE EMBEDDER (ALWAYS RETURNS 384 DIM)
# ======================================
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        self.fitted = False

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
            self.fitted = True
        except Exception as e:
            logger.error(f"Embedder fit failed: {e}")

    def encode(self, text: str):
        if not self.fitted:
            # fallback vector if not fitted yet
            return [0.0] * VECTOR_DIM  

        vec = self.vectorizer.transform([text]).toarray()[0]
        return vec.tolist()   # ALWAYS 384-dim


# ======================================
# RAG Engine
# ======================================
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")

        self.embedder = SafeEmbedder()

        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # 1️⃣ Fit embedder first
        self._fit_embedder()

        # 2️⃣ Create collection every time (fresh rebuild)
        self._init_collection()

        # 3️⃣ Index CSV data
        self._index_all()


    # Fit embedder on all CSV text
    def _fit_embedder(self):
        all_texts = []

        for file in [self.csv_hotels, self.csv_activities, self.csv_places]:
            if os.path.exists(file):
                df = pd.read_csv(file)
                for _, row in df.iterrows():
                    all_texts.append(
                        f"{row.get('name','')} {row.get('description','')}"
                    )

        self.embedder.fit(all_texts)
        print("Embedder fitted on CSV files.")


    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )
        print("Qdrant collection recreated.")


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

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vector = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload
                )
            )

        self.client.upsert(collection_name=COLLECTION, points=points)
        print(f"Indexed {len(points)} → {data_type}")


    def _index_all(self):
        print("Indexing all CSV files...")
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
        print("Index complete!")


    # ===========================
    # SEARCH FUNCTION
    # ===========================
    def search(self, query, top_k=10, min_eco_score=7.0):
        vector = self.embedder.encode(query)

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=vector,
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
