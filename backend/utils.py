import json
import re
from utils.logger import logger


def extract_json(text: str):
    """
    Extract JSON from a model response safely.
    Supports:
    - Raw JSON
    - JSON inside backticks (```json ... ```)
    - Messy text with JSON inside
    """

    if not text:
        return None

    # Try strict JSON first
    try:
        return json.loads(text)
    except:
        pass

    # Extract inside ```json ... ```
    code_block = re.findall(r"```json(.*?)```", text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block[0].strip())
        except Exception as e:
            logger.error(f"Failed to parse JSON block → {e}")

    # Extract first {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception as e:
            logger.error(f"Regex JSON parse failed → {e}")

    logger.error("extract_json: No valid JSON found")
    return None
