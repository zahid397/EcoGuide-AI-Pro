import streamlit as st
import json
from utils.logger import logger

def render_chat_tab(agent, itinerary):
    st.subheader("🤖 Ask AI about your Trip")
    st.info("Ask follow-up questions about your plan, the location, or local customs.")
    
    # 1. Initialize Chat History if missing
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 2. Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # 3. Handle User Input
    if prompt := st.chat_input("e.g., Is Dubai safe at night?"):
        # Show User Message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Generate AI Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Convert itinerary to string context
                    plan_context = json.dumps(itinerary, default=str)
                    
                    response = agent.ask_question(
                        plan_context=plan_context,
                        question=prompt
                    )
                    
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    logger.exception(f"Chatbot failed: {e}")
                    st.error("Sorry, I couldn't process that question.")
                    
