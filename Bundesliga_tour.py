"""
Render Bundesliga Today newspaper layout onto magazine background.
Layout based on executive summary coordinates (2000x2500 reference).

Areas:
  - Header (date/season):     (237, 354)  1445x60
  - Standings table:          (237, 409)  1032x1675
  - Matchday results:         (1289, 409)  393x200
  - Top 5 scorers:            (1289, 619)  393x1465
  - Matchday footer:          (237, 2084) 1445x50
"""
import asyncio
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot
from aiogram.types import FSInputFile

# Config
MODULE_DIR = Path("/home/hermes/.hermes/BundesligaToday")
ASSETS_DIR = MODULE_DIR / "assets"
OUTPUT_DIR = MODULE_DIR / "output"
from config import BUNDESLIGA_BOT_TOKEN, EPSE1LON_BOT_TOKEN, EPS_A_BOT_TOKEN

# ===== Canvas (reference layout from executive summary) =====
REF_W = 2000
REF_H = 2500

# Zone colors
ZONE_COLORS = {
    "zone-cl": (0, 120, 255),
    "zone-el": (180, 0, 80),
    "zone-7": (0, 200, 80),
    "zone-relegation": (255, 60, 60),
    "zone-neutral": (200, 200, 200),
}
ZONE_WIDTHS = {
    "zone-cl": 6,
    "zone-el": 6,
    "zone-7": 6,
    "zone-relegation": 6,
    "zone-neutral": 0,
}

# Shorten club names for tour results (match MR column width)
# Copied from render_cup.py to keep consistency
TOUR_SHORT_NAMES = {
    "Borussia Mönchengladbach": "Borussia M",
    "Borussia Dortmund": "Borussia D",
    "Bayer 04 Leverkusen": "Bayer 04",
    "Eintracht Frankfurt": "Eintracht",
    "Eintracht Braunschweig": "Eintr. Br.",
    "1. FC Köln": "1. FC Köln",
    "1. FC Nürnberg": "1. FC Nürn",
    "1. FC Heidenheim": "Heidenheim",
    "1. FC Heidenheim 1846": "Heidenheim",
    "1. FC Kaiserslautern": "K'lautern",
    "1. FC Magdeburg": "Magdeburg",
    "1. FC Union Berlin": "Union",
    "1. FSV Mainz 05": "Mainz 05",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "VfL Wolfsburg": "Wolfsburg",
    "VfB Stuttgart": "Stuttgart",
    "FC Bayern München": "Bayern",
    "FC St. Pauli": "St. Pauli",
    "FC St. Pauli 1910": "St. Pauli",
    "FC Augsburg": "Augsburg",
    "FC Erzgebirge Aue": "Erzgebirge",
    "FC Wacker Innsbruck": "Wacker Inns.",
    "SV Darmstadt 98": "Darmstadt",
    "SV Wehen Wiesbaden": "Wehen",
    "SC Paderborn 07": "Paderborn",
    "SC Freiburg": "Freiburg",
    "Rot-Weiss Essen": "RWE",
    "Arminia Bielefeld": "Arminia",
    "Fortuna Düsseldorf": "Fortuna",
    "Karlsruher SC": "Karlsruhe",
    "Hamburger SV": "HSV",
    "Hertha BSC": "Hertha",
    "Schalke 04": "Schalke",
    "Alemannia Aachen": "Aachen",
    "VfL Bochum": "Bochum",
    "Viktoria Berlin": "Viktoria",
    "Viktoria Köln": "Viktoria Köln",
    "Holstein Kiel": "Kiel",
    "Werder Bremen": "Werder",
    "SV Werder Bremen": "Werder",
    "RB Leipzig": "RB Leipzig",
    "TSV 1860 München": "1860 Mün.",
    "TSV Großkirchheim": "Großkirch.",
    "SSV Ulm 1846": "Ulm",
    "Lokomotive Leipzig": "Lok. Leipz.",
    "TSV Havelse": "Havelse",
    "BSV Rehden": "Rehden",
    "FC Gießen": "Gießen",
    "FC Neumarkt": "Neumarkt",
    "TSV Schwarz-Weiß": "TSV SW",
    "FSV Mainz 05": "FSV Mainz",
    "Hannover 96": "Hannover",
    "VfL Osnabrück": "Osnabrück",
}


