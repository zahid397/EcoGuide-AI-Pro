import streamlit as st

def render_analysis(itinerary):
    st.subheader("🤖 AI Plan Analysis")
    
    # Safe Data Extraction
    health = itinerary.get('plan_health_score', 75)
    time_rpt = itinerary.get('ai_time_planner_report', "Schedule looks balanced.")
    risk_rpt = itinerary.get('risk_safety_report', "Standard safety precautions apply.")
    leak_rpt = itinerary.get('cost_leakage_report', "No major cost leaks detected.")
    dup_rpt = itinerary.get('duplicate_trip_detector', "This is a unique trip plan.")
    
    # Display
    st.metric("Plan Health Score", f"{health}/100")
    st.progress(health / 100)
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**⏱️ Time Analysis:**\n{time_rpt}")
        st.info(f"**🛡️ Risk Analysis:**\n{risk_rpt}")
    with c2:
        st.markdown(f"**💰 Cost Analysis:**\n{leak_rpt}")
        st.success(f"**🔄 Uniqueness:**\n{dup_rpt}")
        
