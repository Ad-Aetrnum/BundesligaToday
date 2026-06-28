"""
Bundesliga Today Bot — Database module
"""
import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE = os.path.join(os.path.dirname(__file__), "bundesliga_today.db")


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    """Создаёт/обновляет таблицы БД и заполняет начальные данные."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT,
            first_name    TEXT,
            last_name     TEXT,
            language_code TEXT DEFAULT 'ru',
            is_premium    INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now')),
            last_active   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS clubs (
            club_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT UNIQUE NOT NULL,
            short_name    TEXT,
            city          TEXT,
            stadium       TEXT,
            capacity      INTEGER,
            founded       INTEGER,
            team_api_id   INTEGER,
            emoji         TEXT DEFAULT '⚽',
            page_name     TEXT,
            sort_order    INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS club_news (
            news_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            club_name     TEXT NOT NULL,
            title         TEXT NOT NULL,
            body          TEXT,
            published_at  TEXT DEFAULT (datetime('now')),
            is_active     INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS club_trophies (
            trophy_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            club_name     TEXT NOT NULL,
            bl_titles     INTEGER DEFAULT 0,
            bl_last       INTEGER,
            dfb_pokals    INTEGER DEFAULT 0,
            dfb_pokal_last INTEGER,
            champions_league INTEGER DEFAULT 0,
            cl_last       INTEGER,
            europa_league INTEGER DEFAULT 0,
            el_last       INTEGER,
            conference_league INTEGER DEFAULT 0,
            ecl_last      INTEGER,
            super_cups    INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            club       TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, club)
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            club       TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, club)
        );

        CREATE TABLE IF NOT EXISTS matches_cache (
            match_id    INTEGER PRIMARY KEY,
            league      TEXT,
            season      TEXT,
            matchday    INTEGER,
            home_team   TEXT,
            away_team   TEXT,
            home_score  INTEGER,
            away_score  INTEGER,
            status      TEXT,
            kickoff_utc TEXT,
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_sub_user ON subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_fav_user ON favorites(user_id);
        CREATE INDEX IF NOT EXISTS idx_match_status ON matches_cache(status);
        CREATE INDEX IF NOT EXISTS idx_news_club ON club_news(club_name);

        -- Универсальная таблица новостей
        CREATE TABLE IF NOT EXISTS news (
            news_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            summary       TEXT DEFAULT '',          -- краткая выжимка
            description   TEXT,                     -- полное описание/контент
            url           TEXT UNIQUE,
            source        TEXT DEFAULT '',
            author        TEXT DEFAULT '',
            image_url     TEXT DEFAULT '',
            image_type    TEXT DEFAULT 'og',        -- og / generated / manual
            type          TEXT DEFAULT '',          -- match/transfer/injury/contract/interview/coach/standing/rumor/announcement
            topic         TEXT DEFAULT '',          -- bundesliga/world_cup/national_team/champions_league/europa_league/dfb_pokal/club/german_abroad
            priority      INTEGER DEFAULT 5,        -- 1-10
            status        TEXT DEFAULT 'draft',     -- draft/approved/published/archived
            published_at  TEXT,
            fetched_at    TEXT DEFAULT (datetime('now')),
            is_active     INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_news_type ON news(type);
        CREATE INDEX IF NOT EXISTS idx_news_topic ON news(topic);
        CREATE INDEX IF NOT EXISTS idx_news_priority ON news(priority DESC);
        CREATE INDEX IF NOT EXISTS idx_news_status ON news(status);
        CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at DESC);

        -- Many-to-many: новости ↔ клубы
        CREATE TABLE IF NOT EXISTS news_clubs (
            news_id       INTEGER NOT NULL,
            club_tag      TEXT NOT NULL,            -- FCB, BVB и т.д.
            PRIMARY KEY (news_id, club_tag),
            FOREIGN KEY (news_id) REFERENCES news(news_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_news_clubs_tag ON news_clubs(club_tag);

        -- Many-to-many: новости ↔ сущности (игроки, тренеры, турниры)
        CREATE TABLE IF NOT EXISTS news_entities (
            news_id       INTEGER NOT NULL,
            entity_type   TEXT NOT NULL,            -- club / player / coach / competition
            entity_id     TEXT NOT NULL,            -- имя или ID сущности
            PRIMARY KEY (news_id, entity_type, entity_id),
            FOREIGN KEY (news_id) REFERENCES news(news_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_news_entities ON news_entities(entity_type, entity_id);
    """)

    _seed_clubs(db)
    _seed_trophies(db)
    _seed_news(db)

    db.commit()
    db.close()
    logger.info("Database initialized.")


