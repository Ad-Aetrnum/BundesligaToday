"""
Bundesliga Today Bot — Config

Credentials are loaded from .env file (not committed to repository).
Copy .env.example to .env and fill in your tokens.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ============================================================
# BOT TOKENS — set in .env, never commit real values
# ============================================================
BUNDESLIGA_BOT_TOKEN = os.getenv("BUNDESLIGA_BOT_TOKEN")
if not BUNDESLIGA_BOT_TOKEN:
    raise ValueError("BUNDESLIGA_BOT_TOKEN не задан в .env файле")

EPSE1LON_BOT_TOKEN = os.getenv("EPSE1LON_BOT_TOKEN", "")
EPS_A_BOT_TOKEN = os.getenv("EPS_A_BOT_TOKEN", "")

# ============================================================
# CHAT / CHANNEL IDs — adjust for your deployment
# ============================================================
ADMIN_IDS = [1999236552]  # Replace with your admin Telegram ID
CHANNEL_ID = -1004288431568  # Replace with your channel ID
GROUP_ID = -1003949134111  # Replace with your group ID

# Premium cost (in XTR — Telegram Stars)
PREMIUM_COST = {"1 месяц": 99, "3 месяца": 249, "Год": 799}

# News page
BUNDESLIGA_NEWS = {"emoji": "🇩🇪", "page_name": "🇩🇪 Новости Бундеслиги"}

# Club → topic name mapping (Telegram group topics)
CLUB_TOPIC_NAMES = {
    "[FCB] FC Bayern München | Бавария": "Бавария",
    "[BVB] Borussia Dortmund | Боруссия Д": "Боруссия Д",
    "[RBL] RB Leipzig | РБ Лейпциг": "РБ Лейпциг",
    "[B04] Bayer 04 Leverkusen | Байер 04": "Байер 04",
    "[VFB] VfB Stuttgart | Штутгарт": "Штутгарт",
    "[SGE] Eintracht Frankfurt | Айнтрахт": "Айнтрахт",
    "[BMG] Borussia Mönchengladbach | Боруссия М": "Боруссия М",
    "[SCF] SC Freiburg | Фрайбург": "Фрайбург",
    "[SVW] SV Werder Bremen | Вердер": "Вердер",
    "[TSG] TSG 1899 Hoffenheim | Хоффенхайм": "Хоффенхайм",
    "[FCU] 1. FC Union Berlin | Унион Берлин": "Унион Берлин",
    "[HSV] Hamburger SV | Гамбург": "Гамбург",
    "[KOE] 1. FC Köln | Кёльн": "Кёльн",
    "[M05] 1. FSV Mainz 05 | Майнц 05": "Майнц 05",
    "[FCA] FC Augsburg | Аугсбург": "Аугсбург",
    "[SCP] SC Paderborn 07 | Падерборн 07": "Падерборн 07",
    "[S04] FC Schalke 04 | Шальке 04": "Шальке 04",
    "[SVE] SV Elversberg | Эльферсберг": "Эльферсберг",
}
