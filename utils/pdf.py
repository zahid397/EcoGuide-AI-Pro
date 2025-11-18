from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def clean_text(text: Any) -> str:
    """Ensures text is safe for PDF (Removes Emoji/Unicode)."""
    if text is None:
        return ""
    text = str(text)
    # Encode to ASCII/Latin-1, ignore errors to prevent crash
    return text.encode('latin-1', 'ignore').decode('latin-1')

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Generates a PDF bytes object safely."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "EcoGuide AI - Travel Plan", 0, 1, 'C')
        
        pdf.set_font("Arial", '', 11)
        
        # --- PLAN SECTION ---
        raw_plan = itinerary_data.get('plan', 'No plan text.')
        # Remove Markdown symbols
        clean_plan = raw_plan.replace('#', '').replace('*', '-')
        pdf.multi_cell(0, 5, clean_text(clean_plan))
        
        pdf.ln(10)
        
        # --- ACTIVITIES SECTION ---
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Activities & Costs", 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        
        activities = itinerary_data.get('activities', [])
        if activities:
            for item in activities:
                name = clean_text(item.get('name', 'Activity'))
                cost = clean_text(item.get('cost', 0))
                line = f"- {name} : ${cost}"
                pdf.cell(0, 8, line, 0, 1)
        else:
            pdf.cell(0, 8, "No specific activities listed.", 0, 1)

        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logger.exception(f"PDF Gen Failed: {e}")
        return None
        
