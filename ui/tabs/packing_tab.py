import streamlit as st
from utils.profile import load_profile
from utils.logger import logger
import json

def render_packing_tab(agent, itinerary, user_name):
    st.subheader("🎒 AI-Generated Packing List")
    
    # 1. List Type Selection
    list_type = st.radio(
        "Select List Type:",
        ("Smart List", "Minimal List", "Ultra-Light List"),
        horizontal=True, 
        key="packing_list_radio"  # Unique key to prevent errors
    )
    
    try:
        # 2. Check if we need to generate it
        # Ensure session_state.packing_list is a dictionary
        if not isinstance(st.session_state.packing_list, dict):
            st.session_state.packing_list = {}

        if list_type not in st.session_state.packing_list:
            with st.spinner(f"Generating your '{list_type}'..."):
                # Load User Data
                user_profile = load_profile(user_name)
                
                # Convert Plan to Text for AI
                plan_context = json.dumps(itinerary, default=str)
                
                # Call AI Agent
                packing_list_md = agent.generate_packing_list(
                    plan_context=plan_context,
                    user_profile=user_profile,
                    list_type=list_type
                )
                
                # Save to Cache
                st.session_state.packing_list[list_type] = packing_list_md
                
        # 3. Display Result
        if list_type in st.session_state.packing_list:
            st.markdown(st.session_state.packing_list[list_type])
        else:
            st.warning("Click 'Generate Plan' first to see packing items.")

    except Exception as e:
        logger.exception(f"Failed to generate packing list: {e}")
        st.error(f"Could not generate packing list. Error: {e}")
        
