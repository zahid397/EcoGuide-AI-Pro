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
            help="Enter your name to load your profile.",
        )

        profile = load_profile(user_name) if user_name else {}

        fav_interests = st.multiselect(
            "My Favorite Interests",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", ["Adventure"]),   # ⭐ FIX 1: Always non-empty
        )

        pref_budget = st.slider(
            "My Usual Budget ($)", 100, 5000,
            profile.get("budget", 1000), 100
        )

        # Save Profile
        if st.button("Save Profile", use_container_width=True):
            if not user_name or len(user_name) < 2:
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

        priorities = {
            "eco": st.slider("🟩 Eco Priority", 1, 10, 8),
            "budget": st.slider("🟥 Budget Priority", 1, 10, 6),
            "comfort": st.slider("🟧 Comfort Priority", 1, 10, 5),
        }

        # ⭐ FIX 1: trip_interest always has at least 1 value
        st.multiselect(
            "Interests for this trip",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", ["Adventure"]),
            key="trip_interests",
        )

        st.slider(
            "Total Budget ($)", 100, 10000,
            profile.get("budget", 1500),
            100,
            key="trip_budget",
        )

        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Number of Days", 1, 30, 3, key="trip_days")
        with col2:
            st.number_input("Number of Travelers", 1, 20, 1, key="trip_travelers")

        st.selectbox("Base Location",
                     ["Dubai", "Abu Dhabi", "Sharjah"],
                     key="trip_location")

        # ⭐ FIX 2: Eco minimum lowered (previously 8.0 → too strict)
        st.slider(
            "Minimum Eco Score",
            7.0, 9.5,
            7.5,     # better results
            0.1,
            key="trip_min_eco",
        )

        # -------------------------
        # GENERATE BUTTON
        # -------------------------
        if st.button("Generate Plan 🚀", use_container_width=True):

            if not user_name:
                st.error("Please enter your name first.")
                return

            if not st.session_state.trip_interests:
                st.error("Please select at least one interest.")
                return

            # Clear old data
            st.session_state.itinerary = None

            with st.status("Generating your eco-friendly trip...", expanded=True) as status:
                try:
                    status.write("🧠 Step 1: Building your travel query...")

                    query = (
                        f"{st.session_state.trip_days}-day trip to "
                        f"{st.session_state.trip_location} for "
                        f"{st.session_state.trip_travelers} people. "
                        f"Interests: {', '.join(st.session_state.trip_interests)}"
                    )

                    status.write("🔍 Step 2: Searching eco-friendly spots...")
                    rag_results = rag.search(
                        query=query,
                        top_k=15,
                        min_eco_score=st.session_state.trip_min_eco,
                    )

                    if not rag_results:
                        status.update("No eco-friendly results found.", state="error")
                        return

                    status.write("🤖 Step 3: Creating itinerary using AI...")
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
                        status.update("✅ Done!", state="complete")
                        st.toast("Your Eco-Trip Plan is Ready! 🌍✨")
                    else:
                        status.update("AI failed to respond.", state="error")

                except Exception as e:
                    logger.exception(f"Generation failed: {e}")
                    status.update("Error occurred.", state="error")
                    st.error(str(e))

        st.divider()
        st.caption(f"EcoGuide AI — Version {app_version}")
