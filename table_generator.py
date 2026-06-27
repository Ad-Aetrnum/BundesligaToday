"""
Bundesliga Today — Tour image generator.
Generates a single tour image that gets overwritten on each update.
Uses Bundesliga_tour.py (Pillow-based renderer) for full newspaper layout.
Fetches real data from football-data.org API.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from database import get_season_standings
from Bundesliga_tour import render_full

MODULE_DIR = Path(__file__).parent
OUTPUT_PATH = MODULE_DIR / "output" / "bl_today.png"

load_dotenv(MODULE_DIR / ".env")
API_TOKEN = os.getenv("FOOTBALL_DATA_API_KEY", "")
API_BASE = "https://api.football-data.org/v4"


async def _fetch_api(session, path: str) -> dict | None:
    headers = {"X-Auth-Token": API_TOKEN}
    async with session.get(f"{API_BASE}{path}", headers=headers) as r:
        if r.status == 200:
            return await r.json()
        return None


async def _fetch_matchday_results(season: str = "2025") -> list[dict]:
    """Fetch last completed matchday results."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        data = await _fetch_api(session, f"/competitions/BL1/matches?season={season}&status=FINISHED")
        if not data:
            return []

        matches = data.get("matches", [])
        if not matches:
            return []

        # Group by matchday, find last completed
        by_md = {}
        for m in matches:
            md = m.get("matchday", 0)
            by_md.setdefault(md, []).append(m)

        if not by_md:
            return []

        last_md = max(by_md.keys())
        results = []
        for m in by_md[last_md]:
            results.append({
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "score_h": m["score"]["fullTime"]["home"],
                "score_a": m["score"]["fullTime"]["away"],
            })
        return results


async def _fetch_top_scorers(season: str = "2025", limit: int = 10) -> list[dict]:
    """Fetch top scorers."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        data = await _fetch_api(session, f"/competitions/BL1/scorers?season={season}&limit={limit}")
        if not data:
            return []

        scorers = []
        for s in data.get("scorers", []):
            scorers.append({
                "name": s["player"]["name"],
                "club": s["team"]["shortName"] or s["team"]["name"],
                "goals": s.get("goals", 0),
                "assists": s.get("assists", 0),
            })
        return scorers


async def generate_tour_image(season: str = "2025-26") -> str:
    """Генерирует финальное изображение тура и возвращает путь.

    Returns:
        Path to the generated PNG file.
    """
    standings = get_season_standings(season)
    if not standings:
        raise ValueError(f"No standings data for season {season}")

    table = []
    for row in standings:
        zone = row.get("zone", "")
        zone_class = {
            "ЛЧ": "zone-cl",
            "ЛЕ": "zone-el",
            "ЛКК": "zone-7",
            "Плей-офф": "zone-neutral",
            "Вылет": "zone-relegation",
        }.get(zone, "zone-neutral")
        table.append({
            "position": row["position"],
            "club_name": row["team_name_de"],
            "mp": row["games_played"],
            "w": row["wins"],
            "d": row["draws"],
            "l": row["losses"],
            "gf": row["goals_for"],
            "ga": row["goals_against"],
            "pts": row["points"],
            "zone": zone_class,
        })

    # Fetch real data from API
    api_season = season.split("-")[0]  # "2025-26" -> "2025"
    matchday_results = await _fetch_matchday_results(api_season)
    top_scorers = await _fetch_top_scorers(api_season)

    matchday = table[0]["mp"] if table else "?"

    data = {
        "season": season.replace("-", "/"),
        "matchday": matchday,
        "table": table,
        "matchday_results": matchday_results,
        "top_scorers": top_scorers,
    }

    result = render_full(data, "bl_today")
    return result


if __name__ == "__main__":
    out = generate_tour_image()
    print(f"Generated: {out}")
