#!/usr/bin/env python3
"""
Парсер составов клубов Bundesliga через football-data.org API
Запускать: раз в час (rate limit: 10 req/min)
"""
import urllib.request
import json
import time
from datetime import datetime
import sqlite3
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_KEY = 'a34c7156031746769ca24c0623e8cf7c'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'X-Auth-Token': API_KEY}

# Все 18 клубов
TEAMS = [
    (1, "1. FC Köln"),
    (2, "TSG 1899 Hoffenheim"),
    (3, "Bayer 04 Leverkusen"),
    (4, "Borussia Dortmund"),
    (5, "FC Bayern München"),
    (6, "VfB Stuttgart"),
    (7, "Eintracht Frankfurt"),
    (8, "SC Freiburg"),
    (9, "SV Werder Bremen"),
    (10, "FC Augsburg"),
    (11, "1. FC Union Berlin"),
    (12, "Hamburger SV"),
    (13, "1. FSV Mainz 05"),
    (14, "FC Schalke 04"),
    (15, "SC Paderborn 07"),
    (16, "SV Elversberg"),
    (17, "Borussia Mönchengladbach"),
    (18, "RB Leipzig"),
]

POS_MAP = {
    'Goalkeeper': 'GK',
    'Defence': 'DF',
    'Midfield': 'MF',
    'Attacker': 'FW',
}

DB_PATH = os.path.join(os.path.dirname(__file__), 'bundesliga_today.db')


def parse_all_squads():
    """Парсит составы всех клубов."""
    db = sqlite3.connect(DB_PATH)
    
    # Очищаем старые данные
    db.execute("DELETE FROM players")
    
    total = 0
    success = 0
    
    for team_id, team_name in TEAMS:
        logger.info(f"Парсинг {team_name}...")
        try:
            url = f"https://api.football-data.org/v4/teams/{team_id}"
            req = urllib.request.Request(url, headers=HEADERS)
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                remaining_reqs = int(resp.headers.get('X-Requests-Available-Minute', 0))
            
            squad = data.get('squad', [])
            
            for p in squad:
                name = p.get('name', '')
                position = p.get('position', '')
                dob = p.get('dateOfBirth', '')
                
                # Маппинг позиции
                pos_short = POS_MAP.get(position, position[:2] if position else None)
                
                # Вычисляем возраст
                age = None
                if dob:
                    try:
                        age = datetime.now().year - int(dob[:4])
                    except:
                        pass
                
                # Национальность
                nat = p.get('nationality', '')
                
                db.execute("""
                    INSERT INTO players (club_name, name, position, pos_name, number, nationality, age, is_foreigner)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (team_name, name, pos_short, position, None, nat, age, 0))
                
                total += 1
            
            db.commit()
            success += 1
            logger.info(f"  ✅ {len(squad)} игроков (запросов: {remaining_reqs})")
            
            # Адаптивная задержка
            if remaining_reqs <= 1:
                logger.info(f"  ⏳ Мало запросов, ждём 65 сек...")
                time.sleep(65)
            else:
                time.sleep(7)
            
        except Exception as e:
            logger.error(f"  ❌ {e}")
            if '403' in str(e):
                # Ждём до следующего часа
                now = datetime.now()
                wait = (60 - now.minute) * 60 - now.second + 10
                logger.info(f"  ⏳ Rate limit, ждём {wait} сек до начала часа...")
                time.sleep(wait)
    
    # Статистика
    stats = db.execute("""
        SELECT club_name, COUNT(*) as cnt, 
               SUM(CASE WHEN position='GK' THEN 1 ELSE 0 END) as gk,
               SUM(CASE WHEN position='DF' THEN 1 ELSE 0 END) as df,
               SUM(CASE WHEN position='MF' THEN 1 ELSE 0 END) as mf,
               SUM(CASE WHEN position='FW' THEN 1 ELSE 0 END) as fw
        FROM players GROUP BY club_name ORDER BY club_name
    """).fetchall()
    
    logger.info(f"\n=== ИТОГО: {total} игроков из {success} клубов ===")
    for row in stats:
        logger.info(f"  {row[0]}: {row[1]} (GK:{row[2]} DF:{row[3]} MF:{row[4]} FW:{row[5]})")
    
    db.close()
    return total


if __name__ == '__main__':
    total = parse_all_squads()
    sys.exit(0 if total > 0 else 1)
