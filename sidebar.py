import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine
import time

def render_sidebar(agent: AgentWorkflow, rag: RAGEngine, app_version: str) -> None:
    with st.sidebar:
        st.header("✈️ Plan Your Trip")
        st.divider()
        
        # --- Profile Section ---
        st.header("👤 My Profile")
        user_name = st.text_input("Your Name", value=st.session_state.user_name, key="user_name_input")
        if user_name: st.session_state.user_name = user_name
        
        profile = load_profile(user_name)
        fav_interests = st.multiselect("My Favorite Interests", ["Beach", "History", "Adventure", "Food", "Nature"], default=profile.get("interests", []))
        pref_budget = st.slider("My Usual Budget ($)", 100, 5000, profile.get("budget", 1000), 100)
        
        if st.button("Save Profile", use_container_width=True):
            save_profile(user_name, fav_interests, pref_budget)
        
        st.divider()
        
        # --- Trip Plan Section ---
        st.header("📍 Plan a New Trip")
        
        # Priorities
        st.subheader("Trip Priorities")
        eco_p = st.slider("🟩 Eco Priority", 1, 10, 8)
        bud_p = st.slider("🟥 Budget Priority", 1, 10, 6)
        com_p = st.slider("🟧 Comfort Priority", 1, 10, 5)
        
        # Inputs
        interests = st.multiselect("Interests", ["Beach", "History", "Adventure", "Food", "Nature"], default=profile.get("interests", []))
        budget = st.slider("Total Budget ($)", 100, 10000, profile.get("budget", 1500), 100)
        
        c1, c2 = st.columns(2)
        days = c1.number_input("Days", 1, 30, 3)
        pax = c2.number_input("Travelers", 1, 20, 1)
        loc = st.selectbox("Location", ["Dubai", "Abu Dhabi", "Sharjah"])
        min_eco = st.slider("Min Eco Score", 7.0, 9.5, 8.0, 0.1)

        # --- GENERATE BUTTON ---
        if st.button("Generate Plan 🚀", use_container_width=True):
            if not interests:
                st.warning("⚠️ Please select at least one interest.")
            else:
                # Clear old data
                st.session_state.itinerary = None
                st.session_state.chat_history = []
                
                # ✳️ FIX: 'expand' -> 'expanded' (Corrected Typo)
                with st.status(f"Generating plan for {user_name}...", expanded=True) as status:
                    try:
                        status.write("🧠 Analyzing preferences...")
                        
                        # 1. Search RAG
                        status.write("🔍 Searching eco-spots...")
                        rag_results = rag.search(f"{loc} {interests}", top_k=15, min_eco_score=min_eco)
                        
                        # 2. Call AI Agent
                        status.write("🤖 Building itinerary...")
                        user_profile = {"name": user_name, "interests": fav_interests}
                        priorities = {"eco": eco_p, "budget": bud_p, "comfort": com_p}
                        
                        # Safe Query Build
                        query = f"{days}-day trip to {loc} for {pax} people. Budget: ${budget}. Interests: {interests}"
                        
                        itinerary = agent.run(
                            query=query, rag_data=rag_results, budget=budget,
                            interests=interests, days=days, location=loc, travelers=pax,
                            user_profile=user_profile, priorities=priorities
                        )
                        
                        if itinerary:
                            # Save to Session State
                            st.session_state.itinerary = itinerary
                            st.session_state.query = query
                            # Save current context for refining later
                            st.session_state.current_trip_days = days
                            st.session_state.current_trip_travelers = pax
                            st.session_state.current_trip_budget = budget
                            st.session_state.current_trip_location = loc
                            st.session_state.current_trip_interests = interests
                            st.session_state.current_trip_priorities = priorities
                            
                            status.update(label="✅ Plan Ready!", state="complete")
                            time.sleep(0.5)
                            st.rerun() # Force refresh to show content
                        else:
                            status.update(label="❌ AI returned empty plan.", state="error")
                            st.error("The AI could not generate a valid JSON plan. Please try again.")
                            
                    except Exception as e:
                        logger.exception(e)
                        status.update(label="❌ System Error", state="error")
                        st.error(f"Error: {str(e)}")

        st.divider()
        st.caption(f"v{app_version}")
        
