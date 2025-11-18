import streamlit as st
from utils.charts import generate_radar_chart

def render(data, budget, travelers):
    c1, c2 = st.columns(2)
    with c1:
        st.image(data.get('ai_image_prompt', 'https://placehold.co/600x400'), caption="Trip Preview")
        st.info(f"🌱 Offset: {data.get('carbon_offset_suggestion', 'None')}")
    with c2:
        st.plotly_chart(generate_radar_chart(data, budget), use_container_width=True)
        
