from functools import lru_cache
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import HybridRAG   # <-- use NEW engine

@lru_cache(maxsize=1)
def get_agent():
    return AgentWorkflow()

@lru_cache(maxsize=1)
def get_rag():
    return HybridRAG()    # <-- FIXED
