from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def clean_text(text: str) -> str:
    """Forces text to be PDF-compatible (ASCII only)."""
    if not text: return ""
    # ইমোজি এবং নন-ল্যাটিন অক্ষর বাদ দেওয়া হচ্ছে যাতে ক্র্যাশ না করে
    return text.encode('latin-1', 'ignore').decode('latin-1')

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Generates a PDF bytes object safely."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "EcoGuide AI - Your Travel Plan", 0, 1, 'C')
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Detailed Itinerary", 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        
        # --- FIX: Clean Text Aggressively ---
        raw_plan = str(itinerary_data.get('plan', 'No detailed plan available.'))
        plan_text = raw_plan.replace('### ', '').replace('## ', '').replace('* ', '- ')
        
        pdf.multi_cell(0, 5, clean_text(plan_text))
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Selected Activities", 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        
        activities = itinerary_data.get('activities', [])
        if activities:
            for item in activities:
                name = clean_text(str(item.get('name', 'Unknown')))
                dtype = clean_text(str(item.get('data_type', 'Activity')))
                eco = clean_text(str(item.get('eco_score', 'N/A')))
                cost = clean_text(str(item.get('cost', 0)))
                
                item_text = f"- {name} ({dtype}) | Eco: {eco} | ${cost}"
                pdf.multi_cell(0, 5, item_text)
        
        # Budget Section
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Budget Breakdown", 0, 1, 'L')
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(60, 8, 'Category', 1)
        pdf.cell(30, 8, 'Cost ($)', 1, 1)
        
        pdf.set_font("Arial", '', 10)
        budget_data = itinerary_data.get('budget_breakdown', {})
        if budget_data:
            for category, cost in budget_data.items():
                pdf.cell(60, 8, clean_text(str(category)), 1)
                pdf.cell(30, 8, clean_text(str(cost)), 1, 1)
                
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logger.exception(f"Failed to generate PDF: {e}")
        return None
        
