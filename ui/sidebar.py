import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger

def render_sidebar(agent, rag, app_version: str) -> None:
    """Render Sidebar UI without session_state conflicts."""
    with st.sidebar:

        st.header("✈️ Plan Your Trip")
        st.divider()

        # --------------------------
        # 🧍 User Profile
        # --------------------------
        st.header("👤 My Profile")

        # Safe text_input (no default from code AND session state)
        user_name = st.text_input(
            "Your Name",
            key="user_name",
            help="Enter your name to load your travel preferences."
        )

        profile = load_profile(user_name) if user_name else {}

        fav_interests = st.multiselect(
            "My Favorite Interests",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", [])
        )

        pref_budget = st.slider(
            "My Usual Budget ($)",
            min_value=100,
            max_value=5000,
            value=profile.get("budget", 1000),
            step=100
        )

        if st.button("Save Profile", use_container_width=True):
            if len(user_name) < 2:
                st.error("Name must be at least 2 characters.")
            else:
                save_profile(user_name, fav_interests, pref_budget)
                st.success("Profile Saved!")

        st.divider()
        st.header("📍 Plan a New Trip")
        st.subheader("Trip Priorities")

        # --------------------------
        # ⭐ Trip Priority Sliders
        # --------------------------
        priorities = {
            "eco": st.slider("🟩 Eco Priority", 1, 10, 8, key="prio_eco"),
            "budget": st.slider("🟥 Budget Priority", 1, 10, 6, key="prio_budget"),
            "comfort": st.slider("🟧 Comfort Priority", 1, 10, 5, key="prio_comfort")
        }

        # --------------------------
        # 🎯 Trip Interest
        # --------------------------
        st.multiselect(
            "Interests for this trip",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
            key="trip_interests"
        )

        # --------------------------
        # 💰 Budget
        # --------------------------
        st.slider(
            "Total Budget ($)",
            100, 10000,
            value=profile.get("budget", 1500),
            step=100,
            key="trip_budget"
        )

        # --------------------------
        # 📆 Days + Travelers
        # --------------------------
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Number of Days",
                min_value=1,
                max_value=30,
                value=3,
                key="trip_days"
            )
        with col2:
            st.number_input(
                "Number of Travelers",
                min_value=1,
                max_value=20,
                value=1,
                key="trip_travelers"
            )

        # --------------------------
        # 📍 Location
        # --------------------------
        st.selectbox(
            "Base Location",
            ["Dubai", "Abu Dhabi", "Sharjah"],
            key="trip_location"
        )

        # --------------------------
        # 🍃 Minimum Eco Score
        # --------------------------
        st.slider(
            "Minimum Eco Score",
            min_value=7.0,
            max_value=9.5,
            value=8.0,
            step=0.1,
            key="trip_min_eco"
        )

        # --------------------------
        # 🚀 Generate Button
        # --------------------------
        if st.button("Generate Plan 🚀", use_container_width=True):

            if not user_name:
                st.error("Please enter your name first.")
                return

            if not st.session_state.trip_interests:
                st.error("Select at least one interest.")
                return

            _clear_session()

            with st.status("Generating your eco-friendly itinerary...", expanded=True) as status:

                try:
                    # Build search query
                    status.write("🧠 Step 1: Building query...")

                    query = (
                        f"{st.session_state.trip_days}-day trip to "
                        f"{st.session_state.trip_location} for "
                        f"{st.session_state.trip_travelers} people. "
                        f"Interests: {', '.join(st.session_state.trip_interests)}"
                    )

                    # RAG Search
                    status.write("🔍 Step 2: Searching eco-friendly places...")
                    rag_results = rag.search(
                        query=query,
                        top_k=15,
                        min_eco_score=st.session_state.trip_min_eco
                    )

                    if not rag_results:
                        status.update("No eco-friendly results found.", state="error")
                        return

                    # AI Itinerary
                    status.write("🤖 Step 3: Creating itinerary with AI...")
                    itinerary = agent.run(
                        query=query,
                        rag_data=rag_results,
                        budget=st.session_state.trip_budget,
                        interests=st.session_state.trip_interests,
                        days=st.session_state.trip_days,
                        location=st.session_state.trip_location,
                        travelers=st.session_state.trip_travelers,
                        user_profile=profile,
                        priorities=priorities
                    )

                    if itinerary:
                        st.session_state.itinerary = itinerary
                        status.update("✅ Your eco-trip is ready!", state="complete")
                        st.toast("Plan Ready! 🌍✨")
                    else:
                        status.update("AI failed to generate plan.", state="error")

                except Exception as e:
                    logger.exception(f"Generation failed: {e}")
                    status.update("Error occurred.", state="error")
                    st.error(str(e))

        st.divider()
        st.caption(f"EcoGuide AI — Version {app_version}")


# --------------------------
# 🔄 Clear Session Data
# --------------------------
def _clear_session():
    st.session_state.itinerary = None
    st.session_state.chat_history = []
    st.session_state.packing_list = {}
    st.session_state.travel_story = ""
    st.session_state.upgrade_suggestions = ""
