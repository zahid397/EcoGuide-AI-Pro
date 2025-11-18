import streamlit as st
from utils.tts import generate_tts
from utils.pdf import generate_pdf
from utils.logger import logger
from typing import Dict, Any

def render_plan(itinerary: Dict[str, Any], location: str, user_name: str) -> None:
    st.subheader("Your Day-by-Day Itinerary (w/ Smart Clock ⏱️)")
    plan_text = itinerary.get("plan", "No plan generated.")
    st.markdown(plan_text)

    st.divider()
    st.subheader("Listen to your trip plan 🎧")
    with st.spinner("Generating audio..."):
        audio_bytes = generate_tts(plan_text.replace("#", ""))
        if audio_bytes:
            st.audio(audio_bytes, format='audio/mp3')
        else:
            st.error("Could not generate audio.")

    st.divider()
    try:
        pdf_bytes = generate_pdf(itinerary)
        st.download_button(
            label="Download Full Plan as PDF 📄",
            data=pdf_bytes,
            file_name=f"EcoGuide_Plan_{location}_{user_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        logger.exception(f"Failed to generate PDF: {e}")
        st.error("Failed to generate PDF: Could not generate PDF. Please try again.")
