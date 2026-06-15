"""
Bundesliga Today — News Parser module
Комбинированный парсер: NewsAPI.org + RSS-ленты немецких спортивных сайтов
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# API ключи
import os
from dotenv import load_dotenv

_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# ── Ключевые слова для определения клуба по тексту новости ──

CLUB_KEYWORDS: dict[str, list[str]] = {
    "FCB": ["bayern", "бавария", "münchen", "munich", "muller", "müller", "kane", "musiala", "neuer", "davies", "kimmich", "gnabry", "sane", "sané", "leroy", "fcb", "fc bayern"],
    "BVB": ["dortmund", "боруссия д", "bvb", "can", "adeyemi", "brandt", "sabitzer", "kobel", "borussia dortmund"],
    "RBL": ["leipzig", "лейпциг", "rb leipzig", "simmons", "olmo", "sesko", "raum", "rbl"],
    "B04": ["leverkusen", "леверкузен", "bayer", "wirtz", "frimpong", "hincapie", "terrier", "boniface", "bayer 04"],
    "VFB": ["stuttgart", "штутгарт", "vfb", "undav", "millot", "darvich", "führich", "silas", "vfb stuttgart"],
    "SGE": ["frankfurt", "франкфурт", "eintracht", "marmoush", "koch", "trapp", "grahl", "eintracht frankfurt", "hütter", "hütter"],
    "BMG": ["gladbach", "мёнхенгладбach", "borussia m", "koaneki", "clemens", "hack", "mönchengladbach", "gladbach"],
    "SCF": ["freiburg", "фрайбург", "scf", "grifo", "egendorff", "lehmann", "sc freiburg"],
    "SVW": ["bremen", "бремен", "werder", "stage", "weiser", "demir", "burke", "werder bremen"],
    "TSG": ["hoffenheim", "хоффенхайм", "tsg", "kramaric", "bebou", "prinz", "bulter", "1899 hoffenheim", "tsg 1899"],
    "FCU": ["union berlin", "унион берлин", "union", "schäfer", "rychter", "juranovic", "1. fc union"],
    "HSV": ["hamburg", "гамбург", "hsv", "selke", "glatzel", "dompé", "reis", "hamburger sv", "vuskovic"],
    "KOE": ["köln", "кёльн", "cologne", "fc köln", "heintz", "martel", "schwirten", "1. fc köln"],
    "M05": ["mainz", "майнц", "fsv mainz", "amiri", "sieb", "da costa", "mainz 05", "1. fsv mainz"],
    "FCA": ["augsburg", "аугсбург", "fca", "essende", "mbuku", "gouweleeuw", "fc augsburg"],
    "SCP": ["paderborn", "падерборн", "sc paderborn", "platte", "bilbija", "michel", "sc paderborn 07"],
    "S04": ["schalke", "шальке", "s04", "brandt", "mohr", "lasme", "castelle", "fc schalke", "schalke 04"],
    "SVE": ["elversberg", "эльверсберг", "sv elversberg", "damar", "strickler", "schnellbacher", "sv elversberg"],
}

# Футбольные ключевые слова для фильтрации (отсеиваем баскетбол, тэннис и т.д.)
FOOTBALL_KEYWORDS = [
    "fußball", "fussball", "football", "soccer", "bundesliga", "liga",
    "tor", "goal", "spiel", "match", "trainer", "coach", "transfer",
    "verpflichtet", "signs", "joined", "wechselt", "transfermarkt",
    "nationalmannschaft", "national team", "wm", "world cup", "em", "euro",
    "champions league", "europa league", "conference league",
    "dfb-pokal", "dfb pokal", "pokal", "cup",
    "elf", "lineup", "aufstellung", "kader", "squad",
    "gastgeber", "away", "heim", "home", "spieltag", "matchday",
    "sieg", "win", "niederlage", "defeat", "remis", "draw", "unentschieden",
    "punkt", "points", "tabelle", "table", "liga", "league",
    "meister", "champion", "meister", "title",
    "abstieg", "relegation", "aufstieg", "promotion",
    "verletzung", "injury", "gesperrt", "suspended",
    "elfmeter", "penalty", "freistoss", "corner", "abseits", "offside",
    "nationalspieler", "international", "national team",
    "bayern", "dortmund", "leipzig", "leverkusen", "stuttgart",
    "frankfurt", "gladbach", "freiburg", "bremen", "hoffenheim",
    "union berlin", "hamburg", "köln", "mainz", "augsburg",
    "paderborn", "schalke", "elversberg", "wolfsburg",
]

# Анти-ключевые слова — если есть эти, новость НЕ футбольная
ANTI_FOOTBALL = [
    "basketball", "alba berlin", "tischtennis", "tennis", "handball", "volleyball",
    "eishockey", "hockey", "baseball", "cricket", "rugby", "golf",
    "schwimmen", "swimming", "leichtathletik", "athletics",
    "radfahren", "cycling", "motorsport", "formel 1", "formula 1",
    "boxen", "boxing", "kampfsport", "mma", "ufc",
    "wintersport", "ski", "skispringen",
    # Дополнительные анти-индикаторы
    "105:86", "halbfinale",  # баскетбольные счёты
]


def _is_football(text: str) -> bool:
    """Проверяет, что новость именно про футбол."""
    text_lower = text.lower()
    # Если есть анти-ключевые слова — это не футбол
    if any(kw in text_lower for kw in ANTI_FOOTBALL):
        return False
    # Должно быть хотя бы одно футбольное ключевое слово
    return any(kw in text_lower for kw in FOOTBALL_KEYWORDS)

# Категории по ключевым словам
CATEGORY_KEYWORDS = {
    "transfer": ["transfer", "подпись", "контракт", "переход", "подписал", "signs", "joined", "verpflichtet", "wechselt"],
    "injury": ["injury", "травма", "повреждение", "injury return", "вернётся", "ausfall", "verletzung"],
    "bundesliga": ["bundesliga", "матч", "тур", "гол", "match", "goal", "spieltag", "tor"],
}


def _detect_club(text: str) -> str:
    """Определяет клуб по ключевым словам в тексте."""
    text_lower = text.lower()
    best_club = ""
    best_score = 0
    for club_tag, keywords in CLUB_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_club = club_tag
    return best_club if best_score >= 1 else ""  # минимум 1 совпадение


def _detect_category(text: str) -> str:
    """Определяет категорию новости."""
    text_lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return cat
    return "bundesliga"


def _normalize_date(date_str: str) -> str:
    """Приводит дату к формату ISO 8601."""
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    # Пробуем разные форматы
    for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S GMT", "%Y-%m-%d %H:%M:%S"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()


def _make_item(title: str, description: str, url: str, source: str,
               author: str = "", image_url: str = "", published_at: str = "") -> dict:
    """Создаёт нормализованный словарь новости."""
    full_text = f"{title} {description}"
    return {
        "title": title.strip(),
        "description": (description or "")[:2000],
        "url": url,
        "source": source,
        "author": author[:100],
        "image_url": image_url,
        "published_at": _normalize_date(published_at),
        "club_tag": _detect_club(full_text),
        "category": _detect_category(full_text),
    }


# ── NewsAPI.org ──

class NewsAPIParser:
    """Парсер NewsAPI.org — агрегация новостей по Бундеслиге."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._cache: dict[str, tuple[float, list]] = {}
        self._cache_ttl = 600  # 10 мин
        self._requests_today = 0
        self._max_requests = 95  # запас от лимита 100/день

    def _cache_get(self, key: str):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.monotonic() - ts < self._cache_ttl:
                return val
            del self._cache[key]
        return None

    def _cache_set(self, key: str, val):
        self._cache[key] = (time.monotonic(), val)

    async def _fetch(self, session: aiohttp.ClientSession, endpoint: str, params: dict) -> dict:
        if self._requests_today >= self._max_requests:
            logger.warning("NewsAPI daily limit reached")
            return {}
        cache_key = hashlib.md5(f"{endpoint}{params}".encode()).hexdigest()
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        url = f"{self.BASE_URL}/{endpoint}"
        params["apiKey"] = self._api_key
        for attempt in range(3):
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    self._requests_today += 1
                    if resp.status == 200:
                        data = await resp.json()
                        self._cache_set(cache_key, data)
                        return data
                    logger.warning("NewsAPI %s → %d", endpoint, resp.status)
            except Exception as e:
                if attempt == 2:
                    logger.error("NewsAPI fetch failed: %s", e)
                    return {}
                await asyncio.sleep(1 * (attempt + 1))
        return {}

    async def search_bundesliga(self, session: aiohttp.ClientSession, query: str = "Bundesliga", page_size: int = 20) -> list[dict]:
        """Поиск новостей по запросу."""
        data = await self._fetch(session, "everything", {
            "q": query,
            "language": "de",
            "sortBy": "publishedAt",
            "pageSize": page_size,
        })
        if not data or data.get("status") != "ok":
            return []
        items = []
        for a in data.get("articles", []):
            title = a.get("title", "")
            if "[Removed]" in title:
                continue
            items.append(_make_item(
                title=title,
                description=a.get("description", ""),
                url=a.get("url", ""),
                source=a.get("source", {}).get("name", "NewsAPI"),
                author=a.get("author", ""),
                image_url=a.get("urlToImage", ""),
                published_at=a.get("publishedAt", ""),
            ))
        return items

    async def headlines(self, session: aiohttp.ClientSession) -> list[dict]:
        """Главные новости спорта из Германии."""
        data = await self._fetch(session, "top-headlines", {
            "country": "de",
            "category": "sports",
            "pageSize": 20,
        })
        if not data or data.get("status") != "ok":
            return []
        items = []
        for a in data.get("articles", []):
            title = a.get("title", "")
            if "[Removed]" in title:
                continue
            items.append(_make_item(
                title=title,
                description=a.get("description", ""),
                url=a.get("url", ""),
                source=a.get("source", {}).get("name", "NewsAPI"),
                author=a.get("author", ""),
                image_url=a.get("urlToImage", ""),
                published_at=a.get("publishedAt", ""),
            ))
        return items


