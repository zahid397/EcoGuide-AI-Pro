from fpdf import FPDF
from utils.logger import logger

def safe(text):
    """Safely convert any value to Latin-1 printable text."""
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

        # TITLE
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, safe("EcoGuide AI — Travel Plan"), ln=True, align="C")
        pdf.ln(5)

        # SUMMARY
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Summary", ln=True)

        pdf.set_font("Arial", "", 11)
        summary = itinerary_data.get("summary", "No summary available.")
        pdf.multi_cell(0, 6, safe(summary))
        pdf.ln(5)

        # ACTIVITIES
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Activities", ln=True)
        pdf.set_font("Arial", "", 11)

        activities = itinerary_data.get("activities", [])
        if not activities:
            pdf.multi_cell(0, 6, safe("- No activities available."))
        else:
            for item in activities:
                line = f"- {safe(item.get('name', 'Unknown'))} | Eco Score: {safe(item.get('eco_score', 'N/A'))}"
                pdf.multi_cell(0, 6, safe(line))

        pdf.ln(5)

        # DAILY PLAN
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Daily Plan", ln=True)
        pdf.set_font("Arial", "", 11)

        daily = itinerary_data.get("daily_plan", [])
        if not daily:
            pdf.multi_cell(0, 6, safe("No day-by-day plan available."))
        else:
            for day in daily:
                line = f"Day {safe(day.get('day', '?'))}: {safe(day.get('plan', 'No plan'))}"
                pdf.multi_cell(0, 6, safe(line))

        # Return bytes (MUST wrap in bytes() or Streamlit fails)
        return bytes(pdf.output(dest="S"))

    except Exception as e:
        logger.exception(f"Failed to generate PDF: {e}")
        raise Exception("Could not generate PDF. Please try again.")
