import streamlit as st
def init_session_state():
    defaults = {
        'itinerary': None, 'query': "", 'user_name': "Zahid",
        'chat_history': [], 'packing_list': {}, 'travel_story': "",
        'upgrade_suggestions': "", 'trip_days': 3, 'trip_travelers': 1,
        'trip_budget': 1500, 'trip_location': "Dubai", 'trip_interests': [],
        'trip_min_eco': 8.0, 'current_trip_days': 3, 'current_trip_budget': 1500
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
          
