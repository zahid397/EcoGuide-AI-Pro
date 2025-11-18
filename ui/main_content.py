import streamlit as st
from utils.cards import get_card_css
from utils.cost import calculate_real_cost
from ui.tabs import overview_tab, analysis_tab, plan_tab, list_tab, packing_tab, story_tab, chat_tab

def render_main_content(agent, rag):
    if not st.session_state.itinerary:
        st.info("Please generate a plan from the sidebar.")
        return

    data = st.session_state.itinerary
    st.markdown(get_card_css(), unsafe_allow_html=True)
    
    # Metrics
    days = st.session_state.get("current_trip_days", 3)
    pax = st.session_state.get("current_trip_travelers", 1)
    cost = calculate_real_cost(data.get('activities', []), days, pax)
    
    st.subheader("🚀 Your Eco-Trip Plan")
    c1, c2, c3 = st.columns(3)
    c1.metric("Est. Cost", f"${cost}")
    c2.metric("Eco Score", f"{data.get('eco_score', 0)}/10")
    c3.metric("Carbon Saved", data.get('carbon_saved', '0kg'))
    
    # Tabs
    tabs = st.tabs(["Overview", "Analysis", "Plan", "Activities", "Packing", "Story", "Chat"])
    
    with tabs[0]: overview_tab.render(data, 1500, pax) # Pass budget manually or from state
    with tabs[1]: analysis_tab.render(data)
    with tabs[2]: plan_tab.render(data, "Dubai", "User")
    with tabs[3]: list_tab.render(data)
    with tabs[4]: packing_tab.render(agent, data, "User")
    with tabs[5]: story_tab.render(agent, data, "User")
    with tabs[6]: chat_tab.render(agent, data)
        
