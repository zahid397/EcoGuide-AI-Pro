import io
import streamlit as st
from gtts import gTTS
from utils.logger import logger

@st.cache_data(ttl=3600)
def generate_tts(text: str) -> bytes:
    try:
        if not text: return None
        # Fix: Remove emojis/markdown for cleaner audio
        clean_text = text.replace("#", "").replace("*", "")
        tts = gTTS(text=clean_text[:500], lang='en') # Limit length for speed
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        logger.exception(f"TTS Error: {e}")
        return None
      
