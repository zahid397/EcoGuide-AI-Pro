import streamlit as st
import io
from gtts import gTTS
from typing import Optional
from utils.logger import logger

@st.cache_data(ttl=3600) # Fix 5: Cache expires after 1 hour
def generate_tts(text_to_speak: str) -> Optional[bytes]:
    """Generates TTS audio and caches it."""
    try:
        tts = gTTS(text=text_to_speak, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        logger.exception(f"Error generating TTS: {e}")
        return None
      
