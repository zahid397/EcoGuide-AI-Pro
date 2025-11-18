from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger


def _safe(text: str) -> str:
    """
    Removes emojis/unicode because FPDF supports only latin-1.
    Replaces invalid characters with '?'.
    """
    if not isinstance(text, str):
        text = str(text)

    return text.encode("latin-1", "replace").decode("latin-1")


def generate_pdf(itinerary: Dict[str, Any]) -> bytes:
    """
    SUPER SAFE PDF Generator — never crashes.
    Converts all text into latin-1 and strips emojis.
    """

    try:
        pdf = FPDF()
        pdf.add_page()

        # Title
        pdf.set_font("Arial", "B", 18)
        pdf.multi_cell(0, 10, _safe("EcoGuide AI — Your Travel Plan"))
        pdf.ln(5)

        # ----- PLAN -----
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 8, _safe("Trip Itinerary"))
        pdf.ln(2)

        pdf.set_font("Arial", "", 11)
        plan_text = itinerary.get("plan", "No plan available.")
        plan_text = plan_text.replace("#", "").replace("* ", "- ")

        for line in plan_text.split("\n"):
            pdf.multi_cell(0, 5, _safe(line))

        pdf.ln(8)

        # ----- ACTIVITIES -----
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 8, _safe("Activities & Recommendations"))
        pdf.ln(2)

        pdf.set_font("Arial", "", 10)

        activities = itinerary.get("activities", [])
        if not activities:
            pdf.multi_cell(0, 5, _safe("No activities found."))
        else:
            for item in activities:
                name = item.get("name", "Activity")
                eco = item.get("eco_score", "N/A")
                ctype = item.get("data_type", "Activity")

                line = f"- {name} ({ctype}) — Eco Score: {eco}"
                pdf.multi_cell(0, 5, _safe(line))

        pdf.ln(8)

        # ----- BUDGET -----
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 8, _safe("Budget Breakdown"))
        pdf.ln(2)

        pdf.set_font("Arial", "", 10)

        budget = itinerary.get("budget_breakdown", {})
        if not budget:
            pdf.multi_cell(0, 5, _safe("Budget data not available."))
        else:
            for category, amount in budget.items():
                line = f"{category}: ${amount}"
                pdf.multi_cell(0, 5, _safe(line))

        # Return PDF bytes
        return pdf.output(dest="S").encode("latin-1")

    except Exception as e:
        logger.exception(f"PDF generation failed: {e}")
        raise Exception("Could not generate PDF. Please try again.")
