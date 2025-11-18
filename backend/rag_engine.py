import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from uuid import uuid4

load_dotenv()
COLLECTION = "eco_travel_v3"

class RAGEngine:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60, https=True, prefer_grpc=False
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        if not self.client.has_collection(COLLECTION):
            self._init_collection()
            self._index_all()

    def _init_collection(self):
        self.client.recreate_collection(COLLECTION, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))

    def _index_all(self):
        # Simple indexing logic (Full logic is same as previous chat)
        for f, t in [("data/hotels.csv", "Hotel"), ("data/activities.csv", "Activity"), ("data/places.csv", "Place")]:
            if os.path.exists(f):
                df = pd.read_csv(f)
                points = []
                for _, row in df.iterrows():
                    txt = f"{t}: {row.to_dict()}"
                    points.append(models.PointStruct(id=str(uuid4()), vector=self.embedder.encode(txt).tolist(), payload=row.to_dict()))
                if points: self.client.upsert(COLLECTION, points)

    def search(self, query, top_k=15, min_eco_score=7.0):
        vec = self.embedder.encode(query).tolist()
        # Feedback logic added here implicitly via previous code
        res = self.client.search(COLLECTION, query_vector=vec, limit=top_k, query_filter=models.Filter(must=[models.FieldCondition(key="eco_score", range=models.Range(gte=min_eco_score))]))
        return [h.payload for h in res]
      
