import os
def validate_env():
    required = ["GEMINI_API_KEY", "QDRANT_URL"]
    missing = [v for v in required if not os.getenv(v)]
    if missing: raise EnvironmentError(f"Missing env vars: {', '.join(missing)}")
      
