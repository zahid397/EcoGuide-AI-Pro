import streamlit as st

def render_plan(itinerary, location, user_name):
    st.subheader("Your Trip Plan")
    st.markdown(itinerary.get("plan", "No plan generated."))

    st.info("PDF download is disabled for the hackathon demo.")
