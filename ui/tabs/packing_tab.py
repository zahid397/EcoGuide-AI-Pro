import streamlit as st

def render(agent, data, user):
    if st.button("🎒 Generate Packing List"):
        with st.spinner("Generating..."):
            res = agent.generate_packing_list(str(data), {"name": user}, "Smart")
            st.markdown(res)
            
