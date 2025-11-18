from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger


# ----------------------------------------------------
# C++ Style ASCII Sanitizer (PDF-safe)
# ----------------------------------------------------
def cpp_filter_ascii(text: str) -> str:
    """
    C++ style ASCII-only filter.
    Keeps only printable ASCII 32–126.
    Everything else becomes '?'.
    """
    result = []
    for ch in text:
        if 32 <= ord(ch) <= 126:  # printable ASCII
            result.append(ch)
        else:
            result.append('?')
    return "".join(result)


# ----------------------------------------------------
# PDF Generator (Fully Error-Proof)
# ----------------------------------------------------
def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=12)

        # -------- HEADER --------
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "EcoGuide AI - Travel Plan", ln=1, align="C")

        # -------- MAIN PLAN --------
        raw_plan = itinerary_data.get("plan", "No plan available.")
        safe_plan = cpp_filter_ascii(raw_plan)

        pdf.set_font("Arial", "", 11)
        for line in safe_plan.split("\n"):
            pdf.multi_cell(0, 6, line)

        # -------- ACTIVITIES --------
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Activities", ln=1)

        pdf.set_font("Arial", "", 10)
        activities = itinerary_data.get("activities", [])

        if not activities:
            pdf.multi_cell(0, 6, "No activities available.")
        else:
            for a in activities:
                line = f"- {a.get('name','Unknown')} | Eco: {a.get('eco_score','N/A')}"
                pdf.multi_cell(0, 6, cpp_filter_ascii(line))

        # -------- BUDGET --------
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Budget Breakdown", ln=1)

        pdf.set_font("Arial", "", 11)
        budget_data = itinerary_data.get("budget_breakdown", {})

        if not budget_data:
            pdf.multi_cell(0, 6, "No budget data.")
        else:
            for k, v in budget_data.items():
                line = f"{k}: ${v}"
                pdf.multi_cell(0, 6, cpp_filter_ascii(line))

        # -------- OUTPUT PDF --------
        return pdf.output(dest='S').encode('latin-1')


    except Exception as e:
        logger.exception(f"PDF ERROR → {e}")
        raise Exception("PDF generation failed.")
