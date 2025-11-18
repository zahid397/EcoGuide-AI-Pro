import json
import re
from typing import Optional, Any, Dict


# ======================================================
# MAIN FUNCTION → Extract safest JSON
# ======================================================
def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract valid JSON from mixed LLM output.
    Handles:
      - text before/after JSON
      - multiple JSON blocks
      - markdown ```json``` blocks
      - broken commas, quotes, unicode
      - arrays [] or objects {}
    """

    if not text or not isinstance(text, str):
        return None

    # ------------------------------
    # 1) First try: clean direct JSON
    # ------------------------------
    try:
        return json.loads(text)
    except:
        pass

    # ------------------------------
    # 2) Extract inside ```json code blocks```
    # ------------------------------
    md_match = re.findall(r"```json(.*?)```", text, re.DOTALL | re.IGNORECASE)
    for block in md_match:
        fixed = attempt_parse(block)
        if fixed:
            return fixed

    # ------------------------------
    # 3) Extract first {...} block
    # ------------------------------
    json_blocks = re.findall(r"\{[\s\S]*?\}", text)
    for jb in json_blocks:
        fixed = attempt_parse(jb)
        if fixed:
            return fixed

    # ------------------------------
    # 4) Extract [...] arrays
    # ------------------------------
    array_blocks = re.findall(r"\[[\s\S]*?\]", text)
    for ab in array_blocks:
        fixed = attempt_parse(ab)
        if fixed:
            return fixed

    # ------------------------------
    # 5) Nothing found
    # ------------------------------
    return None



# ======================================================
# TRY PARSING AFTER CLEANING
# ======================================================
def attempt_parse(block: str) -> Optional[Dict[str, Any]]:
    """Try parse JSON → if fails clean → try again."""

    try:
        return json.loads(block)
    except:
        cleaned = clean_json(block)
        try:
            return json.loads(cleaned)
        except:
            return None



# ======================================================
# REPAIR COMMON LLM JSON ERRORS
# ======================================================
def clean_json(data: str) -> str:
    """
    Fix:
      - trailing commas
      - smart quotes
      - extra spaces
      - weird unicode
      - repeated commas
    """

    if not data:
        return data

    # Remove markdown wrappers
    data = re.sub(r"```json|```", "", data)

    # Remove trailing commas
    data = re.sub(r",\s*([\]}])", r"\1", data)

    # Replace smart quotes
    data = data.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    # Remove invisible unicode characters
    data = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", data)

    # Remove double commas
    data = re.sub(r",\s*,", ",", data)

    # Remove newlines in keys
    data = re.sub(r"\n+", " ", data)

    return data
