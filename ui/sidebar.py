import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger
from typing import Any


def render_sidebar(agent, rag, app_version: str) -> None:
    """Renders the sidebar UI and handles plan generation."""
    with st.sidebar:

        # -------------------------
        # USER PROFILE SECTION
        # -------------------------
        st.header("👤 My Profile")

        user_name = st.text_input(
            "Your Name",
            key="user_name",
            help="Enter your name to load your saved profile.",
        )

        profile = load_profile(user_name) if user_name else {}

        fav_interests = st.multiselect(
            "My Favorite Interests",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
        )

        pref_budget = st.slider(
            "My Usual Budget ($)", 100, 5000,
            profile.get("budget", 1000), step=100
        )

        if st.button("Save Profile", use_container_width=True):
            if len(user_name) < 2:
                st.error("Name must be at least 2 characters.")
            else:
                save_profile(user_name, fav_interests, pref_budget)
                st.success("Profile saved successfully!")

        st.divider()

        # -------------------------
        # TRIP BUILDER SECTION
        # -------------------------
        st.header("📍 Plan a New Trip")
        st.subheader("Trip Priorities")

        priorities = {
            "eco": st.slider("🟩 Eco Priority", 1, 10, 8, key="eco_priority"),
            "budget": st.slider("🟥 Budget Priority", 1, 10, 6, key="budget_priority"),
            "comfort": st.slider("🟧 Comfort Priority", 1, 10, 5, key="comfort_priority"),
        }

        st.multiselect(
            "Interests for this Trip",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
            key="trip_interests",
        )

        st.slider(
            "Total Budget ($)", 100, 10000,
            profile.get("budget", 1500), step=100,
            key="trip_budget"
        )

        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Number of Days", 1, 30, 3, key="trip_days")
        with col2:
            st.number_input("Travelers", 1, 20, 1, key="trip_travelers")

        st.selectbox(
            "Base Location",
            ["Dubai", "Abu Dhabi", "Sharjah"],
            key="trip_location",
        )

        st.slider(
            "Minimum Eco Score", 7.0, 9.5, 8.0, step=0.1,
            key="trip_min_eco"
        )

        # -------------------------
        # GENERATE PLAN BUTTON
        # -------------------------
        if st.button("Generate Plan 🚀", use_container_width=True):

            if not user_name:
                st.error("Please enter your name first.")
                return

            if not st.session_state.trip_interests:
                st.error("Please select at least one interest.")
                return

            _clear_session()

            # SAFE STATUS (no expand error)
            with st.spinner("Generating your eco-friendly trip..."):

                try:
                    # STEP 1: Build query
                    query = (
                        f"{st.session_state.trip_days}-day trip to "
                        f"{st.session_state.trip_location} for "
                        f"{st.session_state.trip_travelers} people. "
                        f"Interests: {', '.join(st.session_state.trip_interests)}"
                    )

                    # STEP 2: RAG Search
                    rag_results = rag.search(
                        query=query,
                        top_k=15,
                        min_eco_score=st.session_state.trip_min_eco,
                    )

                    if not rag_results:
                        st.error("No eco-friendly places found for this query.")
                        return

                    # STEP 3: Ask AI to create plan
                    itinerary = agent.run(
                        query=query,
                        rag_data=rag_results,
                        budget=st.session_state.trip_budget,
                        interests=st.session_state.trip_interests,
                        days=st.session_state.trip_days,
                        location=st.session_state.trip_location,
                        travelers=st.session_state.trip_travelers,
                        user_profile=profile,
                        priorities=priorities,
                    )

                    if itinerary:
                        st.session_state.itinerary = itinerary
                        st.success("Plan Ready! 🎉")
                        st.toast("Your eco-trip is ready! 🌍✨")
                    else:
                        st.error("AI failed to generate the itinerary.")

                except Exception as e:
                    logger.exception(f"Generation failed: {e}")
                    st.error(f"Error: {e}")

        st.divider()
        st.caption(f"EcoGuide AI — Version {app_version}")


def _clear_session():
    st.session_state.itinerary = None
    st.session_state.chat_history = []
    st.session_state.packing_list = {}
    st.session_state.travel_story = ""
    st.session_state.upgrade_suggestions = ""
