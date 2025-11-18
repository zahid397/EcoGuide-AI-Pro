import streamlit as st

def render_analysis(itinerary: dict):
    """Renders the Analysis tab safely without throwing UI errors."""

    if not isinstance(itinerary, dict):
        st.error("Invalid itinerary data.")
        return

    st.subheader("🔬 Trip Analysis")

    # --- Eco & Safety Analysis ---
    st.write("### 🌱 Eco & Safety Insights")

    st.write(f"**Carbon Saved:** {itinerary.get('carbon_saved', '0kg')}")
    st.write(f"**Waste-Free Score:** {itinerary.get('waste_free_score', 0)}/10")
    st.write(f"**Risk & Safety Report:** {itinerary.get('risk_safety_report', 'No data available')}")

    st.divider()

    # --- Time Planning ---
    st.write("### ⏱️ Time Planner Report")
    st.info(itinerary.get("ai_time_planner_report", "No time analysis available."))

    st.divider()

    # --- Cost Leakage ---
    st.write("### 💸 Cost Leakage Report")
    st.warning(itinerary.get("cost_leakage_report", "No cost issues detected."))

    st.divider()

    # --- Weather Contingency ---
    st.write("### 🌦 Weather Contingency")
    st.write(itinerary.get("weather_contingency", "No weather notes available."))

    st.divider()

    # --- Duplicate Trip Detector ---
    st.write("### 🔁 Duplicate Trip Check")
    st.write(itinerary.get("duplicate_trip_detector", "Unique trip"))
