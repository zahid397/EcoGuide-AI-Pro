import json
import re

def extract_json(text: str):
    """
    Extracts clean JSON from the AI response.
    It removes Markdown ```json ... ``` tags if present.
    """
    if not text:
        return {}
        
    try:
        # Try loading directly
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # If direct load fails, try finding JSON via Regex
    try:
        # Search for text between ```json and ```
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
        # Or just search for { ... }
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
    except Exception:
        pass

    print("Warning: Could not extract JSON from LLM response.")
    return {}
    
