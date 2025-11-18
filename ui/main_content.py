import streamlit as st
from utils.cost import calculate_real_cost
from utils.cards import get_card_css
from utils.logger import logger
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab,
    packing_tab, story_tab, map_tab, chat_tab, share_tab
)
import json


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
    user_profile = st.session_state.get("user_profile", {"name": "Traveler"})
    user_name = user_profile.get("name", "Traveler")

    real_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)

    st.subheader(f"🌍 {user_name}'s Eco Trip — {location}")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${real_cost}")
    col2.metric("Avg Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0kg')}")

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
    # 🔁 REFINEMENT SYSTEM (FULL FIX)
    # ================================

    st.divider()
    st.subheader("🤖 Refine Your Trip Plan")

    if "refine_text" not in st.session_state:
        st.session_state.refine_text = ""

    manual_text = st.text_input(
        "Tell AI what to improve:",
        placeholder="Example: Make it cheaper, make it more fun...",
        key="refine_input_box"
    )

    # Buttons
    c1, c2, c3, c4 = st.columns(4)

    if c1.button("💰 Cheaper", use_container_width=True):
        st.session_state.refine_text = "Find cheaper alternatives."
        st.rerun()

    if c2.button("🎉 More Fun", use_container_width=True):
        st.session_state.refine_text = "Add more fun and exciting activities."
        st.rerun()

    if c3.button("🌿 More Eco", use_container_width=True):
        st.session_state.refine_text = "Increase sustainability. More eco-friendly options."
        st.rerun()

    if c4.button("😌 Relaxing", use_container_width=True):
        st.session_state.refine_text = "Make the trip slower and more relaxing."
        st.rerun()

    refine_query = manual_text or st.session_state.refine_text

    # RUN REFINEMENT
    if st.button("🔄 Update Plan", use_container_width=True):
        if not refine_query:
            st.warning("Please enter what to refine.")
            return

        try:
            previous_json = json.dumps(itinerary)  # SAFE

            rag_data = st.session_state.get("rag_raw_data", [])

            updated_plan = agent.refine_plan(
                previous_plan_json=previous_json,
                feedback_query=refine_query,
                rag_data=rag_data,
                user_profile=user_profile,
                priorities=priorities,
                travelers=travelers,
                days=days,
                budget=budget
            )

            if updated_plan:
                st.session_state.itinerary = updated_plan
                st.success("Plan refined successfully! 🎉")
                st.session_state.refine_text = ""
                st.rerun()
            else:
                st.error("AI could not refine the plan. Try a different instruction.")

        except Exception as e:
            logger.exception(e)
            st.error("Failed to refine plan.")
