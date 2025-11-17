import streamlit as st
from typing import Dict, Any
import pandas as pd
from utils.cost import calculate_real_cost
from utils.profile import load_profile
from utils.cards import get_card_css
from utils.logger import logger
from ui.tabs import (
    overview_tab, analysis_tab, plan_tab, list_tab, 
    packing_tab, story_tab, map_tab, chat_tab, share_tab
)
import time
import json
from backend.agent_workflow import AgentWorkflow
from backend.rag_engine import RAGEngine
from typing import Any

def render_main_content(agent: AgentWorkflow, rag: RAGEngine) -> None:
    """Renders the main content area (metrics, tabs, and refine logic)."""
    
    if not st.session_state.itinerary:
        st.info("Please fill in your trip details in the sidebar and click 'Generate Plan 🚀'.")
        return

    # --- Load Itinerary & Trip Params (Fix 4) ---
    itinerary = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)
    
    # Get current trip params from session state (set during generation)
    days = st.session_state.get("current_trip_days", 3)
    travelers = st.session_state.get("current_trip_travelers", 1)
    budget = st.session_state.get("current_trip_budget", 1000)
    location = st.session_state.get("current_trip_location", "Dubai")
    interests = st.session_state.get("current_trip_interests", [])
    priorities = st.session_state.get("current_trip_priorities", {})
    min_eco = st.session_state.get("trip_min_eco", 8.0)
    user_name = st.session_state.get("user_name", "Zahid")

    # Calculate real cost (does not write to session state)
    real_cost = calculate_real_cost(itinerary.get("activities", []), days, travelers)
    
    st.subheader(f"🚀 {user_name}'s Custom Eco-Tour: {location}")
    
    # --- Metrics (Fix 4) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cost (Calculated)", f"${real_cost}")
    col2.metric("Average Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col3.metric("Carbon Saved (Approx.)", f"{itinerary.get('carbon_saved', '0kg')}")
    
    # --- Tabs ---
    tab_overview, tab_analysis, tab_plan, tab_list, tab_pack, tab_story, tab_map, tab_chat, tab_share = st.tabs([
        "✨ Overview", "🔬 AI Analysis", "📅 Detailed Plan", "🏄‍♂️ Activity List", "🎒 Packing List", 
        "📖 My Travel Story", "🗺️ Location Map", "🤖 Ask AI", "🔗 Share Plan"
    ])

    with tab_overview:
        overview_tab.render_overview(itinerary, budget, travelers)
    with tab_analysis:
        analysis_tab.render_analysis(itinerary)
    with tab_plan:
        plan_tab.render_plan(itinerary, location, user_name)
    with tab_list:
        list_tab.render_list(itinerary)
    with tab_pack:
        packing_tab.render_packing_tab(agent, itinerary, user_name)
    with tab_story:
        story_tab.render_story_tab(agent, itinerary, user_name)
    with tab_map:
        map_tab.render_map_tab(location)
    with tab_chat:
        chat_tab.render_chat_tab(agent, itinerary)
    with tab_share:
        share_tab.render_share_tab(days, location, interests, budget)

    # --- Refine Plan Section ---
    st.divider()
    st.subheader("🤖 Refine Your Plan")
    refinement_query = st.text_input("What would you like to change?", key="refine_input", label_visibility="visible", placeholder="e.g., 'Make it cheaper' or 'Add more beach activities'")
    
    st.markdown("##### **One-Click Replan & What-If Simulator**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if col1.button("💰 Cheaper", use_container_width=True, help="Find cheaper alternatives"):
        refinement_query = "Find cheaper alternatives for the hotels and activities to reduce the total cost."
    if col2.button("🎉 More Fun", use_container_width=True, help="Add more high-rated activities"):
        refinement_query = "Add more high-rated activities, even if it increases the cost slightly."
    if col3.button("😌 More Relaxed", use_container_width=True, help="Reduce the number of activities"):
        refinement_query = "The plan looks too busy. Make it more relaxed with more free time."
    if col4.button("🗓️ Add 1 Day", use_container_width=True, help="What if I add one more day?"):
        refinement_query = f"What if I add 1 more day? Re-plan the trip for {days + 1} days."
    if col5.button("💸 Cut Budget 20%", use_container_width=True, help="What if I reduce my budget by 20%?"):
        refinement_query = f"What if I reduce my budget by 20%? The new budget is ${budget * 0.8}."
    
    if st.button("Refine Plan 🔄", use_container_width=True, type="primary"):
        pass # Will be caught by the logic below

    if refinement_query: # This triggers if any button was pressed
        st.session_state.chat_history = []; st.session_state.packing_list = {}; st.session_state.travel_story = ""; st.session_state.upgrade_suggestions = ""
        
        with st.status(f"Refining plan based on: '{refinement_query}'...", expand=True) as status:
            # --- Fix 10: Error Wrapper ---
            try:
                status.write("🧠 [1/3] Re-analyzing your request...")
                user_profile = load_profile(user_name); user_profile['name'] = user_name
                
                status.write("🔍 [2/3] Searching for new matching spots...")
                rag_results = rag.search(refinement_query, top_k=15, min_eco_score=min_eco)
                
                status.write("🤖 [3/3] Re-building the itinerary...")
                
                new_days = days + 1 if "add 1 more day" in refinement_query else days
                new_budget = budget * 0.8 if "reduce my budget by 20%" in refinement_query else budget

                new_itinerary = agent.refine_plan(
                    previous_plan_json=json.dumps(itinerary),
                    feedback_query=refinement_query,
                    rag_data=rag_results, user_profile=user_profile,
                    priorities=priorities, travelers=travelers, 
                    days=new_days, budget=new_budget
                )
                
                if new_itinerary:
                    st.session_state.itinerary = new_itinerary # Write once
                    
                    st.session_state.current_trip_days = new_days
                    st.session_state.current_trip_budget = new_budget

                    status.update(label="✅ Plan refined successfully!", state="complete")
                    time.sleep(0.5)
                    st.toast("Plan updated! 🤖🔄", icon="✅")
                    st.rerun()
                else:
                    status.update(label="AI failed to refine.", state="error")
                    st.error("The AI agent failed to refine the plan. Please try a different request.")
            except Exception as e:
                logger.exception(f"Plan refinement failed: {e}") # Fix 3
                status.update(label="Refinement failed.", state="error")
                st.error(f"An unexpected error occurred during refinement: {e}")

    # --- AI Upgrade Suggestions (Fix 4) ---
    if st.button("Suggest Premium Upgrades ✨", use_container_width=True):
        if not st.session_state.upgrade_suggestions:
            with st.spinner("Analyzing upgrade potential..."):
                try:
                    rag_results = rag.search("luxury comfort premium eco", top_k=5, min_eco_score=min_eco)
                    suggestions = agent.get_upgrade_suggestions(
                        plan_context=json.dumps(st.session_state.itinerary),
                        user_profile=load_profile(user_name),
                        rag_data=rag_results
                    )
                    st.session_state.upgrade_suggestions = suggestions
                except Exception as e:
                    logger.exception(f"Upgrade suggestion failed: {e}")
                    st.error(f"Could not get upgrades: {e}")
        
        with st.expander("🌟 AI Upgrade Ideas", expanded=True):
            st.markdown(st.session_state.get("upgrade_suggestions", "No suggestions available."))
            
    _render_feedback_section(itinerary)

def _render_feedback_section(itinerary: Dict[str, Any]) -> None:
    """Renders the user feedback section."""
    st.divider()
    st.subheader("How was this plan?")
    feedback_rating = st.slider("Rate this plan (1-5 ⭐)", 1, 5, 3, help="Your rating trains the AI to make better suggestions next time.")
    
    if st.button("Submit Feedback"):
        feedback_data = []
        for item in itinerary.get("activities", []):
            if 'name' in item: 
                feedback_data.append({
                    "query": st.session_state.query, 
                    "rating": feedback_rating, 
                    "item_name": item.get('name')
                })
        if feedback_data:
            try:
                df = pd.DataFrame(feedback_data)
                df.to_csv(FEEDBACK_FILE, mode='a', index=False, header=not os.path.exists(FEEDBACK_FILE))
                st.toast("Feedback submitted! 🌍✨", icon="👍")
            except Exception as e:
                logger.exception(f"Failed to save feedback: {e}")
                st.error("Could not save feedback.")
                  
