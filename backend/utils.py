import json
import re
from typing import Optional, Any, Dict


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract valid JSON from messy LLM output."""
    if not text:
        return None

    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None

        json_block = match.group(0)

        return json.loads(json_block)

    except json.JSONDecodeError:
        repaired = clean_json(json_block)
        try:
            return json.loads(repaired)
        except:
            return None
    except Exception:
        return None


def clean_json(data: str) -> str:
    """Fix common JSON issues."""
    if not data:
        return data

    data = re.sub(r",\s*([\]}])", r"\1", data)
    data = data.replace("“", '"').replace("”", '"')
    data = re.sub(r"[\u200b-\u200f]", "", data)

    return data
