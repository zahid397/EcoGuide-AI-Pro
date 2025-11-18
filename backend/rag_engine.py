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
            # Fallback to memory if env var missing
            self.client = QdrantClient(":memory:")
        else:
            try:
                # Connect to Cloud/Local
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=60,
                    https=True,
                    prefer_grpc=False
                )
            except Exception as e:
                logger.error(f"Qdrant Connection Failed: {e}")
                self.client = QdrantClient(":memory:") # Fallback

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # --- ✳️ UNIVERSAL FIX: Check Collection Safely ---
        if not self._safe_collection_exists(COLLECTION):
            self._init_collection()
            self._index_all()

    def _safe_collection_exists(self, name: str) -> bool:
        """Checks if collection exists, compatible with all Qdrant versions."""
        try:
            # Try New Method (v1.7+)
            return self.client.collection_exists(collection_name=name)
        except AttributeError:
            # Fallback: Try Old Method (List all and check)
            try:
                collections = self.client.get_collections().collections
                for c in collections:
                    if c.name == name:
                        return True
                return False
            except Exception:
                return False
        except Exception as e:
            logger.error(f"Collection check failed: {e}")
            return False

    def _init_collection(self) -> None:
        try:
            self.client.recreate_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
        except Exception as e:
            logger.error(f"Init collection failed: {e}")

    def _index_file(self, file_path: str, data_type: str) -> None:
        if not os.path.exists(file_path):
             # Try finding relative to root
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_path, file_path)
            if not os.path.exists(file_path):
                return

        try:
            df = pd.read_csv(file_path)
            points: List[models.PointStruct] = []

            for _, row in df.iterrows():
                payload = row.to_dict()
                payload['data_type'] = data_type
                
                # Fix missing fields
                payload.setdefault('cost', 0)
                payload.setdefault('eco_score', 5.0)
                payload.setdefault('image_url', "https://placehold.co/100")

                text_to_embed = f"{data_type}: {payload}"
                embedding = self.embedder.encode(text_to_embed).tolist()
                
                points.append(
                    models.PointStruct(
                        id=str(uuid4()),
                        vector=embedding,
                        payload=payload
                    )
                )
            
            if points:
                self.client.upsert(collection_name=COLLECTION, points=points, wait=True)
                print(f"Indexed {len(points)} from {file_path}")
                
        except Exception as e:
            logger.exception(f"Index file error: {e}")

    def _index_all(self) -> None:
        self._index_file("data/hotels.csv", "Hotel")
        self._index_file("data/activities.csv", "Activity")
        self._index_file("data/places.csv", "Place")

    def search(self, query: str, top_k: int = 10, min_eco_score: float = 7.0) -> List[Dict[str, Any]]:
        try:
            query_vector = self.embedder.encode(query).tolist()
            
            # Remove strict filter if it causes issues, but try to keep it
            eco_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="eco_score",
                        range=models.Range(gte=min_eco_score)
                    )
                ]
            )

            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=query_vector,
                query_filter=eco_filter,
                limit=top_k,
                with_payload=True
            )
            
            return [hit.payload for hit in results]
        except Exception as e:
            logger.exception(f"Search failed: {e}")
            return []
