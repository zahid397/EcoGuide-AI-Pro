import streamlit as st
import urllib.parse

def render_share_tab(days, location, interests, budget):
    st.subheader("🔗 Share Your Trip Plan")
    
    # Generate Social Media Text
    interests_str = ", ".join(interests)
    plan_summary = f"I just planned a {days}-day eco-trip to {location} using EcoGuide AI! 🌍 We're focusing on {interests_str} with a budget of ${budget}. #SustainableTravel"
    
    # Generate WhatsApp Link
    whatsapp_text = urllib.parse.quote_plus(plan_summary)
    whatsapp_url = f"https://wa.me/?text={whatsapp_text}"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💬 WhatsApp")
        st.link_button("Share on WhatsApp", whatsapp_url, use_container_width=True)
        
    with col2:
        st.markdown("#### 📸 Instagram Caption")
        st.text_area("Copy this caption:", value=plan_summary, height=100)
        
