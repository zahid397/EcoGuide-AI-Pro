import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger


def render_sidebar(agent, rag, app_version: str) -> None:
    with st.sidebar:

        # -------------------------
        # USER PROFILE
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
            "My Usual Budget ($)",
            100, 5000,
            profile.get("budget", 1000),
            100,
        )

        # Save Profile
        if st.button("Save Profile", use_container_width=True):
            if not user_name or len(user_name) < 2:
                st.error("Name must be at least 2 characters.")
            else:
                try:
                    save_profile(user_name, fav_interests, pref_budget)
                    st.success("Profile Saved!")
                except Exception as e:
                    logger.exception(e)
                    st.error(f"Failed to save profile: {e}")

        st.divider()

        # -------------------------
        # TRIP BUILDER
        # -------------------------
        st.header("📍 Plan a New Trip")

        st.subheader("Trip Priorities")

        priorities = {
            "eco": st.slider("🟩 Eco Priority", 1, 10, 8, key="p_eco"),
            "budget": st.slider("🟥 Budget Priority", 1, 10, 6, key="p_budget"),
            "comfort": st.slider("🟧 Comfort Priority", 1, 10, 5, key="p_comfort"),
        }

        trip_interests = st.multiselect(
            "Interests for this trip",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
            key="trip_interests",
        )

        trip_budget = st.slider(
            "Total Budget ($)",
            100,
            10000,
            profile.get("budget", 1500),
            100,
            key="trip_budget",
        )

        days = st.number_input("Number of Days", 1, 30, 3, key="trip_days")
        travelers = st.number_input("Travelers", 1, 20, 1, key="trip_travelers")

        location = st.selectbox(
            "Base Location",
            ["Dubai", "Abu Dhabi", "Sharjah"],
            key="trip_location",
        )

        min_eco = st.slider(
            "Minimum Eco Score",
            7.0, 9.5, 7.5, 0.1,
            key="trip_min_eco"
        )

        # -------------------------
        # GENERATE PLAN BUTTON
        # -------------------------
        if st.button("Generate Plan 🚀", use_container_width=True):

            if not user_name:
                st.error("Please enter your name first.")
                return

            if not trip_interests:
                st.error("Select at least one interest.")
                return

            _clear_session()

            with st.status("Generating your eco-friendly trip...", expanded=True) as status:
                try:
                    status.write("🧠 Step 1: Building query...")
                    query = (
                        f"{days}-day trip to {location} for {travelers} people. "
                        f"Interests: {', '.join(trip_interests)}"
                    )

                    status.write("🔍 Step 2: Searching eco-friendly places...")
                    rag_results = rag.search(
                        query=query,
                        top_k=15,
                        min_eco_score=min_eco,
                    )

                    if not rag_results:
                        status.update(label="❌ No eco-friendly results found.", state="error")
                        return

                    status.write("🤖 Step 3: Creating Itinerary with AI...")
                    itinerary = agent.run(
                        query=query,
                        rag_data=rag_results,
                        budget=trip_budget,
                        interests=trip_interests,
                        days=days,
                        location=location,
                        travelers=travelers,
                        user_profile=profile,
                        priorities=priorities,
                    )

                    if itinerary:
                        st.session_state.itinerary = itinerary
                        status.update(label="✅ Done!", state="complete")
                        st.toast("Plan Ready! 🌍✨")
                    else:
                        status.update(label="AI failed to generate plan.", state="error")

                except Exception as e:
                    logger.exception(e)
                    status.update(label="Error occurred.", state="error")
                    st.error(str(e))

        st.divider()
        st.caption(f"EcoGuide AI — Version {app_version}")


def _clear_session():
    st.session_state.itinerary = None
    st.session_state.chat_history = []
    st.session_state.packing_list = {}
    st.session_state.travel_story = ""
    st.session_state.upgrade_suggestions = ""
