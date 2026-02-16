from database import get_total_laporan, simpan_badge

async def cek_badge(username, bot, group_id):
    total = get_total_laporan(username)

    if total == 7:
        simpan_badge(username, "Istiqomah 7 Hari")
        await bot.send_message(
            chat_id=group_id,
            text=f"🎖 @{username} mendapatkan Badge Istiqomah 7 Hari!"
        )
