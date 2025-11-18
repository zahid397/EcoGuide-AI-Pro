import streamlit as st
import os
import sys

# --- 🛠️ CRITICAL PATH FIX ---
# This forces Python to see the current folder as the main project root
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# ---------------------------

from utils.env_validator import validate_env
from utils.caching import get_agent, get_rag
from utils.state import init_session_state
from utils.logger import logger
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content
from version import APP_VERSION

def main() -> None:
    st.set_page_config(page_title="🌍 EcoGuide AI Pro", layout="wide", initial_sidebar_state="expanded")
    
    init_session_state()
    st.title("🌍 EcoGuide AI Pro — Adaptive Travel Planner")

    # Error Handling for Setup
    try:
        validate_env()
        agent = get_agent()
        rag = get_rag()
    except Exception as e:
        st.error("⚠️ System Startup Error")
        st.error(f"Details: {e}")
        st.stop()

    # Render UI
    try:
        render_sidebar(agent, rag, APP_VERSION)
        render_main_content(agent, rag)
    except Exception as e:
        st.error("⚠️ UI Rendering Error")
        st.code(str(e))
        logger.exception(e)

if __name__ == "__main__":
    main()
    
