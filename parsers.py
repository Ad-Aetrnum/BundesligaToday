"""
Bundesliga Today Bot — Parser module
Источник данных: OpenLigaDB API
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone

import aiohttp

logger = logging.getLogger(__name__)

BASE_URL = "https://www.openligadb.de/api"


def current_season() -> str:
    now = datetime.now(timezone.utc)
    if now.month >= 7:
        return str(now.year)
    return str(now.year - 1)


class BundesligaAPI:
    """Асинхронный клиент для OpenLigaDB с кешированием и retry."""

    def __init__(self, ttl: int = 120):
        self._ttl = ttl
        self._cache: dict[str, tuple[float, any]] = {}

    def _cache_get(self, key: str):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.monotonic() - ts < self._ttl:
                return val
            del self._cache[key]
        return None

    def _cache_set(self, key: str, val):
        self._cache[key] = (time.monotonic(), val)

    async def _fetch(self, session: aiohttp.ClientSession, path: str):
        key = hashlib.md5(path.encode()).hexdigest()
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        url = f"{BASE_URL}/{path}"
        for attempt in range(3):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        self._cache_set(key, data)
                        return data
                    logger.warning("OpenLigaDB %s → %d", url, resp.status)
            except Exception as e:
                if attempt == 2:
                    logger.error("OpenLigaDB fetch failed: %s", e)
                    return []
                await aiohttp.sleep(1 * (attempt + 1))
        return []

    async def get_table(self, session: aiohttp.ClientSession, season: str | None = None):
        s = season or current_season()
        return await self._fetch(session, f"getbltable/bl1/{s}")

    async def get_current_matchday(self, session: aiohttp.ClientSession, season: str | None = None) -> int:
        s = season or current_season()
        data = await self._fetch(session, f"getcurrentgroup/bl1/{s}")
        if isinstance(data, dict):
            return data.get("GroupOrderID", 0)
        return 0

    async def get_matchday(self, session: aiohttp.ClientSession, matchday: int, season: str | None = None):
        s = season or current_season()
        return await self._fetch(session, f"getmatchdata/bl1/{s}/{matchday}")


# ── Форматированные выводы ──

# ── Картинка таблицы ──
def _generate_table_image(season: str, standings: list[dict], out_path: str) -> str:
    """Генерирует PNG-картинку таблицы с фоновым изображением."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import os

    MODULE_DIR = os.path.dirname(__file__)

    table_data = []
    for row in standings:
        table_data.append((
            row["position"], row["team_name_de"],
            row["games_played"], row["wins"], row["draws"], row["losses"],
            row["goals_for"], row["goals_against"],
            row["goal_difference"], row["points"]
        ))

    zones = {}
    for row in standings:
        z = row.get("zone", "")
        if z:
            zones[row["position"]] = z

    zone_colors = {
        "ЛЧ": (80, 160, 255),
        "ЛЕ": (50, 200, 120),
        "ЛКК": (100, 220, 80),
        "Плей-офф": (240, 180, 40),
        "Вылет": (240, 70, 70),
    }

    # ── Размеры ──
    W, H = 1000, 1300

    # ── Фон: загружаем шаблон или создаём градиент ──
    bg_path = os.path.join(MODULE_DIR, "assets", "bg_template.jpg")
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
        # Размываем фон для лучшей читаемости
        bg = bg.filter(ImageFilter.GaussianBlur(radius=3))
        # Масштабируем до нужного размера
        bg = bg.resize((W, H), Image.Resampling.LANCZOS)
        img = bg.copy()

        # Затемняем фон для контраста (оверлей 50% чёрный)
        overlay = Image.new("RGB", (W, H), (0, 0, 0))
        img = Image.blend(img, overlay, alpha=0.45)
    else:
        img = Image.new("RGB", (W, H), (15, 20, 50))

    draw = ImageDraw.Draw(img)

    # ── Шрифты ──
    font_dir = "/usr/share/fonts/truetype/dejavu/"
    font_base = "/usr/share/fonts/truetype/liberation/"
    try:
        if os.path.exists(font_dir + "DejaVuSans-Bold.ttf"):
            font_title = ImageFont.truetype(font_dir + "DejaVuSans-Bold.ttf", 26)
            font_header = ImageFont.truetype(font_dir + "DejaVuSans-Bold.ttf", 14)
            font_regular = ImageFont.truetype(font_dir + "DejaVuSans.ttf", 13)
            font_bold = ImageFont.truetype(font_dir + "DejaVuSans-Bold.ttf", 13)
            font_small = ImageFont.truetype(font_dir + "DejaVuSans.ttf", 11)
        elif os.path.exists(font_base + "LiberationSans-Bold.ttf"):
            font_title = ImageFont.truetype(font_base + "LiberationSans-Bold.ttf", 26)
            font_header = ImageFont.truetype(font_base + "LiberationSans-Bold.ttf", 14)
            font_regular = ImageFont.truetype(font_base + "LiberationSans-Regular.ttf", 13)
            font_bold = ImageFont.truetype(font_base + "LiberationSans-Bold.ttf", 13)
            font_small = ImageFont.truetype(font_base + "LiberationSans-Regular.ttf", 11)
        else:
            font_title = font_header = font_regular = font_bold = font_small = ImageFont.load_default()
    except Exception:
        font_title = font_header = font_regular = font_bold = font_small = ImageFont.load_default()

    # ── Заголовок ──
    season_display = season.replace("-", "/")
    title1 = f"BUNDESLIGA {season_display}"
    title2 = "Итоги сезона"

    # Тень для заголовка
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            bbox = draw.textbbox((0, 0), title1, font=font_title)
            tw = bbox[2] - bbox[0]
            x = (W - tw) / 2 + dx
            y = 22 + dy
            draw.text((x, y), title1, fill=(0, 0, 0), font=font_title)

    bbox = draw.textbbox((0, 0), title1, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, 22), title1, fill=(255, 225, 100), font=font_title)

    bbox2 = draw.textbbox((0, 0), title2, font=font_header)
    sw = bbox2[2] - bbox2[0]
    draw.text(((W - sw) / 2, 58), title2, fill=(200, 210, 240), font=font_header)

    # ── Декоративная линия под заголовком ──
    line_y = 85
    draw.line([(W // 2 - 120, line_y), (W // 2 + 120, line_y)], fill=(180, 160, 140), width=1)

    # ── Формируем колонки таблицы ──
    cols = ["#", "Команда", "И", "В", "Н", "П", "МЗ-МЧ", "Р", "О"]
    col_widths = [34, 240, 28, 28, 28, 28, 70, 44, 40]
    table_x = 30
    table_y = 95
    row_h = 29
    header_h = 34
    total_w = sum(col_widths)

    # ── Логотипы клубов (если есть) ──
    logos = {}
    logos_dir = os.path.join(MODULE_DIR, "assets", "logos")
    if os.path.isdir(logos_dir):
        for pos, name, *_ in table_data:
            # Ищем файл логотипа: по позиции или по имени
            for ext in ["png", "jpg", "jpeg", "webp"]:
                logo_file = os.path.join(logos_dir, f"{pos:02d}.{ext}")
                if os.path.exists(logo_file):
                    try:
                        logo_img = Image.open(logo_file).convert("RGBA")
                        logo_img = logo_img.resize((20, 20), Image.Resampling.LANCZOS)
                        logos[pos] = logo_img
                    except Exception:
                        pass
                    break

    # ── Полупрозрачный фон таблицы ──
    table_bottom = table_y + header_h + row_h * len(table_data) + 10
    table_bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    table_draw = ImageDraw.Draw(table_bg)
    # Прямоугольник таблицы (скруглённые углы имитируем)
    margin = 15
    table_draw.rectangle(
        [table_x - margin, table_y - 6,
         table_x + total_w + margin, table_bottom],
        fill=(20, 25, 50, 180),  # полупрозрачный тёмный
        outline=(100, 120, 180, 200),
        width=1
    )

    # Композитим фон таблицы
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, table_bg)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Заголовок таблицы ──
    cx = table_x
    for col, cw in zip(cols, col_widths):
        bbox = draw.textbbox((0, 0), col, font=font_header)
        tw = bbox[2] - bbox[0]
        draw.text((cx + (cw - tw) / 2, table_y + 10), col, fill=(140, 180, 255), font=font_header)
        cx += cw

    # Линия под заголовком
    draw.line(
        [(table_x - margin + 2, table_y + header_h - 2),
         (table_x + total_w + margin - 2, table_y + header_h - 2)],
        fill=(80, 100, 160), width=1
    )

    # ── Строки таблицы ──
    for row_idx, (pos, name, gp, w, d, l, gf, ga, gd, pts) in enumerate(table_data):
        ry = table_y + header_h + row_idx * row_h

        # Фон строки (чередование)
        if row_idx % 2 == 0:
            row_bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            rd = ImageDraw.Draw(row_bg)
            rd.rectangle(
                [table_x - margin + 1, ry,
                 table_x + total_w + margin - 1, ry + row_h],
                fill=(255, 255, 255, 15)
            )
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, row_bg)
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)

        # Цветовой индикатор зоны (слева)
        zone_name = zones.get(pos, "")
        zc = zone_colors.get(zone_name)
        if zc:
            ind = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            idraw = ImageDraw.Draw(ind)
            idraw.rectangle(
                [table_x - margin + 1, ry + 1, table_x - margin + 6, ry + row_h - 1],
                fill=(*zc, 220)
            )
            idraw.rectangle(
                [table_x - margin + 6, ry + 1,
                 table_x + total_w + margin - 1, ry + row_h - 1],
                fill=(*zc, 20)
            )
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, ind)
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)

        # Цвет позиции
        if pos <= 4:
            pos_color = (120, 200, 255)
        elif pos <= 7:
            pos_color = (100, 255, 160)
        elif pos >= 17:
            pos_color = (255, 100, 100)
        elif pos == 16:
            pos_color = (255, 190, 60)
        else:
            pos_color = (240, 240, 240)

        cx = table_x

        # Логотип клуба
        logo = logos.get(pos)
        logo_x = cx + 2
        logo_y = ry + 4
        if logo:
            img.paste(logo, (logo_x, logo_y), logo)
            cx += 26
        else:
            cx += 4

        # Позиция
        pos_str = f"{pos}."
        bbox = draw.textbbox((0, 0), pos_str, font=font_bold)
        tw = bbox[2] - bbox[0]
        pcx = cx + 6 if not logo else cx
        draw.text((pcx, ry + 8), pos_str, fill=pos_color, font=font_bold)
        name_x = pcx + tw + 8
        cx = table_x + col_widths[0]

        # Название команды
        # Обрезаем если длинное
        name_display = name
        while draw.textbbox((0, 0), name_display, font=font_regular)[2] > col_widths[1] - 10 and len(name_display) > 5:
            name_display = name_display[:-4] + "..."
        draw.text((cx + 4, ry + 8), name_display, fill=(245, 245, 245), font=font_regular)
        cx += col_widths[1]

        # Числовые колонки
        values = [gp, w, d, l, f"{gf}-{ga}", f"{gd:+d}", pts]
        for vi, (val, cw) in enumerate(zip(values, col_widths[2:])):
            val_str = str(val)
            if vi == 5:  # GD
                color = (100, 255, 120) if gd > 0 else (255, 100, 100) if gd < 0 else (200, 200, 200)
            elif vi == 6:  # Pts
                color = pos_color
            else:
                color = (225, 225, 225)
            bbox = draw.textbbox((0, 0), val_str, font=font_regular)
            tw = bbox[2] - bbox[0]
            draw.text((cx + (cw - tw) / 2, ry + 8), val_str, fill=color, font=font_regular)
            cx += cw

        # Зона (справа от таблицы)
        if zone_name and zc:
            zx = table_x + total_w + margin + 10
            z_font = font_small
            bbox = draw.textbbox((0, 0), zone_name, font=z_font)
            zw = bbox[2] - bbox[0]
            zh = bbox[3] - bbox[1]
            # Фон зоны
            draw.rectangle(
                [zx - 2, ry + (row_h - zh) // 2 - 2,
                 zx + zw + 2, ry + (row_h - zh) // 2 + zh + 2],
                fill=(*zc[:3],)
            )
            draw.text((zx, ry + (row_h - zh) // 2 - 1), zone_name, fill=(0, 0, 0), font=z_font)

    # ── Легенда ──
    ly = table_bottom + 15
    legend_items = [
        ("■", (80, 160, 255), "Лига Чемпионов"),
        ("■", (50, 200, 120), "Лига Европы"),
        ("■", (100, 220, 80), "Конференц-Лига"),
        ("■", (240, 180, 40), "Плей-офф"),
        ("■", (240, 70, 70), "Вылет"),
    ]
    lx = table_x + 5
    for sym, color, desc in legend_items:
        draw.rectangle([lx, ly, lx + 10, ly + 10], fill=color)
        draw.text((lx + 14, ly - 1), desc, fill=(200, 200, 200), font=font_small)
        bbox = draw.textbbox((0, 0), desc, font=font_small)
        lx += bbox[2] - bbox[0] + 24

    # ── Футер ──
    footer = "@BLTD_bot  •  Bundesliga Today"
    bbox = draw.textbbox((0, 0), footer, font=font_small)
    fw = bbox[2] - bbox[0]
    draw.text(((W - fw) / 2, H - 30), footer, fill=(120, 130, 160), font=font_small)

    # Сохраняем
    img.save(out_path, "PNG")
    return out_path


async def get_table_formatted(season: str | None = None) -> str:
    """Возвращает путь к PNG-картинке таблицы (без сезона — картинка, с сезоном — текст)."""
    from database import get_season_standings
    import os

    s = season or "2025-26"
    standings = get_season_standings(s)

    if not standings:
        standings = _fetch_espn_standings(s)
        if not standings:
            return "⚠️ Данные таблицы сезона ещё не записаны."

    # Если сезон ещё не начался — отправляем картинку
    out_path = os.path.join(os.path.dirname(__file__), f"table_{s}.png")
    _generate_table_image(s, standings, out_path)
    return out_path


def _fetch_espn_standings(season: str) -> list[dict] | None:
    """Fallback: загружает таблицу из ESPN API и сохраняет в БД."""
    import requests
    from database import get_db

    try:
        url = 'https://site.api.espn.com/apis/v2/sports/soccer/ger.1/standings'
        r = requests.get(url, timeout=15)
        d = r.json()
        entries = d['children'][0]['standings']['entries']
    except Exception:
        return None

    name_map = {
        'Bayern Munich': 'FC Bayern München',
        'Borussia Dortmund': 'Borussia Dortmund',
        'RB Leipzig': 'RB Leipzig',
        'VfB Stuttgart': 'VfB Stuttgart',
        'TSG Hoffenheim': 'TSG 1899 Hoffenheim',
        'Bayer Leverkusen': 'Bayer 04 Leverkusen',
        'SC Freiburg': 'SC Freiburg',
        'Eintracht Frankfurt': 'Eintracht Frankfurt',
        'FC Augsburg': 'FC Augsburg',
        'Mainz': '1. FSV Mainz 05',
        '1. FC Union Berlin': '1. FC Union Berlin',
        'Borussia Mönchengladbach': 'Borussia Mönchengladbach',
        'Hamburger SV': 'Hamburger SV',
        'Hamburg SV': 'Hamburger SV',
        'FC Cologne': '1. FC Köln',
        'Werder Bremen': 'SV Werder Bremen',
        'VfL Wolfsburg': 'VfL Wolfsburg',
        '1. FC Heidenheim 1846': '1. FC Heidenheim 1846',
        'St. Pauli': 'FC St. Pauli',
    }

    result = []
    db = get_db()
    db.execute("DELETE FROM season_standings WHERE season = ?", (season,))

    for e in entries:
        stats = {s['abbreviation']: s.get('value') for s in e['stats']}
        note = e.get('note', {})
        zone_raw = note.get('description', '')

        pos = int(stats.get('R', 0) or 0)
        name_en = e['team']['displayName']
        name_de = name_map.get(name_en, name_en)
        gp = int(stats.get('GP', 0) or 0)
        w = int(stats.get('W', 0) or 0)
        dr = int(stats.get('D', 0) or 0)
        l = int(stats.get('L', 0) or 0)
        gf = int(stats.get('F', 0) or 0)
        ga = int(stats.get('A', 0) or 0)
        gd = int(stats.get('GD', 0) or 0)
        pts = int(stats.get('P', 0) or 0)

        if 'Champions League' in zone_raw:
            zone = 'ЛЧ'
        elif 'Europa League' in zone_raw:
            zone = 'ЛЕ'
        elif 'Conference' in zone_raw:
            zone = 'ЛКК'
        elif 'Relegation playoff' in zone_raw:
            zone = 'Плей-офф'
        elif 'Relegation' in zone_raw:
            zone = 'Вылет'
        else:
            zone = ''

        db.execute("""INSERT INTO season_standings 
            (season, position, team_name, team_name_de, games_played, wins, draws, losses,
             goals_for, goals_against, goal_difference, points, zone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (season, pos, name_en, name_de, gp, w, dr, l, gf, ga, gd, pts, zone))

        result.append({
            'position': pos, 'team_name_de': name_de, 'games_played': gp,
            'wins': w, 'draws': dr, 'losses': l, 'goals_for': gf,
            'goals_against': ga, 'goal_difference': gd, 'points': pts, 'zone': zone,
        })

    db.commit()
    db.close()
    return result


async def get_matchday_formatted(matchday: int | None = None, season: str | None = None) -> str:
    api = BundesligaAPI()
    async with aiohttp.ClientSession() as session:
        if matchday is None:
            md = await api.get_current_matchday(session, season)
            matchday = md if md > 0 else 1

        matches = await api.get_matchday(session, matchday, season)

    if not matches:
        return f"⚠️ Матчи тура {matchday} не найдены или сезон ещё не начался."

    lines = [f"⚽ *{matchday}-й тур Бундеслиги*\n"]

    for m in matches:
        home = m.get("Team1", {}).get("TeamName", "—")
        away = m.get("Team2", {}).get("TeamName", "—")

        goals = m.get("Goals", [])
        home_goals = sum(1 for g in goals if g.get("ScoreTeam1", 0) > 0) if goals else 0
        away_goals = sum(1 for g in goals if g.get("ScoreTeam2", 0) > 0) if goals else 0
        score_str = f"{home_goals}:{away_goals}" if goals else "—:—"

        finished = m.get("MatchIsFinished", False)
        dt_str = m.get("MatchDateTime", "")
        kickoff = ""
        if dt_str:
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                offset = datetime.now().astimezone().utcoffset()
                dt_local = dt.astimezone(timezone(offset))
                kickoff = dt_local.strftime("%d.%m %H:%M")
            except Exception:
                kickoff = dt_str[:16].replace("T", " ")

        flag = "✅" if finished else ("🕐" if kickoff else "⏳")
        lines.append(f"{flag} *{home}* {score_str} *{away}*  `{kickoff}`")

    return "\n".join(lines)
