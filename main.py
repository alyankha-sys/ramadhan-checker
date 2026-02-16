import logging
import os
import asyncio
from threading import Thread

from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN, HASHTAG, GROUP_ID
from database import init_db, simpan_laporan
from badge import cek_badge
from scheduler import ranking_job, reminder_job, export_job

logging.basicConfig(level=logging.INFO)

# =========================
# Flask & Telegram Setup
# =========================
app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TOKEN).build()

# =========================
# POINT SYSTEM
# =========================
def hitung_poin(data):
    return (
        data.get("subuh",0) * 5 +
        data.get("dzuhur",0) * 5 +
        data.get("ashar",0) * 5 +
        data.get("maghrib",0) * 5 +
        data.get("isya",0) * 5 +
        data.get("tadarus",0) * 3 +
        data.get("sedekah",0) * 4 +
        data.get("qiyamul",0) * 6 +
        data.get("puasa",0) * 10
    )

def parse_laporan(text):
    lines = text.split("\n")
    data = {
        "subuh":0,"dzuhur":0,"ashar":0,"maghrib":0,"isya":0,
        "tadarus":0,"sedekah":0,"qiyamul":0,"puasa":0
    }
    for line in lines:
        if "=" in line:
            key, value = line.split("=")
            key = key.strip().lower()
            if key in data:
                try:
                    data[key] = int(value.strip())
                except ValueError:
                    data[key] = 0
    return data

# =========================
# MESSAGE HANDLER
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        user_id = update.message.from_user.id
        username = update.message.from_user.username or str(user_id)  # fallback pakai user_id

        logging.info(f"Pesan diterima dari {username}: {text}")

        if HASHTAG in text.lower():
            data = parse_laporan(text)
            total = hitung_poin(data)
            simpan_laporan(username, data, total)

            reply_text = f"Laporan diterima ✅ Total poin: {total}"
            await update.message.reply_text(reply_text)

            await cek_badge(username, context.bot, GROUP_ID)
    except Exception as e:
        logging.exception("Error handle_message")

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

# =========================
# FLASK WEBHOOK (synchronous)
# =========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, telegram_app.bot)
        # jalankan async bot di event loop
        asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            asyncio.get_event_loop()
        )
        return "ok"
    except Exception as e:
        logging.exception("Webhook gagal")
        return "ok"

@app.route("/")
def home():
    return "Bot is running"

# =========================
# MAIN FUNCTION
# =========================
async def main():
    init_db()

    # Scheduler
    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")
    scheduler.add_job(ranking_job, "cron", hour=4, minute=0, args=[telegram_app])
    scheduler.add_job(reminder_job, "cron", hour=18, minute=0, args=[telegram_app])
    scheduler.add_job(export_job, "cron", hour=4, minute=5, args=[telegram_app])
    scheduler.start()

    # Start Telegram bot
    await telegram_app.initialize()
    await telegram_app.start()

    # Jalankan Flask di thread terpisah
    def run_flask():
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port)
    Thread(target=run_flask).start()

    # Biar loop tetap jalan
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down bot & scheduler...")
        await telegram_app.stop()
        scheduler.shutdown()

if __name__ == "__main__":
    # Pastikan ada event loop untuk asyncio.run_coroutine_threadsafe
    loop = asyncio.get_event_loop()
    asyncio.run(main())
