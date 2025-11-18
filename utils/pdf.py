from fpdf import FPDF
from utils.logger import logger

def generate_pdf(itinerary):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "EcoGuide AI - Travel Plan", 0, 1, "C")

        pdf.set_font("Arial", "", 12)
        plan_text = itinerary.get("plan", "No plan available.")

        if not plan_text or plan_text.strip() == "":
            plan_text = "No detailed plan available."

        safe_text = plan_text.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 10, safe_text)

        return pdf.output(dest="S").encode("latin-1")

    except Exception as e:
        logger.exception(f"PDF generation failed: {e}")
        raise Exception("Could not generate PDF. Please try again.")
