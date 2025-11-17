import streamlit as st
import os
import sys # ✳️ Import sys

# --- ✳️ FIX: Add project root to Python path ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
# --- End Fix ---

from utils.env_validator import validate_env
from utils.caching import get_agent, get_rag
from utils.state import init_session_state
from utils.logger import logger
from ui.sidebar import render_sidebar
from ui.main_content import render_main_content
from version import APP_VERSION

def main() -> None:
    """Main function to run the Streamlit app."""
    
    # --- Page Config & State Init ---
    st.set_page_config(page_title="🌍 EcoGuide AI Pro",
                       layout="wide",
                       initial_sidebar_state="expanded")
    
    # Initialize all session state keys
    init_session_state()

    st.title("🌍 EcoGuide AI Pro — Adaptive Travel Planner")

    # --- Fix 5: Environment Validator ---
    try:
        validate_env()
    except EnvironmentError as e:
        st.error(str(e))
        logger.error(str(e))
        st.stop()

    # --- Fix 2: Load Cached AI & RAG Engines ---
    try:
        agent = get_agent()
        rag = get_rag()
    except Exception as e:
        st.error(f"Failed to initialize AI components: {e}")
        logger.exception(f"Failed to initialize AI components: {e}")
        st.stop()

    # --- Render UI ---
    render_sidebar(agent, rag, APP_VERSION)
    render_main_content(agent, rag)

if __name__ == "__main__":
    main()
