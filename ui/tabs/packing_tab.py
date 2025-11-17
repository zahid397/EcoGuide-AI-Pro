import streamlit as st
from utils.profile import load_profile
from utils.logger import logger
from backend.agent_workflow import AgentWorkflow
import json
from typing import Dict, Any

def render_packing_tab(agent: AgentWorkflow, itinerary: Dict[str, Any], user_name: str) -> None:
    st.subheader("AI-Generated Packing List")
    
    list_type = st.radio(
        "Select List Type:",
        ("Smart List", "Minimal List", "Ultra-Light List"),
        horizontal=True, key="packing_list_type"
    )
    
    try:
        if list_type not in st.session_state.packing_list:
            with st.spinner(f"Generating your '{list_type}'..."):
                user_profile = load_profile(user_name)
                packing_list_md = agent.generate_packing_list(
                    plan_context=json.dumps(itinerary),
                    user_profile=user_profile,
                    list_type=list_type
                )
                st.session_state.packing_list[list_type] = packing_list_md
                st.markdown(packing_list_md)
        else:
            st.markdown(st.session_state.packing_list[list_type])
    except Exception as e:
        logger.exception(f"Failed to generate packing list: {e}")
        st.error(f"Could not generate packing list: {e}")
      
