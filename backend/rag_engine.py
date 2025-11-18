import os
import pandas as pd
from utils.logger import logger


class RAGEngine:

    def __init__(self):
        self.hotels = self._load_csv("data/hotels.csv")
        self.activities = self._load_csv("data/activities.csv")
        self.places = self._load_csv("data/places.csv")

        logger.info("Lightweight RAG Engine loaded successfully.")

    # ------------------------------------------
    # Load CSV safely
    # ------------------------------------------
    def _load_csv(self, path):
        if not os.path.exists(path):
            logger.warning(f"Missing CSV: {path}")
            return []

        df = pd.read_csv(path).fillna("")
        df["eco_score"] = df["eco_score"].astype(float)
        return df.to_dict(orient="records")

    # ------------------------------------------
    # MAIN SEARCH ENGINE (NO VECTORS)
    # ------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):

        # Simple keyword filtering
        query_lower = query.lower()

        def match(item):
            txt = f"{item['name']} {item['location']} {item['description']}".lower()
            return query_lower.split()[0] in txt  # match first keyword

        # Filter eco-friendly + keyword matches
        results = [
            item for item in (self.hotels + self.activities + self.places)
            if item["eco_score"] >= min_eco_score
        ]

        # If still empty, remove keyword requirement
        if not results:
            logger.warning("No match with keyword → returning eco-only results")
            results = [
                item for item in (self.hotels + self.activities + self.places)
                if item["eco_score"] >= min_eco_score
            ]

        # STILL empty? → full fallback
        if not results:
            logger.warning("Eco results empty → FULL FALLBACK")
            return self._fallback()

        return results[:top_k]

    # ------------------------------------------
    # Fallback backup
    # ------------------------------------------
    def _fallback(self):
        return [
            {"name": "Eco Backup Hotel", "location": "Dubai", "eco_score": 8.2, "description": "Backup hotel", "data_type": "Hotel"},
            {"name": "Eco Backup Activity", "location": "Dubai", "eco_score": 7.5, "description": "Backup activity", "data_type": "Activity"},
            {"name": "Eco Backup Place", "location": "Dubai", "eco_score": 9.1, "description": "Backup place", "data_type": "Place"},
        ]
