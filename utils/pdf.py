from fpdf import FPDF
from typing import Dict, Any
from utils.logger import logger

def clean_text(text: Any) -> str:
    """
    NUCLEAR CLEANER: Removes EVERYTHING except basic English letters/numbers.
    This guarantees PDF generation will never crash due to encoding.
    """
    if text is None: return ""
    text = str(text)
    
    # 1. Remove Markdown
    text = text.replace('#', '').replace('*', '').replace('`', '').replace('_', '')
    
    # 2. FORCE ASCII ONLY (Nuclear Option)
    # This deletes Bangla, Emojis, Special Symbols completely.
    return text.encode('ascii', 'ignore').decode('ascii')

def generate_pdf(itinerary_data: Dict[str, Any]) -> bytes:
    """Generates a fail-safe PDF."""
    try:
        # Check data validity
        if not isinstance(itinerary_data, dict):
            logger.error("PDF generator received invalid data type")
            return None

        pdf = FPDF()
        pdf.add_page()
        
        # Use standard fonts only (Helvetica is safest)
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, "EcoGuide AI Plan", 0, 1, 'C')
        pdf.ln(5)
        
        # --- PLAN BODY ---
        pdf.set_font("Helvetica", '', 11)
        
        raw_plan = str(itinerary_data.get('plan', 'No plan text.'))
        safe_plan = clean_text(raw_plan)
        
        # Multi_cell is safer for long text
        pdf.multi_cell(0, 5, safe_plan)
        pdf.ln(10)
        
        # --- ACTIVITIES ---
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Activities", 0, 1, 'L')
        pdf.set_font("Helvetica", '', 10)
        
        activities = itinerary_data.get('activities', [])
        if isinstance(activities, list) and activities:
            for item in activities:
                # Individual try-except block for each item
                try:
                    name = clean_text(item.get('name', 'Activity'))
                    cost = clean_text(item.get('cost', '0'))
                    eco = clean_text(item.get('eco_score', 'N/A'))
                    
                    line = f"- {name} (Eco: {eco}) : ${cost}"
                    pdf.cell(0, 6, line, 0, 1)
                except:
                    continue # Skip bad item, don't crash PDF
        else:
            pdf.cell(0, 6, "No activities listed.", 0, 1)

        # --- BUDGET ---
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "Budget", 0, 1, 'L')
        pdf.set_font("Helvetica", '', 10)
        
        budget_data = itinerary_data.get('budget_breakdown', {})
        if isinstance(budget_data, dict) and budget_data:
            for cat, cost in budget_data.items():
                try:
                    line = f"{clean_text(cat)}: ${clean_text(cost)}"
                    pdf.cell(0, 6, line, 0, 1)
                except:
                    continue

        # --- FINAL OUTPUT ---
        # 'latin-1' encoding is required by FPDF's output method
        return pdf.output(dest='S').encode('latin-1', 'ignore')
        
    except Exception as e:
        # If all else fails, return a simple error PDF bytes
        logger.exception(f"CRITICAL PDF FAILURE: {e}")
        return None
        
