import pandas as pd
import os


DATA_DIR = "data"


class RAGEngine:
    """
    Simple Hybrid RAG Engine
    - Loads CSV files
    - Filters by eco_score
    - Keyword ranking based on query words
    """

    def __init__(self):
        # Load all datasets
        self.hotels = self._load_csv("hotels.csv")
        self.activities = self._load_csv("activities.csv")
        self.places = self._load_csv("places.csv")

        print("RAGEngine Loaded ✓")
        print(f"Hotels: {len(self.hotels)} | Activities: {len(self.activities)} | Places: {len(self.places)}")

    def _load_csv(self, filename):
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"❗ Missing CSV: {path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(path)
            return df
        except Exception as e:
            print(f"❗ CSV parse error in {filename}: {e}")
            return pd.DataFrame()

    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0):
        """
        Hybrid local search
        1. Filter by eco_score >= min
        2. Keyword match scoring on text fields
        3. Return top-K results
        """

        # Merge all data
        df = pd.concat([self.hotels, self.activities, self.places], ignore_index=True)

        if df.empty:
            print("❗ No data loaded in RAGEngine")
            return []

        # --- Step 1: ECO SCORE FILTER ---
        df = df[df["eco_score"] >= float(min_eco_score)]

        if df.empty:
            print("❗ Eco filter found nothing")
            return []

        # --- Step 2: KEYWORD RANKING ---
        query = query.lower()

        def calc_score(row):
            text = f"{row.get('name', '')} {row.get('description', '')} {row.get('location', '')}".lower()
            score = 0
            for w in query.split():
                if w in text:
                    score += 1
            return score

        df["match_score"] = df.apply(calc_score, axis=1)

        # --- Step 3: RANK & SELECT ---
        df = df.sort_values(by="match_score", ascending=False)

        results = df.head(top_k).to_dict(orient="records")

        print(f"🔍 RAG Search Returned: {len(results)} items")

        return results