# ── RSS Parser ──

class RSSParser:
    """Парсер RSS-лент немецких спортивных сайтов."""

    FEEDS = {
        "kicker_bundesliga": "https://www.kicker.de/bundesliga/rss",
        "kicker_transfers": "https://www.kicker.de/transfermarkt/rss",
        "bundesliga_official": "https://www.bundesliga.com/de/bundesliga/rss/news",
        "goal_com": "https://www.goal.com/feeds/en/news",
        "sport1": "https://www.sport1.de/news/fussball/bundesliga/rss",
        "transfermarkt": "https://www.transfermarkt.de/rss/news",
        "fcn_news": "https://www.news.de/sport/fussball/bundesliga/rss",
        "spiegel_sport": "https://www.spiegel.de/sport/fussball/index.rss",
    }

    def __init__(self):
        self._cache: dict[str, tuple[float, list]] = {}
        self._cache_ttl = 300  # 5 мин
        self._ns = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "media": "http://search.yahoo.com/mrss/",
        }

    def _cache_get(self, key: str):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.monotonic() - ts < self._cache_ttl:
                return val
            del self._cache[key]
        return None

    def _cache_set(self, key: str, val):
        self._cache[key] = (time.monotonic(), val)

    async def _fetch_feed(self, session: aiohttp.ClientSession, name: str, url: str) -> list[dict]:
        """Загружает и парсит одну RSS-ленту."""
        cached = self._cache_get(name)
        if cached is not None:
            return cached
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15),
                                   headers={"User-Agent": "Mozilla/5.0 (compatible; BundesligaBot/1.0)"}) as resp:
                if resp.status != 200:
                    logger.debug("RSS %s → %d", name, resp.status)
                    return []
                content = await resp.text()
        except Exception as e:
            logger.debug("RSS %s fetch error: %s", name, e)
            return []

        items = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            # Ищем item элементы
            for item_el in root.iter("item"):
                title_el = item_el.find("title")
                link_el = item_el.find("link")
                desc_el = item_el.find("description")
                pub_el = item_el.find("pubDate") or item_el.find("date") or item_el.find("{%s}date" % self._ns["dc"])
                author_el = item_el.find("author") or item_el.find("{%s}creator" % self._ns["dc"])
                # media:content или media:thumbnail для картинки
                img_el = item_el.find("{%s}content" % self._ns["media"]) or item_el.find("{%s}thumbnail" % self._ns["media"])
                image_url = ""
                if img_el is not None:
                    image_url = img_el.get("url", "")
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else ""
                desc = ""
                if desc_el is not None and desc_el.text:
                    import html as html_mod
                    desc = html_mod.unescape(desc_el.text).strip()
                    # Убираем HTML-теги
                    import re
                    desc = re.sub(r'<[^>]+>', '', desc)
                pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ""
                author = author_el.text.strip() if author_el is not None and author_el.text else ""
                if title and link:
                    items.append(_make_item(
                        title=title,
                        description=desc[:500],
                        url=link,
                        source=name,
                        author=author,
                        image_url=image_url,
                        published_at=pub_date,
                    ))
        except ET.ParseError as e:
            logger.warning("RSS parse error %s: %s", name, e)
        except Exception as e:
            logger.warning("RSS process error %s: %s", name, e)

        self._cache_set(name, items)
        return items

    async def fetch_all(self, session: aiohttp.ClientSession) -> list[dict]:
        """Загружает все RSS-ленты параллельно."""
        tasks = [self._fetch_feed(session, name, url) for name, url in self.FEEDS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_items = []
        for r in results:
            if isinstance(r, list):
                all_items.extend(r)
            elif isinstance(r, Exception):
                logger.debug("RSS feed error: %s", r)
        return all_items


# ── Верхнеуровневая функция ──

async def fetch_all_news() -> list[dict]:
    """
    Собирает новости из всех источников.
    Возвращает список нормализованных новостей.
    """
    all_items: list[dict] = []

    async with aiohttp.ClientSession() as session:
        # 1. NewsAPI — 2 запроса (headlines + bundesliga search)
        if NEWS_API_KEY:
            newsapi = NewsAPIParser(NEWS_API_KEY)
            try:
                headlines = await newsapi.headlines(session)
                all_items.extend(headlines)
                logger.info("NewsAPI headlines: %d", len(headlines))
            except Exception as e:
                logger.error("NewsAPI headlines error: %s", e)
            try:
                articles = await newsapi.search_bundesliga(session)
                all_items.extend(articles)
                logger.info("NewsAPI search: %d", len(articles))
            except Exception as e:
                logger.error("NewsAPI search error: %s", e)

        # 2. RSS — все ленты параллельно
        rss = RSSParser()
        try:
            rss_items = await rss.fetch_all(session)
            all_items.extend(rss_items)
            logger.info("RSS total: %d", len(rss_items))
        except Exception as e:
            logger.error("RSS error: %s", e)

    logger.info("Total news fetched: %d", len(all_items))
    # Фильтруем не-футбольные новости
    football_items = [i for i in all_items if _is_football(f"{i['title']} {i['description']}")]
    logger.info("Football news: %d (filtered %d non-football)", len(football_items), len(all_items) - len(football_items))
    return football_items


def fetch_all_news_sync() -> list[dict]:
    """Синхронная обёртка для использования из бота/крона."""
    return asyncio.run(fetch_all_news())