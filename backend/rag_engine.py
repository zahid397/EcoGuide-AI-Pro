import os
import pandas as pd
from uuid import uuid4
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from utils.logger import logger


COLLECTION = "eco_travel_v3"
VECTOR_DIM = 384
DATA_DIR = "data"


# ------------------------------------------------------
# SAFE EMBEDDER (TF-IDF, No GPU, No Torch)
# ------------------------------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM, stop_words="english")
        self.fitted = False
        self.texts = []

    def fit(self, texts):
        if not texts:
            return
        self.texts = texts
        self.vectorizer.fit(texts)
        self.fitted = True

    def encode(self, text):
        if not self.fitted:
            self.fit([text])
        vec = self.vectorizer.transform([text]).toarray()[0]
        return vec.tolist()


# ------------------------------------------------------
# RAG ENGINE – QDRANT CLOUD (FINAL VERSION)
# ------------------------------------------------------
class RAGEngine:
    def __init__(self):

        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60,
            https=True,
            prefer_grpc=False
        )

        self.embedder = SafeEmbedder()

        collections = self.client.get_collections().collections
        names = [c.name for c in collections]

        # Always rebuild (safe)
        if COLLECTION not in names:
            self._init_collection()
            self._index_all()


    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=VECTOR_DIM, distance=models.Distance.COSINE),
        )
        logger.info(f"Recreated collection: {COLLECTION}")


    def _index_file(self, path, data_type):
        if not os.path.exists(path):
            logger.warning(f"Missing CSV: {path}")
            return

        df = pd.read_csv(path).fillna("")
        texts = []
        payloads = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            try:
                payload["eco_score"] = float(payload.get("eco_score", 0))
            except:
                payload["eco_score"] = 0.0

            text = f"{payload.get('name', '')} {payload.get('location', '')} {payload.get('description', '')} {data_type}"
            texts.append(text)
            payloads.append(payload)

        # Fit once per file
        self.embedder.fit(texts)

        points = []
        for txt, payload in zip(texts, payloads):
            vector = self.embedder.encode(txt)
            points.append(models.PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload=payload
            ))

        self.client.upsert(collection_name=COLLECTION, points=points)
        logger.info(f"Indexed {len(points)} items from {path}")


    def _index_all(self):
        logger.info("Indexing ALL CSV files...")
        self._index_file(f"{DATA_DIR}/hotels.csv", "Hotel")
        self._index_file(f"{DATA_DIR}/activities.csv", "Activity")
        self._index_file(f"{DATA_DIR}/places.csv", "Place")
        logger.info("Indexing DONE.")


    def search(self, query, top_k=10, min_eco_score=7.0):
        try:
            qvec = self.embedder.encode(query)

            eco_filter = models.Filter(
                must=[models.FieldCondition(
                    key="eco_score",
                    range=models.Range(gte=float(min_eco_score))
                )]
            )

            # Qdrant Cloud compatible
            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=qvec,
                limit=top_k,
                with_payload=True,
                filter=eco_filter
            )

            return [hit.payload for hit in results]

        except Exception as e:
            logger.exception(f"RAG Search failed: {e}")
            return []
