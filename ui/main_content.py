import streamlit as st
import pandas as pd
from utils.cards import get_card_css
from utils.cost import calculate_real_cost

# ALL TABS
from ui.tabs import (
    overview_tab,
    analysis_tab,
    plan_tab,
    list_tab,
    packing_tab,
    story_tab,
    chat_tab,
    map_tab,
    share_tab
)

def render_main_content(agent, rag):

    # --- No Itinerary Loaded ---
    if not st.session_state.itinerary:
        st.info("👈 Please fill in your trip details in the sidebar and click **Generate Plan 🚀**.")
        return

    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    # ---- Load Session Data ----
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    location = st.session_state.get("current_trip_location", "Dubai")
    budget = st.session_state.get("current_trip_budget", 1500)
    interests = st.session_state.get("current_trip_interests", [])
    user_name = st.session_state.get("user_name", "Traveler")

    # ---- Cost Calculation ----
    total_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)

    # ---- Header ----
    st.subheader(f"🌍 {user_name}'s Eco Trip — {location}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${total_cost}")
    col2.metric("Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0kg')}")

    # ---- Tabs ----
    tabs = st.tabs([
        "✨ Overview",
        "🔬 Analysis",
        "📅 Plan",
        "🏄 Activities",
        "🎒 Packing",
        "📖 Story",
        "🤖 Ask AI",
        "🗺️ Map",
        "🔗 Share"
    ])

    # Correct Tab Calls
    with tabs[0]:
        overview_tab.render_overview(itinerary, budget, travelers)

    with tabs[1]:
        analysis_tab.render_analysis(itinerary)

    with tabs[2]:
        plan_tab.render_plan(itinerary, location, user_name)

    with tabs[3]:
        list_tab.render_list(itinerary)

    with tabs[4]:
        packing_tab.render_packing_tab(agent, itinerary, user_name)

    with tabs[5]:
        story_tab.render_story_tab(agent, itinerary, user_name)

    with tabs[6]:
        chat_tab.render_chat_tab(agent, itinerary)

    with tabs[7]:
        map_tab.render_map_tab(location)

    with tabs[8]:
        share_tab.render_share_tab(days, location, interests, budget)
