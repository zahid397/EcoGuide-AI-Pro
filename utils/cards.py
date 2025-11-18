def get_card_css():
    return """<style>.eco-card{background:#F8F9FA;border:1px solid #E0E0E0;border-radius:10px;padding:15px;margin-bottom:10px;display:flex;align-items:center;}.eco-card img{width:100px;height:100px;object-fit:cover;margin-right:15px;border-radius:8px;}.eco-score{color:white;background:#28a745;padding:2px 8px;border-radius:12px;font-size:0.8em;}</style>"""

def render_card(item: dict) -> str:
    img = item.get('image_url', "https://placehold.co/100x100?text=No+Image")
    tag = "💎 Hidden Gem" if item.get('tag') == 'hidden_gem' else ""
    return f"""
    <div class="eco-card">
        <img src="{img}">
        <div style="flex-grow:1;">
            <div style="font-weight:bold; font-size:1.1em;">{item.get('name')} <span style="color:#007bff;font-size:0.8em;">{tag}</span></div>
            <div style="color:#555;font-size:0.9em;margin:5px 0;">{item.get('description')}</div>
            <div>
                <span class="eco-score">Eco: {item.get('eco_score')}/10</span>
                <span style="background:#ffc107;padding:2px 8px;border-radius:12px;font-size:0.8em;">⭐ {item.get('avg_rating')}</span>
                <span style="background:#007bff;color:white;padding:2px 8px;border-radius:12px;font-size:0.8em;">${item.get('cost')}</span>
            </div>
        </div>
    </div>
    """
  
