import unicodedata
import pandas as pd

def smart_split(text, limit=4000):
    lines = text.split('\n')
    chunks = []
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) + 1 > limit:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def format_price(value):
    if value is None: return "0.00"
    if value >= 1000: return f"{value:,.2f}"
    elif value >= 1: return f"{value:,.2f}"
    else: return f"{value:.4f}"

def clean_symbol(text):
    if pd.isna(text): return ""
    text = str(text).upper().strip()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace(" ", "")
    return text

def get_traffic_light(dist_pct):
    pct = dist_pct * 100
    if pct < 7: return "🟢🟢", f"{pct:.2f}%"
    elif 7 <= pct < 15: return "🟢", f"{pct:.2f}%"
    elif 15 <= pct < 30: return "🟡", f"{pct:.2f}%"
    elif 30 <= pct < 50: return "🟡🟡", f"{pct:.2f}%"
    else: return "🔴", f"{pct:.2f}%"

def calculate_distance(market_price, entry_min, entry_max):
    if entry_min <= market_price <= entry_max: return 0.0 
    dist_min = abs(market_price - entry_min)
    dist_max = abs(market_price - entry_max)
    closest_dist = min(dist_min, dist_max)
    target_price = entry_min if dist_min < dist_max else entry_max
    return closest_dist / target_price

def get_direction_sign(current_price, entry_min, entry_max):
    if current_price < entry_min: return "+"
    elif current_price > entry_max: return "-"
    else: return ""