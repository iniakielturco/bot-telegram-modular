# runbot.py
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, Application
from telegram.request import HTTPXRequest

# Importamos nuestros módulos propios
import config
from utils import smart_split
from data_manager import DataManager, BinanceClient
from tables import format_main_table
from alerts import format_close_table
from scheduler import calcular_intervalo_auto

async def analizar_y_enviar(context: ContextTypes.DEFAULT_TYPE):
    if context.job:
        chat_id = context.job.data 
    else:
        chat_id = context._chat_id 
    
    dm = DataManager()
    df = dm.get_pending_operations()
    if df.empty:
        if context.job is None: 
            await context.bot.send_message(chat_id=chat_id, text="⚠️ CSV Vacío o sin pendientes.")
        else:
            print(f"ℹ️ [{datetime.now().strftime('%H:%M')}] CSV vacío. Nada que enviar.")
        return

    bc = BinanceClient()
    symbols = df['Symbol'].unique().tolist()
    market_data = bc.get_market_prices(symbols)
    if not market_data:
        if context.job is None: await context.bot.send_message(chat_id=chat_id, text="❌ Error Binance.")
        return

    # Usamos las funciones importadas
    msg_tabla = format_main_table(df, market_data)
    msg_cercana = format_close_table(df, market_data) 

    try:
        for chunk in smart_split(msg_tabla):
            await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode='Markdown')
        
        for chunk in smart_split(msg_cercana):
            await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode='Markdown', disable_web_page_preview=True)
            
        print(f"✅ [{datetime.now().strftime('%H:%M')}] Mensajes enviados a {chat_id}.")
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

async def update_schedule(application, chat_id):
    job_queue = application.job_queue
    for job in job_queue.get_jobs_by_name('auto_scan'):
        job.schedule_removal()

    mode = config.BOT_STATE["mode"]
    interval = config.FREQ_LOW
    msg_status = ""

    if mode == "AUTO":
        interval, msg_status = calcular_intervalo_auto()
    elif mode == "DIA":
        interval = config.FREQ_HIGH
        msg_status = "Manual: Día ☀️ (10m)"
    elif mode == "NOCHE":
        interval = config.FREQ_LOW
        msg_status = "Manual: Noche 🌙 (60m)"

    job_queue.run_repeating(analizar_y_enviar, interval=interval, first=1, data=chat_id, name='auto_scan')
    return msg_status

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["👀 VER AHORA"],
        ["🔄 AUTO (UTC-3)"],
        ["☀️ MODO DÍA", "🌙 MODO NOCHE"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 **Bot Iniciado**\n\n🕒 **Horario Automático:**\n☀️ 05:00 - 18:00 (10 min)\n🌙 18:00 - 05:00 (60 min)", 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    config.BOT_STATE["mode"] = "AUTO"
    msg = await update_schedule(context.application, update.effective_chat.id)
    await update.message.reply_text(f"⚙️ Estado: {msg}")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if text == "👀 VER AHORA":
        await update.message.reply_text("🔎 Analizando...")
        context._chat_id = chat_id
        context.job = None 
        await analizar_y_enviar(context)
        
    elif text == "🔄 AUTO (UTC-3)":
        config.BOT_STATE["mode"] = "AUTO"
        msg = await update_schedule(context.application, chat_id)
        await update.message.reply_text(f"✅ Configurado: {msg}")
        
    elif text == "☀️ MODO DÍA":
        config.BOT_STATE["mode"] = "DIA"
        msg = await update_schedule(context.application, chat_id)
        await update.message.reply_text(f"✅ Configurado: {msg}")
        
    elif text == "🌙 MODO NOCHE":
        config.BOT_STATE["mode"] = "NOCHE"
        msg = await update_schedule(context.application, chat_id)
        await update.message.reply_text(f"✅ Configurado: {msg}")

async def post_init(application: Application):
    print("🚀 Auto-Arranque iniciado...")
    config.BOT_STATE["mode"] = "AUTO"
    interval, msg = calcular_intervalo_auto()
    
    application.job_queue.run_repeating(
        analizar_y_enviar, 
        interval=interval, 
        first=2,
        data=config.TELEGRAM_CHAT_ID, 
        name='auto_scan'
    )
    try:
        await application.bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID, 
            text=f"🤖 **Bot Reiniciado**\n⚙️ {msg}", 
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"⚠️ Error inicio: {e}")

if __name__ == "__main__":
    print("🤖 Bot Modular Ejecutándose...")
    t_request = HTTPXRequest(connection_pool_size=8, connect_timeout=60, read_timeout=60)
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).request(t_request).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    app.run_polling()   