def _seed_clubs(db):
    """Заполняет таблицу клубов начальными данными (если пустая)."""
    existing = db.execute("SELECT COUNT(*) as n FROM clubs").fetchone()["n"]
    if existing > 0:
        return

    clubs = [
        (1, "FC Bayern München",        "FCB", "Мюнхен",           "Allianz Arena",                    75000, 1900, 40,  "🔴⚪", "🔴 Бавария",        1),
        (2, "Borussia Dortmund",        "BVB", "Дортмунд",         "Signal Iduna Park",               81365, 1909, 7,   "🟡⚫", "🟡 Боруссия Д",     2),
        (3, "RB Leipzig",               "RBL", "Лейпциг",          "Red Bull Arena",                  47800, 2009, 1635,"🔴⚪", "🔴 РБ Лейпциг",     3),
        (4, "Bayer 04 Leverkusen",     "B04", "Леверкузен",       "BayArena",                        30210, 1904, 6,   "🔴⚫", "🔴 Байер 04",       4),
        (5, "VfB Stuttgart",            "VFB", "Штутгарт",         "MHPArena",                        60000, 1893, 16,  "🔴⚪", "🔴 Штутгарт",        5),
        (6, "Eintracht Frankfurt",      "SGE", "Франкфурт-на-Майне","Deutsche Bank Park",              58000, 1899, 91,  "🔴⚫", "🔴 Айнтрахт",       6),
        (7, "Borussia Mönchengladbach", "BMG", "Мёнхенгладбах",   "Borussia-Park",                   54000, 1900, 87,  "⚫🔴", "⚫ Боруссия М",     7),
        (8, "SC Freiburg",              "SCF", "Фрайбург-им-Брайсгау","Europa-Park Stadion",            34700, 1904, 112, "🔴⚫", "🔴 Фрайбург",       8),
        (9, "SV Werder Bremen",         "SVW", "Бремен",           "Weserstadion",                    42000, 1899, 134, "🟢⚪", "🟢 Вердер",          9),
        (10, "TSG 1899 Hoffenheim",     "TSG", "Зинсхайм",         "PreZero Arena",                   30150, 1899, 175, "🔵⚪", "🔵 Хоффенхайм",     10),
        (11, "1. FC Union Berlin",      "FCU", "Берлин",           "Stadion An der Alten Försterei",  22000, 1966, 80,  "🔴⚪", "🔴 Унион Берлин",   11),
        (12, "Hamburger SV",            "HSV", "Гамбург",          "Volksparkstadion",                57000, 1887, 100, "🔵⚪", "🔵 Гамбург",        12),
        (13, "1. FC Köln",              "KOE", "Кёльн",            "RheinEnergieStadion",            50000, 1948, 65,  "🔴⚪", "🔴 Кёльн",          13),
        (14, "1. FSV Mainz 05",         "M05", "Майнц",            "MEWA Arena",                      34000, 1905, 81,  "🔴⚪", "🔴 Майнц 05",       14),
        (15, "FC Augsburg",             "FCA", "Аугсбург",         "WWK Arena",                       30660, 1907, 95,  "🔴🟢", "🔴 Аугсбург",       15),
        (16, "SC Paderborn 07",         "SCP", "Падерборн",        "Home Deluxe Arena",               15000, 1907, 253, "⚫⚪", "⚫ Падерборн 07",   16),
        (17, "FC Schalke 04",           "S04", "Гельзенкирхен",   "Veltins-Arena",                   62000, 1904, 327, "🔵⚪", "🔵 Шальке 04",     17),
        (18, "SV Elversberg",           "SVE", "Шпайерен-Эльверсберг","Waldstadion Kaiserlinde",       10000, 1907, 841, "🔴🔵", "🔴 Эльферсберг",   18),
    ]

    db.executemany("""
        INSERT OR IGNORE INTO clubs
            (club_id, name, short_name, city, stadium, capacity, founded, team_api_id, emoji, page_name, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, clubs)
    logger.info("Seeded %d clubs.", len(clubs))


def _seed_trophies(db):
    """Заполняет трофеи (если пустая)."""
    existing = db.execute("SELECT COUNT(*) as n FROM club_trophies").fetchone()["n"]
    if existing > 0:
        return

    trophies = [
        ("FC Bayern München",        35, 2023, 20, 2020, 6, 2020, 1, 1996, 0, None, 10),
        ("Borussia Dortmund",        8, 2012, 5,  2021, 1, 1997, 1, 1966, 0, None,  6),
        ("RB Leipzig",               0, None, 2,  2023, 0, None, 0, None, 0, None,  0),
        ("Bayer 04 Leverkusen",      1, 2024, 2,  2024, 0, None, 1, 1988, 0, None,  1),
        ("VfB Stuttgart",            5, 2007, 4,  1997, 0, None, 0, None, 0, None,  1),
        ("Eintracht Frankfurt",      1, 1959, 5,  2018, 0, None, 2, 2022, 0, None,  0),
        ("Borussia Mönchengladbach", 5, 1977, 3,  1995, 0, None, 2, 1979, 0, None,  1),
        ("SC Freiburg",              0, None, 0,  None, 0, None, 0, None, 0, None,  0),
        ("SV Werder Bremen",         4, 2004, 6,  2009, 0, None, 1, 1992, 0, None,  3),
        ("TSG 1899 Hoffenheim",      0, None, 0,  None, 0, None, 0, None, 0, None,  0),
        ("1. FC Union Berlin",       0, None, 0,  None, 0, None, 0, None, 0, None,  0),
        ("Hamburger SV",             6, 1983, 3,  1987, 1, 1983, 1, 1977, 0, None,  2),
        ("1. FC Köln",               3, 1978, 4,  1983, 0, None, 0, None, 0, None,  0),
        ("1. FSV Mainz 05",          0, None, 0,  None, 0, None, 0, None, 0, None,  0),
        ("FC Augsburg",              0, None, 0,  None, 0, None, 0, None, 0, None,  0),
        ("SC Paderborn 07",          0, None, 0,  None, 0, None, 0, None, 0, None,  0),
        ("FC Schalke 04",            7, 1958, 5,  2011, 0, None, 1, 1997, 0, None,  1),
        ("SV Elversberg",            0, None, 0,  None, 0, None, 0, None, 0, None,  0),
    ]

    db.executemany("""
        INSERT OR IGNORE INTO club_trophies
            (club_name, bl_titles, bl_last, dfb_pokals, dfb_pokal_last,
             champions_league, cl_last, europa_league, el_last,
             conference_league, ecl_last, super_cups)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, trophies)
    logger.info("Seeded %d trophy records.", len(trophies))


