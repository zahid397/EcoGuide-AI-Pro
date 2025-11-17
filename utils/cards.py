def get_card_css() -> str:
    """Injects CSS for the beautiful UI cards."""
    return """<style> .eco-card { background-color: #F8F9FA; border: 1px solid #E0E0E0; border-radius: 10px; padding: 15px; margin-bottom: 10px; display: flex; align-items: center; transition: box-shadow 0.3s; } .eco-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); } .eco-card img { border-radius: 8px; width: 100px; height: 100px; object-fit: cover; margin-right: 15px; } .eco-card-content { flex-grow: 1; } .eco-card-title { font-size: 1.1rem; font-weight: bold; color: #333; } .eco-card-desc { font-size: 0.9rem; color: #555; margin-top: 5px; } .eco-badge-container { display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; } .eco-badge { padding: 4px 10px; border-radius: 15px; font-size: 0.8rem; font-weight: bold; white-space: nowrap; } .eco-score-badge { background-color: #28a745; color: white; } .rating-badge { background-color: #ffc107; color: #333; } .cost-badge { background-color: #007bff; color: white; } </style>"""

def render_card(item: dict) -> str:
    """Renders a single activity/hotel card with safe gets."""
    img_url = item.get('image_url', f"https://placehold.co/100x100/grey/white?text={item.get('data_type', 'Item')}")
    description = item.get('description', 'No description available.')
    if len(description) > 120: description = description[:120] + "..."
    gem_tag = "💎 Hidden Gem" if item.get('tag') == 'hidden_gem' else ""
    return f"""<div class="eco-card"><img src="{img_url}" alt="{item.get('name')}"><div class="eco-card-content"><div class="eco-card-title">{item.get('name')} ({item.get('data_type', '')}) <span style='color: #007bff; font-size: 0.9rem;'>{gem_tag}</span></div><div class="eco-card-desc">{description}</div><div class="eco-badge-container"><span class="eco-badge eco-score-badge">Eco Score: {item.get('eco_score', 'N/A')}/10</span><span class="eco-badge rating-badge">Rating: {item.get('avg_rating', '3.0')} ⭐</span><span class="eco-badge cost-badge">Cost: ${item.get('cost', 0)} ({item.get('cost_type', 'one_time')})</span></div></div></div>"""
  
