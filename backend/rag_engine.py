
import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

COLLECTION = "eco_travel_v3"

# ============================================================
# BASE FOLDER FOR CSV DATA
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")


# ============================================================
# SAFE TF-IDF EMBEDDER (ALWAYS RETURNS VECTOR SIZE = 384)
# ============================================================
class SafeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)
        self.fitted = False

    def fit_once(self, texts):
        """Fit only one time (first run)."""
        if not self.fitted:
            try:
                self.vectorizer.fit(texts)
                self.fitted = True
            except:
                pass

    def encode(self, text: str):
        """Always return vector = 384 dims."""
        if not self.fitted:
            self.fit_once([text])

        try:
            vec = self.vectorizer.transform([text]).toarray()
        except:
            self.fit_once([text])
            vec = self.vectorizer.transform([text]).toarray()

        emb = vec[0].tolist()

        # Padding if TF-IDF returned smaller vector
        if len(emb) < 384:
            emb = emb + [0.0] * (384 - len(emb))

        return emb[:384]


# ============================================================
# RAG ENGINE
# ============================================================
class RAGEngine:
    def __init__(self):
        """
        Use local Qdrant with unique folder to avoid file-locking in Streamlit Cloud.
        """
        storage_path = os.path.join(BASE_DIR, "..", "qdrant_local_store")

        self.client = QdrantClient(path=storage_path)
        self.embedder = SafeEmbedder()

        # Check collections
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
        except:
            names = []

        if COLLECTION not in names:
            logger.info("⚡ Creating new Qdrant collection...")
            self._init_collection()
            self._index_all()
        else:
            logger.info("✔ Qdrant collection already exists. Skipping indexing.")

    # --------------------------------------------------------------
    def _init_collection(self):
        """Create fresh vector DB collection."""
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )
        logger.info("✔ Collection Initialized.")

    # --------------------------------------------------------------
    def _index_file(self, csv_path: str, data_type: str):
        if not os.path.exists(csv_path):
            logger.error(f"❌ CSV missing: {csv_path}")
            return

        df = pd.read_csv(csv_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type

            # Ensure eco_score exists
            payload["eco_score"] = float(payload.get("eco_score", 0))

            # Build text for embedding
            text = (
                f"{payload.get('name', '')} "
                f"{payload.get('location', '')} "
                f"{payload.get('description', '')} "
                f"{data_type}"
            )

            vector = self.embedder.encode(text)

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            logger.info(f"✔ Indexed {len(points)} items from {csv_path}")

    # --------------------------------------------------------------
    def _index_all(self):
        logger.info("🚀 Indexing all data sources...")

        self._index_file(os.path.join(DATA_DIR, "hotels.csv"), "Hotel")
        self._index_file(os.path.join(DATA_DIR, "activities.csv"), "Activity")
        self._index_file(os.path.join(DATA_DIR, "places.csv"), "Place")

        logger.info("✨ All CSV files indexed successfully!")

    # --------------------------------------------------------------
    def search(self, query: str, top_k: int = 15, min_eco_score: float = 7.0):

        vector = self.embedder.encode(query)

        eco_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="eco_score",
                    range=models.Range(gte=min_eco_score)
                )
            ]
        )

        try:
            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=vector,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True,
            )

            if not results:
                return []

            formatted = [hit.payload for hit in results]
            return formatted

        except Exception as e:
            logger.exception(f"❌ RAG Search failed: {e}")
            return []
