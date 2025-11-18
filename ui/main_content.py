import streamlit as st
from utils.cost import calculate_real_cost
from utils.cards import get_card_css
from utils.logger import logger
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab,
    packing_tab, story_tab, map_tab, chat_tab, share_tab
)

# =====================================================
# SAFE SESSION SETTER (no crashes)
# =====================================================
def safe_set(key, value):
    if key not in st.session_state:
        st.session_state[key] = value
    else:
        st.session_state[key] = value


# =====================================================
# MAIN CONTENT
# =====================================================
def render_main_content(agent, rag):

    if not st.session_state.itinerary:
        st.info("Please fill in your trip details and click **Generate Plan 🚀**.")
        return

    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    # Trip State
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    budget = st.session_state.get("current_trip_budget", 1000)
    location = st.session_state.get("current_trip_location", "Dubai")
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    user_name = st.session_state.get("user_name", "Traveler")

    real_cost = calculate_real_cost(
        itinerary.get("activities", []),
        days,
        travelers
    )

    st.subheader(f"🌍 {user_name}'s Eco Trip — {location}")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${real_cost}")
    col2.metric("Avg Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0 kg')}")

    # -----------------------------------------------------
    # TABS
    # -----------------------------------------------------
    tab_overview, tab_analysis, tab_plan, tab_list, tab_pack, tab_story, tab_map, tab_chat, tab_share = st.tabs([
        "✨ Overview", "🔬 AI Analysis", "📅 Detailed Plan", "🏄 Activities",
        "🎒 Packing", "📖 Story", "🗺️ Map", "🤖 Ask AI", "🔗 Share"
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

    # =====================================================
    # 🧠 REFINEMENT ENGINE (FULL FIXED VERSION)
    # =====================================================

    st.divider()
    st.subheader("🤖 Refine Your Trip Plan")

    # A. create safe refine storage
    if "refine_text" not in st.session_state:
        st.session_state.refine_text = ""

    # Input box
    user_refine_box = st.text_input(
        "Describe what you want to improve:",
        key="refine_box",
        placeholder="Example: Make it cheaper, more fun, more relaxing..."
    )

    # Safe apply-function
    def apply_refine(text):
        st.session_state.refine_text = text
        st.rerun()

    # Quick buttons
    c1, c2, c3, c4 = st.columns(4)

    if c1.button("💰 Cheaper", use_container_width=True):
        apply_refine("Reduce total cost. Replace expensive hotels and activities with cheaper options.")

    if c2.button("🎉 More Fun", use_container_width=True):
        apply_refine("Add more fun and exciting activities, even if price increases slightly.")

    if c3.button("🌿 More Eco", use_container_width=True):
        apply_refine("Increase eco-friendly hotels and activities with higher sustainability ratings.")

    if c4.button("😌 Relaxing", use_container_width=True):
        apply_refine("Make the itinerary more relaxing with slow-paced experiences.")

    # Final refinement request
    refine_query = st.session_state.refine_text or user_refine_box

    # Update Plan
    if st.button("🔄 Update Plan", use_container_width=True):
        if not refine_query:
            st.warning("Please tell what you want to refine.")
        else:
            try:
                refined_itinerary = agent.refine_plan(
                    itinerary=itinerary,
                    refinement_query=refine_query,
                )
                st.session_state.itinerary = refined_itinerary
                st.success("Trip updated successfully! 🎉")
            except Exception as e:
                st.error("Failed to refine the plan.")
                logger.exception(e)
