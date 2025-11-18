import streamlit as st
from utils.pdf import generate_pdf
from utils.tts import generate_tts

def render(data, loc, user):
    st.markdown(data.get('plan', 'No plan.'))
    
    if st.button("🔊 Listen"):
        audio = generate_tts(data.get('plan', ''))
        if audio: st.audio(audio)
        
    pdf = generate_pdf(data)
    if pdf:
        st.download_button("📄 Download PDF", pdf, "plan.pdf", "application/pdf")
        
