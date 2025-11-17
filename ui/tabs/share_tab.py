import streamlit as st
import urllib.parse
from typing import List

def render_share_tab(days: int, location: str, interests: List[str], budget: int) -> None:
    st.subheader("Share Your Trip Plan")
    
    interests_str = ", ".join(interests)
    plan_summary = f"Check out my {days}-day eco-trip to {location} planned by EcoGuide AI! We're focusing on {interests_str} with a budget of ${budget}."
    
    st.markdown("#### Share on WhatsApp")
    whatsapp_text = urllib.parse.quote_plus(plan_summary)
    st.link_button("Share on WhatsApp 💬", f"https-://wa.me/?text={whatsapp_text}", use_container_width=True)
    
    st.markdown("#### Instagram Caption Idea")
    st.text_area("Caption:", f"{plan_summary} #EcoGuideAI #SustainableTravel #{location.replace(' ','')}", height=100)
  
