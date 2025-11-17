from functools import lru_cache
from backend.agent_workflow import TravelAgent
from backend.rag_engine import RAGEngine

@lru_cache(maxsize=1)
def get_agent():
    """Return a cached instance of the TravelAgent."""
    return TravelAgent()

@lru_cache(maxsize=1)
def get_rag():
    """Return a cached instance of the RAGEngine."""
    return RAGEngine()
