import os
import pandas as pd
from uuid import uuid4
from qdrant_client import QdrantClient, models
from openai import OpenAI
from utils.logger import logger

COLLECTION = "eco_travel_v3"
DATA_DIR = "data"

EMBED_MODEL = "text-embedding-3-small"   # 1536 dim


class RAGEngine:
    def __init__(self):
        logger.info("🚀 Initializing RAG Engine...")

        self.client = QdrantClient(path="qdrant_local")
        self.openai = OpenAI()

        # ALWAYS recreate collection to prevent old dimension issues
        try:
            self.client.delete_collection(COLLECTION)
        except:
            pass

        self._init_collection()
        self._index_all()

        logger.info("✅ RAG Engine Ready!")

    # --------------------------
    # Create Collection
    # --------------------------
    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=1536,                     # fixed dimension
                distance=models.Distance.COSINE
            )
        )
        logger.info("Created Qdrant collection with 1536-dim vectors")

    # --------------------------
    # Embedding function
    # --------------------------
    def embed(self, text: str):
        try:
            res = self.openai.embeddings.create(
                model=EMBED_MODEL,
                input=text
            )
            return res.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return [0.0] * 1536

    # --------------------------
    # Index all CSVs
    # --------------------------
    def _index_all(self):
        logger.info("Indexing all CSV files...")

        csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

        points = []

        for file_name in csv_files:
            path = os.path.join(DATA_DIR, file_name)

            df = pd.read_csv(path).fillna("")
            dtype = file_name.replace(".csv", "").capitalize()

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload["data_type"] = dtype

                try:
                    payload["eco_score"] = float(payload.get("eco_score", 0))
                except:
                    payload["eco_score"] = 0.0

                text = (
                    f"{payload.get('name','')} "
                    f"{payload.get('location','')} "
                    f"{payload.get('description','')}"
                )

                vec = self.embed(text)

                points.append(
                    models.PointStruct(
                        id=str(uuid4()),
                        vector=vec,
                        payload=payload
                    )
                )

        if points:
            self.client.upsert(collection_name=COLLECTION, points=points)

        logger.info(f"Indexed total {len(points)} items.")

    # --------------------------
    # Search
    # --------------------------
    def search(self, query, top_k=10, min_eco_score=7.0):
        try:
            qvec = self.embed(query)

            flt = models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=float(min_eco_score))
                    )
                ]
            )

            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=qvec,
                filter=flt,
                limit=top_k,
                with_payload=True
            )

            return [hit.payload for hit in results]

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
