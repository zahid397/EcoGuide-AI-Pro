import json
import re

def extract_json(text: str):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group(0))
    except:
        return {}
