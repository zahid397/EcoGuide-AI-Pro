import os
import pandas as pd

DATA_DIR = "data"
COL_HOTEL = os.path.join(DATA_DIR, "hotels.csv")
COL_ACT = os.path.join(DATA_DIR, "activities.csv")
COL_PLACE = os.path.join(DATA_DIR, "places.csv")


class HybridRAG:
    """Fast CSV-based hybrid RAG (no Qdrant needed)."""

    def __init__(self):
        self.data = []

        self._load_csv(COL_HOTEL, "Hotel")
        self._load_csv(COL_ACT, "Activity")
        self._load_csv(COL_PLACE, "Place")

        print(f"HybridRAG Loaded {len(self.data)} items.")

    # -----------------------------
    # LOAD CSV
    # -----------------------------
    def _load_csv(self, path, dtype):
        if not os.path.exists(path):
            print(f"Missing CSV: {path}")
            return
        
        df = pd.read_csv(path)

        for _, row in df.iterrows():
            item = row.to_dict()
            item["data_type"] = dtype
            item["eco_score"] = float(item.get("eco_score", 0))
            self.data.append(item)

    # -----------------------------
    # SIMPLE SMART SEARCH (NO QDRANT)
    # -----------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):

        query = query.lower()
        results = []

        for item in self.data:
            # Filter eco score
            if item.get("eco_score", 0) < min_eco_score:
                continue

            text = (
                f"{item.get('name','')} "
                f"{item.get('location','')} "
                f"{item.get('description','')}"
            ).lower()

            # keyword match score
            score = 0
            for word in query.split():
                if word in text:
                    score += 1

            if score > 0:
                item["match_score"] = score
                results.append(item)

        # sort by match score
        results = sorted(results, key=lambda x: x["match_score"], reverse=True)

        return results[:top_k]
