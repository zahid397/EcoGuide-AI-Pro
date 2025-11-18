import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger


# ======================================================
# SIDEBAR RENDER FUNCTION
# ======================================================
def render_sidebar(agent, rag, app_version: str):

    with st.sidebar:

        # -------------------------
        # USER PROFILE
        # -------------------------
        st.header("👤 My Profile")

        user_name = st.text_input(
            "Your Name",
            value=st.session_state.get("user_name", ""),
            key="user_name_input",
        )

        # store name in session
        if user_name:
            st.session_state.user_name = user_name

        profile = load_profile(user_name) if user_name else {}

        fav_interests = st.multiselect(
            "My Favorite Interests",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
            key="profile_interests"
        )

        pref_budget = st.slider(
            "My Usual Budget ($)", 100, 5000,
            profile.get("budget", 1500),
            100, key="profile_budget"
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

        eco_priority = st.slider("🟩 Eco Priority", 1, 10, 8)
        budget_priority = st.slider("🟥 Budget Priority", 1, 10, 6)
        comfort_priority = st.slider("🟧 Comfort Priority", 1, 10, 5)

        trip_interests = st.multiselect(
            "Interests for this trip",
            ["Beach", "History", "Adventure", "Food", "Nature"],
            default=profile.get("interests", []),
        )

        trip_budget = st.slider(
            "Total Trip Budget ($)", 100, 10000,
            profile.get("budget", 1500),
            100,
            key="trip_budget"
        )

        days = st.number_input("Number of Days", 1, 30, 3)
        travelers = st.number_input("Travelers", 1, 20, 1)

        location = st.selectbox(
            "Base Location",
            ["Dubai", "Abu Dhabi", "Sharjah"],
        )

        min_eco = st.slider(
            "Minimum Eco Score", 6.0, 9.5, 7.5, step=0.1
        )

        # -------------------------
        # GENERATE BUTTON
        # -------------------------
        if st.button("Generate Plan 🚀", use_container_width=True):

            if not user_name:
                st.error("Please enter your name first.")
                return

            if not trip_interests:
                st.error("Please select at least one interest.")
                return

            _clear_session()

            with st.status(f"Generating plan for {user_name}...", expanded=True) as status:
                try:

                    # step 1 — build query
                    status.write("🧠 Step 1: Building your query...")
                    query = f"A {days}-day eco-friendly trip to {location} for {travelers} people interested in: {', '.join(trip_interests)}."

                    priorities = {
                        "eco": eco_priority,
                        "budget": budget_priority,
                        "comfort": comfort_priority
                    }

                    # fixed
                    user_profile = load_profile(user_name)
                    user_profile["name"] = user_name

                    # step 2 — rag search
                    status.write("🔍 Step 2: Searching eco-friendly locations...")

                    rag_results = rag.search(
                        query=query,
                        top_k=20,
                        min_eco_score=min_eco,
                    )

                    if not rag_results:
                        status.update(label="❌ No eco-friendly results found.", state="error")
                        return

                    # step 3 — generate plan
                    status.write("🤖 Step 3: Creating itinerary...")

                    itinerary = agent.run(
                        query=query,
                        rag_data=rag_results,
                        budget=trip_budget,
                        interests=trip_interests,
                        days=days,
                        location=location,
                        travelers=travelers,
                        user_profile=user_profile,
                        priorities=priorities
                    )

                    if itinerary:
                        _save_generated(itinerary, query, priorities)
                        status.update(label="✅ Done!", state="complete")
                        st.toast("Your eco-trip plan is ready! 🌍✨")
                    else:
                        status.update(label="AI failed to generate plan.", state="error")

                except Exception as e:
                    logger.exception(e)
                    status.update(label="Error occurred.", state="error")
                    st.error(str(e))

        st.divider()
        st.caption(f"EcoGuide AI — Version {app_version}")


# ======================================================
# HELPERS
# ======================================================

def _clear_session():
    st.session_state.itinerary = None
    st.session_state.chat_history = []
    st.session_state.packing_list = {}
    st.session_state.travel_story = ""
    st.session_state.upgrade_suggestions = ""


def _save_generated(itinerary, query, priorities):
    st.session_state.itinerary = itinerary
    st.session_state.query = query
    st.session_state.current_trip_days = st.session_state.get("trip_days", 3)
    st.session_state.current_trip_budget = st.session_state.get("trip_budget", 1500)
    st.session_state.current_trip_location = st.session_state.get("trip_location", "Dubai")
    st.session_state.current_trip_travelers = st.session_state.get("trip_travelers", 1)
    st.session_state.current_trip_interests = st.session_state.get("trip_interests", [])
    st.session_state.current_trip_priorities = priorities
