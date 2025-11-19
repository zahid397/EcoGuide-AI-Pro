from typing import List, Dict, Any

def calculate_real_cost(activities_list: List[Dict[str, Any]], trip_days: int, travelers: int) -> float:
    """Calculates real cost safely, handling strings and missing values."""
    total_cost = 0.0
    
    if not activities_list: 
        return 0.0
    
    for item in activities_list:
        # Safe conversion to float
        try:
            raw_cost = item.get('cost', 0)
            item_cost = float(str(raw_cost).replace('$', '').replace(',', ''))
        except:
            item_cost = 0.0
            
        cost_type = item.get('cost_type', 'one_time')
            
        if cost_type == 'per_night': 
            # Assume 1 room per 2 travelers
            rooms = max(1, (travelers + 1) // 2)
            total_cost += (item_cost * rooms) * max(1, trip_days)
        else: 
            # Per-person activity cost
            total_cost += (item_cost * travelers)
            
    return round(total_cost, 2)
    
