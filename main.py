import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN, HASHTAG, GROUP_ID
from database import init_db, simpan_laporan
from badge import cek_badge
from scheduler import ranking_job, reminder_job, export_job

# =========================
# POINT SYSTEM
# =========================

def hitung_poin(data):
    return (
        data["subuh"] * 5 +
        data["dzuhur"] * 5 +
        data["ashar"] * 5 +
        data["maghrib"] * 5 +
        data["isya"] * 5 +
        data["tadarus"] * 3 +
        data["sedekah"] * 4 +
        data["qiyamul"] * 6 +
        data["puasa"] * 10
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
                data[key] = int(value.strip())
    return data

# =========================
# HANDLE MESSAGE
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    username = update.message.from_user.username

    if not username:
        return

    if HASHTAG in text:
        data = parse_laporan(text)
        total = hitung_poin(data)

        simpan_laporan(username, data, total)

        await update.message.reply_text(f"Laporan diterima ✅ Total poin: {total}")

        await cek_badge(username, context.bot, GROUP_ID)

# =========================
# MAIN
# =========================

def main():
    logging.basicConfig(level=logging.INFO)

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

    scheduler.add_job(ranking_job, "cron", hour=4, minute=0, args=[app])
    scheduler.add_job(reminder_job, "cron", hour=18, minute=0, args=[app])
    scheduler.add_job(export_job, "cron", hour=4, minute=5, args=[app])

    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()
