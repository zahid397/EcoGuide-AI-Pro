import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger
import time
from typing import Any
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine


def render_sidebar(agent: AgentWorkflow, rag: RAGEngine, app_version: str) -> None:

    with st.sidebar:

        # -------------------------
        # USER PROFILE
        # -------------------------
        st.header("👤 My Profile")

        user_name = st.text_input(
            "Your Name",
            value=st.session_state.get("user_name", ""),   # ✅ FIX
            key="user_name_input",
            help="Enter your name to save and load your personal profile."
        )

        if user_name:
            st.session_state.user_name = user_name

        profile = load_profile(user_name) if user_name else {}

        fav_interests = st.multiselect(
            "My Favorite Interests",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
        )

        pref_budget = st.slider(
            "My Usual Budget ($)", 100, 5000,
            profile.get("budget", 1000), 100
        )

        if st.button("Save Profile", use_container_width=True):
            if len(user_name) < 2:
                st.error("Name must be at least 2 characters.")
            else:
                save_profile(user_name, fav_interests, pref_budget)
                st.success("Profile Saved!")

        st.divider()

        # -------------------------
        # TRIP BUILDER
        # -------------------------
        st.header("📍 Plan a New Trip")
        st.subheader("Trip Priorities")

        st.slider("🟩 Eco Priority", 1, 10, 8, key="trip_eco_priority")
        st.slider("🟥 Budget Priority", 1, 10, 6, key="trip_budget_priority")
        st.slider("🟧 Comfort Priority", 1, 10, 5, key="trip_comfort_priority")

        st.multiselect(
            "Interests for this trip",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
            key="trip_interests"
        )

        st.slider(
            "Total Budget ($)", 100, 10000,
            profile.get("budget", 1500), 100,
            key="trip_budget"
        )

        st.number_input("Number of Days", 1, 30, 3, key="trip_days")
        st.number_input("Travelers", 1, 20, 1, key="trip_travelers")

        st.selectbox(
            "Base Location",
            ["Dubai", "Abu Dhabi", "Sharjah"],
            key="trip_location"
        )

        st.slider(
            "Minimum Eco Score",
            7.0, 9.5, 8.0, 0.1,
            key="trip_min_eco"
        )

        # -------------------------
        # GENERATE BUTTON
        # -------------------------
        if st.button("Generate Plan 🚀", use_container_width=True):

            if not user_name:
                st.error("Please enter your name first.")
                return

            if not st.session_state.trip_interests:
                st.error("Select at least one interest.")
                return

            _clear_session_state()

            with st.status(f"Generating plan for {user_name}...", expanded=True) as status:
                try:
                    status.write("🧠 Step 1: Building your query...")

                    priorities, query, user_profile = _build_query_and_profile()

                    status.write("🔍 Step 2: Searching eco-friendly locations...")
                    rag_results = rag.search(
                        query=query,
                        top_k=15,
                        min_eco_score=st.session_state.trip_min_eco
                    )

                    if not rag_results:
                        status.update("❌ No eco-friendly results found.", state="error")
                        return

                    status.write("🤖 Step 3: Creating itinerary...")

                    itinerary = agent.run(
                        query=query,
                        rag_data=rag_results,
                        budget=st.session_state.trip_budget,
                        interests=st.session_state.trip_interests,
                        days=st.session_state.trip_days,
                        location=st.session_state.trip_location,
                        travelers=st.session_state.trip_travelers,
                        user_profile=user_profile,
                        priorities=priorities
                    )

                    if itinerary:
                        _set_session_state_on_generate(itinerary, query, priorities)
                        status.update("✅ Done!", state="complete")
                        st.toast("Your eco-trip plan is ready! 🌍✨")
                        time.sleep(0.5)
                    else:
                        status.update("AI failed to generate.", state="error")

                except Exception as e:
                    logger.exception(e)
                    status.update("Error occurred.", state="error")
                    st.error(str(e))

        st.divider()
        st.caption(f"EcoGuide AI — Version {app_version}")


def _validate_inputs():
    return True


def _clear_session_state():
    st.session_state.itinerary = None
    st.session_state.chat_history = []
    st.session_state.packing_list = {}
    st.session_state.travel_story = ""
    st.session_state.upgrade_suggestions = ""


def _build_query_and_profile():
    priorities = {
        "eco": st.session_state.trip_eco_priority,
        "budget": st.session_state.trip_budget_priority,
        "comfort": st.session_state.trip_comfort_priority
    }

    query = (
        f"A {st.session_state.trip_days}-day trip to {st.session_state.trip_location} "
        f"for {st.session_state.trip_travelers} people, focusing on "
        f"{', '.join(st.session_state.trip_interests)}."
    )

    user_profile = load_profile(st.session_state.user_name)
    user_profile["name"] = st.session_state.user_name

    return priorities, query, user_profile


def _set_session_state_on_generate(itinerary, query, priorities):
    st.session_state.itinerary = itinerary
    st.session_state.query = query
    st.session_state.current_trip_days = st.session_state.trip_days
    st.session_state.current_trip_budget = st.session_state.trip_budget
    st.session_state.current_trip_location = st.session_state.trip_location
    st.session_state.current_trip_travelers = st.session_state.trip_travelers
    st.session_state.current_trip_interests = st.session_state.trip_interests
    st.session_state.current_trip_priorities = priorities
