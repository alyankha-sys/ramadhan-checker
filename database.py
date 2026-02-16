import sqlite3
from config import TIMEZONE
from datetime import datetime

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        username TEXT,
        tanggal TEXT,
        subuh INTEGER,
        dzuhur INTEGER,
        ashar INTEGER,
        maghrib INTEGER,
        isya INTEGER,
        tadarus INTEGER,
        sedekah INTEGER,
        qiyamul INTEGER,
        puasa INTEGER,
        total_poin INTEGER,
        waktu_kirim TEXT,
        PRIMARY KEY (username, tanggal)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        username TEXT,
        badge_name TEXT,
        tanggal TEXT
    )
    """)

    conn.commit()

def simpan_laporan(username, data, total_poin):
    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    now_time = datetime.now(TIMEZONE).strftime("%H:%M:%S")

    cursor.execute("""
    INSERT OR REPLACE INTO reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        username, today,
        data["subuh"], data["dzuhur"], data["ashar"],
        data["maghrib"], data["isya"], data["tadarus"],
        data["sedekah"], data["qiyamul"], data["puasa"],
        total_poin, now_time
    ))

    conn.commit()

def get_ranking_harian(tanggal):
    cursor.execute("""
    SELECT username, total_poin FROM reports
    WHERE tanggal=?
    ORDER BY total_poin DESC, waktu_kirim ASC
    LIMIT 3
    """, (tanggal,))
    return cursor.fetchall()

def get_usernames_today(tanggal):
    cursor.execute("SELECT username FROM reports WHERE tanggal=?", (tanggal,))
    return [row[0] for row in cursor.fetchall()]

def get_all_usernames():
    cursor.execute("SELECT DISTINCT username FROM reports")
    return [row[0] for row in cursor.fetchall()]

def get_total_laporan(username):
    cursor.execute("SELECT COUNT(*) FROM reports WHERE username=?", (username,))
    return cursor.fetchone()[0]

def get_total_rekap():
    cursor.execute("""
    SELECT username, SUM(total_poin)
    FROM reports
    GROUP BY username
    ORDER BY SUM(total_poin) DESC
    """)
    return cursor.fetchall()

def simpan_badge(username, badge):
    cursor.execute("INSERT INTO badges VALUES (?,?,?)",
                   (username, badge, datetime.now(TIMEZONE)))
    conn.commit()
