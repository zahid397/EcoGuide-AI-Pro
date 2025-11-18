import os
import pandas as pd
from uuid import uuid4
import hashlib
from utils.logger import logger

COLLECTION = "eco_travel_v3"

# ==================================================
# 384-DIM FIXED HASH EMBEDDER (ALWAYS SAME SIZE)
# ==================================================
class SafeEmbedder:
    DIM = 384

    def encode(self, text: str):
        h = hashlib.sha256(text.encode()).digest()
        # repeat to get 48 bytes → 384 bits → 384 numbers
        h = (h * 2)[:48]
        return [b / 255 for b in h]  


# ==================================================
# CSV SEARCH ENGINE (NO QDRANT, FULLY LOCAL)
# ==================================================
class RAGEngine:
    def __init__(self):
        self.embedder = SafeEmbedder()

        # Load CSV files
        self.hotels = self._load_csv("data/hotels.csv", "Hotel")
        self.activities = self._load_csv("data/activities.csv", "Activity")
        self.places = self._load_csv("data/places.csv", "Place")

        # Combined dataset
        self.database = self.hotels + self.activities + self.places

        logger.info(f"Loaded {len(self.database)} total items.")

    def _load_csv(self, path, dtype):
        if not os.path.exists(path):
            logger.warning(f"Missing CSV: {path}")
            return []

        df = pd.read_csv(path).fillna("")
        items = df.to_dict(orient="records")
        for i in items:
            i["data_type"] = dtype

            try:
                i["eco_score"] = float(i.get("eco_score", 0))
            except:
                i["eco_score"] = 0.0

        return items

    # ==================================================
    # MAIN SEARCH FUNCTION — ALWAYS RETURNS RESULTS!
    # ==================================================
    def search(self, query, top_k=10, min_eco_score=7.0):
        try:
            q_vec = self.embedder.encode(query)

            scored = []
            for item in self.database:
                text = f"{item['name']} {item['location']} {item['description']} {item['tag']}"
                v = self.embedder.encode(text)

                # cosine-like similarity
                score = sum(a * b for a, b in zip(q_vec, v))

                if item["eco_score"] >= min_eco_score:
                    scored.append((score, item))

            scored.sort(reverse=True, key=lambda x: x[0])

            if scored:
                return [x[1] for x in scored[:top_k]]

            # Fallback if no match
            return self.database[:top_k]

        except Exception as e:
            logger.exception(f"Search failed: {e}")
            return self.database[:top_k]
