import streamlit as st

def init_session_state():
    """Initialize session state variables safely."""
    
    defaults = {
        "chat_history": [],
        "generated_plan": None,
        "rag_results": [],
        "last_query": "",
        "user_profile": {
            "name": "User",
            "interests": []
        },
        "priorities": {
            "eco": 5,
            "budget": 5,
            "comfort": 5
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
