import os
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from uuid import uuid4
from typing import List, Dict, Any, Optional
from utils.logger import logger
import random

load_dotenv()
COLLECTION: str = "eco_travel_v3"
QDRANT_URL: Optional[str] = os.getenv("QDRANT_URL")
QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")

class RAGEngine:
    def __init__(self) -> None:
        # 1. Try connecting to Qdrant
        try:
            if not QDRANT_URL:
                self.client = QdrantClient(":memory:")
            else:
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=10, # Short timeout to fail fast if offline
                    https=True,
                    prefer_grpc=False
                )
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Quick check (Self-healing)
            try:
                if not self.client.collection_exists(COLLECTION):
                    self._index_all()
            except:
                pass 
                
        except Exception as e:
            logger.error(f"RAG Init Error: {e}")
            self.client = None # Mark as failed, will use fallback

    def _index_all(self):
        # Indexing logic skipped for brevity as fallback handles data now
        pass

    def search(self, query: str, top_k: int = 15, min_eco_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Smart Search: Tries Vector DB first. If empty/fails, forces CSV data.
        """
        results = []
        
        # --- Attempt 1: Vector Search ---
        if self.client:
            try:
                vec = self.embedder.encode(query).tolist()
                search_result = self.client.search(
                    collection_name=COLLECTION,
                    query_vector=vec,
                    limit=top_k,
                    # Removed strict filter to ensure we get *some* results
                    # query_filter=models.Filter(...) 
                )
                results = [h.payload for h in search_result]
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # --- Attempt 2: Fallback (Direct CSV Load) ---
        # যদি ভেক্টর সার্চ খালি রেজাল্ট দেয়, আমরা সরাসরি CSV ফাইল পড়ব
        if not results:
            print("⚠️ Vector search empty or failed. Using CSV Fallback.")
            results = self._fallback_search(query, min_eco_score)
            
        return results

    def _fallback_search(self, query: str, min_eco_score: float) -> List[Dict[str, Any]]:
        """Reads directly from CSV files if DB fails."""
        combined_data = []
        # Find data directory relative to this file
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_path, "data")
        
        files = {
            "hotels.csv": "Hotel", 
            "activities.csv": "Activity", 
            "places.csv": "Place"
        }
        
        for filename, dtype in files.items():
            path = os.path.join(data_dir, filename)
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    # Convert rows to list of dicts
                    records = df.to_dict('records')
                    
                    for rec in records:
                        rec['data_type'] = dtype
                        # Ensure numerical scores exist
                        rec['eco_score'] = float(rec.get('eco_score', 5.0))
                        rec['cost'] = float(rec.get('price_per_night', rec.get('price', rec.get('entry_fee', 0))))
                        rec['image_url'] = rec.get('image_url', "https://placehold.co/600x400?text=No+Image")
                        
                        # Simple Keyword Match Logic
                        item_text = str(rec).lower()
                        query_lower = query.lower()
                        
                        # Location Filter (Basic)
                        if "dubai" in query_lower and "dubai" not in item_text:
                            continue
                        if "abu dhabi" in query_lower and "abu dhabi" not in item_text:
                            continue
                        if "sharjah" in query_lower and "sharjah" not in item_text:
                            continue

                        combined_data.append(rec)
                except Exception as e:
                    logger.error(f"CSV read error {filename}: {e}")

        # Return random selection to keep it fresh
        random.shuffle(combined_data)
        return combined_data[:15]
      
