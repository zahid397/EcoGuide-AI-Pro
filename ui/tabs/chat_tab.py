import streamlit as st
import json
from utils.logger import logger
from datetime import datetime

def render_chat_tab(agent, itinerary):
    """
    Interactive AI chat interface for asking questions about your travel itinerary.
    
    Features:
    - Contextual Q&A based on your trip plan
    - Conversation history with smart context management
    - Optimized token usage for long itineraries
    - Safety tips, recommendations, and trip modifications
    
    Args:
        agent: AI agent workflow instance with ask_question method
        itinerary: Complete travel plan dictionary
    """
    st.subheader("🤖 Ask AI About Your Trip")
    
    st.info("💬 Ask me anything about your itinerary: safety tips, alternatives, local customs, best times to visit, etc.")
    
    # Initialize chat history with proper structure
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize itinerary hash for change detection
    if "chat_itinerary_hash" not in st.session_state:
        st.session_state.chat_itinerary_hash = None
    
    # Validate inputs
    if not agent:
        st.error("❌ AI agent not available. Please check your configuration.")
        return
    
    if not itinerary:
        st.warning("⚠️ No itinerary loaded. Please generate a travel plan first to ask questions.")
        return
    
    # Check if itinerary has changed (invalidate chat context)
    try:
        current_hash = hash(json.dumps(itinerary, sort_keys=True, default=str))
    except Exception as e:
        logger.warning(f"Could not hash itinerary: {e}")
        current_hash = hash(str(itinerary))
    
    if st.session_state.chat_itinerary_hash != current_hash:
        # Itinerary changed - notify user
        if st.session_state.chat_history:
            st.warning("🔄 Your itinerary has changed. Previous chat context may be outdated.")
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
                st.session_state.chat_itinerary_hash = current_hash
                st.rerun()
        st.session_state.chat_itinerary_hash = current_hash
    
    # Sidebar with helpful prompts
    with st.sidebar:
        st.markdown("### 💡 Suggested Questions")
        sample_questions = [
            "Is this place safe at night?",
            "What are the best local restaurants?",
            "How do I get around the city?",
            "What should I pack for the weather?",
            "Are there any cultural customs I should know?",
            "What's the best time to visit these attractions?",
            "Can you suggest alternatives if it rains?",
            "What are some hidden gems nearby?"
        ]
        
        for q in sample_questions:
            if st.button(q, key=f"sample_{hash(q)}", use_container_width=True):
                # Trigger question programmatically
                st.session_state.pending_question = q
    
    # Display chat history with better formatting
    for i, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Add timestamp for better UX
            if "timestamp" in msg:
                st.caption(f"_{msg['timestamp']}_")
    
    # Clear chat button
    if st.session_state.chat_history:
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("🗑️ Clear Chat", help="Delete all chat history"):
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            # Export chat as text
            chat_export = "\n\n".join([
                f"{'User' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
                for msg in st.session_state.chat_history
            ])
            st.download_button(
                label="📥 Export",
                data=chat_export,
                file_name="travel_chat.txt",
                mime="text/plain",
                help="Download chat history"
            )
    
    # Handle pending question from sidebar
    if "pending_question" in st.session_state:
        prompt = st.session_state.pending_question
        del st.session_state.pending_question
        st.rerun()
    else:
        prompt = None
    
    # New question input
    user_input = st.chat_input("e.g., Is this place safe at night?")
    
    if user_input or prompt:
        question = user_input if user_input else prompt
        
        # Validate question
        if not question.strip():
            st.warning("Please enter a valid question.")
            return
        
        # Add user message to history
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user", 
            "content": question,
            "timestamp": timestamp
        })
        
        with st.chat_message("user"):
            st.markdown(question)
            st.caption(f"_{timestamp}_")
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Prepare optimized context
                    # Include recent chat for continuity but limit size
                    recent_chat = st.session_state.chat_history[-6:]  # Last 3 exchanges
                    chat_context = "\n".join([
                        f"{msg['role']}: {msg['content']}" 
                        for msg in recent_chat[:-1]  # Exclude current question
                    ])
                    
                    # Optimize itinerary context - prioritize relevant sections
                    plan_summary = _create_smart_context(itinerary, question)
                    
                    # Combine contexts efficiently
                    full_context = f"""
ITINERARY SUMMARY:
{plan_summary}

RECENT CONVERSATION:
{chat_context if chat_context else 'First question'}

CURRENT QUESTION: {question}
"""
                    
                    # Call AI with optimized context (max ~4000 chars)
                    response = agent.ask_question(
                        plan_context=full_context[:4000],
                        question=question
                    )
                    
                    # Validate response
                    if not response or not response.strip():
                        response = "I'm sorry, I couldn't generate an answer. Please try rephrasing your question."
                        logger.warning("Empty response from agent.ask_question()")
                    
                    # Clean up response
                    response = response.strip()
                    
                    # Display response
                    st.markdown(response)
                    response_timestamp = datetime.now().strftime("%I:%M %p")
                    st.caption(f"_{response_timestamp}_")
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response,
                        "timestamp": response_timestamp
                    })
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON serialization error: {e}")
                    error_msg = "⚠️ Error processing itinerary data. Please regenerate your plan."
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    
                except ConnectionError as e:
                    logger.error(f"Connection error: {e}")
                    error_msg = "🔌 Network error. Please check your connection and try again."
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    
                except Exception as e:
                    logger.exception(f"Chat error: {e}")
                    error_msg = "❌ An unexpected error occurred. Please try again."
                    st.error(error_msg)
                    
                    # Show error details in expander
                    with st.expander("🔍 Error Details"):
                        st.code(str(e))
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })


