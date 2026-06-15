#!/usr/bin/env python3
"""
Парсер полных составов клубов с Transfermarkt через браузер
Использует browser tool для обхода bot-detection
"""
import json
import time
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'bundesliga_today.db')

# Маппинг slug клубов на Transfermarkt
CLUBS_TM = {
    "[FCB] FC Bayern München | Бавария": "bayern-munich",
    "[BVB] Borussia Dortmund | Боруссия Д": "borussia-dortmund",
    "[RBL] RB Leipzig | РБ Лейпциг": "rb-leipzig",
    "[B04] Bayer 04 Leverkusen | Байер 04": "bayer-leverkusen",
    "[SGE] Eintracht Frankfurt | Айнтрахт": "eintracht-frankfurt",
    "[BMG] Borussia Mönchengladbach | Боруссия М": "borussia-monchengladbach",
    "[VFB] VfB Stuttgart | Штутгарт": "stuttgart",
    "[SCF] SC Freiburg | Фрайбург": "freiburg",
    "[SVW] SV Werder Bremen | Вердер": "werder-bremen",
    "[TSG] TSG 1899 Hoffenheim | Хоффенхайм": "1899-hoffenheim",
    "[FCU] 1. FC Union Berlin | Унион Берлин": "union-berlin",
    "[HSV] Hamburger SV | Гамбург": "hamburg",
    "[KOE] 1. FC Köln | Кёльн": "fc-koln",
    "[M05] 1. FSV Mainz 05 | Майнц 05": "mainz",
    "[FCA] FC Augsburg | Аугсбург": "augsburg",
    "[SCP] SC Paderborn 07 | Падерборн 07": "paderborn-07",
    "[S04] FC Schalke 04 | Шальке 04": "schalke-04",
    "[SVE] SV Elversberg | Эльверсберг": "elversberg",
}

POS_MAP_TM = {
    "TW": "GK", "Torwart": "GK", "Goalkeeper": "GK",
    "IV": "DF", "Innenverteidiger": "DF", "Centre-Back": "DF",
    "LV": "DF", "Linker Verteidiger": "DF", "Left-Back": "DF",
    "RV": "DF", "Rechter Verteidiger": "DF", "Right-Back": "DF",
    "RB": "DF", "Rechtsverteidiger": "DF",
    "LV": "DF", "Linksverteidiger": "DF",
    "ZM": "MF", "Zentrales Mittelfeld": "MF", "Central Midfield": "MF",
    "LM": "MF", "Links Mittelfeld": "MF", "Left Midfield": "MF",
    "RM": "MF", "Rechts Mittelfeld": "MF", "Right Midfield": "MF",
    "DM": "MF", "Defensives Mittelfeld": "MF", "Defensive Midfield": "MF",
    "AM": "MF", "Offensives Mittelfeld": "MF", "Attacking Midfield": "MF",
    "LW": "FW", "Linker Flügel": "FW", "Left Winger": "FW",
    "RW": "FW", "Rechter Flügel": "FW", "Right Winger": "FW",
    "ST": "FW", "Stürmer": "FW", "Centre-Forward": "FW",
    "CF": "FW", "Center Forward": "FW", "Striker": "FW",
}


def get_full_squads_from_tm():
    """
    Получает полные составы с Transfermarkt через браузер
    Возвращает dict {club_name: [players]}
    """
    # Используем browser tool для парсинга
    # Это 函数的 для вызова из основного скрипта
    from hermes_tools import browser_navigate, browser_console
    
    all_squads = {}
    
    for club_name, slug in CLUBS_TM.items():
        url = f"https://www.transfermarkt.com/{slug}/kader/verein/{list(CLUBS_TM.values()).index(slug)+1}/saison_id/2025"
        
        print(f"Парсинг {club_name}...")
        browser_navigate(url)
        time.sleep(3)
        
        # Извлекаем данные через JavaScript
        js = """
        (function() {
            const rows = document.querySelectorAll('.items tbody tr');
            const players = [];
            
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 4) {
                    const name = cells[1]?.innerText?.trim();
                    const pos = cells[3]?.innerText?.trim();
                    
                    // Номер из первой ячейки
                    const number = cells[0]?.innerText?.trim();
                    
                    if (name && pos) {
                        players.push({
                            name: name,
                            position: pos,
                            number: number
                        });
                    }
                }
            });
            
            return JSON.stringify(players);
        })();
        """
        
        result = browser_console(js)
        
        if result:
            try:
                players = json.loads(result)
                all_squads[club_name] = players
                print(f"  ✅ {len(players)} игроков")
            except:
                print(f"  ❌ Ошибка парсинга")
        
        time.sleep(2)  # Пауза между запросами
    
    return all_squads


def save_squads_to_db(squads: dict):
    """Сохраняет составы в БД"""
    db = sqlite3.connect(DB_PATH)
    
    for club_name, players in squads.items():
        # Удаляем старые данные
        db.execute("DELETE FROM players WHERE club_name = ?", (club_name,))
        
        for p in players:
            pos = p.get('position', '')
            pos_short = POS_MAP_TM.get(pos, pos[:2] if pos else None)
            
            db.execute("""
                INSERT INTO players (club_name, name, position, pos_name, number, nationality, age, is_foreigner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                club_name,
                p.get('name', ''),
                pos_short,
                pos,
                p.get('number'),
                p.get('nationality', ''),
                p.get('age'),
                0
            ))
    
    db.commit()
    db.close()
    print(f"✅ Сохранено {sum(len(p) for p in squads.values())} игроков")


if __name__ == "__main__":
    squads = get_full_squads_from_tm()
    save_squads_to_db(squads)
