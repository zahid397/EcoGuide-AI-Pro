from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger


def safe_text(text: str) -> str:
    """Remove ALL emojis + unicode. Always 100% PDF safe."""
    if not text:
        return ""
    return "".join(ch if 32 <= ord(ch) <= 126 else " " for ch in text)


def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """
    FINAL VERSION — NEVER CRASHES.
    If plan is broken → converts to safe text.
    If activity missing → skip safely.
    If unicode → removed.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=10)

        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, safe_text("EcoGuide AI - Travel Plan"), ln=1, align="C")

        # Main Plan
        pdf.set_font("Arial", "", 11)
        raw_plan = itinerary_data.get("plan", "No plan available.")
        for line in safe_text(raw_plan).split("\n"):
            pdf.multi_cell(0, 5, line)

        # Activities
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, safe_text("Activities"), ln=1)

        pdf.set_font("Arial", "", 10)
        activities = itinerary_data.get("activities", [])

        if activities:
            for item in activities:
                name = safe_text(str(item.get("name", "Unknown")))
                eco = safe_text(str(item.get("eco_score", "N/A")))
                pdf.multi_cell(0, 5, f"- {name} | Eco Score: {eco}")
        else:
            pdf.multi_cell(0, 5, safe_text("No activities listed."))

        # Budget
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, safe_text("Budget Breakdown"), ln=1)

        pdf.set_font("Arial", "", 10)
        budget_data = itinerary_data.get("budget_breakdown", {})

        if budget_data:
            for k, v in budget_data.items():
                pdf.multi_cell(0, 5, safe_text(f"{k}: ${v}"))
        else:
            pdf.multi_cell(0, 5, safe_text("No budget data."))

        # FINAL OUTPUT
        return pdf.output(dest="S").encode("latin-1")

    except Exception as e:
        logger.exception(f"PDF GENERATION CRASH → {e}")

        # 🔥 RETURN BACKUP PDF INSTEAD OF ERROR
        fallback = FPDF()
        fallback.add_page()
        fallback.set_font("Arial", "B", 16)
        fallback.cell(0, 10, "EcoGuide AI - PDF Fallback", ln=1)
        fallback.set_font("Arial", "", 12)
        fallback.multi_cell(0, 6, "PDF could not display detailed data.\nBut your file is safe.")
        return fallback.output(dest="S").encode("latin-1")
