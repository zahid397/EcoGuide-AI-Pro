import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger
import time

def render_sidebar(agent, rag, app_version):
    with st.sidebar:
        st.header("✈️ Plan Trip")
        # ... (User Profile Code same as before) ...
        
        if st.button("Generate Plan 🚀", use_container_width=True):
             with st.status("Generating...", expand=True) as status:
                try:
                    # ... Logic ...
                    itinerary = agent.run(
                        query=query, rag_data=rag_results, budget=budget, interests=interests,
                        days=days, location=location, travelers=travelers,
                        user_profile=user_profile, priorities=priorities
                    )
                    if itinerary:
                        st.session_state.itinerary = itinerary
                        status.update(label="✅ Done!", state="complete")
                    else:
                        status.update(label="❌ Failed", state="error")
                except Exception as e:
                    logger.exception(e)
                    status.update(label="Error", state="error")

