import os
import pandas as pd
from utils.logger import logger

DATA_DIR = "data"

class HybridRAG:
    def __init__(self):
        # Load all CSVs into memory (fast)
        self.hotels = self._load_csv("hotels.csv")
        self.activities = self._load_csv("activities.csv")
        self.places = self._load_csv("places.csv")

        # Merge all data
        self.all_items = (
            self.hotels +
            self.activities +
            self.places
        )

        print(f"HybridRAG Loaded: {len(self.all_items)} items.")

    def _load_csv(self, filename):
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            logger.error(f"Missing CSV: {filename}")
            return []

        df = pd.read_csv(path).fillna("")
        return df.to_dict(orient="records")

    # -------------------------
    # MAIN SEARCH SYSTEM
    # -------------------------
    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        """
        Hybrid Search Algorithm:
        1. Keyword match (CSV)
        2. Eco-score filter
        3. AI ranking (optional)
        """

        query_lower = query.lower()

        # Step 1 — Filter by eco score
        eco_filtered = [
            item for item in self.all_items
            if float(item.get("eco_score", 0)) >= min_eco_score
        ]

        # Step 2 — Keyword matching
        matched = []
        for item in eco_filtered:
            text = (
                f"{item.get('name', '')} "
                f"{item.get('location', '')} "
                f"{item.get('description', '')}"
            ).lower()

            if any(word in text for word in query_lower.split()):
                matched.append(item)

        # Step 3 — If no match, fallback = return top eco items
        if not matched:
            matched = sorted(eco_filtered,
                             key=lambda x: float(x.get("eco_score", 0)),
                             reverse=True)

        # Step 4 — Return top_k
        return matched[:top_k]
