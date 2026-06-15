#!/usr/bin/env python3
"""
Исправление позиций игроков в БД
"""
import sqlite3

db = sqlite3.connect('/home/hermes/.hermes/BundesligaToday/bundesliga_today.db')
db.execute("PRAGMA journal_mode=WAL")

# Маппинг: полное название → короткое (GK/DF/MF/FW)
pos_map = {
    'Goalkeeper': 'GK',
    'Centre-Back': 'DF',
    'Right-Back': 'DF',
    'Left-Back': 'DF',
    'Defence': 'DF',
    'Full-Back': 'DF',
    'Wing-Back': 'DF',
    'Central Midfield': 'MF',
    'Defensive Midfield': 'MF',
    'Attacking Midfield': 'MF',
    'Right Midfield': 'MF',
    'Left Midfield': 'MF',
    'Midfield': 'MF',
    'Centre-Forward': 'FW',
    'Offence': 'FW',
    'Left Winger': 'FW',
    'Right Winger': 'FW',
    'Forward': 'FW',
    'Striker': 'FW',
    'Second Striker': 'FW',
    'Winger': 'FW',
}

# Удаляем дубликаты — игроки которые есть и в старых данных и в новых
# Сначала посмотрим что есть
print("=== До обновления ===")
rows = db.execute('SELECT pos_name, COUNT(DISTINCT name) FROM players GROUP BY pos_name ORDER BY COUNT(*) DESC').fetchall()
for r in rows:
    print(f"  {r[0]:25}: {r[1]}")

# Обновляем позиции
for full_name, short_name in pos_map.items():
    updated = db.execute(
        "UPDATE players SET position = ? WHERE pos_name = ?",
        (short_name, full_name)
    ).rowcount
    if updated > 0:
        print(f"  '{full_name}' → '{short_name}': {updated}")

db.commit()

# Удаляем игроков с некорректными позициями (без номера позиции)
db.execute("DELETE FROM players WHERE position IS NULL OR position = ''")
db.commit()

# Проверяем
print("\n=== После обновления ===")
rows = db.execute('SELECT position, COUNT(*) FROM players GROUP BY position ORDER BY position').fetchall()
for r in rows:
    print(f"  {r[0]:3}: {r[1]}")

# Бавария
print("\n=== Состав Баварии ===")
rows = db.execute('''
    SELECT name, position, pos_name, age, nationality 
    FROM players 
    WHERE club_name LIKE "%Бавария" 
    ORDER BY position, name
''').fetchall()
for r in rows:
    print(f"  {r[1]:3} {r[0]:25} {r[3] or '—':3} {r[4] or '—'}")

db.close()
print("\n✅ Позиции исправлены!")
