from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def safe_text(text: Any) -> str:
    """Converts any text to safe Latin-1 for FPDF, replacing emojis."""
    if not isinstance(text, str):
        text = str(text)

    return text.encode("latin-1", "replace").decode("latin-1")


def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Fully safe PDF generator (no crashes)."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, safe_text("EcoGuide AI - Your Travel Plan"), 0, 1, "C")

        # -------------------------
        # PLAN SECTION
        # -------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, safe_text("Detailed Itinerary"), 0, 1)

        pdf.set_font("Arial", "", 11)
        raw_plan = itinerary_data.get("plan", "No plan available.")

        # FIX: if plan is dict/list
        if not isinstance(raw_plan, str):
            raw_plan = safe_text(str(raw_plan))

        plan_text = (
            raw_plan.replace("###", "")
            .replace("##", "")
            .replace("*", "-")
        )

        pdf.multi_cell(0, 6, safe_text(plan_text))

        # -------------------------
        # ACTIVITIES
        # -------------------------
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, safe_text("Selected Activities"), 0, 1)

        pdf.set_font("Arial", "", 11)
        activities = itinerary_data.get("activities", [])

        if not activities:
            pdf.cell(0, 8, safe_text("No activities listed."), 0, 1)
        else:
            for item in activities:
                name = safe_text(item.get("name", "Activity"))
                eco = item.get("eco_score", "N/A")
                dtype = safe_text(item.get("data_type", "Activity"))
                line = f"- {name} | {dtype} | Eco Score: {eco}"
                pdf.multi_cell(0, 6, safe_text(line))

        # -------------------------
        # BUDGET TABLE
        # -------------------------
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, safe_text("Budget Breakdown"), 0, 1)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(80, 8, "Category", 1)
        pdf.cell(40, 8, "Cost ($)", 1, 1)

        pdf.set_font("Arial", "", 10)
        budget_data = itinerary_data.get("budget_breakdown", {})

        if isinstance(budget_data, dict):
            for cat, val in budget_data.items():
                pdf.cell(80, 8, safe_text(cat), 1)
                pdf.cell(40, 8, safe_text(val), 1, 1)
        else:
            pdf.cell(0, 8, safe_text("No budget details available."), 1, 1)

        # -------------------------
        # OUTPUT AS BYTES
        # -------------------------
        pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
        return pdf_bytes

    except Exception as e:
        logger.exception(f"PDF generation failed: {e}")
        raise Exception("Could not generate PDF. Please try again.")
