# commands.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import BinanceClient, DataManager
from utils import format_price, smart_split
from alerts import format_close_table # <--- Importamos la lógica de alertas
import config

# --- COMANDO START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el panel de control actualizado."""
    is_active = config.BOT_STATE.get("active", True)
    toggle_text = "🔴 PAUSAR BOT" if is_active else "🟢 ACTIVAR BOT"
    
    keyboard = [
        ["👀 VER AHORA", toggle_text],
        ["🔥 ZONA DE DISPARO", "❓ AYUDA"] # <--- Botón Nuevo
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    status = "✅ ACTIVO" if is_active else "⏸️ PAUSADO"
    
    await update.message.reply_text(
        f"🤖 **Panel de Control**\n"
        f"Estado: **{status}**\n\n"
        "🕒 **Modo Automático Permanente:**\n"
        "☀️ Día (05-18h): Cada 10 min\n"
        "🌙 Noche (18-05h): Cada 60 min", 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    if "active" not in config.BOT_STATE:
        config.BOT_STATE["active"] = True

# --- COMANDO HELP ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📚 **AYUDA** 📚\n\n"
        "• **🟢 ACTIVAR / 🔴 PAUSAR:** Enciende o apaga el escaneo automático.\n"
        "• **👀 VER AHORA:** Informe completo (Tabla + Alertas).\n"
        "• **🔥 ZONA DE DISPARO:** Muestra SOLO las operaciones cercanas o en rango.\n"
        "• **AUTO:** El bot cambia solo la frecuencia (10m/60m)."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- COMANDO PRECIO INDIVIDUAL ---
async def price_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Uso: `/precio BTC`")
        return

    symbol_input = context.args[0].upper()
    symbol = symbol_input if symbol_input.endswith("USDT") else f"{symbol_input}USDT"
    
    bc = BinanceClient()
    market_data = bc.get_market_prices([symbol])
    
    if symbol in market_data:
        data = market_data[symbol]
        price = format_price(data['price'])
        change = data['change_percent']
        icon = "🟢" if change >= 0 else "🔴"
        await update.message.reply_text(f"🪙 **{symbol}** {icon}\n💰 ${price} ({change}%)", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ No encontré {symbol}")

# --- NUEVO: SOLO ZONA DE DISPARO ---
async def check_fire_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Escanea y envía SOLO las alertas de la Zona de Disparo."""
    await update.message.reply_text("🔥 Analizando Zona de Disparo...")
    
    # 1. Obtener Datos
    dm = DataManager()
    df = dm.get_pending_operations()
    
    if df.empty:
        await update.message.reply_text("⚠️ Tabla vacía.")
        return

    # 2. Obtener Precios
    symbols = df['Symbol'].unique().tolist()
    bc = BinanceClient()
    market_data = bc.get_market_prices(symbols)
    
    if not market_data:
        await update.message.reply_text("❌ Error Binance.")
        return
        
    # 3. Generar SOLO el mensaje de alertas
    msg_cercana = format_close_table(df, market_data)
    
    # 4. Enviar
    for chunk in smart_split(msg_cercana):
        await update.message.reply_text(chunk, parse_mode='Markdown', disable_web_page_preview=True)