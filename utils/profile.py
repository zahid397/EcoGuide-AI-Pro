import os
import json

PROFILE_DIR = "data/profiles"

# Create folder if missing
os.makedirs(PROFILE_DIR, exist_ok=True)

def load_profile(username: str):
    file_path = os.path.join(PROFILE_DIR, f"profile_{username}.json")

    if not os.path.exists(file_path):
        return {"interests": [], "budget": 1000}

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return {"interests": [], "budget": 1000}


def save_profile(username: str, interests, budget):
    file_path = os.path.join(PROFILE_DIR, f"profile_{username}.json")
    os.makedirs(PROFILE_DIR, exist_ok=True)

    try:
        with open(file_path, "w") as f:
            json.dump(
                {"interests": interests, "budget": budget},
                f,
                indent=4
            )
        return True
    except Exception as e:
        return str(e)
