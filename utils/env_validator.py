# utils/env_validator.py

import os

def validate_env():
    if not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError("GEMINI_API_KEY missing in environment!")
