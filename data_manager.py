# data_manager.py
import glob
import re
import pandas as pd
import requests
from utils import clean_symbol

class DataManager:
    def __init__(self):
        self.files = glob.glob("*.csv")

    def _parse_entry(self, entry_str):
        if pd.isna(entry_str): return None, None
        s = str(entry_str).replace(',', '.').strip()
        parts = re.split(r'\s*-\s*|\s+a\s+|\s*/\s*|\s*--\s*', s, flags=re.IGNORECASE)
        try:
            nums = [float(p) for p in parts if p]
            if len(nums) >= 2: return min(nums), max(nums)
            elif len(nums) == 1: return nums[0], nums[0]
        except ValueError:
            return None, None
        return None, None

    def get_pending_operations(self):
        self.files = glob.glob("*datos.csv")
        all_data = []
        col_map = {
            'Activo': 'Symbol', 'CRYPTO': 'Symbol', 'Crypto': 'Symbol',
            'Estado': 'Status', 'Estado ': 'Status',
            'Entry': 'Entry_Raw', 'Entry ': 'Entry_Raw', 'Precio': 'Entry_Raw',
            'Trade': 'Direction', 'OPERACION': 'Direction', 'Operación': 'Direction',
            'Análisis técnico/CHART': 'Chart', 'GRAFICA': 'Chart', 'link': 'Chart'
        }

        print(f"📂 Leyendo archivos CSV...")
        for file in self.files:
            if "datos_normalizados" in file or not file.lower().endswith('.csv'):
                continue
            try:
                df = pd.read_csv(file)
                df['Excel_Row'] = df.index + 2
                df = df.rename(columns=col_map)
                
                if 'Symbol' not in df.columns or 'Entry_Raw' not in df.columns: continue
                if 'Status' in df.columns:
                    df['Status'] = df['Status'].astype(str).str.strip().str.capitalize()
                    df = df[df['Status'] == 'Pendiente']
                if df.empty: continue

                df['Symbol'] = df['Symbol'].apply(clean_symbol)
                df['Symbol'] = df['Symbol'].apply(lambda x: x + 'USDT' if not x.endswith(('USDT', 'USD', 'BUSD')) else x)
                entries = df['Entry_Raw'].apply(lambda x: self._parse_entry(x))
                df['Entry_Min'] = entries.apply(lambda x: x[0])
                df['Entry_Max'] = entries.apply(lambda x: x[1])
                df = df.dropna(subset=['Entry_Min'])
                if 'Chart' not in df.columns: df['Chart'] = ''
                all_data.append(df)
            except Exception as e:
                print(f"⚠️ Error leyendo {file}: {e}")

        if not all_data: return pd.DataFrame()
        final_df = pd.concat(all_data, ignore_index=True)
        final_df = final_df.sort_values(by=['Excel_Row'])
        return final_df

class BinanceClient:
    def get_market_prices(self, symbols):
        unique_symbols = list(set(symbols))
        prices = {}
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        try:
            response = requests.get(url, timeout=20) 
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    s = item['symbol']
                    if s in unique_symbols:
                        prices[s] = {
                            'price': float(item['lastPrice']),
                            'change_val': float(item['priceChange']),
                            'change_percent': float(item['priceChangePercent'])
                        }
        except Exception as e:
            print(f"⚠️ Error conexión Binance: {e}")
        return prices