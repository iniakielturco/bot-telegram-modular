import pandas as pd
from utils import format_price, calculate_distance, get_traffic_light, get_direction_sign

def format_main_table(df, market_data):
    lines = ["📊 **TABLERO OPERATIVO** 📊", ""]
    grouped = df.groupby('Symbol')
    
    for symbol, group in grouped:
        m_data = market_data.get(symbol)
        
        if m_data:
            price_fmt = format_price(m_data['price']) 
            change_pct = m_data['change_percent']
            
            if change_pct >= 0:
                trend_icon = "🟢"
                sign = "+"
            else:
                trend_icon = "🔴"
                sign = "" 
            
            header = f"🪙 {symbol} {trend_icon} | ${price_fmt} ({sign}{change_pct}%)"
        else:
            header = f"🪙 {symbol} | (Sin Datos)"
        
        lines.append(header)
        
        group = group.sort_values('Excel_Row')
        
        for _, row in group.iterrows():
            raw_dir = row.get('Direction', 'Trade')
            direction = str(raw_dir).lower() if pd.notna(raw_dir) else "trade"
            entry_raw = row['Entry_Raw']
            excel_row = row['Excel_Row']
            
            dist_str = ""
            if m_data:
                dist = calculate_distance(m_data['price'], row['Entry_Min'], row['Entry_Max'])
                emoji, pct_str = get_traffic_light(dist)
                dir_sign = get_direction_sign(m_data['price'], row['Entry_Min'], row['Entry_Max'])
                dist_str = f"| {emoji} {dir_sign}{pct_str}"
            
            lines.append(f"   🔹 #{excel_row} {direction}   🎯 Entry: {entry_raw} {dist_str}")
        
        lines.append("") 
        
    return "\n".join(lines)