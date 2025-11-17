import streamlit as st
import pandas as pd
from typing import Dict, Any

LOCATION_COORDS: Dict[str, Any] = {
    "Dubai": pd.DataFrame({'name': ['Dubai'], 'lat': [25.2048], 'lon': [55.2708]}),
    "Abu Dhabi": pd.DataFrame({'name': ['Abu Dhabi'], 'lat': [24.4539], 'lon': [54.3773]}),
    "Sharjah": pd.DataFrame({'name': ['Sharjah'], 'lat': [25.3463], 'lon': [55.4209]}),
}

def render_map_tab(location: str) -> None:
    st.subheader(f"Map of {location}")
    map_data = LOCATION_COORDS.get(location)
    if map_data is not None:
        st.map(map_data, zoom=10)
    else:
        st.error("Location coordinates not found.")
      
