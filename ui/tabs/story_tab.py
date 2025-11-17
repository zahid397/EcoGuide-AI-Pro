import streamlit as st
from backend.agent_workflow import AgentWorkflow
import json
from typing import Dict, Any
from utils.logger import logger

def render_story_tab(agent: AgentWorkflow, itinerary: Dict[str, Any], user_name: str) -> None:
    st.subheader("Your AI-Generated Travel Story")
    
    try:
        if not st.session_state.travel_story:
            with st.spinner(f"Writing {user_name}'s travel story..."):
                story_md = agent.generate_story(
                    plan_context=json.dumps(itinerary),
                    user_name=user_name
                )
                st.session_state.travel_story = story_md
                st.markdown(story_md)
        else:
            st.markdown(st.session_state.travel_story)
    except Exception as e:
        logger.exception(f"Failed to generate story: {e}")
        st.error(f"Could not generate story: {e}")
      
