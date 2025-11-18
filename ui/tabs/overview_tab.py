import streamlit as st

def render_overview(itinerary: dict, budget: int, travelers: int):
    """Renders the Overview tab safely."""

    st.subheader("✨ Trip Overview")

    plan = itinerary.get("plan", "No plan available.")

    # Show the markdown plan
    st.markdown(plan)

    st.divider()

    st.write("### Key Metrics")
    col1, col2, col3 = st.columns(3)

    col1.metric("Eco Score", f"{itinerary.get('eco_score', 0)}/10")
    col2.metric("Waste-Free Score", itinerary.get("waste_free_score", 0))
    col3.metric("Plan Health", f"{itinerary.get('plan_health_score', 0)}/100")

    st.divider()

    st.write("### Budget Breakdown")
    bd = itinerary.get("budget_breakdown", {})

    if bd:
        for k, v in bd.items():
            st.write(f"- **{k}:** ${v}")
    else:
        st.info("Budget details missing.")

    st.divider()
    st.write("### Highlights")
    highlights = itinerary.get("experience_highlights", [])

    if highlights:
        for h in highlights:
            st.write(f"• {h}")
    else:
        st.info("No highlights available.")
