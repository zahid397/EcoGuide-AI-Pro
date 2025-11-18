import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from utils.logger import logger
import random

# Load ENV
load_dotenv()

COLLECTION = "eco_travel_v3"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DATA_DIR = os.path.join(BASE_DIR, "data")  # /data folder path


class RAGEngine:
    def __init__(self):
        """Initialize Qdrant + Embedding model, but fallback-safe."""
        try:
            if not QDRANT_URL:
                logger.warning("⚠️ QDRANT_URL missing → Using in-memory DB.")
                self.client = QdrantClient(":memory:")
            else:
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=5,
                    https=True,
                    prefer_grpc=False
                )

            # embedding model
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

            # create collection only if Qdrant is fully connected
            try:
                if not self.client.collection_exists(COLLECTION):
                    logger.info("Creating new vector collection...")
                    self._index_all()
            except:
                logger.warning("⚠️ Skipping index creation (offline mode).")
        except Exception as e:
            logger.error(f"RAG init failed → {e}")
            self.client = None

    def _index_all(self):
        """Skip indexing in hackathon mode."""
        logger.info("Indexing skipped. Using CSV fallback only.")

    # ================================
    # MAIN SEARCH FUNCTION
    # ================================
    def search(self, query: str, top_k: int = 15, min_eco_score: float = 0.0):
        """
        Hybrid search:
        1) Try vector DB
        2) Fallback: CSV search
        """
        results = []

        # --------------- Vector Search ---------------
        if self.client:
            try:
                vector = self.embedder.encode(query).tolist()
                hits = self.client.search(
                    collection_name=COLLECTION,
                    query_vector=vector,
                    limit=top_k
                )
                results = [hit.payload for hit in hits]
            except Exception as e:
                logger.warning(f"Vector search failed → {e}")

        # --------------- CSV Fallback ----------------
        if not results:
            logger.warning("⚠️ Vector empty → Using CSV fallback")
            results = self._fallback_csv(query, min_eco_score)

        return results

    # ================================
    # CSV FALLBACK
    # ================================
    def _fallback_csv(self, query: str, min_eco_score: float) -> List[Dict[str, Any]]:
        data_files = {
            "hotels.csv": "Hotel",
            "activities.csv": "Activity",
            "places.csv": "Place"
        }

        combined = []

        for fname, dtype in data_files.items():
            fpath = os.path.join(DATA_DIR, fname)

            if not os.path.exists(fpath):
                logger.error(f"Missing CSV file: {fpath}")
                continue

            try:
                df = pd.read_csv(fpath)
                items = df.to_dict("records")

                for item in items:
                    # always include type
                    item["data_type"] = dtype

                    # safe numeric values
                    item["eco_score"] = float(item.get("eco_score", 5))
                    item["cost"] = float(
                        item.get("price_per_night", item.get("price", item.get("entry_fee", 0)))
                    )

                    # simple keyword matching
                    i_text = str(item).lower()
                    q = query.lower()

                    # location filter logic
                    if "dubai" in q and "dubai" not in i_text:
                        continue
                    if "abu dhabi" in q and "abu dhabi" not in i_text:
                        continue

                    # only add eco-friendly results
                    if item["eco_score"] >= min_eco_score:
                        combined.append(item)

            except Exception as e:
                logger.error(f"CSV parse error in {fname} → {e}")

        random.shuffle(combined)
        return combined[:15]
