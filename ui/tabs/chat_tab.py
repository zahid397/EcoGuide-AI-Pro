import streamlit as st
import json
from utils.logger import logger

def render_chat_tab(agent, itinerary):
    st.subheader("🤖 Ask AI about your Trip")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # আগের মেসেজ দেখানো
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # নতুন প্রশ্ন নেওয়া
    if prompt := st.chat_input("e.g., Is this place safe at night?"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # কনটেক্সট ছোট করে পাঠানো হচ্ছে যাতে টোকেন লিমিট এরর না খায়
                    plan_context = json.dumps(itinerary, default=str)[:3000]
                    
                    response = agent.ask_question(
                        plan_context=plan_context,
                        question=prompt
                    )
                    
                    if not response:
                        response = "I'm sorry, I couldn't connect to the server right now."
                        
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    logger.exception(e)
                    st.error("Network Error. Please try again.")
                    
