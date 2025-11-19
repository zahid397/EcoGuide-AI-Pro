from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def clean_text(text: Any) -> str:
    """Forces text to be PDF-compatible (ASCII only). Removes Emojis."""
    if text is None: return ""
    text = str(text)
    # ইমোজি এবং নন-ল্যাটিন অক্ষর বাদ দেওয়া হচ্ছে
    return text.encode('latin-1', 'ignore').decode('latin-1')

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "EcoGuide AI - Trip Plan", 0, 1, 'C')
        
        pdf.set_font("Arial", '', 11)
        
        # --- Plan Section ---
        raw_plan = str(itinerary_data.get('plan', 'No detailed plan.'))
        clean_plan = raw_plan.replace('#', '').replace('*', '-')
        pdf.multi_cell(0, 5, clean_text(clean_plan))
        
        pdf.ln(10)
        
        # --- Activities Section ---
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

        # --- Budget Section ---
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Budget Breakdown", 0, 1, 'L')
        pdf.set_font("Arial", 'B', 10)
        
        # Table Header
        pdf.cell(100, 8, 'Category', 1)
        pdf.cell(40, 8, 'Cost ($)', 1, 1)
        
        pdf.set_font("Arial", '', 10)
        budget_data = itinerary_data.get('budget_breakdown', {})
        if budget_data:
            for category, cost in budget_data.items():
                pdf.cell(100, 8, clean_text(str(category)), 1)
                pdf.cell(40, 8, clean_text(str(cost)), 1, 1)
                
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logger.exception(f"PDF Gen Failed: {e}")
        return None
        
