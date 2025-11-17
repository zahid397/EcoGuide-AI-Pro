import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"

# BASE DIR for CSV paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")


# -------------------------------
# Safe TF-IDF Embedder
# -------------------------------
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
            self.fit([text])
            vec = self.vectorizer.transform([text]).toarray()

        v = vec[0].tolist()
        if len(v) < 384:
            v += [0] * (384 - len(v))

        return v


# -------------------------------
# RAG Engine
# -------------------------------
class RAGEngine:
    def __init__(self):
        storage_path = f"qdrant_store_{uuid4().hex}"
        self.client = QdrantClient(path=storage_path)
        self.embedder = SafeEmbedder()

        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
        except:
            names = []

        if COLLECTION not in names:
            self._init_collection()
            self._index_all()

    # ------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )

    # ------------------------------------
    def _index_file(self, path, data_type):
        path = os.path.abspath(path)

        if not os.path.exists(path):
            logger.error(f"CSV file missing: {path}")
            return

        df = pd.read_csv(path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')} {data_type}"
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
            print(f"Indexed {len(points)} → {os.path.basename(path)}")

    # ------------------------------------
    def _index_all(self):
        print("Indexing all CSV data...")

        self._index_file(os.path.join(DATA_DIR, "hotels.csv"), "Hotel")
        self._index_file(os.path.join(DATA_DIR, "activities.csv"), "Activity")
        self._index_file(os.path.join(DATA_DIR, "places.csv"), "Place")

        print("Indexing complete.")

    # ------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        qvec = self.embedder.encode(query)

        eco_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="eco_score",
                    range=models.Range(gte=float(min_eco_score))
                )
            ]
        )

        try:
            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=qvec,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True
            )
        except Exception as e:
            logger.exception(f"Search failed: {e}")
            return []

        output = []
        for r in results:
            output.append(dict(r.payload or {}))

        return output
