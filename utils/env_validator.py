import os
import streamlit as st
from utils.logger import logger

def validate_env() -> None:
    """Checks for required environment variables."""
    required = ["GEMINI_API_KEY", "QDRANT_URL"]
    missing = [v for v in required if not os.getenv(v)]
    
    if missing:
        msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(msg)
        raise EnvironmentError(msg)
    
    # Qdrant ক্লাউডের জন্য কী (Key) না থাকলে ওয়ার্নিং দাও
    if "qdrant.tech" in os.getenv("QDRANT_URL", "") and not os.getenv("QDRANT_API_KEY"):
        msg = "QDRANT_URL is set to Qdrant Cloud, but QDRANT_API_KEY is missing. This is required for cloud deployment."
        logger.warning(msg)
        st.warning(msg) # এটি অ্যাপে একটি ওয়ার্নিং দেখাবে
