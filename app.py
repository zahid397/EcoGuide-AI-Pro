import streamlit as st
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content
from utils.logger import logger

APP_VERSION = "2.0.0-Pro-SaaS"

# ======================================================
# INITIALIZE SESSION STATE
# ======================================================

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None

if "packing_list" not in st.session_state:
    st.session_state.packing_list = {}

if "travel_story" not in st.session_state:
    st.session_state.travel_story = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="EcoGuide AI Pro",
    page_icon="🌍",
    layout="wide"
)


# ======================================================
# LOAD AGENT + RAG ENGINE
# ======================================================
try:
    agent = AgentWorkflow()
    rag = RAGEngine()
except Exception as e:
    st.error("❌ Failed to initialize AI Engine.")
    logger.exception(e)
    st.stop()


# ======================================================
# SIDEBAR
# ======================================================
render_sidebar(agent, rag, APP_VERSION)


# ======================================================
# MAIN CONTENT
# ======================================================
st.title("🌍 EcoGuide AI Pro — Adaptive Travel Planner")

try:
    render_main_content(agent, rag)
except Exception as e:
    st.error("❌ Failed to render main UI.")
    logger.exception(e)
