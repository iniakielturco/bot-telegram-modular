# runbot.py
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, Application
from telegram.request import HTTPXRequest

import config
from utils import smart_split
from data_manager import DataManager, BinanceClient
from tables import format_main_table
from alerts import format_close_table
from scheduler import calcular_intervalo_auto

# Importamos la nueva función check_fire_zone
from commands import start, help_command, price_check, check_fire_zone

async def analizar_y_enviar(context: ContextTypes.DEFAULT_TYPE):
    # ... (Esta función queda igual que antes) ...
    if context.job:
        chat_id = context.job.data 
    else:
        chat_id = context._chat_id 

    if context.job and config.BOT_STATE.get("active", True):
        intervalo_correcto, _ = calcular_intervalo_auto()
        current_interval = context.job.trigger.interval
        if hasattr(current_interval, 'total_seconds'):
            current_interval = current_interval.total_seconds()
        
        if abs(current_interval - intervalo_correcto) > 1:
            print(f"🔄 Cambio de horario detectado. Ajustando frecuencia...")
            await update_schedule(context.application, chat_id)

    dm = DataManager()
    df = dm.get_pending_operations()
    if df.empty:
        if context.job is None: 
            await context.bot.send_message(chat_id=chat_id, text="⚠️ CSV Vacío.")
        else:
            print(f"ℹ️ [{datetime.now().strftime('%H:%M')}] CSV vacío.")
        return

    bc = BinanceClient()
    symbols = df['Symbol'].unique().tolist()
    market_data = bc.get_market_prices(symbols)
    if not market_data:
        if context.job is None: await context.bot.send_message(chat_id=chat_id, text="❌ Error Binance.")
        return

    msg_tabla = format_main_table(df, market_data)
    msg_cercana = format_close_table(df, market_data) 

    try:
        for chunk in smart_split(msg_tabla):
            await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode='Markdown')
        for chunk in smart_split(msg_cercana):
            await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode='Markdown', disable_web_page_preview=True)
        print(f"✅ [{datetime.now().strftime('%H:%M')}] Mensajes enviados.")
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

async def update_schedule(application, chat_id):
    # ... (Esta función queda igual) ...
    job_queue = application.job_queue
    for job in job_queue.get_jobs_by_name('auto_scan'):
        job.schedule_removal()

    if not config.BOT_STATE.get("active", True):
        return "Bot Pausado ⏸️"

    interval, msg_status = calcular_intervalo_auto()

    job_queue.run_repeating(
        analizar_y_enviar, 
        interval=interval, 
        first=1, 
        data=chat_id, 
        name='auto_scan'
    )
    return msg_status

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    
    if text == "🟢 ACTIVAR BOT":
        config.BOT_STATE["active"] = True
        msg = await update_schedule(context.application, chat_id)
        await start(update, context) 
        await update.message.reply_text(f"🚀 {msg}")

    elif text == "🔴 PAUSAR BOT":
        config.BOT_STATE["active"] = False
        await update_schedule(context.application, chat_id)
        await start(update, context)
        await update.message.reply_text("⏸️ Escaneo automático detenido.")

    elif text == "👀 VER AHORA":
        await update.message.reply_text("🔎 Escaneando...")
        context._chat_id = chat_id
        context.job = None 
        await analizar_y_enviar(context)

    # --- CAMBIO AQUÍ: Botón nuevo ---
    elif text == "🔥 ZONA DE DISPARO":
        await check_fire_zone(update, context)

    elif text == "❓ AYUDA":
        await help_command(update, context)

async def post_init(application: Application):
    print("🚀 Auto-Arranque iniciado...")
    config.BOT_STATE["active"] = True
    
    msg = await update_schedule(application, config.TELEGRAM_CHAT_ID)
    
    try:
        await application.bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID, 
            text=f"🤖 **Bot Reiniciado**\n⚙️ Estado: {msg}\nEscribe /start para ver menú.", 
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"⚠️ Error inicio: {e}")

if __name__ == "__main__":
    print("🤖 Bot Modular Ejecutándose...")
    t_request = HTTPXRequest(connection_pool_size=8, connect_timeout=60, read_timeout=60)
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).request(t_request).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start)) 
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("precio", price_check))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    app.run_polling()