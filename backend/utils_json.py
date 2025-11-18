import json
import re

def extract_json(text):
    if not text:
        return None

    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        block = match.group(0)
        return json.loads(block)
    except:
        return None
