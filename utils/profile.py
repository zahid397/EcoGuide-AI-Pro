import os
import json
import streamlit as st
from utils.logger import logger

PROFILE_DIR = "data/profiles"

def save_profile(name: str, interests: list, budget: int) -> None:
    try:
        os.makedirs(PROFILE_DIR, exist_ok=True)
        path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
        with open(path, 'w') as f:
            json.dump({"interests": interests, "budget": budget}, f)
        st.sidebar.success("Profile Saved!")
    except Exception as e:
        st.sidebar.error(f"Error saving profile: {e}")

def load_profile(name: str) -> dict:
    try:
        path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
    except: pass
    return {}
  
