import streamlit as st
import os
import sys

# --- PATH FIX: Add root to system path ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

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

    try:
        validate_env()
        agent = get_agent()
        rag = get_rag()
    except Exception as e:
        st.error(f"System Error: {e}")
        logger.exception(f"Startup failed: {e}")
        st.stop()

    render_sidebar(agent, rag, APP_VERSION)
    render_main_content(agent, rag)

if __name__ == "__main__":
    main()
    
