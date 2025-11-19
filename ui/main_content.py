import streamlit as st
import pandas as pd
import json
import time  
from utils.cards import get_card_css
from utils.cost import calculate_real_cost

# Import ALL tabs
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab, 
    packing_tab, story_tab, chat_tab, map_tab, share_tab
)

def render_main_content(agent, rag):
    if not st.session_state.itinerary:
        st.info("👈 Please fill in your trip details in the sidebar and click 'Generate Plan 🚀'.")
        return

    # --- Ensure Itinerary is a Dictionary ---
    data = st.session_state.itinerary
    
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            st.error(f"Data Error: Could not parse itinerary. {e}")
            return 
            
    st.session_state.itinerary = data
    # ----------------------------------------

    st.markdown(get_card_css(), unsafe_allow_html=True)
    
    # Metrics
    days = st.session_state.get("current_trip_days", 3)
    pax = st.session_state.get("current_trip_travelers", 1)
    loc = st.session_state.get("current_trip_location", "Dubai")
    budget = st.session_state.get("current_trip_budget", 1500)
    interests = st.session_state.get("current_trip_interests", [])
    user = st.session_state.get("user_name", "User")
    
    # Safe Cost Calculation
    activities = data.get('activities', [])
    if isinstance(activities, str): activities = [] 
    
    cost = calculate_real_cost(activities, days, pax)
    
    st.subheader(f"🚀 {user}'s Eco-Trip to {loc}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Est. Cost", f"${cost}")
    c2.metric("Eco Score", f"{data.get('eco_score', 0)}/10")
    c3.metric("Carbon Saved", data.get('carbon_saved', '0kg'))
    
    # Tabs
    tabs = st.tabs(["Overview", "Analysis", "Plan", "Activities", "Packing", "Story", "Chat", "Map", "Share"])
    
    with tabs[0]: overview_tab.render_overview(data, budget, pax)
    with tabs[1]: analysis_tab.render_analysis(data)
    with tabs[2]: plan_tab.render_plan(data, loc, user)
    with tabs[3]: list_tab.render_list(data)
    with tabs[4]: packing_tab.render_packing_tab(agent, data, user)
    with tabs[5]: story_tab.render_story_tab(agent, data, user)
    with tabs[6]: chat_tab.render_chat_tab(agent, data)
    with tabs[7]: map_tab.render_map_tab(loc)
    with tabs[8]: share_tab.render_share_tab(days, loc, interests, budget)

    # --- Refine Plan Section ---
    st.divider()
    st.subheader("🤖 Refine Your Plan")
    
    refinement_query = st.text_input("What would you like to change?", key="refine_input", placeholder="e.g., 'Make it cheaper' or 'Add more beach activities'")
    
    st.markdown("##### **One-Click Replan**")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    if c1.button("💰 Cheaper", use_container_width=True):
        refinement_query = "Find cheaper alternatives to reduce cost."
    if c2.button("🎉 More Fun", use_container_width=True):
        refinement_query = "Add more high-rated fun activities."
    if c3.button("😌 Relaxed", use_container_width=True):
        refinement_query = "Make the schedule more relaxed with free time."
    if c4.button("🗓️ +1 Day", use_container_width=True):
        refinement_query = "Add 1 more day to the trip."
    if c5.button("💸 -20% Budget", use_container_width=True):
        refinement_query = "Reduce the budget by 20%."
    
    if st.button("Refine Plan 🔄", type="primary", use_container_width=True) or refinement_query:
        if refinement_query:
            st.session_state.chat_history = []
            st.session_state.packing_list = {}
            
            with st.status(f"Refining plan: '{refinement_query}'...", expanded=True) as status:
                try:
                    status.write("🧠 Re-analyzing request...")
                    from utils.profile import load_profile
                    from backend.rag_engine import RAGEngine 
                    
                    # Re-init RAG just for search context
                    rag = RAGEngine()
                    rag_results = rag.search(refinement_query)
                    
                    user_profile = load_profile(user)
                    user_profile['name'] = user
                    
                    status.write("🤖 Re-building itinerary...")
                    
                    current_json_str = json.dumps(data, default=str)

                    new_itinerary = agent.refine_plan(
                        previous_plan_json=current_json_str,
                        feedback_query=refinement_query,
                        rag_data=rag_results,
                        user_profile=user_profile,
                        travelers=pax,
                        days=days,
                        budget=budget
                    )
                    
                    if new_itinerary:
                        if isinstance(new_itinerary, str):
                            new_itinerary = json.loads(new_itinerary)
                            
                        st.session_state.itinerary = new_itinerary
                        status.update(label="✅ Plan Refined!", state="complete")
                        time.sleep(0.5) # ✅ Now this will work perfectly
                        st.rerun()
                    else:
                        status.update(label="❌ AI Failed", state="error")
                        st.error("AI could not refine the plan.")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.warning(f"Could not refine plan: {e}")
                    
