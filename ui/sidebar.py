import streamlit as st
from utils.profile import load_profile, save_profile
from utils.logger import logger
import time

def render_sidebar(agent, rag, app_version):
    with st.sidebar:
        st.header("✈️ Plan Your Trip")
        st.divider()
        
        # Profile
        st.subheader("👤 My Profile")
        user = st.text_input("Your Name", value=st.session_state.user_name)
        if user: st.session_state.user_name = user
        profile = load_profile(user)
        
        interests = st.multiselect("Interests", ["Beach", "Adventure", "History", "Food", "Nature"], default=profile.get("interests", []))
        budget = st.slider("Total Budget ($)", 100, 10000, profile.get("budget", 1500))
        
        if st.button("Save Profile"): save_profile(user, interests, budget)
        
        st.divider()
        # Inputs
        st.subheader("📍 Trip Details")
        loc = st.selectbox("Location", ["Dubai", "Abu Dhabi", "Sharjah"])
        days = st.number_input("Days", 1, 14, 3)
        travelers = st.number_input("Travelers", 1, 10, 1)
        
        # Priorities
        eco_p = st.slider("Eco Priority", 1, 10, 8)
        bud_p = st.slider("Budget Priority", 1, 10, 6)
        com_p = st.slider("Comfort Priority", 1, 10, 5)

        if st.button("Generate Plan 🚀", use_container_width=True):
            if not interests: st.warning("Select an interest!"); return
            
            with st.status("Generating...", expand=True) as status:
                try:
                    status.write("🧠 Analyzing...")
                    priorities = {"eco": eco_p, "budget": bud_p, "comfort": com_p}
                    query = f"{days}-day trip to {loc} for {travelers} ppl, interest {interests}"
                    
                    rag_data = rag.search(query)
                    itinerary = agent.run(query, rag_data, budget, interests, days, loc, travelers, profile, priorities)
                    
                    if itinerary:
                        st.session_state.itinerary = itinerary
                        st.session_state.query = query
                        # Update current trip state
                        st.session_state.current_trip_days = days
                        st.session_state.current_trip_travelers = travelers
                        
                        status.update(label="✅ Done!", state="complete")
                        st.toast("Plan Ready!")
                    else:
                        status.update(label="Failed", state="error")
                        st.error("AI returned empty plan.")
                except Exception as e:
                    logger.exception(e)
                    status.update(label="Error", state="error")
        
        st.caption(f"v{app_version}")
        
