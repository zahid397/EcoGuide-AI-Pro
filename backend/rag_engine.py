import os
import pandas as pd
from uuid import uuid4
from qdrant_client import QdrantClient, models
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"

# ALL CSV FILES
CSV_HOTELS = os.path.join(DATA_DIR, "hotels.csv")
CSV_ACTIVITIES = os.path.join(DATA_DIR, "activities.csv")
CSV_PLACES = os.path.join(DATA_DIR, "places.csv")

VECTOR_DIM = 32   # small dimension to avoid errors


# ------------------------------------------------------------
# Light-Weight Keyword Based Embedding (Fastest + No Errors)
# ------------------------------------------------------------
class TinyEmbedder:
    """
    No torch, no transformer, no sentence-transformer.
    Pure keyword hashing → ALWAYS fixed 32-d vector.
    """
    def __init__(self, dim=VECTOR_DIM):
        self.dim = dim

    def encode(self, text: str):
        vec = [0] * self.dim
        for word in text.lower().split():
            vec[hash(word) % self.dim] += 1
        return vec


# ------------------------------------------------------------
# RAG ENGINE (Final Stable Version)
# ------------------------------------------------------------
class RAGEngine:
    def __init__(self):

        self.client = QdrantClient(path="qdrant_local")
        self.embedder = TinyEmbedder()

        # Ensure fresh collection
        try:
            self.client.get_collection(COLLECTION)
            print("🧹 Recreating Qdrant collection...")
            self.client.delete_collection(COLLECTION)
        except:
            pass

        self._init_collection()
        self._index_all()
        print("✅ RAG Engine Loaded Successfully")

    # --------------------------------------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIM,
                distance=models.Distance.COSINE
            )
        )
        print("📦 New Qdrant collection created.")

    # --------------------------------------------------------
    def _index_file(self, file_path, data_type):
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Missing file: {file_path}")
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
                f"{payload.get('description','')} "
                f"{data_type}"
            )

            vec = self.embedder.encode(text)  # ALWAYS 32-d

            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)
            print(f"📥 Indexed {len(points)} items → {data_type}")

    # --------------------------------------------------------
    def _index_all(self):
        print("📚 Indexing all CSV files...")
        self._index_file(CSV_HOTELS, "Hotel")
        self._index_file(CSV_ACTIVITIES, "Activity")
        self._index_file(CSV_PLACES, "Place")
        print("✅ Indexing complete!")

    # --------------------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):

        # Convert query → vector
        qvec = self.embedder.encode(query)

        def do_search(score):
            try:
                return self.client.search(
                    collection_name=COLLECTION,
                    query_vector=qvec,
                    query_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="eco_score",
                                range=models.Range(gte=score)
                            )
                        ]
                    ),
                    limit=top_k
                )
            except Exception as e:
                logger.error(f"Qdrant search error: {e}")
                return []

        # Try strict eco filter
        results = do_search(min_eco_score)

        # If none found → lower eco score
        if not results:
            print("⚠️ Lowering eco score to 7.0")
            results = do_search(7.0)

        # If STILL empty → return top hotels manually
        if not results:
            print("⚠️ Still empty → manual fallback results")
            df = pd.read_csv(CSV_HOTELS)
            df = df.sort_values("eco_score", ascending=False)
            return df.head(5).to_dict(orient="records")

        return [hit.payload for hit in results]
