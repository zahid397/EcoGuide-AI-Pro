import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384   # fixed vector dimension


# --------------------------------------------------------
# Stable TF-IDF Embedder (always 384-dim)
# --------------------------------------------------------
class TFIDFEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        self.is_fitted = False

    def fit(self, texts):
        if not self.is_fitted and len(texts) > 0:
            self.vectorizer.fit(texts)
            self.is_fitted = True

    def encode(self, text):
        try:
            vec = self.vectorizer.transform([text]).toarray()[0]
        except:
            vec = [0.0] * VECTOR_DIM
        return vec.tolist()


# --------------------------------------------------------
#                  RAG ENGINE (NO TORCH)
# --------------------------------------------------------
class RAGEngine:
    def __init__(self):
        # local Qdrant
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = TFIDFEmbedder()

        # data files
        self.hotels = f"{DATA_DIR}/hotels.csv"
        self.activities = f"{DATA_DIR}/activities.csv"
        self.places = f"{DATA_DIR}/places.csv"

        # -------- Fit TF-IDF on all CSV text --------
        all_texts = []
        for path in [self.hotels, self.activities, self.places]:
            if os.path.exists(path):
                df = pd.read_csv(path)
                for _, row in df.iterrows():
                    all_texts.append(
                        f"{row.get('name','')} {row.get('location','')} {row.get('description','')}"
                    )

        self.embedder.fit(all_texts)

        # -------- Clean recreate collection --------
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )

        # -------- Index data --------
        self._index_all()


    # -----------------------------------------------------
    def _index_file(self, path, data_type):
        if not os.path.exists(path):
            logger.warning(f"CSV missing: {path}")
            return

        df = pd.read_csv(path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # text for embedding
            text = (
                f"{payload.get('name','')} "
                f"{payload.get('location','')} "
                f"{payload.get('description','')}"
            )

            vec = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"Indexed {len(points)} rows from {path}")


    # -----------------------------------------------------
    def _index_all(self):
        print("Indexing CSV files...")
        self._index_file(self.hotels, "Hotel")
        self._index_file(self.activities, "Activity")
        self._index_file(self.places, "Place")
        print("✔ Done indexing")


    # -----------------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        qvec = self.embedder.encode(query)

        results = self.client.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            limit=top_k,
            query_filter=models.Filter(
                must=[models.FieldCondition(
                    key="eco_score",
                    range=models.Range(gte=min_eco_score)
                )]
            )
        )

        return [hit.payload for hit in results]
