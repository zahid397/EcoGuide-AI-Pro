import streamlit as st
from utils.cards import render_card
from utils.logger import logger

def render(data):
    st.subheader("🏄 Activities in Your Trip")

    activities = data.get("activities", [])

    if not activities:
        st.info("No activities found in the itinerary.")
        return

    try:
        for item in activities:
            # Safe fallback for missing fields
            safe_item = {
                "name": item.get("name", "Unknown"),
                "location": item.get("location", "Unknown"),
                "eco_score": item.get("eco_score", 0),
                "avg_rating": item.get("avg_rating", 0),
                "description": item.get("description", "No description available."),
                "image_url": item.get("image_url", "https://placehold.co/600x400"),
                "cost": item.get("cost", 0),
                "cost_type": item.get("cost_type", "N/A"),
                "data_type": item.get("data_type", "Activity"),
                "tag": item.get("tag", None),
            }

            # Render HTML card
            st.markdown(render_card(safe_item), unsafe_allow_html=True)
            st.markdown("---")

    except Exception as e:
        logger.exception(f"Activity list render failed → {e}")
        st.error("Could not render activity cards.")
