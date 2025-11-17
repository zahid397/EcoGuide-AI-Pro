from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Generates a PDF bytes object from the itinerary (Fix 3 & 4)."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "EcoGuide AI - Your Travel Plan", 0, 1, 'C')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Detailed Itinerary", 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        
        plan_text = itinerary_data.get('plan', 'No plan text.').replace('### ', '').replace('## ', '').replace('* ', '- ')
        plan_text = plan_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, plan_text)
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Selected Activities, Hotels & Places", 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        for item in itinerary_data.get('activities', []):
            item_text = f"- {item.get('name')} (Type: {item.get('data_type')}, Eco: {item.get('eco_score')}, Cost: ${item.get('cost')})"
            item_text = item_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, item_text)
            
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
                pdf.cell(60, 8, str(category), 1)
                pdf.cell(30, 8, str(cost), 1, 1)
                
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        logger.exception(f"Failed to generate PDF: {e}")
        raise
      
