def calculate_real_cost(activities: list, days: int, travelers: int) -> float:
    total = 0.0
    if not activities: return 0.0
    for item in activities:
        c = float(item.get('cost', 0))
        if item.get('cost_type') == 'per_night':
            rooms = max(1, (travelers + 1) // 2)
            total += (c * rooms) * max(1, days)
        else:
            total += (c * travelers)
    return total
  
