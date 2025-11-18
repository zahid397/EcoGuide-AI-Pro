import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from uuid import uuid4
from typing import List, Dict, Any, Optional
from utils.logger import logger

load_dotenv()
COLLECTION: str = "eco_travel_v3"
QDRANT_URL: Optional[str] = os.getenv("QDRANT_URL")
QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
FEEDBACK_FILE: str = "data/feedback.csv"

class RAGEngine:
    client: QdrantClient
    embedder: SentenceTransformer
    vector_size: int = 384

    def __init__(self) -> None:
        if not QDRANT_URL:
            # Fallback for local testing if env is missing
            print("⚠️ QDRANT_URL not found, using in-memory storage.")
            self.client = QdrantClient(":memory:")
        elif QDRANT_URL == ":memory:":
            # Explicit memory mode from .env
            self.client = QdrantClient(":memory:")
        else:
            # Standard Server/Cloud mode
            try:
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=60,
                    https=True,
                    prefer_grpc=False
                )
            except Exception as e:
                print(f"⚠️ Connection failed to {QDRANT_URL}. Switching to :memory: mode.")
                logger.error(f"Qdrant connection failed: {e}")
                self.client = QdrantClient(":memory:")

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Auto-initialize if collection is missing or memory mode (which wipes on restart)
        try:
            if not self.client.collection_exists(collection_name=COLLECTION):
                self._init_collection()
                self._index_all()
            elif self.client.count(collection_name=COLLECTION).count == 0:
                 self._index_all()
        except Exception as e:
            logger.exception(f"Init failed: {e}")

    def _init_collection(self) -> None:
        self.client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE
            )
        )

    def _index_file(self, file_path: str, data_type: str) -> None:
        if not os.path.exists(file_path):
            # Try finding file relative to project root
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(root, file_path)
            if not os.path.exists(file_path):
                return
            
        try:
            df = pd.read_csv(file_path)
            points: List[models.PointStruct] = []
            for _, row in df.iterrows():
                payload = row.to_dict()
                payload['data_type'] = data_type
                # ... (Standardizing fields logic omitted for brevity, assume cleaner CSVs or keep previous logic)
                # Ensure defaults
                payload.setdefault('cost', 0)
                payload.setdefault('cost_type', 'free')
                payload.setdefault('image_url', "https://placehold.co/100")
                
                text = f"{data_type}: {payload}"
                vec = self.embedder.encode(text).tolist()
                points.append(models.PointStruct(id=str(uuid4()), vector=vec, payload=payload))
            
            if points:
                self.client.upsert(collection_name=COLLECTION, points=points)
                print(f"✅ Indexed {len(points)} items from {os.path.basename(file_path)}")
        except Exception as e:
            logger.exception(f"Index failed: {e}")

    def _index_all(self) -> None:
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")

    def search(self, query: str, top_k: int = 10, min_eco_score: float = 0.0) -> List[Dict[str, Any]]:
        try:
            vec = self.embedder.encode(query).tolist()
            res = self.client.search(
                collection_name=COLLECTION,
                query_vector=vec,
                limit=top_k,
                query_filter=models.Filter(must=[models.FieldCondition(key="eco_score", range=models.Range(gte=min_eco_score))])
            )
            return [h.payload for h in res]
        except Exception as e:
            logger.exception(f"Search failed: {e}")
            return []
            
