from typing import List, Dict, Any

def calculate_real_cost(activities_list: List[Dict[str, Any]], trip_days: int, travelers: int) -> float:
    """Calculates the real cost of the trip."""
    total_cost = 0.0
    if not isinstance(activities_list, list): return 0.0
    
    for item in activities_list:
        item_cost = item.get('cost', 0)
        cost_type = item.get('cost_type', 'one_time')
        
        # Ensure item_cost is a number
        try:
            item_cost = float(item_cost)
        except (ValueError, TypeError):
            item_cost = 0.0
            
        if cost_type == 'per_night': 
            # Assume 1 room per 2 travelers
            rooms = max(1, (travelers + 1) // 2)
            total_cost += (item_cost * rooms) * max(1, trip_days)
        else: 
            # Per-person activity cost
            total_cost += (item_cost * travelers)
    return total_cost
  
