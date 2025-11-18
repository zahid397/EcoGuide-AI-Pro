import streamlit as st
from utils.cost import calculate_real_cost
from utils.cards import get_card_css
from utils.logger import logger
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab,
    packing_tab, story_tab, map_tab, chat_tab, share_tab
)
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine


def render_main_content(agent: AgentWorkflow, rag: RAGEngine) -> None:
    """Render the main content area."""

    # -------------------------------
    # No itinerary yet
    # -------------------------------
    if not st.session_state.itinerary:
        st.info("Please fill in your trip details in the sidebar and click **Generate Plan 🚀**.")
        return

    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    # Restore saved trip state
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    budget = st.session_state.get("current_trip_budget", 1000)
    location = st.session_state.get("current_trip_location", "Dubai")
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    user_name = st.session_state.get("user_name", "Traveler")

    # -------------------------------
    # Metrics section
    # -------------------------------
    real_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)

    st.subheader(f"🚀 {user_name}'s Eco Trip — {location}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${real_cost}")
    col2.metric("Avg Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0kg')}")

    # -------------------------------
    # TABS
    # -------------------------------
    (
        tab_overview,
        tab_analysis,
        tab_plan,
        tab_list,
        tab_pack,
        tab_story,
        tab_map,
        tab_chat,
        tab_share
    ) = st.tabs([
        "✨ Overview", "🔬 AI Analysis", "📅 Detailed Plan", "🏄‍♂️ Activities",
        "🎒 Packing List", "📖 Story", "🗺️ Map", "🤖 Chat", "🔗 Share"
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

    # ----------------------------------------------------
    #  🤖 Refine Section (FINAL FIXED)
    # ----------------------------------------------------
    st.divider()
    st.subheader("🤖 Refine Your Plan")

    refinement_query = st.text_input(
        "What would you like to change?",
        key="refine_input",
        placeholder="e.g., Make it cheaper, Add more beaches..."
    )

    # Quick buttons
    col1, col2, col3, col4 = st.columns(4)

    if col1.button("💰 Cheaper", use_container_width=True):
        st.session_state.refine_input = "Make the trip cheaper."
        refinement_query = st.session_state.refine_input

    if col2.button("🎉 More Fun", use_container_width=True):
        st.session_state.refine_input = "Add more fun, exciting activities."
        refinement_query = st.session_state.refine_input

    if col3.button("🌿 More Eco", use_container_width=True):
        st.session_state.refine_input = "Increase eco-friendly activities and hotels."
        refinement_query = st.session_state.refine_input

    if col4.button("😌 More Relaxed", use_container_width=True):
        st.session_state.refine_input = "Make the trip more relaxing."
        refinement_query = st.session_state.refine_input

    # -------------------------------
    # UPDATE PLAN BUTTON
    # -------------------------------
    if st.button("🔁 Update Plan", use_container_width=True):
        if not refinement_query.strip():
            st.warning("Please type a refinement request first.")
            return

        with st.spinner("Updating your itinerary..."):
            try:
                new_plan = agent.refine_plan(
                    itinerary=itinerary,
                    refinement_query=refinement_query
                )
                st.session_state.itinerary = new_plan
                st.success("Your itinerary has been updated! 🎉")
            except Exception as e:
                logger.exception(e)
                st.error("Failed to refine plan.")
