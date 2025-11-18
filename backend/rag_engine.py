import os
import pandas as pd
from uuid import uuid4
from typing import List
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384


# -----------------------------------------------------
# Simple TF-IDF Embedder (No Torch, No GPU, No Errors)
# -----------------------------------------------------
class SimpleEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        self.is_fitted = False

    def fit(self, texts: List[str]):
        try:
            self.vectorizer.fit(texts)
            self.is_fitted = True
        except Exception as e:
            logger.error(f"Vectorizer fit failed: {e}")

    def encode(self, text: str):
        if not self.is_fitted:
            self.fit([text])

        try:
            vec = self.vectorizer.transform([text]).toarray()[0]
            return vec.tolist()
        except:
            return [0.0] * VECTOR_DIM


# -----------------------------------------------------
# RAG Engine (Qdrant Local Mode)
# -----------------------------------------------------
class RAGEngine:
    def __init__(self):
        # Local Qdrant DB inside Streamlit
        self.client = QdrantClient(path="qdrant_local")

        # Our embedder
        self.embedder = SimpleEmbedder()

        # Load CSVs
        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        # Always recreate collection (safe + resets bugs)
        self._init_collection()
        self._index_all()

    # -------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )
        print("Created Qdrant Collection (Local)")

    # -------------------------------------------------
    def _index_file(self, file_path: str, data_type: str):
        if not os.path.exists(file_path):
            logger.warning(f"Missing CSV file: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []
        training_texts = []

        # Prepare embedder training data
        for _, row in df.iterrows():
            txt = f"{row.get('name','')} {row.get('location','')} {row.get('description','')}"
            training_texts.append(txt)

        self.embedder.fit(training_texts)

        # Index each row
        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')} {data_type}"
            vec = self.embedder.encode(text)  # always 384-dim

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(COLLECTION, points)
            print(f"Indexed {len(points)} items from {file_path}")

    # -------------------------------------------------
    def _index_all(self):
        print("Indexing all CSV files...")
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
        print("Indexing DONE ✔")

    # -------------------------------------------------
    # 🔥 NEW SEARCH USING query_points() (NOT search())
    # -------------------------------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        try:
            qvec = self.embedder.encode(query)

            result = self.client.query_points(
                collection_name=COLLECTION,
                query=models.Query(
                    vector=qvec,
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="eco_score",
                                range=models.Range(gte=min_eco_score)
                            )
                        ]
                    )
                ),
                limit=top_k,
                with_payload=True
            )

            output = []
            for p in result.points:
                if p.payload:
                    output.append(p.payload)

            return output

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
