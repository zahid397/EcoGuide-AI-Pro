import os
import pandas as pd
from uuid import uuid4
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer
from utils.logger import logger
import shutil

DATA_DIR = "data"
COLLECTION = "eco_travel_v3"


class RAGEngine:

    def __init__(self):

        # Always rebuild clean DB
        if os.path.exists("qdrant_local"):
            shutil.rmtree("qdrant_local")

        self.client = QdrantClient(path="qdrant_local")

        # Load CSVs first (so TF-IDF can train)
        self.dataframes = self._load_all_csv()

        # Build TF-IDF on all text once
        self.vectorizer = self._build_vectorizer()

        # Create Qdrant collection with auto vector size
        vector_size = len(self.vectorizer.get_feature_names_out())
        self._init_collection(vector_size)

        # Now index everything
        self._index_all()

        print("✅ RAG Engine Ready.")


    # -------------------------------------------------------
    def _load_all_csv(self):
        dfs = []
        for file in os.listdir(DATA_DIR):
            if file.endswith(".csv"):
                path = os.path.join(DATA_DIR, file)
                try:
                    df = pd.read_csv(path)
                    df["__source_type"] = file.replace(".csv", "")
                    dfs.append(df)
                except Exception as e:
                    logger.error(f"Failed to read {file}: {e}")
        return dfs


    # -------------------------------------------------------
    def _build_vectorizer(self):
        all_text = []

        for df in self.dataframes:
            for _, row in df.iterrows():
                text = f"{row.get('name','')} {row.get('location','')} {row.get('description','')}"
                all_text.append(text)

        vectorizer = TfidfVectorizer(max_features=500)  # autosize
        vectorizer.fit(all_text)

        print("TF-IDF vectorizer trained.")
        return vectorizer


    # -------------------------------------------------------
    def _init_collection(self, vector_size):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            ),
        )
        print(f"Collection created → vector size {vector_size}")


    # -------------------------------------------------------
    def _index_all(self):
        for df in self.dataframes:
            dtype = df["__source_type"].iloc[0].capitalize()
            self._index_dataframe(df, dtype)


    # -------------------------------------------------------
    def _index_dataframe(self, df, data_type):
        points = []

        for _, row in df.iterrows():
            payload = row.to_dict()
            payload["data_type"] = data_type
            payload["eco_score"] = float(payload.get("eco_score", 0))
            payload["image_url"] = payload.get("image_url", "https://placehold.co/100")

            text = f"{payload.get('name','')} {payload.get('location','')} {payload.get('description','')}"
            vec = self.vectorizer.transform([text]).toarray()[0].tolist()

            points.append(
                models.PointStruct(id=str(uuid4()), vector=vec, payload=payload)
            )

        if points:
            self.client.upsert(COLLECTION, points)
            print(f"Indexed {len(points)} items → {data_type}")


    # -------------------------------------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        try:
            qvec = self.vectorizer.transform([query]).toarray()[0].tolist()

            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=qvec,
                with_payload=True,
                limit=top_k,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="eco_score",
                            range=models.Range(gte=min_eco_score)
                        )
                    ]
                )
            )

            return [r.payload for r in results]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
