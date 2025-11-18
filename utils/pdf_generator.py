from fpdf import FPDF
from utils.logger import logger

def clean_text(text: str) -> str:
    """Convert any text to latin-1 safe printable text."""
    if not text:
        return ""
    return text.encode("latin-1", "replace").decode("latin-1")

def generate_pdf(itinerary_data):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 10, clean_text("EcoGuide AI — Travel Plan"), ln=True, align="C")

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, clean_text("Summary"), ln=True)

        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, clean_text(itinerary_data.get("summary", "")))

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, clean_text("Activities"), ln=True)

        pdf.set_font("Arial", "", 10)
        acts = itinerary_data.get("activities", [])
        if acts:
            for a in acts:
                text = f"- {a.get('title','N/A')} (Eco: {a.get('eco_score','N/A')})"
                pdf.multi_cell(0, 5, clean_text(text))
        else:
            pdf.multi_cell(0, 5, clean_text("No activities provided."))

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, clean_text("Daily Plan"), ln=True)

        pdf.set_font("Arial", "", 10)
        for day in itinerary_data.get("daily_plan", []):
            line = f"Day {day.get('day')}: {day.get('plan')}"
            pdf.multi_cell(0, 5, clean_text(line))

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, clean_text("Budget Breakdown"), ln=True)

        pdf.set_font("Arial", "", 10)
        budget_data = itinerary_data.get("budget_breakdown", {})
        if budget_data:
            for category, cost in budget_data.items():
                pdf.multi_cell(0, 5, clean_text(f"{category}: ${cost}"))
        else:
            pdf.multi_cell(0, 5, "No budget data available.")

        return bytes(pdf.output(dest="S"))

    except Exception as e:
        logger.exception(f"Failed to generate PDF: {e}")
        raise Exception("Could not generate PDF. Please try again.")
