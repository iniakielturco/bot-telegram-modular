import pandas as pd
from utils import format_price, calculate_distance, get_traffic_light, get_direction_sign

def format_close_table(df, market_data):
    lines = ["🚨 **ZONA DE DISPARO (<15%)** 🚨", ""]
    close_ops = []
    for _, row in df.iterrows():
        symbol = row['Symbol']
        m_data = market_data.get(symbol)
        if not m_data: continue
        
        dist = calculate_distance(m_data['price'], row['Entry_Min'], row['Entry_Max'])
        
        if dist < 0.15:
            row['Distance'] = dist
            row['Market_Price'] = m_data['price']
            close_ops.append(row)
    
    if not close_ops: return "✅ Todo tranquilo (<15%)."

    df_close = pd.DataFrame(close_ops)
    df_close = df_close.sort_values('Distance', ascending=True)
    
    for _, row in df_close.iterrows():
        symbol = row['Symbol']
        market_price = row['Market_Price']
        entry_raw = row['Entry_Raw']
        excel_row = row['Excel_Row']
        dist = row['Distance']
        
        setup_info = f"{row.get('Setup', '')} {row.get('Risk', '')}".strip()
        raw_dir = row.get('Direction', 'Trade')
        direction = str(raw_dir).upper() if pd.notna(raw_dir) else "TRADE"
        
        emoji, pct_str = get_traffic_light(dist)
        mkt_fmt = format_price(market_price)
        dir_sign = get_direction_sign(market_price, row['Entry_Min'], row['Entry_Max'])
        
        link = row.get('Chart', '')
        link_line = ""
        if link and str(link) != 'nan' and str(link).strip() != '':
                link_line = f"\n   📊 [Ver Gráfico]({link})"
        
        lines.append(f"🔥 #{excel_row} {symbol} {setup_info} {direction}")
        lines.append(f"   🎯 Entry: {entry_raw} | 🏦 Price: {mkt_fmt}")
        lines.append(f"   ⚠️ Dist: {emoji} {dir_sign}{pct_str}{link_line}")
        lines.append("")

    return "\n".join(lines)