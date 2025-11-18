import streamlit as st
from utils.cards import render_card

def render_list(itinerary: dict):
    """Renders the Activities tab safely."""

    st.subheader("🏄 Activities & Places")

    activities = itinerary.get("activities", [])

    # No activities?
    if not activities:
        st.info("No activities found in this itinerary.")
        return

    # Render each item using Safe HTML card renderer
    for item in activities:
        try:
            card_html = render_card(item)
            st.markdown(card_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to render item: {e}")
