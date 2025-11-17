import streamlit as st
import pandas as pd
from utils.charts import generate_radar_chart
from typing import Dict, Any

def render_overview(itinerary: Dict[str, Any], user_budget: int, travelers: int) -> None:
    st.subheader("Trip Overview & Impact")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Trip Mood Indicator")
        mood_data = itinerary.get('trip_mood_indicator', {})
        if mood_data:
            mood_df = pd.DataFrame.from_dict(mood_data, orient='index', columns=['Intensity'])
            st.bar_chart(mood_df, height=250)
        
        st.markdown("#### Top 3 Highlights")
        highlights = itinerary.get('experience_highlights', [])
        if highlights:
            for i, high in enumerate(highlights):
                st.success(f"**{i+1}:** {high}")
    
    with col2:
        st.markdown("#### Trip Preview 📸")
        ai_prompt = itinerary.get('ai_image_prompt', '...')[0:100] + "..."
        st.image("https://placehold.co/600x400/28a745/white?text=AI+Generated+Trip+Preview", caption=ai_prompt)
        
        st.markdown("#### Carbon Offset 🌱")
        offset_suggestion = itinerary.get('carbon_offset_suggestion', 'No suggestion available.')
        st.info(f"**Suggestion:** {offset_suggestion}")
    
    st.divider()
    st.subheader("Sustainability Dashboard")
    fig = generate_radar_chart(itinerary, user_budget)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Budget Breakdown 💵")
    budget_data = itinerary.get('budget_breakdown', {})
    if budget_data:
        st.table(pd.DataFrame.from_dict(budget_data, orient='index', columns=[f"Est. Cost for {travelers} p."]))
      
