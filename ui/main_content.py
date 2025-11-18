import streamlit as st
import pandas as pd
import time
import json
import os
from utils.cards import get_card_css
from utils.cost import calculate_real_cost
from utils.profile import load_profile
from utils.logger import logger

# Import ALL tabs
from ui.tabs import (
    overview_tab,
    analysis_tab,
    plan_tab,
    list_tab,
    packing_tab,
    story_tab,
    chat_tab,
    map_tab,
    share_tab
)

def render_main_content(agent, rag):

    # --- 1. Check if Plan Exists ---
    if not st.session_state.itinerary:
        st.info("👈 Please fill in your trip details in the sidebar and click **Generate Plan 🚀**.")
        return

    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)

    # --- 2. Load Session Data ---
    # Using .get() for safety
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    location = st.session_state.get("current_trip_location", "Dubai")
    budget = st.session_state.get("current_trip_budget", 1500)
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    min_eco = st.session_state.get("trip_min_eco", 8.0)
    user_name = st.session_state.get("user_name", "Traveler")

    # --- 3. Metrics & Header ---
    total_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)

    st.subheader(f"🌍 {user_name}'s Eco Trip — {location}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost", f"${total_cost}")
    col2.metric("Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved", f"{itinerary.get('carbon_saved', '0kg')}")

    # --- 4. Render Tabs ---
    tabs = st.tabs([
        "✨ Overview", "🔬 Analysis", "📅 Plan", "🏄 Activities", 
        "🎒 Packing", "📖 Story", "🤖 Ask AI", "🗺️ Map", "🔗 Share"
    ])

    with tabs[0]:
        overview_tab.render_overview(itinerary, budget, travelers)
    with tabs[1]:
        analysis_tab.render_analysis(itinerary)
    with tabs[2]:
        plan_tab.render_plan(itinerary, location, user_name)
    with tabs[3]:
        list_tab.render_list(itinerary)
    with tabs[4]:
        # Passing agent to generate list on demand
        packing_tab.render_packing_tab(agent, itinerary, user_name)
    with tabs[5]:
        story_tab.render_story_tab(agent, itinerary, user_name)
    with tabs[6]:
        chat_tab.render_chat_tab(agent, itinerary)
    with tabs[7]:
        map_tab.render_map_tab(location)
    with tabs[8]:
        share_tab.render_share_tab(days, location, interests, budget)

    # --- 5. Refine Plan Section (IMPORTANT) ---
    st.divider()
    st.subheader("🤖 Refine Your Plan")
    
    refinement_query = st.text_input("What would you like to change?", key="refine_input", placeholder="e.g., 'Make it cheaper' or 'Add more beach activities'")
    
    st.markdown("##### **One-Click Replan**")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Quick Action Buttons
    if c1.button("💰 Cheaper", use_container_width=True):
        refinement_query = "Find cheaper alternatives to reduce cost."
    if c2.button("🎉 More Fun", use_container_width=True):
        refinement_query = "Add more high-rated fun activities."
    if c3.button("😌 Relaxed", use_container_width=True):
        refinement_query = "Make the schedule more relaxed with free time."
    if c4.button("🗓️ +1 Day", use_container_width=True):
        refinement_query = f"Add 1 more day to the trip."
    if c5.button("💸 -20% Budget", use_container_width=True):
        refinement_query = f"Reduce the budget by 20%."
    
    # Logic to handle Refinement
    if st.button("Refine Plan 🔄", type="primary", use_container_width=True) or refinement_query:
        if refinement_query:
            # Reset tab caches
            st.session_state.chat_history = []
            st.session_state.packing_list = {}
            st.session_state.travel_story = ""
            
            with st.status(f"Refining plan: '{refinement_query}'...", expanded=True) as status:
                try:
                    status.write("🧠 Re-analyzing request...")
                    user_profile = load_profile(user_name)
                    user_profile['name'] = user_name
                    
                    status.write("🔍 Finding new spots...")
                    rag_results = rag.search(refinement_query, top_k=15, min_eco_score=min_eco)
                    
                    status.write("🤖 Re-building itinerary...")
                    
                    # Adjust days/budget if requested
                    new_days = days + 1 if "+1 Day" in refinement_query or "Add 1" in refinement_query else days
                    new_budget = budget * 0.8 if "-20%" in refinement_query else budget

                    new_itinerary = agent.refine_plan(
                        previous_plan_json=json.dumps(itinerary),
                        feedback_query=refinement_query,
                        rag_data=rag_results,
                        user_profile=user_profile,
                        priorities=priorities,
                        travelers=travelers,
                        days=new_days,
                        budget=new_budget
                    )
                    
                    if new_itinerary:
                        st.session_state.itinerary = new_itinerary
                        # Update session state with new constraints
                        st.session_state.current_trip_days = new_days
                        st.session_state.current_trip_budget = new_budget
                        
                        status.update(label="✅ Plan Refined!", state="complete")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        status.update(label="❌ AI Failed", state="error")
                        st.error("AI could not refine the plan.")
                except Exception as e:
                    logger.exception(e)
                    status.update(label="Error", state="error")
                    st.error(f"Refinement Error: {e}")

    # --- 6. Feedback Section ---
    st.divider()
    st.subheader("How was this plan?")
    rating = st.slider("Rate (1-5)", 1, 5, 3)
    if st.button("Submit Feedback"):
        # Save feedback to CSV for RAG improvement
        data = [{"query": location, "rating": rating, "item_name": act.get('name')} for act in itinerary.get('activities', [])]
        if data:
            try:
                df = pd.DataFrame(data)
                file_path = "data/feedback.csv"
                df.to_csv(file_path, mode='a', index=False, header=not os.path.exists(file_path))
                st.success("Feedback Submitted! 👍")
            except Exception as e:
                st.error("Could not save feedback.")
                
