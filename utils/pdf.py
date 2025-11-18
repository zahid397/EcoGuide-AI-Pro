from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger
import re

def safe_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("### ", "").replace("## ", "").replace("* ", "- ")
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "EcoGuide AI - Travel Plan", 0, 1, 'C')
        pdf.ln(5)

        # ---------------- PLAN ----------------
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Your Plan", 0, 1)
        pdf.set_font("Arial", '', 11)

        plan_text = safe_text(itinerary_data.get("plan", "No plan available."))
        pdf.multi_cell(0, 5, plan_text)

        # ---------------- ACTIVITIES ----------------
        pdf.ln(8)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Activities", 0, 1)
        pdf.set_font("Arial", '', 10)

        activities = itinerary_data.get("activities", [])
        if activities:
            for item in activities:
                line = f"- {item.get('name', 'Item')} | Eco: {item.get('eco_score', 'N/A')}"
                pdf.multi_cell(0, 5, safe_text(line))
        else:
            pdf.multi_cell(0, 5, "No activities found.")

        # ---------------- BUDGET ----------------
        pdf.ln(8)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Budget Breakdown", 0, 1)
        pdf.set_font("Arial", '', 10)

        for k, v in itinerary_data.get("budget_breakdown", {}).items():
            pdf.cell(60, 8, safe_text(str(k)), 1)
            pdf.cell(30, 8, safe_text(str(v)), 1, 1)

        return pdf.output(dest="S").encode("latin-1", "replace")

    except Exception as e:
        logger.exception(f"PDF Error: {e}")
        raise Exception("Could not generate PDF. Please try again.")
