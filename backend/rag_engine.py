import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384


# -------------------------------------
# SAFE TF-IDF EMBEDDER
# -------------------------------------
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM, stop_words="english")
        self.is_fitted = False
        self.corpus = []

    def fit(self, texts):
        if texts:
            self.vectorizer.fit(texts)
            self.is_fitted = True
            self.corpus = texts

    def encode(self, text):
        if not self.is_fitted:
            self.fit([text])
        vec = self.vectorizer.transform([text]).toarray()[0]
        return vec.tolist()


# -------------------------------------
# RAG ENGINE (FORCE COMPUTE VERSION)
# -------------------------------------
class RAGEngine:
    def __init__(self):
        logger.info("🔥 FORCE COMPUTE MODE ENABLED — rebuilding database...")

        # Always start fresh
        self.client = QdrantClient(path="qdrant_local")
        self.embedder = SafeEmbedder()

        # Delete old collection every run
        try:
            self.client.delete_collection(COLLECTION)
        except:
            pass

        self._init_collection()
        self._index_all()

        logger.info("✅ Database rebuild completed successfully")

    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            ),
        )
        logger.info("Created new Qdrant collection.")

    def _index_all(self):
        logger.info("Indexing all CSV files...")

        csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

        all_texts = []
        row_batches = []

        for file in csv_files:
            path = os.path.join(DATA_DIR, file)

            df = pd.read_csv(path).fillna("")
            data_type = file.replace(".csv", "").capitalize()

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = data_type

                # force eco_score to float
                try:
                    payload["eco_score"] = float(payload.get("eco_score", 0))
                except:
                    payload["eco_score"] = 0.0

                text = (
                    f"{payload.get('name','')} "
                    f"{payload.get('location','')} "
                    f"{payload.get('description','')} "
                    f"{payload.get('tag','')} "
                    f"{data_type}"
                )

                all_texts.append(text)
                row_batches.append(payload)

        # Fit embedder once on all data
        self.embedder.fit(all_texts)

        # Upload all to Qdrant
        points = []
        for text, payload in zip(all_texts, row_batches):
            vec = self.embedder.encode(text)
            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(COLLECTION, points)
            logger.info(f"Indexed total {len(points)} items.")

    def search(self, query, top_k=10, min_eco_score=7.0):
        try:
            qvec = self.embedder.encode(query)

            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=qvec,
                limit=top_k,
                with_payload=True,
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="eco_score",
                            range=models.Range(gte=float(min_eco_score))
                        )
                    ]
                )
            )

            return [hit.payload for hit in results]

        except Exception as e:
            logger.exception(f"Search error: {e}")
            return []
