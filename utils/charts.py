import streamlit as st
import plotly.graph_objects as go

@st.cache_data
def generate_radar_chart(data: dict, budget: int) -> go.Figure:
    eco = data.get('eco_score', 0)
    waste = data.get('waste_free_score', 0)
    cost = data.get('total_cost', 0)
    
    # Calculate efficiency (0-10)
    eff = max(0, min(10, ((budget - cost) / budget) * 10)) if budget > 0 else 0
    
    fig = go.Figure(data=go.Scatterpolar(
        r=[eco, waste, eff, eco],
        theta=['Eco Score', 'Waste Free', 'Budget Fit', 'Eco Score'],
        fill='toself'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, height=300, margin=dict(t=20, b=20, l=40, r=40))
    return fig
  
