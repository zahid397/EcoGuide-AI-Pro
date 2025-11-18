import streamlit as st
import json
from utils.logger import logger

def render_story_tab(agent, itinerary, user_name):
    st.subheader("📖 Your AI-Generated Travel Story")
    
    try:
        # Check if story already exists in session
        if not st.session_state.get("travel_story"):
            with st.spinner(f"Writing {user_name}'s travel story..."):
                
                # Convert plan to text
                plan_context = json.dumps(itinerary, default=str)
                
                # Call AI
                story_md = agent.generate_story(
                    plan_context=plan_context,
                    user_name=user_name
                )
                
                # Save to session
                st.session_state.travel_story = story_md
                st.markdown(story_md)
        else:
            # Show cached story
            st.markdown(st.session_state.travel_story)
            
    except Exception as e:
        logger.exception(f"Failed to generate story: {e}")
        st.error("Could not generate travel story.")
        
