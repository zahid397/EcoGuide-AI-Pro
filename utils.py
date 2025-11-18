import json
import re

def extract_json(text: str):
    """
    Safely extract the first valid JSON object from LLM output.
    Works even if the model mixes markdown, text, or extra content.
    """

    if not text:
        return {}

    # Remove markdown fences
    cleaned = text.replace("```json", "").replace("```", "")

    # Try direct json.loads
    try:
        return json.loads(cleaned)
    except:
        pass

    # Fallback: regex find JSON object
    match = re.search(r"{(?:[^{}]|(?:{[^{}]*}))*}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return {}

    return {}
