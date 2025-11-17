import streamlit as st
from backend.agent_workflow import AgentWorkflow
import json
from typing import Dict, Any
from utils.logger import logger

def render_chat_tab(agent: AgentWorkflow, itinerary: Dict[str, Any]) -> None:
    st.subheader("Ask me anything about your trip")
    st.info("Ask follow-up questions about your plan, the location, or local customs.")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("e.g., Is Dubai safe at night?"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = agent.ask_question(
                        plan_context=json.dumps(itinerary),
                        question=prompt
                    )
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    logger.exception(f"Chatbot failed: {e}")
                    st.error(f"Chatbot failed: {e}")
                  
