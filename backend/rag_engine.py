import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"


# ---------------------- TF-IDF Embedder ----------------------
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
            v = self.vectorizer.transform([text]).toarray()
        except:
            self.fit([text])
            v = self.vectorizer.transform([text]).toarray()
        return v[0].tolist()


# ---------------------- RAG Engine ----------------------
class RAGEngine:
    def __init__(self):
        # LOCAL QDRANT (Streamlit safe!)
        self.client = QdrantClient(path="qdrant_local")

        self.embedder = SafeEmbedder()

        self._ensure_collection()
        self._index_all()


    # Create collection if missing
    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
        except:
            names = []

        if COLLECTION not in names:
            self.client.recreate_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )


    # ------------------ Indexing ------------------
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.error(f"❌ Missing CSV: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            # TEXT FOR EMBEDDING
            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')} {data_type}"

            embed = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=embed,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(COLLECTION, points)
            print(f"Indexed {len(points)} items from {file_path}")


    def _index_all(self):
        print("Indexing data...")
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")


    # ------------------ SEARCH ------------------
    def search(self, query, top_k=20, min_eco_score=7.0):

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
                with_payload=True
            ) or []

            return [hit.payload for hit in results]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
