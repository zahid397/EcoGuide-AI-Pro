import streamlit as st

def render(agent, data):
    q = st.chat_input("Ask about trip...")
    if q:
        st.chat_message("user").write(q)
        with st.spinner("..."):
            ans = agent.ask_question(str(data), q)
            st.chat_message("ai").write(ans)
            
