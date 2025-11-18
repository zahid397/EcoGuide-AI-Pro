import streamlit as st
from utils.profile import load_profile
from utils.logger import logger
import json

def render_packing(agent, itinerary: dict, user_name: str):
    """Renders the Packing List tab safely."""
    
    st.subheader("🎒 AI-Generated Packing List")

    # Choose list type
    list_type = st.radio(
        "Packing Style:",
        ["Smart", "Minimal", "Ultra-Light"],
        horizontal=True
    )

    # Load user profile (safe)
    user_profile = load_profile(user_name)
    if not user_profile:
        user_profile = {"name": user_name}

    # Session cache init
    if "packing_cache" not in st.session_state:
        st.session_state.packing_cache = {}

    cache_key = f"{list_type}_{user_name}"

    # Already generated?
    if cache_key in st.session_state.packing_cache:
        st.markdown(st.session_state.packing_cache[cache_key])
        return

    # Generate
    if st.button("✨ Generate Packing List"):
        try:
            with st.spinner("Preparing your packing list..."):
                output = agent.generate_packing_list(
                    plan_context=json.dumps(itinerary),
                    user_profile=user_profile,
                    list_type=list_type
                )

                # Save to session
                st.session_state.packing_cache[cache_key] = output

                st.markdown(output)

        except Exception as e:
            logger.exception(f"Packing list error: {e}")
            st.error("⚠️ Could not generate packing list.")

# ⭐⭐⭐ FIX: This alias makes UI call work ⭐⭐⭐
def render_packing_tab(agent, itinerary, user_name):
    return render_packing(agent, itinerary, user_name)
