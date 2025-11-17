import os
import json
import streamlit as st
from typing import Dict, Any, List
from utils.logger import logger

PROFILE_DIR = "data/profiles"

def save_profile(name: str, interests: List[str], budget: int) -> None:
    """Saves user profile to a JSON file."""
    
    try:
        # --- ✳️ FIX: This line prevents the "File exists" error ---
        os.makedirs(PROFILE_DIR, exist_ok=True)
        # ---
        
        profile_path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
        profile_data = {"interests": interests, "budget": budget}
        
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f)
            
        st.sidebar.success("Profile Saved!")
        
    except Exception as e:
        st.sidebar.error(f"Failed to save profile: {e}")
        logger.exception(f"Failed to save profile for {name}: {e}")

def load_profile(name: str) -> Dict[str, Any]:
    """Loads user profile from a JSON file."""
    profile_path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.exception(f"Failed to load profile for {name}: {e}")
            return {}
    return {}import os
import json
import streamlit as st
from typing import Dict, Any, List
from utils.logger import logger

PROFILE_DIR = "data/profiles"

def save_profile(name: str, interests: List[str], budget: int) -> None:
    """Saves user profile to a JSON file."""
    
    try:
        # --- ✳️ FIX: This line prevents the "File exists" error ---
        os.makedirs(PROFILE_DIR, exist_ok=True)
        # ---
        
        profile_path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
        profile_data = {"interests": interests, "budget": budget}
        
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f)
            
        st.sidebar.success("Profile Saved!")
        
    except Exception as e:
        st.sidebar.error(f"Failed to save profile: {e}")
        logger.exception(f"Failed to save profile for {name}: {e}")

def load_profile(name: str) -> Dict[str, Any]:
    """Loads user profile from a JSON file."""
    profile_path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.exception(f"Failed to load profile for {name}: {e}")
            return {}
    return {}import os
import json
import streamlit as st
from typing import Dict, Any, List
from utils.logger import logger

PROFILE_DIR = "data/profiles"

def save_profile(name: str, interests: List[str], budget: int) -> None:
    """Saves user profile to a JSON file."""
    
    try:
        # --- ✳️ FIX: This line prevents the "File exists" error ---
        os.makedirs(PROFILE_DIR, exist_ok=True)
        # ---
        
        profile_path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
        profile_data = {"interests": interests, "budget": budget}
        
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f)
            
        st.sidebar.success("Profile Saved!")
        
    except Exception as e:
        st.sidebar.error(f"Failed to save profile: {e}")
        logger.exception(f"Failed to save profile for {name}: {e}")

def load_profile(name: str) -> Dict[str, Any]:
    """Loads user profile from a JSON file."""
    profile_path = os.path.join(PROFILE_DIR, f"profile_{name}.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.exception(f"Failed to load profile for {name}: {e}")
            return {}
    return {}
