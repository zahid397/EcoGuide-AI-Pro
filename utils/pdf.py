from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Generates a PDF bytes object safely, removing unsupported characters."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "EcoGuide AI - Your Travel Plan", 0, 1, 'C')
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Detailed Itinerary", 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        
        # --- PDF Fix: Handle Text Encoding ---
        raw_plan = itinerary_data.get('plan', 'No detailed plan available.')
        
        # Step 1: Remove Markdown
        plan_text = raw_plan.replace('### ', '').replace('## ', '').replace('* ', '- ')
        
        # Step 2: Encode to Latin-1 to remove Emojis/Unknown chars (Fixes Crash)
        plan_text = plan_text.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.multi_cell(0, 5, plan_text)
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Selected Activities", 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        
        activities = itinerary_data.get('activities', [])
        if activities:
            for item in activities:
                name = item.get('name', 'Unknown').encode('latin-1', 'replace').decode('latin-1')
                dtype = item.get('data_type', 'Activity')
                eco = item.get('eco_score', 'N/A')
                
                item_text = f"- {name} ({dtype}) | Eco: {eco}"
                pdf.multi_cell(0, 5, item_text)
        
        # Budget Breakdown
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
                cat_text = str(category).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(60, 8, cat_text, 1)
                pdf.cell(30, 8, str(cost), 1, 1)
                
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logger.exception(f"Failed to generate PDF: {e}")
        return None
      
