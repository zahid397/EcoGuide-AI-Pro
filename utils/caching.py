from functools import lru_cache
from backend.rag_engine import RAGEngine
from backend.agent_workflow import AgentWorkflow

@lru_cache(maxsize=1)
def get_rag():
    return RAGEngine()

@lru_cache(maxsize=1)
def get_agent():
    return AgentWorkflow()
