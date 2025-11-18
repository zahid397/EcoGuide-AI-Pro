from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def generate_pdf(itinerary: Dict[str, Any]) -> bytes:
    """Generate a safe PDF from the itinerary."""
    try:
        pdf = FPDF()
        pdf.add_page()

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "EcoGuide AI - Travel Plan", ln=True, align="C")

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Trip Summary", ln=True)

        # Summary block
        pdf.set_font("Arial", "", 11)
        summary = itinerary.get("summary", "No summary available.")
        summary = summary.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 6, summary)

        # Activities
        pdf.ln(4)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Activities", ln=True)

        pdf.set_font("Arial", "", 10)
        for item in itinerary.get("activities", []):
            line = f"- {item.get('title', item.get('name','Unknown'))} | Eco: {item.get('eco_score', 'N/A')}"
            line = line.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 5, line)

        # Budget breakdown
        pdf.ln(4)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Budget Breakdown", ln=True)

        pdf.set_font("Arial", "", 10)
        budget_data = itinerary.get("budget_breakdown", {})
        if isinstance(budget_data, dict):
            for category, cost in budget_data.items():
                line = f"{category}: ${cost}"
                line = line.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 5, line)

        # Output
        return pdf.output(dest="S").encode("latin-1")

    except Exception as e:
        logger.exception(f"PDF generation failed: {e}")
        raise Exception("Could not generate PDF. Please try again.")
