from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger
import re

def clean_text(text: Any) -> str:
    """
    Super aggressive cleaner. 
    Removes Emojis, Markdown, and non-Latin characters to prevent PDF crash.
    """
    if text is None: return ""
    text = str(text)
    
    # 1. Remove Markdown (*, #, etc)
    text = text.replace('#', '').replace('*', '').replace('_', '')
    
    # 2. Force Encode to Latin-1 (This kills all Emojis like 💎, 🌿)
    # 'ignore' means if it finds an emoji, it just deletes it.
    text = text.encode('latin-1', 'ignore').decode('latin-1')
    
    return text

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Generates a PDF bytes object safely."""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # --- HEADER ---
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, clean_text("EcoGuide AI - Travel Plan"), 0, 1, 'C')
        pdf.ln(5)
        
        # --- PLAN BODY ---
        pdf.set_font("Arial", '', 11)
        raw_plan = str(itinerary_data.get('plan', 'No detailed plan available.'))
        pdf.multi_cell(0, 5, clean_text(raw_plan))
        pdf.ln(10)
        
        # --- ACTIVITIES TABLE ---
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Activities & Costs"), 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        
        activities = itinerary_data.get('activities', [])
        if activities:
            for item in activities:
                name = clean_text(item.get('name', 'Activity'))
                dtype = clean_text(item.get('data_type', 'Spot'))
                cost = clean_text(item.get('cost', 0))
                
                # Line format: - Name (Type) : $Cost
                line = f"- {name} ({dtype}) : ${cost}"
                pdf.multi_cell(0, 6, line)
        else:
            pdf.cell(0, 6, "No specific activities listed.", 0, 1)

        # --- BUDGET TABLE ---
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Budget Breakdown"), 0, 1, 'L')
        
        # Header
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(100, 8, 'Category', 1)
        pdf.cell(40, 8, 'Cost ($)', 1, 1)
        
        # Rows
        pdf.set_font("Arial", '', 10)
        budget_data = itinerary_data.get('budget_breakdown', {})
        
        if budget_data:
            for category, cost in budget_data.items():
                # Ensure everything is string and clean
                cat_clean = clean_text(str(category))
                cost_clean = clean_text(str(cost))
                
                pdf.cell(100, 8, cat_clean, 1)
                pdf.cell(40, 8, cost_clean, 1, 1)
        else:
            pdf.cell(140, 8, "No budget data available.", 1, 1)

        # Return PDF as bytes
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        # Log the specific error to terminal/file
        print(f"❌ PDF GENERATION FAILED: {e}")
        logger.exception(f"PDF Gen Failed: {e}")
        return None
        
