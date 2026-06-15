"""
Тестовый скрипт: генерация картинки таблицы из БД.
"""
import sys
sys.path.insert(0, "/home/hermes/.hermes/BundesligaToday")

from renderer.engine import render
from database import get_season_standings

standings = get_season_standings("2025-26")

teams = []
for row in standings:
    pos = row["position"]
    zone = row.get("zone", "")
    if zone == "ЛЧ":
        zone_code = "CL"
    elif zone == "ЛЕ":
        zone_code = "EL"
    elif zone == "ЛКК":
        zone_code = "ECL"
    elif zone == "Плей-офф":
        zone_code = "PO"
    elif zone == "Вылет":
        zone_code = "R"
    else:
        zone_code = ""

    teams.append({
        "pos": pos,
        "name": row["team_name_de"],
        "games": row["games_played"],
        "w": row["wins"],
        "d": row["draws"],
        "l": row["losses"],
        "gf": row["goals_for"],
        "ga": row["goals_against"],
        "gd": row["goal_difference"],
        "pts": row["points"],
        "zone": zone_code,
    })

data = {
    "league": "Bundesliga",
    "season": "2025/26",
    "title": "Турнирная таблица",
    "teams": teams,
}

output = render("standings", data, "test_standings")
print(f"Generated: {output}")
