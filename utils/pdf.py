from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger


# ---------------------------------------------------
# CLEAN TEXT HANDLER (Fixes all PDF Unicode errors)
# ---------------------------------------------------
def clean_text(txt: Any) -> str:
    """Ensures all text is safe for PDF (latin-1 fallback)."""
    if isinstance(txt, bytearray):
        txt = txt.decode("utf-8", "ignore")

    if not isinstance(txt, str):
        txt = str(txt)

    # Replace unsupported characters to avoid FPDF crash
    return txt.encode("latin-1", "replace").decode("latin-1")


# ---------------------------------------------------
# PDF GENERATOR (FINAL ERROR-FREE VERSION)
# ---------------------------------------------------
def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Generates safe PDF bytes from itinerary."""
    try:
        pdf = FPDF()
        pdf.add_page()

        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, clean_text("EcoGuide AI – Travel Plan"), 0, 1, 'C')

        # Subtitle
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Detailed Itinerary"), 0, 1, 'L')

        # Main Plan Text
        pdf.set_font("Arial", '', 11)

        plan_text = itinerary_data.get("plan", "No itinerary text available.")
        plan_text = clean_text(plan_text)

        pdf.multi_cell(0, 6, plan_text)

        # Activities Section
        pdf.ln(6)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Activities & Places"), 0, 1)

        pdf.set_font("Arial", '', 11)

        for item in itinerary_data.get("activities", []):
            name = clean_text(item.get("name", "Unknown"))
            dtype = clean_text(item.get("data_type", "N/A"))
            eco = clean_text(item.get("eco_score", "N/A"))
            cost = clean_text(item.get("cost", "N/A"))

            txt = f"- {name} | {dtype} | Eco: {eco} | Cost: {cost}"
            pdf.multi_cell(0, 6, clean_text(txt))

        # Budget Section
        pdf.ln(6)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Budget Breakdown"), 0, 1)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(80, 8, "Category", 1)
        pdf.cell(40, 8, "Cost ($)", 1, 1)

        pdf.set_font("Arial", '', 10)

        for category, cost in itinerary_data.get("budget_breakdown", {}).items():
            pdf.cell(80, 8, clean_text(category), 1)
            pdf.cell(40, 8, clean_text(cost), 1, 1)

        # Final PDF output
        return pdf.output(dest="S").encode("latin-1", "replace")

    except Exception as e:
        logger.exception(f"PDF Generation Failed: {e}")
        raise Exception("Could not generate PDF. Please try again.")
