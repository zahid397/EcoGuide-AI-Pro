import streamlit as st

def render_story_tab(agent, itinerary, user_name):
    """Renders the Story tab safely."""
    
    st.subheader("📖 AI-Generated Travel Story")

    # If already generated, reuse cached story
    if st.session_state.get("travel_story"):
        st.markdown(st.session_state.travel_story)
        return

    # Generate Story Button
    if st.button("✨ Generate Story", use_container_width=True):
        with st.spinner("Writing your travel story..."):
            try:
                story = agent.generate_story(
                    plan_context=str(itinerary),
                    user_name=user_name
                )
                st.session_state.travel_story = story
                st.markdown(story)

            except Exception as e:
                st.error("⚠️ Failed to generate story.")
                st.code(str(e))