def _seed_news(db):
    """Заполняет новости (если пустая)."""
    existing = db.execute("SELECT COUNT(*) as n FROM club_news").fetchone()["n"]
    if existing > 0:
        return

    news = [
        ("FC Bayern München", "Бавария — чемпион Бундеслиги 2025/26!", "Мюнхенцы в очередной раз доказали своё превосходство в немецком футболе.", "2025-05-24"),
        ("FC Bayern München", "Подписан новый контракт с Томасом Мюллером", "Легенда клуба продолжает карьеру в Баварии ещё на один сезон.", "2025-05-20"),
        ("FC Bayern München", "Подготовка к сезону 2026/27 идёт полным ходом", "Команда проводит предсезонные сборы и готовится к новым вызовам.", "2025-05-15"),
        ("Borussia Dortmund", "Боруссия Д готовится к новому сезону", "Дортмундцы активно работают на трансферном рынке.", "2025-05-24"),
        ("Borussia Dortmund", "Новый тренерский штаб утверждён", "Клуб объявил о продлении контракта с главным тренером.", "2025-05-18"),
        ("RB Leipzig", "РБ Лейпциг усиливается к сезону 2026/27", "Лейпциг активно ищет новых игроков для усиления состава.", "2025-05-22"),
        ("RB Leipzig", "Молодёжная академия выпускает новых талантов", "Очередной выпуск академии готов проявить себя в основном составе.", "2025-05-10"),
        ("VfB Stuttgart", "Штутгарт сохраняет ключевых игроков", "Клуб договорился о продлении контрактов с лидерами команды.", "2025-05-24"),
        ("VfB Stuttgart", "Подготовка к Лиге Чемпионов", "Штутгарт готовится к европейским вызовам в новом сезоне.", "2025-05-12"),
        ("TSG 1899 Hoffenheim", "Хоффенхайм ищет нового нападающего", "Тренерский штаб недоволен результативностью атаки.", "2025-05-20"),
        ("Bayer 04 Leverkusen", "Байер 04 — действующий чемпион!", "Леверкузенцы защитили титул чемпионов Бундеслиги.", "2025-05-24"),
        ("Bayer 04 Leverkusen", "Винисиус Жуниор остаётся в команде", "Звёздный полузащитник подписал новый долгосрочный контракт.", "2025-05-15"),
        ("Eintracht Frankfurt", "Айнтрахт готов к еврокубкам", "Франкфуртцы рассчитывают на успешную кампанию в Лиге Европы.", "2025-05-22"),
        ("Eintracht Frankfurt", "Продажа ключевого игрока", "Клуб подтвердил перевод звёздного форварда в зарубежный клуб.", "2025-05-14"),
        ("SV Werder Bremen", "Вердер возвращается в элиту!", "Бременцы обеспечили себе место в Бундеслиге на следующий сезон.", "2025-05-20"),
        ("Hamburger SV", "Гамбург — возвращение легенды!", "HSV вернулся в Бундеслигу после долгого отсутствия. Город празднует!", "2025-05-24"),
        ("Hamburger SV", "Продажи абонементов бьют рекорды", "Volksparkstadion будет заполнен до отказа в каждом матче.", "2025-05-15"),
        ("1. FC Köln", "Кёльн укрепляет оборону", "1. FC Köln подписал нового центрального защитника.", "2025-05-22"),
        ("SC Paderborn 07", "Падерборн 07 — в Бундеслиге!", "SC Paderborn 07 вышел в Бундеслигу через стыковые матчи против Вольфсбурга!", "2025-05-24"),
        ("FC Schalke 04", "Шальке 04 — в Бундеслиге!", "Легендарный клуб вернулся в элитный дивизион! Чемпион 2. Бундеслиги 2025/26.", "2025-05-24"),
        ("FC Schalke 04", "Veltins-Arena ждёт возвращения элиты", "Стадион на 62 000 мест готов к матчам Бундеслиги.", "2025-05-15"),
        ("SV Elversberg", "Эльферсберг — в Бундеслиге!", "SV Elversberg впервые в истории вышел в Бундеслигу! Прямое повышение из 2. Бундеслиги.", "2025-05-24"),
        ("SV Elversberg", "Клуб из города с населением 12 000 — в элите!", "Историческое достижение для маленького клуба.", "2025-05-22"),
        ("Borussia Mönchengladbach", "Боруссия М ищет голкипера", "После ухода основного вратаря клуб ищет замену.", "2025-05-20"),
        ("1. FC Union Berlin", "Унион готов к новому сезону", "Берлинцы планируют сделать рывок в борьбе за еврокубки.", "2025-05-18"),
    ]

    db.executemany("""
        INSERT OR IGNORE INTO club_news (club_name, title, body, published_at)
        VALUES (?, ?, ?, ?)
    """, news)
    logger.info("Seeded %d news items.", len(news))


