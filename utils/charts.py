import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any

@st.cache_data
def generate_radar_chart(_itinerary_data: Dict[str, Any], user_budget: int) -> go.Figure:
    """Creates a Plotly Radar Chart with safe defaults."""
    
    # Safe Extraction
    try:
        eco_score = float(_itinerary_data.get('eco_score', 5.0))
        
        raw_carbon = str(_itinerary_data.get('carbon_saved', "0")).lower().replace('kg', '').strip()
        carbon_saved = float(raw_carbon) if raw_carbon.replace('.', '').isdigit() else 0
        
        total_cost = float(_itinerary_data.get('total_cost', 0))
        waste_score = float(_itinerary_data.get('waste_free_score', 5))
    except:
        # Default fallback values
        eco_score = 5.0
        carbon_saved = 10
        total_cost = 0
        waste_score = 5

    # Calculate Budget Efficiency (0-10 score)
    if user_budget > 0 and total_cost > 0:
        budget_efficiency = max(0, min(1, (user_budget - total_cost) / user_budget)) * 10
    else:
        budget_efficiency = 5 # Default score

    # Normalize Carbon Score (0-10)
    carbon_score = max(0, min(10, (carbon_saved / 50) * 10))
    
    # Data for Chart
    categories = ['Eco Score', 'Carbon Savings', 'Budget Fit', 'Waste-Free']
    values = [eco_score, carbon_score, budget_efficiency, waste_score]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], # Close the loop
        theta=categories + [categories[0]],
        fill='toself',
        name='Trip Score',
        line_color='#00CC96'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        height=300,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig
    
