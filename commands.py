# commands.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import BinanceClient, DataManager
from utils import format_price
import config

# --- COMANDO START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el panel de control simplificado."""
    # Verificamos si está activo para mostrar el botón correcto
    is_active = config.BOT_STATE.get("active", True)
    toggle_text = "🔴 PAUSAR BOT" if is_active else "🟢 ACTIVAR BOT"
    
    keyboard = [
        ["👀 VER AHORA", toggle_text],
        ["💰 PRECIOS TABLA", "❓ AYUDA"]
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
    # Nos aseguramos de inicializar el estado
    if "active" not in config.BOT_STATE:
        config.BOT_STATE["active"] = True

# --- COMANDO HELP ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📚 **AYUDA** 📚\n\n"
        "• **🟢 ACTIVAR / 🔴 PAUSAR:** Enciende o apaga el escaneo automático.\n"
        "• **👀 VER AHORA:** Fuerza un escaneo manual instantáneo (funciona aunque esté pausado).\n"
        "• **💰 PRECIOS TABLA:** Lista rápida de precios.\n"
        "• **AUTO:** El bot cambia solo la frecuencia según la hora (10m de día / 60m de noche)."
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

# --- PRECIOS DE LA TABLA ---
async def check_all_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Consultando precios...")
    dm = DataManager()
    df = dm.get_pending_operations()
    
    if df.empty:
        await update.message.reply_text("⚠️ Tabla vacía.")
        return

    symbols = df['Symbol'].unique().tolist()
    bc = BinanceClient()
    market_data = bc.get_market_prices(symbols)
    
    if not market_data:
        await update.message.reply_text("❌ Error Binance.")
        return
        
    lines = ["💰 **PRECIOS ACTUALES** 💰", ""]
    for symbol in symbols:
        data = market_data.get(symbol)
        if data:
            price = format_price(data['price'])
            change = data['change_percent']
            icon = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            lines.append(f"{icon} **{symbol}**: ${price} ({sign}{change}%)")
            
    msg = "\n".join(lines)
    await update.message.reply_text(msg, parse_mode='Markdown')