def _create_smart_context(itinerary, question):
    """
    Creates an optimized context by extracting relevant parts of itinerary
    based on the question keywords.
    
    Args:
        itinerary: Complete itinerary dictionary
        question: User's question string
    
    Returns:
        Optimized context string (~2000 chars max)
    """
    try:
        # Extract key information always needed
        summary = []
        
        # Basic info
        if "total_cost" in itinerary:
            summary.append(f"Budget: ${itinerary['total_cost']}")
        
        if "eco_score" in itinerary:
            summary.append(f"Eco Score: {itinerary['eco_score']}/10")
        
        # Day-by-day plan (abbreviated)
        if "plan" in itinerary and itinerary["plan"]:
            plan_text = str(itinerary["plan"])
            # Extract just day headers and key activities
            lines = plan_text.split("\n")
            key_lines = [l for l in lines if l.strip().startswith("#") or "Day" in l]
            summary.append("ITINERARY:\n" + "\n".join(key_lines[:15]))
        
        # Activities summary
        if "activities" in itinerary and itinerary["activities"]:
            activities = itinerary["activities"][:5]  # Top 5 activities
            activity_text = "KEY ACTIVITIES:\n" + "\n".join([
                f"- {a.get('name', 'Activity')}: ${a.get('cost', 0)}"
                for a in activities
            ])
            summary.append(activity_text)
        
        # Question-specific context
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["safe", "safety", "danger", "security"]):
            if "risk_safety_report" in itinerary:
                summary.append(f"SAFETY: {itinerary['risk_safety_report']}")
        
        if any(word in question_lower for word in ["weather", "rain", "climate", "temperature"]):
            if "weather_contingency" in itinerary:
                summary.append(f"WEATHER: {itinerary['weather_contingency']}")
        
        if any(word in question_lower for word in ["cost", "budget", "expensive", "price", "money"]):
            if "budget_breakdown" in itinerary:
                breakdown = json.dumps(itinerary["budget_breakdown"])
                summary.append(f"BUDGET BREAKDOWN: {breakdown}")
            if "cost_leakage_report" in itinerary:
                summary.append(f"COST ANALYSIS: {itinerary['cost_leakage_report']}")
        
        if any(word in question_lower for word in ["eco", "green", "sustainable", "carbon"]):
            if "carbon_saved" in itinerary:
                summary.append(f"CARBON SAVED: {itinerary['carbon_saved']}")
            if "carbon_offset_suggestion" in itinerary:
                summary.append(f"OFFSET: {itinerary['carbon_offset_suggestion']}")
        
        # Combine and limit size
        context = "\n\n".join(summary)
        return context[:2000]  # Hard limit for token efficiency
        
    except Exception as e:
        logger.warning(f"Could not create smart context: {e}")
        # Fallback to basic JSON
        return json.dumps(itinerary, default=str)[:2000]
