import streamlit as st

def init_session_state() -> None:
    """Initialize all required Streamlit session_state keys."""

    defaults = {
        # Basic user inputs
        "user_name": "",
        "user_location": "",
        "trip_days": 3,
        "num_travelers": 1,
        "budget": 500,
        "interests": [],
        "preferences": {},

        # Main plan data
        "itinerary": None,          # ✅ FIXED: missing key
        "travel_plan": None,
        "rag_results": [],

        # For plan refinement
        "feedback": "",
        "upgrade_suggestions": "",
        "packing_list": "",
        "travel_story": "",

        # Profile system
        "profile": {
            "name": "User",
            "interests": [],
        },

        # Priority sliders
        "priorities": {
            "eco": 5,
            "budget": 5,
            "comfort": 5,
        },

        # Extra states used in UI
        "generated_plan_json": "",
        "last_query": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
