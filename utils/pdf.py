from fpdf import FPDF
from typing import Dict, Any, Union
from utils.logger import logger
import json

def clean_text(text: Any) -> str:
    """
    Aggressively cleans text for PDF generation.
    Removes Emojis, Markdown symbols, and unsupported characters.
    """
    if text is None: return ""
    text = str(text)
    
    # 1. Remove Markdown syntax
    text = text.replace('#', '').replace('*', '').replace('`', '').replace('_', '')
    
    # 2. Force ASCII/Latin-1 (This kills Emojis like 💎, 🌿 which cause crashes)
    # 'ignore' means drop the bad character instead of crashing
    return text.encode('latin-1', 'ignore').decode('latin-1')

def generate_pdf(itinerary_data: Union[Dict[str, Any], str]) -> bytes:
    """
    Generates a PDF bytes object. 
    Handles both Dictionary and JSON String inputs to prevent crashes.
    """
    try:
        # --- SAFETY FIX: Ensure data is a Dictionary ---
        data = itinerary_data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                logger.error("PDF Generator received invalid JSON string.")
                return None 
        
        if not isinstance(data, dict):
            logger.error("PDF Generator received non-dict data.")
            return None

        pdf = FPDF()
        pdf.add_page()
        
        # --- Header ---
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, clean_text("EcoGuide AI - Trip Plan"), 0, 1, 'C')
        pdf.ln(5)
        
        # --- Plan Body ---
        pdf.set_font("Arial", '', 11)
        raw_plan = str(data.get('plan', 'No detailed plan available.'))
        pdf.multi_cell(0, 5, clean_text(raw_plan))
        pdf.ln(10)
        
        # --- Activities List ---
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Activities & Costs"), 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        
        activities = data.get('activities', [])
        if isinstance(activities, list) and activities:
            for item in activities:
                # Handle rare case where item is a string instead of dict
                if isinstance(item, str): continue
                
                name = clean_text(item.get('name', 'Activity'))
                cost = clean_text(item.get('cost', 0))
                
                line = f"- {name} : ${cost}"
                pdf.multi_cell(0, 6, line)
        else:
            pdf.cell(0, 6, clean_text("No specific activities listed."), 0, 1)

        # --- Budget Breakdown ---
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Budget Breakdown"), 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        
        budget_data = data.get('budget_breakdown', {})
        if isinstance(budget_data, dict) and budget_data:
            for category, cost in budget_data.items():
                line = f"{clean_text(category)}: ${clean_text(cost)}"
                pdf.cell(0, 6, line, 0, 1)
        else:
             pdf.cell(0, 6, clean_text("Budget details not available."), 0, 1)
                
        # Return PDF bytes
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        # Log the full error to see what happened
        print(f"❌ PDF CRITICAL ERROR: {e}") 
        logger.exception(f"PDF Generation Failed: {e}")
        return None
        
