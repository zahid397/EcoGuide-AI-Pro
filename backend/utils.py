import json
import re

def extract_json(text: str):
    """
    AI-এর রেসপন্স থেকে ক্লিন JSON বের করার ফাংশন।
    এটি Markdown ```json ... ``` ট্যাগ রিমুভ করে।
    """
    if not text:
        return {}
        
    try:
        # সরাসরি লোড করার চেষ্টা
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # যদি সরাসরি না হয়, রেজেক্স (Regex) দিয়ে খোঁজা
    try:
        # ```json এবং ``` এর মাঝখানের টেক্সট খোঁজো
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
        # অথবা শুধু { ... } খোঁজো
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
    except Exception:
        pass

    print("Warning: Could not extract JSON from LLM response.")
    return {}
  
