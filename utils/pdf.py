from fpdf import FPDF
from utils.logger import logger

def safe(text):
    """Convert ANY object safely to printable text for PDF."""
    try:
        if text is None:
            return ""
        if isinstance(text, (dict, list)):
            text = str(text)
        if isinstance(text, (bytes, bytearray)):
            text = text.decode("utf-8", "replace")
        return str(text).encode("latin-1", "replace").decode("latin-1")
    except:
        return "N/A"


def generate_pdf(itinerary_data):
    try:
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, safe("EcoGuide AI — Travel Plan"), ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Summary", ln=True)

        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, safe(itinerary_data.get("summary", "")))

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Activities", ln=True)
        pdf.set_font("Arial", "", 11)

        for item in itinerary_data.get("activities", []):
            line = f"- {safe(item.get('name'))} | Eco Score: {safe(item.get('eco_score'))}"
            pdf.multi_cell(0, 6, safe(line))

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Daily Plan", ln=True)
        pdf.set_font("Arial", "", 11)

        for day in itinerary_data.get("daily_plan", []):
            line = f"Day {safe(day.get('day'))}: {safe(day.get('plan'))}"
            pdf.multi_cell(0, 6, safe(line))

        return bytes(pdf.output(dest="S"))

    except Exception as e:
        logger.exception(f"Failed to generate PDF: {e}")
        raise Exception("Could not generate PDF. Please try again.")
