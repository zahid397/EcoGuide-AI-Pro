import streamlit as st

def render(agent, data, user):
    if st.button("📖 Write Story"):
        with st.spinner("Writing..."):
            res = agent.generate_story(str(data), user)
            st.markdown(res)
            
