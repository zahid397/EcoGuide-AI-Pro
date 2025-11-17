import streamlit as st
from typing import Dict, Any

def render_analysis(itinerary: Dict[str, Any]) -> None:
    st.subheader("🤖 AI Plan Analysis (Pro)")
    
    st.markdown("#### Plan Health Score")
    health_score = int(itinerary.get('plan_health_score', 0))
    st.metric(label="Overall Plan Health", value=f"{health_score}/100", 
              delta=f"{(health_score - 75)} vs. balanced (75)" if health_score != 75 else "Balanced",
              delta_color="normal" if health_score > 70 else "inverse")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ⏱️ AI Time Planner")
        time_report = itinerary.get('ai_time_planner_report', "No analysis available.")
        st.warning(time_report)
    
        st.markdown("#### 🛡️ Risk & Safety Module")
        risk_report = itinerary.get('risk_safety_report', "No analysis available.")
        st.info(risk_report)
    
    with col2:
        st.markdown("#### 💸 AI Cost Leakage Detector")
        leak_report = itinerary.get('cost_leakage_report', "No analysis available.")
        st.error(leak_report)
    
        st.markdown("#### 🔄 Duplicate Trip Detector")
        duplicate_report = itinerary.get('duplicate_trip_detector', "No analysis available.")
        st.info(duplicate_report)
      