# ── Функции для работы с данными ──

def get_all_clubs() -> list[dict]:
    """Возвращает все клубы, отсортированные по sort_order."""
    db = get_db()
    rows = db.execute("SELECT * FROM clubs ORDER BY sort_order, name").fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_club(name: str) -> dict | None:
    """Возвращает данные клуба по имени."""
    db = get_db()
    row = db.execute("SELECT * FROM clubs WHERE name = ?", (name,)).fetchone()
    db.close()
    return dict(row) if row else None


def get_featured_clubs() -> dict:
    """Возвращает словарь {name: {emoji, full_name}} для FEATURED_CLUBS."""
    db = get_db()
    rows = db.execute(
        "SELECT name, emoji FROM clubs ORDER BY sort_order"
    ).fetchall()
    db.close()
    return {r["name"]: {"emoji": r["emoji"], "full_name": r["name"]} for r in rows}


def get_trophies(club_name: str) -> dict | None:
    """Возвращает трофеи клуба."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM club_trophies WHERE club_name = ?", (club_name,)
    ).fetchone()
    db.close()
    return dict(row) if row else None


def get_coach(club_name: str) -> dict | None:
    """Возвращает данные тренера клуба."""
    db = get_db()
    row = db.execute(
        "SELECT name, age FROM coaches WHERE club_name = ?", (club_name,)
    ).fetchone()
    db.close()
    return dict(row) if row else None


def get_news(club_name: str, limit: int = 10) -> list[dict]:
    """Возвращает новости клуба."""
    db = get_db()
    rows = db.execute(
        """SELECT * FROM club_news 
           WHERE club_name = ? AND is_active = 1 
           ORDER BY published_at DESC LIMIT ?""",
        (club_name, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_squad(club_name: str) -> dict:
    """Возвращает состав клуба, сгруппированный по позициям."""
    db = get_db()
    
    gk = db.execute(
        "SELECT * FROM players WHERE club_name = ? AND position = 'GK' ORDER BY number",
        (club_name,)
    ).fetchall()
    
    df = db.execute(
        "SELECT * FROM players WHERE club_name = ? AND position = 'DF' ORDER BY number",
        (club_name,)
    ).fetchall()
    
    mf = db.execute(
        "SELECT * FROM players WHERE club_name = ? AND position = 'MF' ORDER BY number",
        (club_name,)
    ).fetchall()
    
    fw = db.execute(
        "SELECT * FROM players WHERE club_name = ? AND position = 'FW' ORDER BY number",
        (club_name,)
    ).fetchall()
    
    total = db.execute(
        "SELECT COUNT(*) as n FROM players WHERE club_name = ?",
        (club_name,)
    ).fetchone()["n"]
    
    foreigners = db.execute(
        "SELECT COUNT(*) as n FROM players WHERE club_name = ? AND is_foreigner = 1",
        (club_name,)
    ).fetchone()["n"]
    
    db.close()
    
    return {
        "gk": [dict(r) for r in gk],
        "df": [dict(r) for r in df],
        "mf": [dict(r) for r in mf],
        "fw": [dict(r) for r in fw],
        "total": total,
        "foreigners": foreigners,
    }


def get_season_standings(season: str = "2025-26") -> list[dict]:
    """Возвращает итоговую таблицу сезона из БД."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM season_standings WHERE season = ? ORDER BY position",
        (season,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_friendlies(club_name: str, limit: int = 10) -> list[dict]:
    """Возвращает товарищеские матчи клуба из БД.
    Поддерживает как чистые имена (FC Bayern München), так и формат [FCB] FC Bayern München | Бавария.
    """
    db = get_db()
    # Если передан формат [ABBR] Name | Russian — извлекаем немецкое имя
    search_name = club_name
    if "|" in search_name:
        search_name = search_name.split("|")[0].strip()
    if "] " in search_name:
        search_name = search_name.split("] ")[-1].strip()
    
    rows = db.execute(
        """SELECT * FROM friendlies 
           WHERE club_name = ? OR club_name LIKE ?
           ORDER BY match_date ASC 
           LIMIT ?""",
        (search_name, search_name + "%", limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── Функции для работы с новостями ──

def translate_news_item(item: dict) -> dict:
    """Переводит title и description новости на русский. Если перевод не удался — оставляем как есть."""
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source='auto', target='ru')
        title = item.get("title", "")
        desc = item.get("description", "")
        item["title"] = t.translate(title)[:500] if title else title
        item["description"] = t.translate(desc)[:2000] if desc else desc
    except Exception as e:
        logger.warning("translate skip: %s", e)
    return item


def save_news(items: list[dict]) -> int:
    """
    Сохраняет список новостей в таблицу news + news_clubs + news_entities.
    Каждая новость автоматически переводится на русский.
    Возвращает количество добавленных новостей.
    """
    db = get_db()
    added = 0
    for item in items:
        try:
            # Переводим на русский
            item = translate_news_item(item)
            # Определяем priority по умолчанию из типа
            default_priority = {
                "match": 9, "transfer": 8, "coach": 8, "standing": 9,
                "injury": 7, "contract": 7, "announcement": 6,
                "interview": 5, "rumor": 4,
            }
            ntype = item.get("type", "")
            priority = item.get("priority", default_priority.get(ntype, 5))
            # Определяем topic из категории (обратная совместимость)
            topic = item.get("topic", "")
            if not topic:
                cat = item.get("category", "")
                topic_map = {
                    "bundesliga": "bundesliga", "transfer": "bundesliga",
                    "injury": "club", "general": "bundesliga",
                }
                topic = topic_map.get(cat, "bundesliga")
            # Вставляем новость
            db.execute("""INSERT OR IGNORE INTO news 
                (title, summary, description, url, source, author, image_url, image_type,
                 type, topic, priority, status, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item.get("title", "")[:500],
                 item.get("summary", "")[:300],
                 item.get("description", "")[:2000],
                 item.get("url", "")[:500],
                 item.get("source", "")[:100],
                 item.get("author", "")[:100],
                 item.get("image_url", "")[:500],
                 item.get("image_type", "og"),
                 ntype, topic, priority,
                 item.get("status", "draft"),
                 item.get("published_at", "")))
            if db.total_changes == 0:
                # Дубликат по URL — пропускам
                continue
            news_id = db.execute("SELECT news_id FROM news WHERE url = ?",
                                 (item.get("url", "")[:500],)).fetchone()["news_id"]
            # Привязка к клубам
            club_tags = item.get("club_tags", [])
            if not club_tags and item.get("club_tag"):
                club_tags = [item["club_tag"]]
            for tag in club_tags:
                db.execute("INSERT OR IGNORE INTO news_clubs (news_id, club_tag) VALUES (?, ?)",
                           (news_id, tag[:10]))
            # Сущности
            entities = item.get("entities", [])
            for etype, eid in entities:
                db.execute("INSERT OR IGNORE INTO news_entities (news_id, entity_type, entity_id) VALUES (?, ?, ?)",
                           (news_id, etype, eid[:100]))
            added += 1
        except Exception as e:
            logger.debug("news skip: %s", e)
    db.commit()
    db.close()
    return added


def get_news(limit: int = 20, ntype: str = None, topic: str = None,
             status: str = "published", min_priority: int = 0) -> list[dict]:
    """Возвращает новости из БД с фильтрацией."""
    db = get_db()
    query = "SELECT * FROM news WHERE is_active = 1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if ntype:
        query += " AND type = ?"
        params.append(ntype)
    if topic:
        query += " AND topic = ?"
        params.append(topic)
    if min_priority:
        query += " AND priority >= ?"
        params.append(min_priority)
    query += " ORDER BY priority DESC, published_at DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(query, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_club_news(club_tag: str, limit: int = 10, min_priority: int = 0) -> list[dict]:
    """Возвращает новости по конкретному клубу через news_clubs."""
    db = get_db()
    query = """SELECT n.* FROM news n
               INNER JOIN news_clubs nc ON n.news_id = nc.news_id
               WHERE n.is_active = 1 AND nc.club_tag = ?"""
    params = [club_tag]
    if min_priority:
        query += " AND n.priority >= ?"
        params.append(min_priority)
    query += " ORDER BY n.priority DESC, n.published_at DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(query, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_bundesliga_news(limit: int = 15, min_priority: int = 5) -> list[dict]:
    """Возвращает новости для общей ленты Бундеслиги."""
    db = get_db()
    rows = db.execute("""SELECT * FROM news 
        WHERE is_active = 1 AND status = 'published'
        AND topic IN ('bundesliga','world_cup','national_team','champions_league','europa_league')
        AND priority >= ?
        ORDER BY priority DESC, published_at DESC LIMIT ?""",
        (min_priority, limit)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def should_publish_to_channel(news_item: dict) -> bool:
    """Правило: публиковать ли новость в канал."""
    priority = news_item.get("priority", 5)
    ntype = news_item.get("type", "")
    if priority >= 8:
        return True
    if ntype in ("match", "transfer", "coach", "standing") and priority >= 7:
        return True
    return False


def update_news_status(news_id: int, status: str):
    """Обновляет статус новости."""
    db = get_db()
    db.execute("UPDATE news SET status = ? WHERE news_id = ?", (status, news_id))
    db.commit()
    db.close()


def cleanup_news(days: int = 30):
    """Удаляет новости старше N дней."""
    db = get_db()
    db.execute("DELETE FROM news WHERE published_at < datetime('now', ?)", (f"-{days} days",))
    db.commit()
    db.close()
