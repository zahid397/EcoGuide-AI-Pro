import streamlit as st
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine

@st.cache_resource
def get_agent(): return AgentWorkflow()

@st.cache_resource
def get_rag(): return RAGEngine()
  
