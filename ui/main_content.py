import streamlit as st
from utils.cost import calculate_real_cost
from utils.cards import get_card_css
from utils.logger import logger
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab,
    packing_tab, story_tab, map_tab, chat_tab, share_tab
)


def render_main_content(agent, rag):

    if not st.session_state.itinerary:
        st.info("Please fill trip details from sidebar and click Generate Plan 🚀.")
        return

    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    # Load trip parameters
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    budget = st.session_state.get("current_trip_budget", 1000)
    location = st.session_state.get("current_trip_location", "Dubai")
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    user_name = st.session_state.get("user_name", "Traveler")

    real_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)

    st.subheader(f"🌍 {user_name}'s Eco Trip — {location}")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${real_cost}")
    col2.metric("Avg Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0 kg')}")

    # Tabs
    tabs = st.tabs([
        "✨ Overview", "🔬 Analysis", "📅 Plan", "🏄 Activities",
        "🎒 Packing", "📖 Story", "🗺️ Map", "🤖 Ask AI", "🔗 Share"
    ])

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
        map_tab.render_map_tab(location)
    with tabs[7]:
        chat_tab.render_chat_tab(agent, itinerary)
    with tabs[8]:
        share_tab.render_share_tab(days, location, interests, budget)

    # ================================
    # 🔁 REFINEMENT SYSTEM (NO ERRORS)
    # ================================

    st.divider()
    st.subheader("🤖 Refine Your Trip Plan")

    # Initialize refine text
    if "refine_text" not in st.session_state:
        st.session_state.refine_text = ""

    # Manual input
    refine_manual = st.text_input(
        "Tell AI what to improve:",
        placeholder="Example: Make it cheaper, add more fun...",
        key="refine_input_box"
    )

    # Quick refine buttons
    c1, c2, c3, c4 = st.columns(4)

    if c1.button("💰 Cheaper", use_container_width=True):
        st.session_state.refine_text = "Make the trip cheaper with budget-friendly alternatives."
        st.rerun()

    if c2.button("🎉 More Fun", use_container_width=True):
        st.session_state.refine_text = "Add more fun, exciting activities."
        st.rerun()

    if c3.button("🌿 More Eco", use_container_width=True):
        st.session_state.refine_text = "Add more sustainable and eco-friendly options."
        st.rerun()

    if c4.button("😌 Relaxing", use_container_width=True):
        st.session_state.refine_text = "Make the trip more relaxing with slow-paced activities."
        st.rerun()

    # Final selected refine text
    refine_query = refine_manual or st.session_state.refine_text

    # Update Plan
    if st.button("🔄 Update Plan", use_container_width=True):
        if not refine_query:
            st.warning("Write something to refine the plan.")
        else:
            try:
                updated = agent.refine_plan(itinerary, refine_query)
                st.session_state.itinerary = updated
                st.success("Plan updated successfully! 🎉")
            except Exception as e:
                st.error("Failed to refine plan.")
                logger.exception(e)
