import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine
import time
from typing import Any

def render_sidebar(agent: AgentWorkflow, rag: RAGEngine, app_version: str) -> None:
    """Renders the sidebar UI and handles plan generation."""
    with st.sidebar:
        st.header("✈️ Plan Your Trip")
        st.divider()
        st.header("👤 My Profile")
        
        user_name = st.text_input("Your Name", 
                                  value=st.session_state.user_name, 
                                  key="user_name_input", 
                                  help="Enter your name to save and load your personal profile.")
        
        if user_name:
             st.session_state.user_name = user_name
        
        profile = load_profile(user_name)
        
        fav_interests = st.multiselect("My Favorite Interests", 
                                       ["Beach", "History", "Adventure", "Food", "Nature"], 
                                       default=profile.get("interests", []), 
                                       help="Select your all-time favorite interests for personalized suggestions.")
        pref_budget = st.slider("My Usual Budget ($)", 100, 5000, 
                                profile.get("budget", 1000), 100, 
                                help="Set your typical budget for the AI to remember.")
        
        if st.button("Save Profile", use_container_width=True):
            if len(user_name) < 2 or len(user_name) > 50:
                st.error("Name must be between 2 and 50 characters.")
            else:
                save_profile(user_name, fav_interests, pref_budget)
        
        st.divider()
        st.header("📍 Plan a New Trip")
        st.subheader("Trip Priorities")
        
        st.slider("🟩 Eco Priority", 1, 10, 8, 
                  help="How important is sustainability? (1=Low, 10=Max)", 
                  key="trip_eco_priority")
        st.slider("🟥 Budget Priority", 1, 10, 6, 
                  help="How strict is your budget? (1=Flexible, 10=Strict)", 
                  key="trip_budget_priority")
        st.slider("🟧 Comfort Priority", 1, 10, 5, 
                  help="How important is comfort/luxury? (1=Basic, 10=Max)", 
                  key="trip_comfort_priority")
        
        st.multiselect("Interests for this trip", 
                       ["Beach", "History", "Adventure", "Food", "Nature"], 
                       default=profile.get("interests", []), 
                       help="Select interests just for this specific trip.", 
                       key="trip_interests")
        st.slider("Total Budget ($)", 100, 10000, 
                  profile.get("budget", 1500), 100, 
                  help="Set the *total* budget for the trip in USD.", 
                  key="trip_budget")
        
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Number of Days", 1, 30, 3, 
                            help="How many days will your trip be?", 
                            key="trip_days")
        with col2:
            st.number_input("Number of Travelers", 1, 20, 1, 
                            help="How many people are traveling?", 
                            key="trip_travelers")
            
        st.selectbox("Base Location", ["Dubai", "Abu Dhabi", "Sharjah"], 
                     help="Choose your starting city.", 
                     key="trip_location")
        st.slider("Minimum Eco Score", 7.0, 9.5, 8.0, 0.1, 
                  help="Filter out locations below this eco-rating (1-10).", 
                  key="trip_min_eco")

        if st.button("Generate Plan 🚀", use_container_width=True):
            
            is_valid = _validate_inputs()
            
            if is_valid:
                _clear_session_state()
                
                with st.status(f"Generating plan for {st.session_state.user_name}...", expand=True) as status:
                    try:
                        status.write("🧠 [1/3] Analyzing your preferences and profile...")
                        priorities, query, user_profile = _build_query_and_profile()
                        
                        status.write("🔍 [2/3] Searching for the best eco-friendly spots...")
                        rag_results = rag.search(query, top_k=15, min_eco_score=st.session_state.trip_min_eco)
                        
                        if not rag_results:
                            status.update(label="No matching spots found.", state="error")
                        else:
                            status.write("🤖 [3/3] Assembling your personalized itinerary...")
                            itinerary = agent.run(
                                query=query, rag_data=rag_results, 
                                budget=st.session_state.trip_budget,
                                interests=st.session_state.trip_interests, 
                                days=st.session_state.trip_days, 
                                location=st.session_state.trip_location,
                                travelers=st.session_state.trip_travelers, 
                                user_profile=user_profile,
                                priorities=priorities
                            )
                            
                            if itinerary:
                                _set_session_state_on_generate(itinerary, query, priorities) # Fix 6
                                status.update(label="✅ Plan generated successfully!", state="complete")
                                st.toast("Your Eco-Trip Plan is ready! 🌍✨", icon="🎉")
                                time.sleep(0.5)
                            else:
                                status.update(label="AI agent failed to respond.", state="error")
                                st.error("The AI agent failed to generate a response. This might be due to a connection issue or an invalid API key. Please try again.")
                    except Exception as e:
                        logger.exception(f"Plan generation failed: {e}") # Fix 3
                        status.update(label="Generation failed.", state="error")
                        st.error(f"An unexpected error occurred: {e}")
        
        # --- Fix 7: App Version ---
        st.divider()
        st.caption(f"EcoGuide AI — Version {app_version}")

def _validate_inputs() -> bool:
    """Fix 9: Validates all sidebar inputs."""
    is_valid = True
    if not st.session_state.trip_interests:
        st.warning("Please select at least one interest.")
        is_valid = False
    if st.session_state.trip_days < 1 or st.session_state.trip_days > 30:
        st.error("Days must be between 1 and 30.")
        is_valid = False
    if st.session_state.trip_travelers < 1 or st.session_state.trip_travelers > 20:
        st.error("Travelers must be between 1 and 20.")
        is_valid = False
    return is_valid

def _clear_session_state() -> None:
    """Clears old plan data before generation."""
    st.session_state.itinerary = None
    st.session_state.chat_history = []
    st.session_state.packing_list = {}
    st.session_state.travel_story = ""
    st.session_state.upgrade_suggestions = ""

def _build_query_and_profile() -> tuple[dict, str, dict]:
    """Builds the query and profile objects from session state."""
    priorities = {
        "eco": st.session_state.trip_eco_priority,
        "budget": st.session_state.trip_budget_priority,
        "comfort": st.session_state.trip_comfort_priority
    }
    query = f"A {st.session_state.trip_days}-day trip to {st.session_state.trip_location} for {st.session_state.trip_travelers} people, focusing on {', '.join(st.session_state.trip_interests)}. Priorities: Eco={priorities['eco']}/10, Budget={priorities['budget']}/10, Comfort={priorities['comfort']}/10. Total budget is ${st.session_state.trip_budget}."
    user_profile = load_profile(st.session_state.user_name)
    user_profile['name'] = st.session_state.user_name
    return priorities, query, user_profile

def _set_session_state_on_generate(itinerary: dict, query: str, priorities: dict) -> None:
    """Fix 6: Writes to session state ONCE after generation."""
    st.session_state.itinerary = itinerary
    st.session_state.query = query
    st.session_state.current_trip_days = st.session_state.trip_days
    st.session_state.current_trip_travelers = st.session_state.trip_travelers
    st.session_state.current_trip_budget = st.session_state.trip_budget
    st.session_state.current_trip_location = st.session_state.trip_location
    st.session_state.current_trip_interests = st.session_state.trip_interests
    st.session_state.current_trip_priorities = priorities
  
