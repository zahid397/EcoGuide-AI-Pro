import os
import pandas as pd
from uuid import uuid4
from qdrant_client import QdrantClient, models
from utils.logger import logger
from sklearn.feature_extraction.text import TfidfVectorizer

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"


# ---------------------------
# Lightweight Safe Embedder
# ---------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)

    def fit(self, texts):
        try:
            self.vectorizer.fit(texts)
        except:
            pass

    def encode(self, text):
        try:
            vec = self.vectorizer.transform([text]).toarray()
        except:
            # If vectorizer not fitted yet – fit now
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()
        return vec[0].tolist()



# ---------------------------
# RAG ENGINE
# ---------------------------
class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        self.csv_hotels = os.path.join(DATA_DIR, "hotels.csv")
        self.csv_activities = os.path.join(DATA_DIR, "activities.csv")
        self.csv_places = os.path.join(DATA_DIR, "places.csv")

        self._init_collection()
        self._index_all()


    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            ),
        )


    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"Missing file: {file_path}")
            return

        df = pd.read_csv(file_path)

        # Fit TF-IDF on all rows
        texts = []
        for _, row in df.iterrows():
            txt = f"{row.get('name','')} {row.get('location','')} {row.get('description','')}"
            texts.append(txt)

        self.embedder.fit(texts)

        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vec = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload,
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"Indexed {len(points)} → {data_type}")


    def _index_all(self):
        print("Indexing CSV files...")
        self._index_file(self.csv_hotels, "Hotel")
        self._index_file(self.csv_activities, "Activity")
        self._index_file(self.csv_places, "Place")
        print("Indexing finished ✔")


    def search(self, query, top_k=10, min_eco_score=7.0):
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
        )

        return [hit.payload for hit in results]
