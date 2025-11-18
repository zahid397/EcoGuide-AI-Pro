import streamlit as st

def render(data):
    st.metric("Health Score", f"{data.get('plan_health_score', 0)}/100")
    c1, c2 = st.columns(2)
    with c1:
        st.warning(f"⏱️ Time: {data.get('ai_time_planner_report', 'N/A')}")
        st.info(f"🛡️ Risk: {data.get('risk_safety_report', 'N/A')}")
    with c2:
        st.error(f"💰 Leaks: {data.get('cost_leakage_report', 'N/A')}")
        
