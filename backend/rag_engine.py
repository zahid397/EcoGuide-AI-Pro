import os
import pandas as pd
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from uuid import uuid4
from utils.logger import logger

# CONSTANTS
COLLECTION = "eco_travel_v3"
DATA_DIR = "data"
VECTOR_DIM = 384      # we MUST output exactly 384-dim vectors


# -----------------------------------------------------
# SAFE TF-IDF EMBEDDER (Always outputs EXACT 384-d vectors)
# -----------------------------------------------------
class SafeTFIDFEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=VECTOR_DIM)
        self.is_fitted = False

    def fit(self, texts):
        """Fit TF-IDF safely"""
        try:
            self.vectorizer.fit(texts)
            self.is_fitted = True
        except Exception as e:
            logger.error(f"Vectorizer fit failed: {e}")

    def encode(self, text: str):
        """Encode text and ALWAYS return EXACT 384-d vector"""
        if not self.is_fitted:
            # minimal fit if needed
            self.fit([text])

        try:
            vec = self.vectorizer.transform([text]).toarray()[0]
        except:
            vec = [0.0] * VECTOR_DIM

        # Force FIX — pad/truncate to exactly 384 dim
        if len(vec) < VECTOR_DIM:
            vec = list(vec) + [0.0] * (VECTOR_DIM - len(vec))
        else:
            vec = list(vec[:VECTOR_DIM])

        return vec


# -----------------------------------------------------
# RAG ENGINE
# -----------------------------------------------------
class RAGEngine:
    def __init__(self):
        # Local Qdrant inside project folder
        self.client = QdrantClient(path="qdrant_local")

        # embedder (fixed-dim)
        self.embedder = SafeTFIDFEmbedder()

        # load CSV paths
        self.hotels_csv = os.path.join(DATA_DIR, "hotels.csv")
        self.activities_csv = os.path.join(DATA_DIR, "activities.csv")
        self.places_csv = os.path.join(DATA_DIR, "places.csv")

        # FORCE REBUILD EVERY TIME (safe option)
        print("🔄 Rebuilding Qdrant collection...")
        self._init_collection()
        self._index_all()
        print("✅ Rebuild complete.\n")

    # -------------------------------------------------
    def _init_collection(self):
        """Create empty collection with correct vector size"""
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )

    # -------------------------------------------------
    def _index_file(self, file_path: str, data_type: str):
        """Index any CSV safely"""
        if not os.path.exists(file_path):
            logger.error(f"CSV missing: {file_path}")
            return

        df = pd.read_csv(file_path)
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))

            text = (
                f"{payload.get('name','')} "
                f"{payload.get('location','')} "
                f"{payload.get('description','')}"
            )

            # get 384-d vector
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
            print(f"Indexed {len(points)} items from {file_path}")

    # -------------------------------------------------
    def _index_all(self):
        """Index all CSV files"""
        print("📦 Indexing CSVs...")
        self._index_file(self.hotels_csv, "Hotel")
        self._index_file(self.activities_csv, "Activity")
        self._index_file(self.places_csv, "Place")
        print("📦 Indexing done.")

    # -------------------------------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        """Search eco items"""
        qvec = self.embedder.encode(query)

        try:
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
                with_payload=True
            )

            return [hit.payload for hit in results]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
