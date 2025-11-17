import json
import re
from typing import Optional, Any, Dict


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the first valid JSON object found inside LLM output.
    Works even if Gemini sends text+json mixed content.
    Example:
        "Here is your plan:\n\n{ ...json... }\nThanks!"
    """
    if not text:
        return None

    # Find JSON-like block using regex
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None

        json_block = match.group(0)

        return json.loads(json_block)

    except json.JSONDecodeError:
        # Try repairing trailing commas or broken JSON
        repaired = clean_json(json_block)
        try:
            return json.loads(repaired)
        except:
            return None
    except Exception:
        return None


def clean_json(data: str) -> str:
    """
    Fixes common LLM JSON issues:
      - trailing commas
      - mismatched quotes
      - line breaks
      - weird unicode
    """
    if not data:
        return data

    # Remove trailing commas before } or ]
    data = re.sub(r",\s*([\]}])", r"\1", data)

    # Replace smart quotes with normal quotes
    data = data.replace("“", '"').replace("”", '"')

    # Remove weird unicode whitespace
    data = re.sub(r"[\u200b-\u200f]", "", data)

    return data
