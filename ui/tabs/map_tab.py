import streamlit as st
import pandas as pd

# ---------------------------------------
# 🌍 Static Coordinates for Supported Cities
# ---------------------------------------
LOCATION_COORDS = {
    "Dubai": pd.DataFrame({"lat": [25.2048], "lon": [55.2708]}),
    "Abu Dhabi": pd.DataFrame({"lat": [24.4539], "lon": [54.3773]}),
    "Sharjah": pd.DataFrame({"lat": [25.3463], "lon": [55.4209]}),
}

# ---------------------------------------
# 🗺️ Map Renderer
# ---------------------------------------
def render_map_tab(location: str):
    st.subheader(f"🗺️ Map of {location}")

    # Fetch coordinates
    map_data = LOCATION_COORDS.get(location)

    if map_data is None:
        st.warning(f"⚠️ No map data available for: {location}")
        return

    # Render map safely
    try:
        st.map(map_data, zoom=10, use_container_width=True)
        st.caption("📍 Showing approximate city location.")
    except Exception as e:
        st.error("⚠️ Failed to render map.")
        st.code(str(e))
