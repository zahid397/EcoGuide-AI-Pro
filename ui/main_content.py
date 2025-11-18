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


# -----------------------------------------
# SAFE SESSION KEYS (Fix for errors)
# -----------------------------------------
if "refine_input" not in st.session_state:
    st.session_state.refine_input = ""

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None


# -----------------------------------------
# MAIN CONTENT
# -----------------------------------------
def render_main_content(agent: AgentWorkflow, rag: RAGEngine) -> None:

    if not st.session_state.itinerary:
        st.info("Please fill trip details from sidebar and click Generate Plan 🚀")
        return

    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    # Fetch stored trip params
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    budget = st.session_state.get("current_trip_budget", 1000)
    location = st.session_state.get("current_trip_location", "Dubai")
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    user_name = st.session_state.get("user_name", "Traveler")

    real_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)

    st.subheader(f"🚀 {user_name}'s Eco Trip — {location}")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${real_cost}")
    col2.metric("Avg Eco Score", f"{itinerary.get('eco_score', 0)} / 10")
    col3.metric("Carbon Saved", itinerary.get("carbon_saved", "0 kg"))

    # Tabs
    tab_overview, tab_analysis, tab_plan, tab_list, tab_pack, tab_story, tab_map, tab_chat, tab_share = st.tabs([
        "✨ Overview", "🔬 AI Analysis", "📅 Detailed Plan", "🏄 Activities",
        "🎒 Packing List", "📖 Story", "🗺️ Map", "🤖 Ask AI", "🔗 Share"
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

    # -----------------------------------------
    # REFINEMENT AREA (FULLY FIXED)
    # -----------------------------------------
    st.divider()
    st.subheader("🤖 Refine Your Plan")

    refinement_query = st.text_input(
        "What would you like to change?",
        key="refine_input",
        placeholder="e.g. Make it cheaper, Add more beach activities..."
    )

    st.markdown("##### Quick Improvements")

    c1, c2, c3, c4 = st.columns(4)

    if c1.button("💰 Cheaper", use_container_width=True):
        st.session_state.refine_input = "Make the trip cheaper with budget options."

    if c2.button("🎉 More Fun", use_container_width=True):
        st.session_state.refine_input = "Add more fun and exciting activities."

    if c3.button("🌿 More Eco", use_container_width=True):
        st.session_state.refine_input = "Increase eco-friendly hotels and activities."

    if c4.button("😌 Relaxing", use_container_width=True):
        st.session_state.refine_input = "Make the plan more relaxing with slow-paced activities."

    st.write(" ")

    # -----------------------------------------
    # REGENERATE UPDATED PLAN
    # -----------------------------------------
    if st.button("🔄 Update Plan", use_container_width=True):

        if not refinement_query:
            st.warning("Please type or choose a refinement option")
            return

        try:
            rag_results = rag.search(
                refinement_query,
                top_k=10,
                min_eco_score=0.0
            )

            new_plan = agent.run(
                query=refinement_query,
                rag_data=rag_results,
                budget=budget,
                interests=interests,
                days=days,
                location=location,
                travelers=travelers,
                user_profile={"name": user_name},
                priorities=priorities
            )

            if new_plan:
                st.session_state.itinerary = new_plan
                st.success("Plan updated successfully! 🎉")
            else:
                st.error("Failed to refine plan. Using fallback.")
        except Exception as e:
            logger.exception(e)
            st.error("Failed to refine plan. Please try again.")
