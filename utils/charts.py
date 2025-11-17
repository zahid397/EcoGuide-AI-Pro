import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any

@st.cache_data
def generate_radar_chart(_itinerary_data: Dict[str, Any], user_budget: int) -> go.Figure:
    """Creates a Plotly Radar Chart with safe gets."""
    eco_score = _itinerary_data.get('eco_score', 0)
    carbon_saved = int(str(_itinerary_data.get('carbon_saved', "0")).replace('kg', ''))
    total_cost = _itinerary_data.get('total_cost', 0)
    waste_score = _itinerary_data.get('waste_free_score', 0)
    
    if user_budget > 0 and total_cost > 0:
        budget_efficiency = max(0, min(1, (user_budget - total_cost) / user_budget)) * 10
    else:
        budget_efficiency = 0
    carbon_score = max(0, min(10, (carbon_saved / 50) * 10))
    
    categories = ['Eco Score', 'Carbon Savings', 'Budget Efficiency', 'Waste-Free Score']
    values = [eco_score, carbon_score, budget_efficiency, waste_score]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', name='Trip Score'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, title="Trip Sustainability Dashboard", height=350, margin=dict(l=40, r=40, t=60, b=40))
    return fig
  
