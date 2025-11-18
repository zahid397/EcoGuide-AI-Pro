import streamlit as st
from backend.agent_workflow import AgentWorkflow
import json
from typing import Dict, Any
from utils.logger import logger


def render_story_tab(agent: AgentWorkflow, itinerary: Dict[str, Any], user_name: str) -> None:
    st.subheader("Your AI-Generated Travel Story")

    # ---- Init safe session key ----
    if "travel_story" not in st.session_state:
        st.session_state.travel_story = ""

    try:
        # ---- Convert itinerary safely to pure JSON ----
        try:
            plan_context = json.dumps(itinerary, default=str)
        except:
            plan_context = "{}"   # fallback if serialization fails

        # ---- If no story exists, generate new ----
        if not st.session_state.travel_story:
            with st.spinner(f"Writing {user_name}'s travel story..."):

                story_md = agent.generate_story(
                    plan_context=plan_context,
                    user_name=user_name
                )

                # ---- Clean unexpected formatting ----
                if not isinstance(story_md, str):
                    story_md = str(story_md)

                # remove accidental code fences
                story_md = story_md.replace("```json", "```")
                story_md = story_md.replace("```", "")

                st.session_state.travel_story = story_md

        # ---- Display story ----
        st.markdown(st.session_state.travel_story)

    except Exception as e:
        logger.exception(f"Failed to generate story: {e}")
        st.error("Could not generate story.")
