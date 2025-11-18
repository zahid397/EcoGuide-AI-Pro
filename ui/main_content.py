import streamlit as st
import pandas as pd
from utils.cards import get_card_css
from utils.cost import calculate_real_cost
# Imported ALL tabs here
from ui.tabs import overview_tab, analysis_tab, plan_tab, list_tab, packing_tab, story_tab, chat_tab, map_tab, share_tab

def render_main_content(agent, rag):
    if not st.session_state.itinerary:
        st.info("👈 Please fill in your trip details in the sidebar and click 'Generate Plan 🚀'.")
        return

    data = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)
    
    # Metrics Calculation
    days = st.session_state.get("current_trip_days", 3)
    pax = st.session_state.get("current_trip_travelers", 1)
    loc = st.session_state.get("current_trip_location", "Dubai")
    budget = st.session_state.get("current_trip_budget", 1500)
    interests = st.session_state.get("current_trip_interests", [])
    user = st.session_state.get("user_name", "User")
    
    cost = calculate_real_cost(data.get('activities', []), days, pax)
    
    st.subheader(f"🚀 {user}'s Eco-Trip to {loc}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Est. Cost", f"${cost}")
    c2.metric("Eco Score", f"{data.get('eco_score', 0)}/10")
    c3.metric("Carbon Saved", data.get('carbon_saved', '0kg'))
    
    # 9 Tabs (Including Map & Share)
    tabs = st.tabs(["Overview", "Analysis", "Plan", "Activities", "Packing", "Story", "Chat", "Map", "Share"])
    
    with tabs[0]: overview_tab.render(data, budget, pax)
    with tabs[1]: analysis_tab.render(data)
    with tabs[2]: plan_tab.render(data, loc, user)
    with tabs[3]: list_tab.render(data)
    with tabs[4]: packing_tab.render(agent, data, user)
    with tabs[5]: story_tab.render(agent, data, user)
    with tabs[6]: chat_tab.render(agent, data)
    with tabs[7]: map_tab.render_map_tab(loc)      # ✅ Added
    with tabs[8]: share_tab.render_share_tab(days, loc, interests, budget) # ✅ Added
