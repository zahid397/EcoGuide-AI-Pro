import streamlit as st
from typing import Dict, Any
from utils.cost import calculate_real_cost
from utils.cards import get_card_css
from utils.logger import logger
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab,
    packing_tab, story_tab, map_tab, chat_tab, share_tab
)

def render_main_content(agent, rag):
    """Renders the main content area."""

    # ---------------------------------------------------
    # If itinerary is missing
    # ---------------------------------------------------
    if not st.session_state.itinerary:
        st.info("Please fill in your trip details in the sidebar and click 'Generate Plan 🚀'.")
        return

    # ---------------------------------------------------
    # Load itinerary & session parameters
    # ---------------------------------------------------
    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    budget = st.session_state.get("current_trip_budget", 1000)
    location = st.session_state.get("current_trip_location", "Dubai")
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    user_name = st.session_state.get("user_name", "Traveler")

    # Cost calculation
    real_cost = calculate_real_cost(
        itinerary.get("activities", []),
        days,
        travelers
    )

    st.subheader(f"🚀 {user_name}'s Custom Eco-Tour: {location}")

    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost (Calculated)", f"${real_cost}")
    col2.metric("Avg Eco Score", f"{itinerary.get('eco_score', 0)} / 10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0kg')}")

    # ---------------------------------------------------
    # Tabs
    # ---------------------------------------------------
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "✨ Overview", "🔬 AI Analysis", "📅 Detailed Plan", "🏄 Activities",
        "🎒 Packing", "📖 Story", "🗺️ Map", "🤖 Chat", "🔗 Share"
    ])

    with tab1:
        overview_tab.render_overview(itinerary, budget, travelers)

    with tab2:
        analysis_tab.render_analysis(itinerary)

    with tab3:
        plan_tab.render_plan(itinerary, location, user_name)

    with tab4:
        list_tab.render_list(itinerary)

    with tab5:
        packing_tab.render_packing_tab(agent, itinerary, user_name)

    with tab6:
        story_tab.render_story_tab(agent, itinerary, user_name)

    with tab7:
        map_tab.render_map_tab(location)

    with tab8:
        chat_tab.render_chat_tab(agent, itinerary)

    with tab9:
        share_tab.render_share_tab(days, location, interests, budget)

    # ---------------------------------------------------
    # Refinement Section
    # ---------------------------------------------------
    st.divider()
    st.subheader("🤖 Refine Your Plan")

    refinement_query = st.text_input(
        "What would you like to change?",
        key="refine_input",
        placeholder="e.g., Make it cheaper or Add more beach activities"
    )

    st.markdown("##### Quick Suggestions")
    c1, c2, c3, c4, c5 = st.columns(5)

    if c1.button("💰 Cheaper"):
        refinement_query = "Make the trip cheaper with budget friendly alternatives."

    if c2.button("🎉 More Fun"):
        refinement_query = "Add more fun and exciting activities."

    if c3.button("😌 Relaxing"):
        refinement_query = "Add more relaxing experiences."

    if c4.button("🌿 More Eco"):
        refinement_query = "Increase eco-friendly choices."

    if c5.button("🧒 Family Friendly"):
        refinement_query = "Make the plan more suitable for families."

    if st.button("🔁 Apply Refinement", use_container_width=True):

        if not refinement_query.strip():
            st.warning("Please type what you want to refine.")
            return

        with st.spinner("Updating your plan..."):
            try:
                refined = agent.refine_plan(
                    itinerary=itinerary,
                    refinement_query=refinement_query
                )

                if refined:
                    st.session_state.itinerary = refined
                    st.success("Your plan has been updated!")
                else:
                    st.error("Could not refine plan.")

            except Exception as e:
                logger.exception(e)
                st.error("Failed to refine plan.")
