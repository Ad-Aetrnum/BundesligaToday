"""Bundesliga Today — Universal HTML → PNG Renderer (Jinja2 version)"""
import json
import os
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

MODULE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = MODULE_DIR / "templates"
ASSETS_DIR = MODULE_DIR / "assets"
OUTPUT_DIR = MODULE_DIR / "output"

# Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader([TEMPLATES_DIR, ASSETS_DIR]),
    autoescape=select_autoescape(['html', 'xml'])
)

def _assetify_html(html: str) -> str:
    """
    Replace CSS url() references to assets with absolute file:// paths.
    Supports both single and double quotes.
    """
    # Pattern: url('...') or url("...")
    def repl(match):
        quote = match.group(1)  # either ' or "
        inner = match.group(2)
        if inner.startswith('assets/'):
            abs_path = (ASSETS_DIR / inner).resolve()
            # file:// URL for local file
            return f'url("file://{abs_path}")'
        return match.group(0)  # unchanged
    # regex: url( optional spaces, optional quote, capture until quote, optional spaces, )
    pattern = r"""url\(\s*(['"])(assets/[^'"]+)\1\s*\)"""
    return re.sub(pattern, repl, html, flags=re.IGNORECASE)

def render(template_name: str, data: dict, output_name: str | None = None,
           width: int = 1080, height: int = 1350) -> str:
    """
    Render HTML template with data to PNG via Playwright.

    Args:
        template_name: имя шаблона (без .html), например "standings"
        data: данные для шаблона (dict)
        output_name: имя выходного файла (без расширения). Если None — генерируется автоматически.
        width: ширина в пикселях
        height: высота в пикселях

    Returns:
        путь к сгенерированному PNG-файлу
    """
    # Ensure template has .html extension
    if not template_name.endswith('.html'):
        template_file = f"{template_name}.html"
    else:
        template_file = template_name
    template_path = TEMPLATES_DIR / template_file
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Render HTML with Jinja2
    template = jinja_env.get_template(template_file)
    html_content = template.render(**data)

    # Convert asset paths to absolute file:// URLs
    html_content = _assetify_html(html_content)

    # Output path
    if not output_name:
        import time
        ts = int(time.time())
        output_name = f"{template_name}_{ts}"
    output_path = OUTPUT_DIR / f"{output_name}.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Render via Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        # Set content (no base_url param)
        page.set_content(html_content)
        # Wait for network idle and fonts
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(300)  # small extra wait for stability
        page.screenshot(path=str(output_path), full_page=False)
        browser.close()

    return str(output_path)

