import streamlit as st
from typing import Dict, Any
from utils.cost import calculate_real_cost
from utils.cards import get_card_css
from utils.logger import logger
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab,
    packing_tab, story_tab, map_tab, chat_tab, share_tab
)

# ------------------------------
# Safe Setter (NO MORE CRASH)
# ------------------------------
def safe_set(key, value):
    st.session_state[key] = value


# ------------------------------
# MAIN CONTENT
# ------------------------------
def render_main_content(agent, rag):
    """Renders the main content area (metrics, tabs, refine feature)."""

    if "itinerary" not in st.session_state or not st.session_state.itinerary:
        st.info("Please fill in your trip details in the sidebar and click **Generate Plan 🚀**.")
        return

    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    # Load trip session parameters
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    budget = st.session_state.get("current_trip_budget", 1000)
    location = st.session_state.get("current_trip_location", "Dubai")
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    user_name = st.session_state.get("user_name", "Traveler")

    # Cost Calculation
    real_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)

    st.subheader(f"🚀 {user_name}'s Eco Trip: {location}")

    # -----------------
    # METRICS
    # -----------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${real_cost}")
    col2.metric("Avg Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0kg')}")

    # -----------------
    # TABS
    # -----------------
    (
        tab_overview, tab_analysis, tab_plan, tab_list,
        tab_pack, tab_story, tab_map, tab_chat, tab_share
    ) = st.tabs([
        "✨ Overview", "🔬 AI Analysis", "📅 Plan",
        "🏄 Activities", "🎒 Packing",
        "📖 Story", "🗺️ Map", "🤖 Ask AI", "🔗 Share"
    ])

    with tab_overview:
        overview_tab.render_overview(itinerary, budget, travelers)
    with tab_analysis:
        analysis_tab.render_analysis(itinerary)
    with tab_plan:
        plan_tab.render_plan(itinerary, location, user_name)
    with tab_list:
        list_tab.render_list(itinerary)
    with tab_pack:
        packing_tab.render_packing_tab(agent, itinerary, user_name)
    with tab_story:
        story_tab.render_story_tab(agent, itinerary, user_name)
    with tab_map:
        map_tab.render_map_tab(location)
    with tab_chat:
        chat_tab.render_chat_tab(agent, itinerary)
    with tab_share:
        share_tab.render_share_tab(days, location, interests, budget)

    # ---------------------------
    # REFINEMENT SECTION
    # ---------------------------
    st.divider()
    st.subheader("🤖 Refine Your Plan")

    refine_box = st.text_input(
        "Tell AI what to improve:",
        key="refine_input",
        placeholder="Example: Make it cheaper, Add more fun, Add more eco activities..."
    )

    st.markdown("### Quick Improvements")
    c1, c2, c3, c4 = st.columns(4)

    if c1.button("💰 Cheaper", use_container_width=True):
        safe_set("refine_input", "Make the trip cheaper with budget-friendly options.")

    if c2.button("🎉 More Fun", use_container_width=True):
        safe_set("refine_input", "Add more fun, exciting and high-rated activities.")

    if c3.button("🌿 More Eco", use_container_width=True):
        safe_set("refine_input", "Increase eco-friendly hotels and activities.")

    if c4.button("😌 Relaxing", use_container_width=True):
        safe_set("refine_input", "Make the plan more relaxing with slow-paced activities.")

    # ---------------------------
    # APPLY REFINEMENT
    # ---------------------------
    if st.button("🔄 Update Plan", use_container_width=True):
        try:
            refined = agent.refine_plan(
                itinerary=itinerary,
                refinement_query=st.session_state.refine_input
            )

            if refined:
                st.session_state.itinerary = refined
                st.success("Plan updated successfully! 🎉")
            else:
                st.error("AI could not refine the plan.")

        except Exception as e:
            logger.exception(e)
            st.error("Failed to refine plan.")
