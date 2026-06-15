"""
Render ONLY the standings table (no matchday/scorers) onto the magazine background.
Output: PNG 1402x1122.
"""
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot
from aiogram.types import FSInputFile

MODULE_DIR = Path("/home/hermes/.hermes/BundesligaToday")
ASSETS_DIR = MODULE_DIR / "assets"
OUTPUT_DIR = MODULE_DIR / "output"
from config import BOT_TOKEN

CANVAS_W = 1402
CANVAS_H = 1122

# Standings area
S_LEFT = 332
S_TOP = 311
S_WIDTH = 680
S_HEIGHT = 700

FONT_DIR = ASSETS_DIR / "fonts"
FONT_BEBAS = str(FONT_DIR / "BebasNeue.ttf") if (FONT_DIR / "BebasNeue.ttf").exists() else None
FONT_INTER = str(FONT_DIR / "Inter.ttf") if (FONT_DIR / "Inter.ttf").exists() else None
FONT_OSWALD = str(FONT_DIR / "Oswald.ttf") if (FONT_DIR / "Oswald.ttf").exists() else None

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


def get_font(name, size):
    path = {"bebas": FONT_BEBAS, "inter": FONT_INTER, "oswald": FONT_OSWALD}.get(name)
    if path and Path(path).exists():
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_standings_only(data: dict, output_name: str = "standings_only") -> str:
    bg_path = ASSETS_DIR / "magazine_bg_v1_resized.jpg"
    bg = Image.open(bg_path).convert("RGBA")
    canvas = bg.copy()
    if canvas.size != (CANVAS_W, CANVAS_H):
        canvas = canvas.resize((CANVAS_W, CANVAS_H))
    canvas_draw = ImageDraw.Draw(canvas)

    font_header = get_font("oswald", 17)
    font_cell = get_font("oswald", 20)
    font_rank = get_font("oswald", 20)
    font_pts = get_font("oswald", 20)

    headers = ["#", "Club", "MP", "W", "D", "L", "GF", "GA", "PTS"]
    col_widths = [30, 180, 35, 35, 35, 35, 40, 40, 50]
    col_x = [0]
    for w in col_widths[:-1]:
        col_x.append(col_x[-1] + w)

    row_header_h = 28
    row_h = 36
    table = data.get("table", [])

    total_h = 10 + 15 + row_header_h + 2 + len(table) * row_h + 10

    table_canvas = Image.new("RGBA", (S_WIDTH, total_h), (255, 255, 255, 0))
    td = ImageDraw.Draw(table_canvas)

    ty = 10

    # Header row
    for i, (h, cx, cw) in enumerate(zip(headers, col_x, col_widths)):
        td.text((cx + 4, ty + 3), h, fill=(0, 0, 0, 255), font=font_header)
    td.line((0, ty + row_header_h, S_WIDTH, ty + row_header_h), fill=(0, 0, 0, 255), width=1)
    ty += row_header_h + 2

    # Table rows
    for idx, row in enumerate(table):
        ry = ty + idx * row_h

        zone = row.get("zone", "")
        z_color = ZONE_COLORS.get(zone, (200, 200, 200))
        z_width = ZONE_WIDTHS.get(zone, 0)
        if z_width > 0:
            td.line((0, ry, 0, ry + row_h), fill=z_color + (255,), width=z_width)

        td.text((col_x[0] + 4, ry + 5), str(row.get("position", "")), fill=(0, 0, 0, 255), font=font_rank)
        td.text((col_x[1] + 4, ry + 5), row.get("club_name", ""), fill=(0, 0, 0, 255), font=font_cell)

        stats = [row.get("mp", ""), row.get("w", ""), row.get("d", ""),
                 row.get("l", ""), row.get("gf", ""), row.get("ga", "")]
        for si, sv in enumerate(stats, start=2):
            bbox = td.textbbox((0, 0), str(sv), font=font_cell)
            sw = bbox[2] - bbox[0]
            td.text((col_x[si] + (col_widths[si] - sw) // 2, ry + 5), str(sv), fill=(60, 60, 60, 255), font=font_cell)

        pts = str(row.get("pts", ""))
        bbox = td.textbbox((0, 0), pts, font=font_pts)
        pw = bbox[2] - bbox[0]
        td.text((col_x[8] + (col_widths[8] - pw) // 2, ry + 5), pts, fill=(0, 0, 0, 255), font=font_pts)

    table_bottom = ty + len(table) * row_h

    canvas.paste(table_canvas, (S_LEFT, S_TOP), table_canvas)

    # Updated after matchday
    matchday = data.get("matchday", "?")
    updated_text = f"Updated After Matchday {matchday}"
    font_updated = get_font("oswald", 24)
    bbox = canvas_draw.textbbox((0, 0), updated_text, font=font_updated)
    tw = bbox[2] - bbox[0]
    tx = S_LEFT + (S_WIDTH - tw) // 2 + 15
    ty_updated = S_TOP + table_bottom + 12
    canvas_draw.text((tx, ty_updated), updated_text, fill=(255, 60, 60, 255), font=font_updated)

    output_path = OUTPUT_DIR / f"{output_name}.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, "PNG", quality=95)
    return str(output_path)


async def send_to_telegram(image_path: str):
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_photo(chat_id=1999236552, photo=FSInputFile(image_path))
        print("✅ Отправлено в Telegram")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
    finally:
        await bot.session.close()


def main():
    data = {
        "season": "2025/26",
        "matchday": 34,
        "table": [
            {"position": 1, "zone": "zone-cl", "club_name": "Bayern Munich", "mp": 34, "w": 28, "d": 3, "l": 3, "gf": 98, "ga": 22, "pts": 87},
            {"position": 2, "zone": "zone-cl", "club_name": "Borussia Dortmund", "mp": 34, "w": 22, "d": 5, "l": 7, "gf": 72, "ga": 38, "pts": 71},
            {"position": 3, "zone": "zone-cl", "club_name": "Bayer Leverkusen", "mp": 34, "w": 20, "d": 7, "l": 7, "gf": 68, "ga": 35, "pts": 67},
            {"position": 4, "zone": "zone-cl", "club_name": "Eintracht Frankfurt", "mp": 34, "w": 18, "d": 8, "l": 8, "gf": 59, "ga": 42, "pts": 62},
            {"position": 5, "zone": "zone-el", "club_name": "RB Leipzig", "mp": 34, "w": 17, "d": 7, "l": 10, "gf": 55, "ga": 44, "pts": 58},
            {"position": 6, "zone": "zone-el", "club_name": "VfB Stuttgart", "mp": 34, "w": 16, "d": 8, "l": 10, "gf": 58, "ga": 48, "pts": 56},
            {"position": 7, "zone": "zone-7", "club_name": "SC Freiburg", "mp": 34, "w": 15, "d": 8, "l": 11, "gf": 50, "ga": 45, "pts": 53},
            {"position": 8, "zone": "zone-neutral", "club_name": "TSG Hoffenheim", "mp": 34, "w": 14, "d": 9, "l": 11, "gf": 52, "ga": 50, "pts": 51},
            {"position": 9, "zone": "zone-neutral", "club_name": "Werder Bremen", "mp": 34, "w": 12, "d": 9, "l": 13, "gf": 48, "ga": 55, "pts": 45},
            {"position": 10, "zone": "zone-neutral", "club_name": "Union Berlin", "mp": 34, "w": 11, "d": 10, "l": 13, "gf": 42, "ga": 48, "pts": 43},
            {"position": 11, "zone": "zone-neutral", "club_name": "FC Augsburg", "mp": 34, "w": 11, "d": 8, "l": 15, "gf": 40, "ga": 52, "pts": 41},
            {"position": 12, "zone": "zone-neutral", "club_name": "VfL Wolfsburg", "mp": 34, "w": 10, "d": 9, "l": 15, "gf": 45, "ga": 58, "pts": 39},
            {"position": 13, "zone": "zone-neutral", "club_name": "B. Mönchengladbach", "mp": 34, "w": 9, "d": 10, "l": 15, "gf": 44, "ga": 60, "pts": 37},
            {"position": 14, "zone": "zone-neutral", "club_name": "Mainz 05", "mp": 34, "w": 9, "d": 8, "l": 17, "gf": 38, "ga": 55, "pts": 35},
            {"position": 15, "zone": "zone-neutral", "club_name": "1. FC Köln", "mp": 34, "w": 7, "d": 10, "l": 17, "gf": 32, "ga": 62, "pts": 31},
            {"position": 16, "zone": "zone-relegation", "club_name": "VfL Bochum", "mp": 34, "w": 7, "d": 6, "l": 21, "gf": 30, "ga": 68, "pts": 27},
            {"position": 17, "zone": "zone-relegation", "club_name": "1. FC Heidenheim", "mp": 34, "w": 5, "d": 8, "l": 21, "gf": 28, "ga": 65, "pts": 23},
            {"position": 18, "zone": "zone-relegation", "club_name": "SV Darmstadt 98", "mp": 34, "w": 4, "d": 7, "l": 23, "gf": 25, "ga": 72, "pts": 19},
        ],
    }

    out = render_standings_only(data, "standings_only")
    print(f"✅ Файл сохранён: {out}")
    asyncio.run(send_to_telegram(out))


if __name__ == "__main__":
    main()
