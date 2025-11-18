import streamlit as st
from utils.profile import load_profile
from utils.logger import logger
from backend.agent_workflow import AgentWorkflow
import json
from typing import Dict, Any

def render_packing_tab(agent: AgentWorkflow, itinerary: Dict[str, Any], user_name: str) -> None:
    st.subheader("🎒 AI-Generated Packing List")

    # -------------------------------------
    # 1️⃣ SAFE SESSION STATE INITIALIZATION
    # -------------------------------------
    if "packing_list" not in st.session_state:
        st.session_state.packing_list = {}

    # -------------------------------------
    # 2️⃣ SELECT LIST TYPE
    # -------------------------------------
    list_type = st.radio(
        "Select List Type:",
        ("Smart List", "Minimal List", "Ultra-Light List"),
        horizontal=True,
        key="packing_list_type"
    )

    try:
        # -------------------------------------
        # 3️⃣ IF LIST NOT CACHED → GENERATE NEW
        # -------------------------------------
        if list_type not in st.session_state.packing_list:

            with st.spinner(f"Generating your '{list_type}' list..."):
                
                user_profile = load_profile(user_name)

                packing_list_md = agent.generate_packing_list(
                    plan_context=json.dumps(itinerary),
                    user_profile=user_profile,
                    list_type=list_type
                )

                # Cache the result
                st.session_state.packing_list[list_type] = packing_list_md

            st.markdown(packing_list_md)

        # -------------------------------------
        # 4️⃣ SHOW FROM CACHE
        # -------------------------------------
        else:
            st.markdown(st.session_state.packing_list[list_type])

    except Exception as e:
        logger.exception(f"Failed to generate packing list: {e}")
        st.error("⚠️ Could not generate packing list. Using fallback list.")

        fallback_md = """
        ### Basic Packing List (Fallback)
        - Passport (Critical!)
        - Phone + Charger
        - Water Bottle
        - Lightweight Clothes
        - Comfortable Shoes
        """
        st.markdown(fallback_md)
