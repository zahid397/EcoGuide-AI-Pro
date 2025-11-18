import json
import re
from typing import Optional, Any, Dict


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the first valid JSON object found inside LLM output.
    Works even if model sends text+json mixed content.
    """
    if not text:
        return None

    try:
        # Find first {...} block
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None

        json_block = match.group(0)
        return json.loads(json_block)

    except json.JSONDecodeError:
        repaired = clean_json(json_block)
        try:
            return json.loads(repaired)
        except Exception:
            return None
    except Exception:
        return None


def clean_json(data: str) -> str:
    """Fixes common JSON issues from LLM output."""
    if not data:
        return data

    # Remove trailing commas
    data = re.sub(r",\s*([\]}])", r"\1", data)

    # Smart quotes → normal quotes
    data = data.replace("“", '"').replace("”", '"')

    # Remove weird zero-width chars
    data = re.sub(r"[\u200b-\u200f]", "", data)

    return data
