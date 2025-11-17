import streamlit as st
from utils.cards import render_card
from typing import Dict, Any

def render_list(itinerary: Dict[str, Any]) -> None:
    st.subheader("Recommended Activities, Hotels & Places (w/ Hidden Gems 💎)")
    st.info("Recommendations are based on your profile and ratings from similar travelers.")
    
    activities = itinerary.get("activities", [])
    if not activities:
        st.warning("No specific items were listed in this plan.")
        
    for item in activities: 
        st.markdown(render_card(item), unsafe_allow_html=True)
      
