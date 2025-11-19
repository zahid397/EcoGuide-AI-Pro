import streamlit as st
import pandas as pd
from utils.charts import generate_radar_chart

def render_overview(itinerary, budget, travelers):
    st.subheader("✨ Trip Overview & Impact")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        # --- FIX: Bar Chart (Trip Mood) ---
        st.markdown("#### 📊 Trip Mood Indicator")
        
        # Safe Get with Default Fallback
        mood_data = itinerary.get('trip_mood_indicator', {})
        
        # যদি AI ডাটা না দেয়, ডিফল্ট ডাটা দেখাও
        if not mood_data:
            mood_data = {"Adventure": 60, "Relax": 40, "Culture": 30, "Luxury": 20}
            
        # Create DataFrame for Bar Chart
        mood_df = pd.DataFrame.from_dict(mood_data, orient='index', columns=['Intensity (%)'])
        st.bar_chart(mood_df, height=200, color="#007BFF")
        
        # --- Highlights ---
        st.markdown("#### 🏆 Top 3 Highlights")
        highlights = itinerary.get('experience_highlights', [])
        if not highlights:
            highlights = ["Explore Local Culture", "Eco-Friendly Stay", "Nature Walk"]
            
        for i, high in enumerate(highlights):
            st.success(f"**{i+1}.** {high}")
    
    with col2:
        # --- Trip Preview Image ---
        st.markdown("#### 📸 Trip Preview")
        ai_prompt = itinerary.get('ai_image_prompt', 'Nature travel preview')
        st.image("https://placehold.co/600x400/28a745/white?text=Trip+Preview", caption="AI Concept Art")
        
        # --- Carbon Offset ---
        st.info(f"🌱 **Offset:** {itinerary.get('carbon_offset_suggestion', 'Plant 2 trees.')}")

    st.divider()
    
    # --- Radar Chart & Budget ---
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📉 Sustainability Dashboard")
        fig = generate_radar_chart(itinerary, budget)
        st.plotly_chart(fig, use_container_width=True)
        
    with col4:
        st.subheader("💵 Budget Breakdown")
        budget_data = itinerary.get('budget_breakdown', {})
        
        # Fallback if budget is missing
        if not budget_data:
            budget_data = {"Hotel": int(budget*0.5), "Food": int(budget*0.2), "Activities": int(budget*0.3)}
            
        st.table(pd.DataFrame.from_dict(budget_data, orient='index', columns=[f"Est. Cost ($)"]))
        
