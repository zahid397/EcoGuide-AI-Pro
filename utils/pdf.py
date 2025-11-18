from fpdf import FPDF
from utils.logger import logger

def generate_pdf(itinerary_data):
    try:
        pdf = FPDF()
        pdf.add_page()

        # 1. Title
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, "EcoGuide AI — Your Travel Plan", ln=True, align="C")

        pdf.ln(5)
        pdf.set_font("Arial", "", 12)

        # 2. Summary
        summary = itinerary_data.get("summary", "No summary available.")
        safe_summary = summary.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, safe_summary)

        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Activities & Items", ln=True)

        # 3. Activities
        pdf.set_font("Arial", "", 11)
        activities = itinerary_data.get("activities", [])

        if not activities:
            pdf.multi_cell(0, 6, "- No activities found.")
        else:
            for item in activities:
                line = f"- {item.get('name','Unknown')} | Eco: {item.get('eco_score','N/A')}"
                safe_line = line.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 6, safe_line)

        # 4. Daily Plan
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Daily Plan", ln=True)
        pdf.set_font("Arial", "", 11)

        daily_plan = itinerary_data.get("daily_plan", [])

        if not daily_plan:
            pdf.multi_cell(0, 6, "- No daily plan available.")
        else:
            for day in daily_plan:
                d = f"Day {day.get('day')}: {day.get('plan')}"
                safe_day = d.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 6, safe_day)

        # RETURN PDF bytes
        return bytes(pdf.output(dest="S"))

    except Exception as e:
        logger.exception(f"PDF generation failed: {e}")
        raise Exception("Could not generate PDF. Please try again.")
