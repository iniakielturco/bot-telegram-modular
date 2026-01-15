# commands.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import BinanceClient
from utils import format_price
import config

# --- COMANDO START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el mensaje de bienvenida y el menú de botones."""
    keyboard = [
        ["👀 VER AHORA"],
        ["🔄 AUTO (UTC-3)"],
        ["☀️ MODO DÍA", "🌙 MODO NOCHE"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 **Bot Iniciado**\n\n"
        "Comandos disponibles:\n"
        "/help - Ver ayuda\n"
        "/precio BTC - Ver precio actual de una moneda\n"
        "\n🕒 **Horario Automático:**\n"
        "☀️ 05:00 - 18:00 (10 min)\n"
        "🌙 18:00 - 05:00 (60 min)", 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    # Inicializamos el modo automático por defecto
    config.BOT_STATE["mode"] = "AUTO"

# --- COMANDO HELP ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información de ayuda."""
    msg = (
        "📚 **AYUDA DEL BOT** 📚\n\n"
        "🔹 **Botones:**\n"
        "• **VER AHORA:** Escanea el CSV y manda el informe al instante.\n"
        "• **AUTO:** Vuelve al horario automático según la hora del día.\n"
        "• **MODO DÍA/NOCHE:** Fuerza la frecuencia de 10m o 60m manual.\n\n"
        "🔹 **Comandos de texto:**\n"
        "• `/precio ETH` -> Te dice el precio actual de Ethereum en Binance.\n"
        "• `/start` -> Reinicia el menú."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- COMANDO PRECIO (Nuevo) ---
async def price_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Permite consultar un precio rápido. 
    Uso: /precio BTC
    """
    if not context.args:
        await update.message.reply_text("⚠️ Uso: `/precio BTC` o `/precio ETH`", parse_mode='Markdown')
        return

    symbol_input = context.args[0].upper()
    # Limpiamos y aseguramos que tenga USDT
    symbol = symbol_input if symbol_input.endswith("USDT") else f"{symbol_input}USDT"
    
    bc = BinanceClient()
    # Reutilizamos tu cliente de Binance existente en data_manager.py
    market_data = bc.get_market_prices([symbol])
    
    if symbol in market_data:
        data = market_data[symbol]
        price = format_price(data['price'])
        change = data['change_percent']
        icon = "🟢" if change >= 0 else "🔴"
        
        await update.message.reply_text(
            f"🪙 **{symbol}** {icon}\n"
            f"💰 Precio: `${price}`\n"
            f"📊 24h: `{change}%`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ No encontré el par **{symbol}** en Binance Futures.", parse_mode='Markdown')