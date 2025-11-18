import streamlit as st
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content

APP_VERSION = "1.0.0"

# ===========================
# APP CONFIG
# ===========================
st.set_page_config(
    page_title="EcoGuide AI 🌍",
    page_icon="🌱",
    layout="wide",
)

# ===========================
# INITIALIZE SESSION KEYS
# ===========================
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "packing_list" not in st.session_state:
    st.session_state.packing_list = {}

if "travel_story" not in st.session_state:
    st.session_state.travel_story = ""

if "upgrade_suggestions" not in st.session_state:
    st.session_state.upgrade_suggestions = ""


# ===========================
# MAIN FUNCTION
# ===========================
def main():

    # Initialize Models
    try:
        rag = RAGEngine()
        agent = AgentWorkflow()
    except Exception as e:
        st.error("Failed to initialize AI components.")
        st.exception(e)
        return

    # LEFT SIDEBAR
    render_sidebar(agent, rag, APP_VERSION)

    # MAIN CONTENT
    render_main_content(agent, rag)


# ===========================
# RUN APP
# ===========================
if __name__ == "__main__":
    main()
