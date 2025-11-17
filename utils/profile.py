import os
import json

PROFILE_DIR = "data/profiles"

# Ensure directory exists
os.makedirs(PROFILE_DIR, exist_ok=True)

def load_profile(username: str):
    """Loads a profile JSON file. Returns defaults if missing."""
    if not username:
        return {"interests": [], "budget": 1000}

    file_path = os.path.join(PROFILE_DIR, f"profile_{username}.json")

    if not os.path.exists(file_path):
        return {"interests": [], "budget": 1000}

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"interests": [], "budget": 1000}


def save_profile(username: str, interests, budget):
    """Saves profile to disk."""
    if not username:
        return False

    file_path = os.path.join(PROFILE_DIR, f"profile_{username}.json")

    data = {
        "interests": interests,
        "budget": budget
    }

    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        return str(e)
