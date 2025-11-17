import os

def validate_env() -> None:
    """Checks for required environment variables."""
    required = ["GEMINI_API_KEY", "QDRANT_URL"]
    missing = [v for v in required if not os.getenv(v)]
    
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
      