def shorten_tour(name: str) -> str:
    """Shorten club name for tour results display."""
    return TOUR_SHORT_NAMES.get(name, name)

# Fonts
FONT_DIR = ASSETS_DIR / "fonts"
FONT_BEBAS = str(FONT_DIR / "BebasNeue.ttf") if (FONT_DIR / "BebasNeue.ttf").exists() else None
FONT_INTER = str(FONT_DIR / "Inter.ttf") if (FONT_DIR / "Inter.ttf").exists() else None
FONT_OSWALD = str(FONT_DIR / "Oswald.ttf") if (FONT_DIR / "Oswald.ttf").exists() else None


def get_font(name, size):
    path = {"bebas": FONT_BEBAS, "inter": FONT_INTER, "oswald": FONT_OSWALD}.get(name)
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_full(data: dict, output_name: str = "bl_today") -> str:
    """Render the full newspaper layout with all 5 areas."""

    # Load background — try .png first, then .jpg
    for ext in ("png", "jpg"):
        bg_path = ASSETS_DIR / f"magazine_bg_v1.{ext}"
        if bg_path.exists():
            break
    else:
        raise FileNotFoundError("No magazine background found in assets/")

    bg = Image.open(bg_path).convert("RGBA")
    cw, ch = bg.size  # actual canvas size (may be 1360x2048 or 2000x2500)

    # Scale factors from reference (2000x2500) to actual
    sx = cw / REF_W
    sy = ch / REF_H

    def S(x, y, w, h):
        """Scale a rectangle from reference coords to actual."""
        return int(x * sx), int(y * sy), int(w * sx), int(h * sy)

    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # ===== GRID (50px step) =====
    # Grid removed

    # ===== HEADER (date / season) =====
    hx, hy, hw, hh = S(237, 324, 1445, 80)  # -30px up for 56px font
    font_header = get_font("oswald", int(56 * sx))  # 56px
    season = data.get("season", "")
    matchday = data.get("matchday", "?")
    header_text = f"Season {season}  |  Matchday {matchday}"
    # Center text in header area
    bbox = draw.textbbox((0, 0), header_text, font=font_header)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((hx + (hw - tw) // 2, hy + (hh - th) // 2),
              header_text, fill=(30, 30, 30, 255), font=font_header)

    # ===== STANDINGS TABLE (left-center) =====
    sx0, sy0, sw, sh = S(352, 659, 1032, 1675)
    sw -= 165  # reduce table width by 165px total (130 + 35)
    sh += 20   # add 20px to table height
    table = data.get("table", [])

    font_th = get_font("oswald", int(53 * sx))    # table header (base)
    font_th_sm = get_font("oswald", int(40 * sx))  # table header small (cols 2-7) (base)
    font_tc = get_font("oswald", int(55 * sx))    # table cell (cols 0, 1 — # and Club) (base)
    font_tc_sm = get_font("oswald", int(40 * sx))  # table cell small (cols 2-7) (base)
    font_tp = get_font("oswald", int(55 * sx))    # table points (base)

    headers = ["#", "Club", "W", "D", "L", "GF", "GA", "PTS"]
    # Set column widths: #=52, Club=232, W=D=L=GF=GA=PTS=42
    col_widths = [0] * 8
    col_widths[0] = 52   # #
    col_widths[1] = 232  # Club
    col_widths[2] = col_widths[3] = col_widths[4] = col_widths[5] = col_widths[6] = col_widths[7] = 42  # W,D,L,GF,GA,PTS
    sw = sum(col_widths)  # truncate table width to exact sum of columns

    col_x = [0]
    for w in col_widths[:-1]:
        col_x.append(col_x[-1] + w)

    row_header_h = int(62 * sy)
    row_h = row_header_h + 3  # data rows same height as header + 3px gap

    # Create transparent canvas for table
    total_table_h = row_header_h + 2 + len(table) * row_h + 30  # +20px bottom padding
    table_canvas = Image.new("RGBA", (sw, total_table_h), (255, 255, 255, 0))
    td = ImageDraw.Draw(table_canvas)

    ty = 10

    # Header row — centered horizontally & vertically
    for i, (h, cx, cw_) in enumerate(zip(headers, col_x, col_widths)):
        f = font_th if i < 2 else font_th_sm
        bbox = td.textbbox((0, 0), h, font=f)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        td.text((cx + (cw_ - tw) // 2, ty + (row_header_h - th) // 2),
                h, fill=(0, 0, 0, 255), font=f)
    # Line under header — removed
    # td.line((0, ty + row_header_h, sw, ty + row_header_h), fill=(0, 0, 0, 255), width=1)
    ty += row_header_h + 2

    # Table rows
    for idx, row in enumerate(table):
        ry = ty + idx * row_h

        # Zone bar
        zone = row.get("zone", "")
        z_color = ZONE_COLORS.get(zone, (200, 200, 200))
        z_width = ZONE_WIDTHS.get(zone, 0)
        if z_width > 0:
            td.line((0, ry, 0, ry + row_h), fill=z_color + (255,), width=z_width)

        # Position
        bbox = td.textbbox((0, 0), str(row.get("position", "")), font=font_tc)
        th = bbox[3] - bbox[1]
        td.text((col_x[0] + 4, ry + (row_h - th) // 2), str(row.get("position", "")),
                fill=(0, 0, 0, 255), font=font_tc)

        # Club name (shortened)
        club = shorten_tour(row.get("club_name", ""))
        bbox = td.textbbox((0, 0), club, font=font_tc)
        th = bbox[3] - bbox[1]
        td.text((col_x[1] + 4, ry + (row_h - th) // 2), club,
                fill=(0, 0, 0, 255), font=font_tc)

        # Stats (W, D, L, GF, GA) — small font
        stats = [row.get("w", ""), row.get("d", ""), row.get("l", ""),
                 row.get("gf", ""), row.get("ga", "")]
        for si, sv in enumerate(stats, start=2):
            bbox = td.textbbox((0, 0), str(sv), font=font_tc_sm)
            sw_ = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            td.text((col_x[si] + (col_widths[si] - sw_) // 2, ry + (row_h - th) // 2),
                    str(sv), fill=(60, 60, 60, 255), font=font_tc_sm)

        # PTS (now index 7) — small font
        pts = str(row.get("pts", ""))
        bbox = td.textbbox((0, 0), pts, font=font_tc_sm)
        pw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        td.text((col_x[7] + (col_widths[7] - pw) // 2, ry + (row_h - th) // 2),
                pts, fill=(0, 0, 0, 255), font=font_tc_sm)

    table_bottom = ty + len(table) * row_h

    # Paste standings onto background
    canvas.paste(table_canvas, (sx0, sy0), table_canvas)

    # Black border around standings table
    draw.rectangle(
        [sx0 - 2, sy0 - 2, sx0 + sw + 2, sy0 + total_table_h + 2],
        outline=(0, 0, 0, 255), width=2
    )

    # ===== MATCHDAY RESULTS (top-right) =====
    # Top edge aligned with ST top edge
    my = sy0  # align top with ST
    mw = 350  # border width
    matchday_results = data.get("matchday_results", [])

    # Pre-compute TS left edge to align MR with it
    ts_th = int(350 * sy)
    ts_bottom = sy0 + total_table_h + 2
    ty0_calc = ts_bottom - ts_th
    tx0, ty0, tw, th_ = S(1159, int(ty0_calc / sy), 523, 550)
    mx = tx0  # MR left edge = TS left edge

    mf_heading = get_font("oswald", int(43 * sx))  # 43px
    mf_cell = get_font("oswald", int(43 * sx))    # 43px
    mf_score = get_font("oswald", int(43 * sx))   # 43px

    mr_row_h = int(44 * sy)  # row height for 43px font
    home_w = 140   # fixed Home width 140px
    score_w = 45   # fixed Score width 45px
    away_w = 140   # fixed Away width 140px

    # Draw heading
    ty_mr = my + 8
    mr_heading_text = f"Matchday {matchday} Results"
    bbox = draw.textbbox((0, 0), mr_heading_text, font=mf_heading)
    mr_tw = bbox[2] - bbox[0]
    draw.text((mx + (mw - mr_tw) // 2, ty_mr), mr_heading_text, fill=(0, 80, 200, 255), font=mf_heading)
    ty_mr += (bbox[3] - bbox[1]) + 20

    # Dark gray separator line under heading (75% of border width, centered)
    sep_w = int(mw * 0.75)
    sep_x = mx + (mw - sep_w) // 2
    draw.line((sep_x, ty_mr, sep_x + sep_w, ty_mr), fill=(80, 80, 80, 255), width=4)
    ty_mr += 14  # 4px separator + 10px gap

    # Draw data rows (4px padding from border)
    col1_x = mx + 4
    col2_x = mx + 4 + home_w
    col3_x = mx + 4 + home_w + score_w

    actual_rows = 0
    for mi, m in enumerate(matchday_results[:9]):
        if ty_mr + mr_row_h > my + 2000:  # safety limit
            break
        home = shorten_tour(m.get("home", ""))
        away = shorten_tour(m.get("away", ""))
        score_str = f"{m.get('score_h', 0)}-{m.get('score_a', 0)}"

        draw.text((col1_x + 4, ty_mr), home, fill=(0, 0, 0, 255), font=mf_cell)
        draw.text((col2_x + 4, ty_mr), score_str, fill=(200, 0, 0, 255), font=mf_score)
        draw.text((col3_x + 4, ty_mr), away, fill=(0, 0, 0, 255), font=mf_cell)

        ty_mr += mr_row_h
        actual_rows += 1

    # Dynamic MR border: heading + separator + rows + bottom padding
    heading_h = (bbox[3] - bbox[1]) + 6 + 4 + 4  # heading + gap + separator + gap
    mh = heading_h + actual_rows * mr_row_h + 24 + 50  # +24 bottom padding + 50px extra

    # ===== TOP 5 SCORERS (bottom-right) =====
    # tx0 already computed above
    top_scorers = data.get("top_scorers", [])

    sf_heading = get_font("oswald", int(40 * sx))  # 40px
    sf_cell = get_font("oswald", int(40 * sx))    # 40px
    sf_club = get_font("oswald", int(34 * sx))    # 34px (Club column, -6px)
    sf_goals = get_font("oswald", int(36 * sx))   # 36px (Goals column, -4px)

    ts_row_h = int(50 * sy)  # row height
    ts_rank_w = 25    # Rank width 25px
    ts_name_w = 160   # Name width 160px
    ts_club_w = 100   # Club width 100px
    ts_goals_w = 45   # Goals width 45px (was 25, increased for "goals/assists" format)

    ts_rank_x = tx0
    ts_name_x = tx0 + ts_rank_w
    ts_club_x = tx0 + ts_rank_w + ts_name_w
    ts_goals_x = tx0 + ts_rank_w + ts_name_w + ts_club_w

    # Calculate TS position dynamically: bottom-aligned with ST
    ts_heading_text = "Top Scorers"
    bbox = draw.textbbox((0, 0), ts_heading_text, font=sf_heading)
    ts_heading_h = (bbox[3] - bbox[1]) + 20 + 4 + 10  # heading + 20px gap + 4px line + 10px gap
    actual_ts_rows = min(len(top_scorers), 10)
    ts_bottom = sy0 + total_table_h + 2  # align with ST bottom
    th_ = ts_heading_h + actual_ts_rows * ts_row_h + 8 + 50  # 8px top padding + 50px bottom extension
    ty0 = ts_bottom - th_

    # Draw heading
    ty_ts = ty0 + 8
    ts_tw = bbox[2] - bbox[0]
    draw.text((tx0 + (tw - ts_tw) // 2, ty_ts), ts_heading_text, fill=(200, 0, 0, 255), font=sf_heading)
    ty_ts += (bbox[3] - bbox[1]) + 20

    # Dark gray separator line under heading (75% of border width, centered)
    sep_w = int(tw * 0.75)
    sep_x = tx0 + (tw - sep_w) // 2
    draw.line((sep_x, ty_ts, sep_x + sep_w, ty_ts), fill=(80, 80, 80, 255), width=4)
    ty_ts += 14  # 4px separator + 10px gap

    # Draw data rows
    for si, scorer in enumerate(top_scorers[:10]):
        rank = str(si + 1)
        name = scorer.get("name", "")
        club = shorten_tour(scorer.get("club", ""))
        goals = str(scorer.get("goals", ""))
        assists = str(scorer.get("assists", ""))
        goals_str = f"{goals}/{assists}" if assists and assists != "0" else goals

        # Vertical centering offsets for smaller fonts
        name_bbox = draw.textbbox((0, 0), name[:16], font=sf_cell)
        name_h = name_bbox[3] - name_bbox[1]
        club_bbox = draw.textbbox((0, 0), club[:12], font=sf_club)
        club_h = club_bbox[3] - club_bbox[1]
        goals_bbox = draw.textbbox((0, 0), goals_str, font=sf_goals)
        goals_h = goals_bbox[3] - goals_bbox[1]
        club_dy = (ts_row_h - club_h) // 2
        goals_dy = (ts_row_h - goals_h) // 2

        draw.text((ts_rank_x + 4, ty_ts), rank, fill=(100, 100, 100, 255), font=sf_cell)
        draw.text((ts_name_x + 4, ty_ts), name[:16], fill=(0, 0, 0, 255), font=sf_cell)
        draw.text((ts_club_x + 4, ty_ts + club_dy), club[:12], fill=(80, 80, 80, 255), font=sf_club)
        draw.text((ts_goals_x + 4, ty_ts + goals_dy), goals_str, fill=(200, 0, 0, 255), font=sf_goals)
        ty_ts += ts_row_h

    # ===== MATCHDAY FOOTER (bottom panel) =====
    fx, fy, fw, fh = S(87, 1984, 1745, 50)  # -200px up (2184→1984)
    # Dark gray separator line above footer (800px centered)
    sep_y = fy - 8
    sep_w = 800
    draw.line((fx + (fw - sep_w) // 2, sep_y, fx + (fw + sep_w) // 2, sep_y), fill=(80, 80, 80, 255), width=3)
    font_footer = get_font("oswald", int(50 * sx))  # 50px
    footer_text = f"Updated After Matchday {matchday}"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    ftw = bbox[2] - bbox[0]
    fth = bbox[3] - bbox[1]
    draw.text((fx + (fw - ftw) // 2 + 15, fy + (fh - fth) // 2),
              footer_text, fill=(255, 60, 60, 255), font=font_footer)

    # ===== DEBUG BORDERS (toggle True/False) =====
    DEBUG_BORDERS = True
    if DEBUG_BORDERS:
        border_color = (0, 0, 0, 255)  # black
        border_w = 2
        # Standings table (real bounds including all rows)
        draw.rectangle([sx0 - 2, sy0 - 2, sx0 + sw + 2, sy0 + total_table_h + 2],
                       outline=border_color, width=border_w)
        # Matchday Results
        draw.rectangle([mx, my, mx + mw, my + mh], outline=border_color, width=border_w)
        # Top Scorers
        draw.rectangle([tx0, ty0, tx0 + tw, ty0 + th_], outline=border_color, width=border_w)

    # Save
    output_path = OUTPUT_DIR / f"{output_name}.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, "PNG", quality=95)
    return str(output_path)


async def send_to_telegram(image_path: str):
    bot = Bot(token=BUNDESLIGA_BOT_TOKEN)
    try:
        await bot.send_photo(
            chat_id=1999236552,
            photo=FSInputFile(image_path),
            caption="📰 Bundesliga Today",
            parse_mode="Markdown"
        )
        print("✅ Отправлено в Telegram (BLTD)")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
    finally:
        await bot.session.close()


async def send_duplicate_to_dev_chat(image_path: str):
    """Отправить дубликат картинки в чат разработки через EPS_A_bot."""
    if not EPS_A_BOT_TOKEN:
        print("⚠️ EPS_A_BOT_TOKEN не задан, дубликат не отправлен")
        return
    bot = Bot(token=EPS_A_BOT_TOKEN)
    try:
        await bot.send_photo(
            chat_id=1999236552,
            photo=FSInputFile(image_path),
            caption="📰 Bundesliga Today (дубликат)"
        )
        print("✅ Дубликат отправлен через EPS_A_bot")
    except Exception as e:
        print(f"❌ Ошибка отправки дубликата: {e}")
    finally:
        await bot.session.close()


def main():
    data = {
        "season": "2025/26",
        "matchday": 33,
        "table": [
            {"position": 1, "zone": "zone-cl", "club_name": "FC Bayern München", "mp": 34, "w": 28, "d": 5, "l": 1, "gf": 122, "ga": 36, "pts": 89},
            {"position": 2, "zone": "zone-cl", "club_name": "Borussia Dortmund", "mp": 34, "w": 22, "d": 5, "l": 7, "gf": 72, "ga": 38, "pts": 71},
            {"position": 3, "zone": "zone-cl", "club_name": "RB Leipzig", "mp": 34, "w": 19, "d": 7, "l": 8, "gf": 58, "ga": 44, "pts": 64},
            {"position": 4, "zone": "zone-cl", "club_name": "Bayer 04 Leverkusen", "mp": 34, "w": 18, "d": 8, "l": 8, "gf": 68, "ga": 39, "pts": 62},
            {"position": 5, "zone": "zone-el", "club_name": "Eintracht Frankfurt", "mp": 34, "w": 17, "d": 8, "l": 9, "gf": 58, "ga": 44, "pts": 59},
            {"position": 6, "zone": "zone-el", "club_name": "VfB Stuttgart", "mp": 34, "w": 15, "d": 9, "l": 10, "gf": 58, "ga": 48, "pts": 54},
            {"position": 7, "zone": "zone-el", "club_name": "SC Freiburg", "mp": 34, "w": 14, "d": 8, "l": 12, "gf": 48, "ga": 45, "pts": 50},
            {"position": 8, "zone": "zone-neutral", "club_name": "TSG 1899 Hoffenheim", "mp": 34, "w": 13, "d": 9, "l": 12, "gf": 50, "ga": 50, "pts": 48},
            {"position": 9, "zone": "zone-neutral", "club_name": "SV Werder Bremen", "mp": 34, "w": 11, "d": 9, "l": 14, "gf": 46, "ga": 56, "pts": 42},
            {"position": 10, "zone": "zone-neutral", "club_name": "1. FC Union Berlin", "mp": 34, "w": 10, "d": 10, "l": 14, "gf": 40, "ga": 48, "pts": 40},
            {"position": 11, "zone": "zone-neutral", "club_name": "FC Augsburg", "mp": 34, "w": 10, "d": 8, "l": 16, "gf": 38, "ga": 52, "pts": 38},
            {"position": 12, "zone": "zone-neutral", "club_name": "VfL Wolfsburg", "mp": 34, "w": 9, "d": 9, "l": 16, "gf": 44, "ga": 58, "pts": 36},
            {"position": 13, "zone": "zone-neutral", "club_name": "Borussia Mönchengladbach", "mp": 34, "w": 8, "d": 10, "l": 16, "gf": 42, "ga": 60, "pts": 34},
            {"position": 14, "zone": "zone-neutral", "club_name": "1. FSV Mainz 05", "mp": 34, "w": 8, "d": 8, "l": 18, "gf": 36, "ga": 56, "pts": 32},
            {"position": 15, "zone": "zone-neutral", "club_name": "1. FC Köln", "mp": 34, "w": 6, "d": 10, "l": 18, "gf": 30, "ga": 62, "pts": 28},
            {"position": 16, "zone": "zone-relegation", "club_name": "VfL Bochum", "mp": 34, "w": 6, "d": 6, "l": 22, "gf": 28, "ga": 68, "pts": 24},
            {"position": 17, "zone": "zone-relegation", "club_name": "1. FC Heidenheim 1846", "mp": 34, "w": 4, "d": 8, "l": 22, "gf": 26, "ga": 66, "pts": 20},
            {"position": 18, "zone": "zone-relegation", "club_name": "SV Darmstadt 98", "mp": 34, "w": 3, "d": 7, "l": 24, "gf": 22, "ga": 72, "pts": 16},
        ],
        "matchday_results": [
            {"home": "SV Werder Bremen", "score_h": 0, "score_a": 2, "away": "Borussia Dortmund"},
            {"home": "1. FC Heidenheim 1846", "score_h": 0, "score_a": 2, "away": "1. FSV Mainz 05"},
            {"home": "SC Freiburg", "score_h": 4, "score_a": 1, "away": "RB Leipzig"},
            {"home": "Eintracht Frankfurt", "score_h": 2, "score_a": 2, "away": "VfB Stuttgart"},
            {"home": "FC St. Pauli 1910", "score_h": 1, "score_a": 3, "away": "VfL Wolfsburg"},
            {"home": "1. FC Union Berlin", "score_h": 4, "score_a": 0, "away": "FC Augsburg"},
            {"home": "Borussia Mönchengladbach", "score_h": 4, "score_a": 0, "away": "TSG 1899 Hoffenheim"},
            {"home": "FC Bayern München", "score_h": 5, "score_a": 1, "away": "1. FC Köln"},
            {"home": "Bayer 04 Leverkusen", "score_h": 1, "score_a": 1, "away": "Hamburger SV"},
        ],
        "top_scorers": [
            {"name": "Harry Kane", "club": "FC Bayern München", "goals": 36, "assists": 12},
            {"name": "Deniz Undav", "club": "VfB Stuttgart", "goals": 19, "assists": 5},
            {"name": "Sehrou Guirassy", "club": "Borussia Dortmund", "goals": 17, "assists": 4},
            {"name": "Patrik Schick", "club": "Bayer 04 Leverkusen", "goals": 16, "assists": 6},
            {"name": "Michael Olise", "club": "FC Bayern München", "goals": 15, "assists": 14},
            {"name": "Florian Wirtz", "club": "Bayer 04 Leverkusen", "goals": 13, "assists": 11},
            {"name": "Jamal Musiala", "club": "FC Bayern München", "goals": 12, "assists": 8},
            {"name": "Victor Boniface", "club": "Bayer 04 Leverkusen", "goals": 11, "assists": 3},
            {"name": "Leroy Sané", "club": "FC Bayern München", "goals": 10, "assists": 9},
            {"name": "Xavi Simons", "club": "RB Leipzig", "goals": 9, "assists": 7},
        ],
    }

    out = render_full(data, "bl_today")
    print(f"✅ Файл сохранён: {out}")
    asyncio.run(send_to_telegram(out))
    asyncio.run(send_duplicate_to_dev_chat(out))


if __name__ == "__main__":
    main()
