import streamlit as st
import os
import sys

# -----------------------------------------
# 🔧 FIX 1 — Absolute Path Injection (Safe)
# -----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# -----------------------------------------
# 🔧 FIX 2 — Import Modules (Protected)
# -----------------------------------------
try:
    from utils.state import init_session_state
    from utils.logger import logger
    from utils.env_validator import validate_env
    from utils.caching import get_agent, get_rag
    from ui.sidebar import render_sidebar
    from ui.main_content import render_main_content
    from version import APP_VERSION
except Exception as e:
    st.error("❌ Import Error: Some required files are missing.")
    st.code(str(e))
    st.stop()

# -----------------------------------------
# MAIN APP FUNCTION
# -----------------------------------------
def main():
    st.set_page_config(
        page_title="🌍 EcoGuide AI Pro",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

    st.title("🌍 EcoGuide AI Pro — Adaptive Travel Planner")

    # -----------------------------------------
    # 🔧 FIX 3 — Validate Environment + Load Core Modules
    # -----------------------------------------
    try:
        validate_env()
        agent = get_agent()
        rag = get_rag()
    except Exception as e:
        st.error("⚠️ Startup Error — Core system failed to load.")
        st.code(str(e))
        return

    # -----------------------------------------
    # 🔧 FIX 4 — Render UI (Fully Safe)
    # -----------------------------------------
    try:
        render_sidebar(agent, rag, APP_VERSION)
        render_main_content(agent, rag)
    except Exception as e:
        st.error("⚠️ UI Error — Unable to render interface.")
        st.code(str(e))
        logger.exception(e)

# -----------------------------------------
# Run App
# -----------------------------------------
if __name__ == "__main__":
    main()
