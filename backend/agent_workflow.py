import os
from utils.logger import logger

# ---- Try OpenAI ----
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

try:
    if OPENAI_KEY:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_KEY)
        HAS_OPENAI = True
    else:
        HAS_OPENAI = False
except Exception as e:
    logger.warning(f"OpenAI load failed: {e}")
    HAS_OPENAI = False


# ---- Try GEMINI ----
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

try:
    if GEMINI_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        HAS_GEMINI = True
    else:
        HAS_GEMINI = False
except Exception as e:
    logger.warning(f"Gemini load failed: {e}")
    HAS_GEMINI = False


class AgentWorkflow:
    """Hybrid LLM Agent: Works with OpenAI + Gemini automatically."""

    def __init__(self):
        if not HAS_OPENAI and not HAS_GEMINI:
            raise RuntimeError(
                "❌ No AI Model Available.\n"
                "Please set at least one key:\n"
                "• OPENAI_API_KEY\n"
                "• GEMINI_API_KEY"
            )

    # ------------------------------
    # MAIN EXECUTION
    # ------------------------------
    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        prompt = self._build_prompt(query, rag_data, budget, interests, days, location, travelers, user_profile, priorities)

        # -----------------------
        # 1️⃣ Try OPENAI first
        # -----------------------
        if HAS_OPENAI:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an eco-travel planning AI."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message["content"]
            except Exception as e:
                logger.warning(f"OpenAI failed, switching to Gemini: {e}")

        # -----------------------
        # 2️⃣ Fallback → Gemini
        # -----------------------
        if HAS_GEMINI:
            try:
                response = gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini failed: {e}")
                return None

        return None

    # -----------------------
    # PROMPT BUILDER
    # -----------------------
    def _build_prompt(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        return f"""
Generate a structured eco-friendly travel plan.

User: {user_profile.get('name')}
Location: {location}
Days: {days}
Budget: {budget}
Travelers: {travelers}
Interests: {interests}
Priorities: {priorities}

Eco-friendly places from RAG:
{rag_data}

Query:
{query}

Return the BEST possible plan.
"""
