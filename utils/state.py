import streamlit as st

def init_session_state() -> None:
    """Initializes all required session_state keys safely."""

    defaults = {
        "user_name": "",
        "user_location": "",
        "trip_days": 3,
        "num_travelers": 1,
        "budget": 500,
        "interests": [],
        "preferences": {},
        "travel_plan": None,
        "rag_results": [],
        "feedback": "",
        "upgrade_suggestions": "",
        "packing_list": "",
        "travel_story": "",
        "profile": {
            "name": "User",
            "interests": [],
        },
        "priorities": {
            "eco": 5,
            "budget": 5,
            "comfort": 5,
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