if __name__ == "__main__":
    # Quick test
    test_data = {
        "season": "2025/26",
        "issue": 112,
        "matchday": 12,
        "table": [
            {"position": 1, "club_name": "Bayern Munich", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/FC_Bayern_M%C3%BCnchen_logo.svg/24px-FC_Bayern_M%C3%BCnchen_logo.svg.png", "mp": 12, "w": 10, "d": 1, "l": 1, "gf": 28, "ga": 8, "pts": 31},
            {"position": 2, "club_name": "Borussia Dortmund", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Borussia_Dortmund_Logo.svg/24px-Borussia_Dortmund_Logo.svg.png", "mp": 12, "w": 8, "d": 3, "l": 1, "gf": 25, "ga": 10, "pts": 27},
            {"position": 3, "club_name": "Bayer Leverkusen", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Bayer_04_Leverkusen_logo.svg/24px-Bayer_04_Leverkusen_logo.svg.png", "mp": 12, "w": 8, "d": 2, "l": 2, "gf": 26, "ga": 12, "pts": 26},
            {"position": 4, "club_name": "RB Leipzig", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/RB_Leipzig_logo.svg/24px-RB_Leipzig_logo.svg.png", "mp": 12, "w": 7, "d": 3, "l": 2, "gf": 22, "ga": 11, "pts": 24},
            {"position": 5, "club_name": "VfB Stuttgart", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/VfB_Stuttgart_Logo.svg/24px-VfB_Stuttgart_Logo.svg.png", "mp": 12, "w": 6, "d": 4, "l": 2, "gf": 20, "ga": 15, "pts": 22},
            {"position": 6, "club_name": "Eintracht Frankfurt", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Eintracht_Frankfurt_Logo.svg/24px-Eintracht_Frankfurt_Logo.svg.png", "mp": 12, "w": 5, "d": 5, "l": 2, "gf": 18, "ga": 13, "pts": 20},
            {"position": 7, "club_name": "TSG Hoffenheim", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/TSG_Hoffenheim_logo.svg/24px-TSG_Hoffenheim_logo.svg.png", "mp": 12, "w": 5, "d": 4, "l": 3, "gf": 19, "ga": 17, "pts": 19},
            {"position": 8, "club_name": "SC Freiburg", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/SC_Freiburg_logo.svg/24px-SC_Freiburg_logo.svg.png", "mp": 12, "w": 4, "d": 5, "l": 3, "gf": 15, "ga": 16, "pts": 17},
            {"position": 9, "club_name": "Borussia Mönchengladbach", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Borussia_M%C3%B6nchengladbach_Logo.svg/24px-Borussia_M%C3%B6nchengladbach_Logo.svg.png", "mp": 12, "w": 4, "d": 4, "l": 4, "gf": 17, "ga": 19, "pts": 16},
            {"position": 10, "club_name": "1. FC Union Berlin", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/1._FC_Union_Berlin.svg/24px-1._FC_Union_Berlin.svg.png", "mp": 12, "w": 4, "d": 3, "l": 5, "gf": 13, "ga": 16, "pts": 15},
            {"position": 11, "club_name": "FC Augsburg", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/FC_Augsburg_Logo.svg/24px-FC_Augsburg_Logo.svg.png", "mp": 12, "w": 3, "d": 5, "l": 4, "gf": 14, "ga": 18, "pts": 14},
            {"position": 12, "club_name": "VfL Wolfsburg", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/VfL_Wolfsburg_Logo.svg/24px-VfL_Wolfsburg_Logo.svg.png", "mp": 12, "w": 3, "d": 4, "l": 5, "gf": 11, "ga": 17, "pts": 13},
            {"position": 13, "club_name": "Eintracht Frankfurt", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/04/Eintracht_Frankfurt_SGE_Logo.svg/24px-Eintracht_Frankfurt_SGE_Logo.svg.png", "mp": 12, "w": 3, "d": 4, "l": 5, "gf": 14, "ga": 19, "pts": 13},
            {"position": 14, "club_name": "TSG Hoffenheim", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/TSG_Hoffenheim_logo.svg/24px-TSG_Hoffenheim_logo.svg.png", "mp": 12, "w": 3, "d": 3, "l": 6, "gf": 16, "ga": 23, "pts": 12},
            {"position": 15, "club_name": "1. FC Köln", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/1._FC_K%C3%B6ln_logo_%282019%29.svg/24px-1._FC_K%C3%B6ln_logo_%282019%29.png", "mp": 12, "w": 2, "d": 4, "l": 6, "gf": 10, "ga": 21, "pts": 10},
            {"position": 16, "club_name": "VfL Bochum", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/VfL_Bochum_1848_Logo.svg/24px-VfL_Bochum_1848_Logo.svg.png", "mp": 12, "w": 2, "d": 3, "l": 7, "gf": 9, "ga": 20, "pts": 9},
            {"position": 17, "club_name": "1. FC Heidenheim", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/1._FC_Heidenheim_1846_Logo.svg/24px-1._FC_Heidenheim_1846_Logo.svg.png", "mp": 12, "w": 2, "d": 3, "l": 7, "gf": 9, "ga": 22, "pts": 9},
            {"position": 18, "club_name": "SV Darmstadt 98", "club_logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/SVDarmstadt1898_Logo.svg/24px-SVDarmstadt1898_Logo.svg.png", "mp": 12, "w": 1, "d": 3, "l": 8, "gf": 10, "ga": 29, "pts": 6}
        ]
    }
    out = render("standings", test_data, "test_standings")
    print(f"Generated: {out}")