import streamlit as st
from utils.pdf import generate_pdf
from utils.tts import generate_tts
from utils.logger import logger

# THIS FUNCTION NAME MUST MATCH WHAT THE MAIN UI CALLS
def render_plan(itinerary, location, user_name):
    st.subheader(f"📅 {user_name}'s Travel Plan — {location}")

    plan_text = itinerary.get("plan", "No plan available.")
    st.markdown(plan_text)

    # --- AUDIO BUTTON ---
    if st.button("🔊 Listen to this Plan"):
        try:
            audio = generate_tts(plan_text)
            if audio:
                st.audio(audio)
            else:
                st.error("Audio could not be generated.")
        except Exception as e:
            logger.exception(e)
            st.error("Audio generation failed.")

    st.divider()

    # --- PDF DOWNLOAD ---
    st.subheader("📄 Download PDF Version")
    try:
        pdf_bytes = generate_pdf(itinerary)
        if pdf_bytes:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name="travel_plan.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.warning("Could not generate PDF.")
    except Exception as e:
        logger.exception(e)
        st.error("PDF generation failed.")
