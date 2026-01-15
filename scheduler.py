import pytz
from datetime import datetime
from config import FREQ_HIGH, FREQ_LOW

def calcular_intervalo_auto():
    tz_ba = pytz.timezone('America/Argentina/Buenos_Aires')
    now_ba = datetime.now(tz_ba)
    
    # De 05:00 a 18:00 (Modo Día - Rápido)
    if 5 <= now_ba.hour < 18:
        return FREQ_HIGH, "Modo Día ☀️ (10m)"
    else:
        return FREQ_LOW, "Modo Noche 🌙 (60m)"