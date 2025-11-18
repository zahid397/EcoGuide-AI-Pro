import streamlit as st
import pandas as pd

# Coordinate Data
LOCATION_COORDS = {
    "Dubai": pd.DataFrame({'name': ['Dubai'], 'lat': [25.2048], 'lon': [55.2708]}),
    "Abu Dhabi": pd.DataFrame({'name': ['Abu Dhabi'], 'lat': [24.4539], 'lon': [54.3773]}),
    "Sharjah": pd.DataFrame({'name': ['Sharjah'], 'lat': [25.3463], 'lon': [55.4209]}),
}

def render_map_tab(location):
    st.subheader(f"🗺️ Map of {location}")
    
    # Check coordinates
    map_data = LOCATION_COORDS.get(location)
    
    if map_data is not None:
        # Show map with zoom level
        st.map(map_data, zoom=10, use_container_width=True)
    else:
        st.warning(f"Could not find map data for {location}")
        
