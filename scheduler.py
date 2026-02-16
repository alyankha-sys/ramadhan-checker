from datetime import datetime, timedelta
from config import TIMEZONE, GROUP_ID
from database import get_ranking_harian, get_usernames_today, get_all_usernames
from excel_export import generate_excel

async def ranking_job(app):
    yesterday = (datetime.now(TIMEZONE) - timedelta(days=1)).strftime("%Y-%m-%d")
    results = get_ranking_harian(yesterday)

    if not results:
        return

    medals = ["🥇", "🥈", "🥉"]
    text = f"🏆 Ranking Ibadah – {yesterday}\n\n"

    for i, row in enumerate(results):
        text += f"{medals[i]} @{row[0]} — {row[1]} poin\n"

    await app.bot.send_message(chat_id=GROUP_ID, text=text)

async def reminder_job(app):
    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")

    sudah = get_usernames_today(today)
    semua = get_all_usernames()

    belum = [u for u in semua if u not in sudah]

    if belum:
        text = "⚠ Reminder Laporan Ramadhan\n\n"
        for u in belum:
            text += f"@{u} "

        await app.bot.send_message(chat_id=GROUP_ID, text=text)

async def export_job(app):
    day = datetime.now(TIMEZONE).day

    if day not in [10, 20, 30]:
        return

    filename = f"rekap_{day}.xlsx"
    generate_excel(filename)

    await app.bot.send_document(chat_id=GROUP_ID, document=open(filename, "rb"))
