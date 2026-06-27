"""
DFB-Pokal Cup Draw Renderer — 1/64 Finals
Two side-by-side tables (16 pairs left, 16 pairs right), transparent background.
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
from config import BUNDESLIGA_BOT_TOKEN, EPS_A_BOT_TOKEN

# ===== Canvas =====
REF_W = 2000
REF_H = 2500

# ===== Fonts =====
FONT_DIR = ASSETS_DIR / "fonts"
FONT_BEBAS = str(FONT_DIR / "BebasNeue.ttf") if (FONT_DIR / "BebasNeue.ttf").exists() else None
FONT_OSWALD = str(FONT_DIR / "Oswald.ttf") if (FONT_DIR / "Oswald.ttf").exists() else None


def get_font(name, size):
    path = {"bebas": FONT_BEBAS, "oswald": FONT_OSWALD}.get(name)
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def shorten(name: str) -> str:
    """Shorten club names to fit column width."""
    replacements = {
        "Borussia Mönchengladbach": "Borussia M",
        "Borussia Dortmund": "Borussia D",
        "Bayer 04 Leverkusen": "Bayer 04",
        "Eintracht Frankfurt": "Eintracht",
        "Eintracht Braunschweig": "Eintr. Br.",
        "1. FC Köln": "1. FC Köln",
        "1. FC Nürnberg": "1. FC Nürn",
        "1. FC Heidenheim": "Heidenheim",
        "1. FC Kaiserslautern": "K'lautern",
        "1. FC Magdeburg": "Magdeburg",
        "1. FC Union Berlin": "Union",
        "1. FSV Mainz 05": "Mainz 05",
        "TSG 1899 Hoffenheim": "Hoffenheim",
        "VfL Wolfsburg": "Wolfsburg",
        "VfB Stuttgart": "Stuttgart",
        "FC Bayern München": "Bayern",
        "FC St. Pauli": "St. Pauli",
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
    }
    return replacements.get(name, name)


def render_cup_draw(data: dict, output_name: str = "dfb_pokal_1_64") -> str:
    """Render DFB-Pokal 1/64 — two side-by-side tables, transparent background."""

    # Load background (cup_bg.jpg)
    bg_path = ASSETS_DIR / "cup_bg2.jpg"
    if not bg_path.exists():
        raise FileNotFoundError("cup_bg.jpg not found in assets/")

    bg = Image.open(bg_path).convert("RGBA")
    cw, ch = bg.size

    sx = cw / REF_W
    sy = ch / REF_H

    def S(x, y, w, h):
        return int(x * sx), int(y * sy), int(w * sx), int(h * sy)

    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # ===== Column widths (reference space) =====
    col_date_w = 130
    col_time_w = 115
    col_home_w = 210
    col_score_w = 165
    col_away_w = 210
    table_w = col_date_w + col_time_w + col_home_w + col_score_w + col_away_w  # 970px

    row_h = int(62 * sy)  # +10px per row × 17 rows ≈ +170px total table height
    header_h = int(58 * sy)
    title_h = int(70 * sy)

    gap_x = int(60 * sx)  # gap between two tables

    # Calculate table X positions: two tables side by side, centered, shifted left 75px
    tables_total_w = int(table_w * sx) * 2 + gap_x
    left_table_x = (cw - tables_total_w) // 2 + int(50 * sx)
    right_table_x = left_table_x + int(table_w * sx) + gap_x

    # ===== Fonts =====
    font_title = get_font("oswald", int(52 * sx))
    font_sub = get_font("oswald", int(40 * sx))
    font_header = get_font("oswald", int(40 * sx))
    font_cell = get_font("oswald", int(40 * sx))
    font_score = get_font("oswald", int(40 * sx))
    font_footer = get_font("oswald", int(36 * sx))

    # ===== Colors =====
    color_title = (0, 0, 0, 255)
    color_sub = (60, 60, 60, 255)
    color_header = (255, 255, 255, 255)
    color_cell = (0, 0, 0, 255)
    color_score = (180, 0, 0, 255)
    color_loser = (200, 0, 0, 255)
    color_dash = (100, 100, 100, 255)
    color_border = (0, 0, 0, 200)
    color_header_bg = (0, 0, 0, 30)
    color_sep = (0, 0, 0, 150)

    # ===== Title =====
    title = data.get("title", "DFB-Pokal 2025/26 — 1/64")
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = bbox[2] - bbox[0]
    # Center title over left table
    title_x = left_table_x + (int(table_w * sx) - title_w) // 2
    title_y = int(60 * sy)
    draw.text((title_x, title_y), title, fill=color_title, font=font_title)

    # Separator under title
    sep_y = title_y + int(60 * sy)
    sep_w = int(500 * sx)
    draw.line((left_table_x + (int(table_w * sx) - sep_w) // 2, sep_y,
               left_table_x + (int(table_w * sx) + sep_w) // 2, sep_y),
              fill=color_sep, width=3)

    # ===== Table data =====
    tables = [
        (left_table_x, data.get("table1", [])),
        (right_table_x, data.get("table2", [])),
    ]

    for table_x, matches in tables:
        cur_y = sep_y + int(30 * sy) + int(750 * sy)  # +750px offset

        # Column headers removed

        col_offsets = [0, col_date_w, col_date_w + col_time_w,
                       col_date_w + col_time_w + col_home_w,
                       col_date_w + col_time_w + col_home_w + col_score_w]

        # Data rows
        for mi, match in enumerate(matches):
            date_str = match.get("date", "")
            time_str = match.get("time", "")
            home = shorten(match.get("home", ""))
            away = shorten(match.get("away", ""))
            score_h = match.get("score_h")
            score_a = match.get("score_a")

            played = score_h is not None and score_a is not None
            if played:
                score_str = f"{score_h}-{score_a}"
                home_won = score_h > score_a
                away_won = score_a > score_h
            else:
                score_str = "—"
                home_won = False
                away_won = False

            # No alternating row background — transparent

            col_x_positions = [
                table_x + int(col_offsets[0] * sx) + int(4 * sx),
                table_x + int(col_offsets[1] * sx) + int(4 * sx),
                table_x + int(col_offsets[2] * sx) + int(4 * sx),
                table_x + int(col_offsets[3] * sx) + int(4 * sx),
                table_x + int(col_offsets[4] * sx) + int(4 * sx),
            ]

            # Date
            bbox = draw.textbbox((0, 0), date_str, font=font_cell)
            th = bbox[3] - bbox[1]
            draw.text((col_x_positions[0], cur_y + (row_h - th) // 2),
                      date_str, fill=color_cell, font=font_cell)

            # Time
            bbox = draw.textbbox((0, 0), time_str, font=font_cell)
            th = bbox[3] - bbox[1]
            draw.text((col_x_positions[1], cur_y + (row_h - th) // 2),
                      time_str, fill=color_cell, font=font_cell)

            # Home team
            bbox = draw.textbbox((0, 0), home, font=font_cell)
            th = bbox[3] - bbox[1]
            home_y = cur_y + (row_h - th) // 2
            draw.text((col_x_positions[2], home_y), home, fill=color_cell, font=font_cell)
            if played and away_won:
                tw = bbox[2] - bbox[0]
                line_y = home_y + th // 2
                draw.line((col_x_positions[2], line_y, col_x_positions[2] + tw, line_y),
                          fill=color_loser, width=2)

            # Score
            bbox = draw.textbbox((0, 0), score_str, font=font_score)
            th = bbox[3] - bbox[1]
            score_color = color_score if played else color_dash
            draw.text((col_x_positions[3], cur_y + (row_h - th) // 2),
                      score_str, fill=score_color, font=font_score)

            # Away team
            bbox = draw.textbbox((0, 0), away, font=font_cell)
            th = bbox[3] - bbox[1]
            away_y = cur_y + (row_h - th) // 2
            draw.text((col_x_positions[4], away_y), away, fill=color_cell, font=font_cell)
            if played and home_won:
                tw = bbox[2] - bbox[0]
                line_y = away_y + th // 2
                draw.line((col_x_positions[4], line_y, col_x_positions[4] + tw, line_y),
                          fill=color_loser, width=2)

            cur_y += row_h

        # Table border
        draw.rectangle(
            [table_x - 6, sep_y + int(30 * sy) + int(750 * sy), table_x + int(table_w * sx) + 6, cur_y + 4],
            outline=color_border, width=2
        )

    # ===== Make background transparent where needed =====
    # Convert: pixels that are pure white/very bright → transparent
    pixels = canvas.load()
    for py in range(ch):
        for px in range(cw):
            r, g, b, a = pixels[px, py]
            # Detect near-white background pixels and make transparent
            if r > 240 and g > 240 and b > 240:
                pixels[px, py] = (255, 255, 255, 0)
            # Slightly transparent for near-white
            elif r > 220 and g > 220 and b > 220:
                alpha = int((255 - r) / 35 * 255)
                pixels[px, py] = (r, g, b, min(alpha, a))

    # Save as PNG with transparency
    output_path = OUTPUT_DIR / f"{output_name}.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG")
    return str(output_path)


async def send_to_telegram(image_path: str):
    bot = Bot(token=BUNDESLIGA_BOT_TOKEN)
    try:
        await bot.send_photo(
            chat_id=1999236552,
            photo=FSInputFile(image_path),
            caption="🏆 DFB-Pokal 1/64",
            parse_mode="Markdown"
        )
        print("✅ Отправлено в Telegram (BLTD)")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
    finally:
        await bot.session.close()


async def send_duplicate(image_path: str):
    """Send duplicate via EPS_A_bot."""
    if not EPS_A_BOT_TOKEN:
        return
    bot = Bot(token=EPS_A_BOT_TOKEN)
    try:
        await bot.send_photo(
            chat_id=1999236552,
            photo=FSInputFile(image_path),
            caption="🏆 DFB-Pokal 1/64 (дубликат)"
        )
        print("✅ Дубликат отправлен")
    except Exception as e:
        print(f"❌ Ошибка дубликата: {e}")
    finally:
        await bot.session.close()


def main():
    data = {
        "title": "DFB-Pokal 1/64",
        "table1": [
            {"date": "22.08", "time": "16:30", "home": "TSV 1860 München", "away": "Holstein Kiel", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "16:30", "home": "Eintracht Braunschweig", "away": "Viktoria Berlin", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "16:30", "home": "Hannover 96", "away": "Karlsruher SC", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "16:30", "home": "Hertha BSC", "away": "Hamburger SV", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "16:30", "home": "Schalke 04", "away": "Alemannia Aachen", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "16:30", "home": "1. FC Nürnberg", "away": "1. FC Heidenheim", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "16:30", "home": "SC Paderborn 07", "away": "VfL Bochum", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "16:30", "home": "1. FC Kaiserslautern", "away": "Werder Bremen", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "SV Darmstadt 98", "away": "SC Freiburg", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "1. FSV Mainz 05", "away": "FC Augsburg", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "1. FC Köln", "away": "VfB Stuttgart", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "RB Leipzig", "away": "VfL Wolfsburg", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "Borussia Dortmund", "away": "Bayer 04 Leverkusen", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "FC Bayern München", "away": "FC St. Pauli", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "1. FC Union Berlin", "away": "TSG 1899 Hoffenheim", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "14:00", "home": "VfL Bochum", "away": "Borussia Mönchengladbach", "score_h": 1, "score_a": 0},
        ],
        "table2": [
            {"date": "22.08", "time": "19:00", "home": "SV Wehen Wiesbaden", "away": "Arminia Bielefeld", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "19:00", "home": "FC Erzgebirge Aue", "away": "Fortuna Düsseldorf", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "19:00", "home": "VfL Osnabrück", "away": "Hertha BSC", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "19:00", "home": "1. FC Magdeburg", "away": "VfB Stuttgart", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "19:00", "home": "Eintracht Braunschweig", "away": "1. FC Nürnberg", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "19:00", "home": "FC Wacker Innsbruck", "away": "RB Leipzig", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "19:00", "home": "TSV Großkirchheim", "away": "Bayer 04 Leverkusen", "score_h": 1, "score_a": 0},
            {"date": "22.08", "time": "19:00", "home": "SSV Ulm 1846", "away": "Eintracht Frankfurt", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "Lokomotive Leipzig", "away": "Borussia Dortmund", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "Rot-Weiss Essen", "away": "FSV Mainz 05", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "TSV Havelse", "away": "FC Augsburg", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "BSV Rehden", "away": "VfL Wolfsburg", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "FC Gießen", "away": "TSG 1899 Hoffenheim", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "Viktoria Köln", "away": "SC Freiburg", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "FC Neumarkt", "away": "1. FC Union Berlin", "score_h": 1, "score_a": 0},
            {"date": "23.08", "time": "16:30", "home": "TSV Schwarz-Weiß", "away": "FC St. Pauli", "score_h": 1, "score_a": 0},
        ],
    }

    out = render_cup_draw(data, "dfb_pokal_1_64")
    print(f"✅ Файл сохранён: {out}")
    asyncio.run(send_to_telegram(out))
    asyncio.run(send_duplicate(out))


if __name__ == "__main__":
    main()
