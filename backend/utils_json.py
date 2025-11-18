import json
import re
from typing import Any, Dict, Optional

def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the first valid JSON object from an LLM output.
    Works even if the model mixes text + JSON.
    """
    if not text:
        return None

    try:
        # Find the JSON using a greedy match
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None

        json_text = match.group(0)

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            cleaned = clean_json(json_text)
            return json.loads(cleaned)

    except Exception:
        return None


def clean_json(raw: str) -> str:
    """
    Cleans common JSON issues:
      - smart quotes
      - trailing commas
      - unicode noise
    """
    if not raw:
        return raw

    # Replace smart quotes
    raw = raw.replace("“", '"').replace("”", '"')

    # Remove trailing commas
    raw = re.sub(r",\s*([\]}])", r"\1", raw)

    # Remove zero-width chars
    raw = re.sub(r"[\u200b-\u200f]", "", raw)

    return raw
