"""
Bundesliga Today — Основной модуль бота
Telegram-бот для фанатов немецкого футбола
"""
import asyncio
import logging
import os
import textwrap

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, PreCheckoutQuery
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import (
    BUNDESLIGA_BOT_TOKEN as BOT_TOKEN, ADMIN_IDS, CHANNEL_ID, GROUP_ID,
    PREMIUM_COST, BUNDESLIGA_NEWS, CLUB_TOPIC_NAMES,
)
from database import (init_db, get_db, get_all_clubs, get_club, get_featured_clubs,
                     get_trophies, get_news as db_get_news, get_club_news as db_get_club_news,
                     get_squad, get_coach, save_news, cleanup_news)
from parsers import get_table_formatted, get_matchday_formatted
from news_parser import fetch_all_news, fetch_all_news_sync
from table_generator import generate_tour_image, OUTPUT_PATH

# ── Логирование ─────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bundesliga_today")

# ── Инициализация ───────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ── Хелперы ────────────────────────────────────────────────────

def register_user(user_id: int, username: str, first_name: str, last_name: str, lang: str):
    db = get_db()
    db.execute("""
        INSERT INTO users (user_id, username, first_name, last_name, language_code)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            last_active=datetime('now')
    """, (user_id, username, first_name, last_name, lang))
    db.commit()
    db.close()


def club_emoji(club_name: str) -> str:
    c = get_club(club_name)
    if c:
        # Извлекаем эмодзи из названия (первые 2 символа)
        name = c.get("name", "")
        if len(name) >= 2:
            return name[:2]
    return "⚽"


# ── Клавиатуры ─────────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Таблица", callback_data="table")],
        [InlineKeyboardButton(text="⚽ Текущий тур", callback_data="matchday"),
         InlineKeyboardButton(text="📅 Расписание", callback_data="schedule")],
        [InlineKeyboardButton(text="🏟️ Страницы клубов", callback_data="pages")],
        [InlineKeyboardButton(text="🔔 Подписки", callback_data="subs"),
         InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites")],
        [InlineKeyboardButton(text="📈 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="💎 Premium", callback_data="premium")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")],
    ])


def clubs_kb(action: str = "sub") -> InlineKeyboardMarkup:
    clubs = get_all_clubs()
    buttons = []
    row = []
    for i, club in enumerate(clubs, 1):
        emoji = club.get("emoji", "⚽")
        name = club["name"]
        row.append(InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"{action}_club:{name}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def pages_kb() -> InlineKeyboardMarkup:
    featured = get_featured_clubs()
    buttons = []
    for name, data in featured.items():
        buttons.append([InlineKeyboardButton(text=data["full_name"], callback_data=f"page:{name}")])
    buttons.append([InlineKeyboardButton(text=BUNDESLIGA_NEWS["page_name"], callback_data="page:news")])
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def club_page_kb(club: str) -> InlineKeyboardMarkup:
    topic_name = CLUB_TOPIC_NAMES.get(club, club)
    buttons = [
        [InlineKeyboardButton(text="📰 Новости", callback_data=f"club_news:{club}")],
        [InlineKeyboardButton(text="📋 Информация", callback_data=f"club_info:{club}")],
        [InlineKeyboardButton(text="👥 Состав", callback_data=f"club_squad:{club}")],
        [InlineKeyboardButton(text="📅 Матчи клуба", callback_data=f"club_matches:{club}")],
        [InlineKeyboardButton(text="📈 Статистика", callback_data=f"club_stats:{club}")],
        [InlineKeyboardButton(text="🏆 Достижения", callback_data=f"club_trophies:{club}")],
        [InlineKeyboardButton(text=f"💬 Обсуждение ({topic_name})", callback_data=f"club_discuss:{club}")],
        [InlineKeyboardButton(text="🔔 Подписаться", callback_data=f"sub_club:{club}")],
        [InlineKeyboardButton(text="« Назад", callback_data="pages")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def news_kb(club: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data=f"page:{club}")],
    ])


def bundesliga_news_kb() -> InlineKeyboardMarkup:
    """Клавиатура для общих новостей Бундеслиги — только кнопка Назад."""
    from config import BUNDESLIGA_NEWS
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data="pages")],
    ])


def premium_kb() -> InlineKeyboardMarkup:
    buttons = []
    for label, price in PREMIUM_COST.items():
        buttons.append([InlineKeyboardButton(
            text=f"💎 {label} — {price} ⭐",
            callback_data=f"buy_premium:{label}:{price}"
        )])
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Handlers: команды ──────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message):
    register_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
        lang=message.from_user.language_code or "ru",
    )
    text = textwrap.dedent("""\
        🇩🇪 *Bundesliga Today* — твой гид по немецкому футболу!

        Что я умею:
        📊 Актуальная таблица Бундеслиги
        ⚽ Результаты матчей и расписание
        🔔 Подписка на матчи любимых клубов
        📈 Статистика команд и игроков
        💎 Premium — расширенная аналитика

        Выбери раздел в меню 👇
    """)
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("📍 *Главное меню*", reply_markup=main_menu_kb())


@router.message(Command("table"))
async def cmd_table(message: Message):
    msg = await message.answer("⏳ Загружаю таблицу...")
    try:
        table = await get_table_formatted()
        await msg.edit_text(table, reply_markup=main_menu_kb())
    except Exception as e:
        logger.error("/table error: %s", e)
        await msg.edit_text("⚠️ Ошибка загрузки таблицы. Попробуйте позже.")


@router.message(Command("matchday"))
async def cmd_matchday(message: Message):
    msg = await message.answer("⏳ Загружаю текущий тур...")
    try:
        data = await get_matchday_formatted()
        await msg.edit_text(data, reply_markup=main_menu_kb())
    except Exception as e:
        logger.error("/matchday error: %s", e)
        await msg.edit_text("⚠️ Ошибка загрузки тура. Попробуйте позже.")


# ── Handlers: callback ──────────────────────────────────────────

@router.callback_query(F.data == "table")
async def cb_table(callback: CallbackQuery):
    await callback.answer()
    try:
        from table_generator import OUTPUT_PATH
        if OUTPUT_PATH.exists():
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=FSInputFile(str(OUTPUT_PATH)),
                caption="📊 *Таблица Бундеслиги 2025/26*",
                parse_mode="Markdown",
                reply_markup=main_menu_kb(),
            )
        else:
            await callback.message.edit_text("⏳ Таблица ещё не сгенерирована. Подождите немного.")
    except Exception as e:
        logger.error("cb_table error: %s", e)
        await callback.answer("⚠️ Ошибка загрузки таблицы", show_alert=True)


@router.callback_query(F.data == "matchday")
async def cb_matchday(callback: CallbackQuery):
    await callback.answer("Загружаю...")
    try:
        data = await get_matchday_formatted()
        await callback.message.edit_text(data, reply_markup=main_menu_kb())
    except Exception as e:
        logger.error("cb_matchday error: %s", e)
        await callback.message.edit_text("⚠️ Ошибка загрузки тура.")


@router.callback_query(F.data == "pages")
async def cb_pages(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏟️ *Страницы клубов*\n\nВыбери клуб или раздел новостей:",
        reply_markup=pages_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def cb_page(callback: CallbackQuery):
    target = callback.data.split(":", 1)[1]
    if target == "news":
        # Показываем последние новости Бундеслиги из БД
        news_items = db_get_news(limit=15, category="bundesliga")
        if not news_items:
            # Fallback: общие новости без фильтра категории
            news_items = db_get_news(limit=15)
        if news_items:
            lines = ["🇩🇪 *Новости Бундеслиги*\n"]
            for i, item in enumerate(news_items, 1):
                title = item.get("title", "")
                date = item.get("published_at", "")[:10]
                source = item.get("source", "")
                club_tag = item.get("club_tag", "")
                url = item.get("url", "")
                tag_str = f" [{club_tag}]" if club_tag else ""
                lines.append(f"*{i}. {title}*")
                if date:
                    lines.append(f"   📅 {date} | 📌 {source}{tag_str}")
                if url:
                    lines.append(f"   🔗 [Читать]({url})")
                lines.append("")
            text = "\n".join(lines)
        else:
            text = "🇩🇪 *Новости Бундеслиги*\n\n📰 _Новостей пока нет_\n\nНовости обновляются автоматически каждые 30 минут."
        await callback.message.edit_text(
            text,
            reply_markup=bundesliga_news_kb(),
            disable_web_page_preview=True,
        )
    else:
        c = get_club(target)
        if c:
            emoji = c.get("emoji", "⚽")
            city = c.get("city", "—")
            stadium = c.get("stadium", "—")
            capacity = c.get("capacity", "—")
            founded = c.get("founded", "—")
            text = (
                f"{emoji} *{c['name']}*\n\n"
                f"🏙️ Город: {city}\n"
                f"📅 Основан: {founded}\n"
                f"🏟️ Стадион: {stadium}\n"
                f"👥 Вместимость: {capacity:,}\n"
            )
        else:
            text = f"⚠️ Клуб не найден: {target}"
        await callback.message.edit_text(
            text,
            reply_markup=club_page_kb(target),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("club_info:"))
async def cb_club_info(callback: CallbackQuery):
    """Информация о клубе из БД."""
    try:
        club_name = callback.data.split(":", 1)[1]
        c = get_club(club_name)
        if not c:
            await callback.answer("⚠️ Клуб не найден", show_alert=True)
            return

        emoji = c.get("emoji", "⚽")
        city = c.get("city", "—")
        stadium = c.get("stadium", "—")
        capacity = c.get("capacity", "—")
        short = c.get("short_name", "—")
        founded = c.get("founded", "—")
        
        # Получаем тренера
        coach = get_coach(club_name)
        coach_line = ""
        if coach:
            coach_name = coach.get("name", "—")
            coach_age = coach.get("age")
            coach_display = f"{coach_name}"
            if coach_age:
                coach_display += f" ({coach_age} лет)"
            coach_line = f"👔 Тренер: {coach_display}\n"

        text = (
            f"{emoji} *{c['name']}*\n\n"
            f"🏙️ Город: {city}\n"
            f"📅 Основан: {founded}\n"
            f"🏟️ Стадион: {stadium}\n"
            f"👥 Вместимость: {capacity:,}\n"
            f"🔤 Сокращение: {short}\n"
            f"{coach_line}\n"
            f"📊 *Сезон 2025/26*\n"
            f"🏆 Бундеслига: _загрузка..._\n"
            f"🏆 DFB-Pokal: _загрузка..._\n"
            f"🏆 Еврокубки: _уточняется_\n"
        )
        await callback.message.edit_text(text, reply_markup=club_page_kb(club_name))
        await callback.answer()
    except Exception as e:
        logger.error("cb_club_info error: %s", e)
        await callback.answer("⚠️ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("club_news:"))
async def cb_club_news(callback: CallbackQuery):
    """Новости клуба из БД (club_news + news)."""
    try:
        club_name = callback.data.split(":", 1)[1]
        emoji = club_emoji(club_name)

        # Новости из новой таблицы news
        news_list = db_get_club_news(club_name, limit=10)

        if not news_list:
            text = f"{emoji} *{club_name}*\n\n📰 _Новостей пока нет_\n\nНовости обновляются автоматически каждые 30 минут."
        else:
            lines = [f"{emoji} *{club_name}* — 📰 Новости\n"]
            for i, item in enumerate(news_list, 1):
                title = item.get("title", "")
                desc = item.get("description", "")
                date = item.get("published_at", "")[:10]
                source = item.get("source", "")
                url = item.get("url", "")
                lines.append(f"*{i}. {title}*")
                if date:
                    lines.append(f"   📅 {date} | 📌 {source}")
                if desc:
                    lines.append(f"   {desc[:200]}")
                if url:
                    lines.append(f"   🔗 [Читать]({url})")
                lines.append("")
            text = "\n".join(lines)

        await callback.message.edit_text(text, reply_markup=news_kb(club_name), disable_web_page_preview=True)
        await callback.answer()
    except Exception as e:
        logger.error("cb_club_news error: %s", e)
        await callback.answer("⚠️ Ошибка загрузки новостей", show_alert=True)


def fmt_squad_line(num, name, nationality):
    """Форматирует строку игрока без Markdown."""
    if num:
        num_str = f"#{num}"
    else:
        num_str = "#—"
    return f"  {num_str} {name} ({nationality})"


@router.callback_query(F.data.startswith("club_squad:"))
async def cb_club_squad(callback: CallbackQuery):
    """Состав клуба из БД."""
    try:
        club_name = callback.data.split(":", 1)[1]
        emoji = club_emoji(club_name)
        squad = get_squad(club_name)

        if not squad["total"]:
            text = f"{emoji} {club_name}\n\n👥 Состав пока не заполнен"
        else:
            lines = [f"{emoji} {club_name} — 👥 Состав"]
            lines.append(f"👤 Всего: {squad['total']} | 🌍 Легионеров: {squad['foreigners']}")

            if squad["gk"]:
                lines.append("\n🧤 Вратари:")
                for p in squad["gk"]:
                    lines.append(fmt_squad_line(p.get("number"), p.get("name", ""), p.get("nationality", "")))

            if squad["df"]:
                lines.append("\n🛡️ Защитники:")
                for p in squad["df"]:
                    lines.append(fmt_squad_line(p.get("number"), p.get("name", ""), p.get("nationality", "")))

            if squad["mf"]:
                lines.append("\n⚡ Полузащитники:")
                for p in squad["mf"]:
                    lines.append(fmt_squad_line(p.get("number"), p.get("name", ""), p.get("nationality", "")))

            if squad["fw"]:
                lines.append("\n⚽ Нападающие:")
                for p in squad["fw"]:
                    lines.append(fmt_squad_line(p.get("number"), p.get("name", ""), p.get("nationality", "")))

            text = "\n".join(lines)

        await callback.message.edit_text(
            text,
            reply_markup=club_page_kb(club_name),
        )
        await callback.answer()
    except Exception as e:
        logger.error("cb_club_squad error: %s", e)
        await callback.answer("⚠️ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("club_trophies:"))
async def cb_club_trophies(callback: CallbackQuery):
    """Достижения клуба из БД."""
    try:
        club_name = callback.data.split(":", 1)[1]
        emoji = club_emoji(club_name)
        t = get_trophies(club_name)

        text = f"{emoji} {club_name} — 🏆 Достижения\n\n"

        if t:
            bl_titles = t.get("bl_titles", 0) or 0
            bl_last = t.get("bl_last")
            dfb_pokals = t.get("dfb_pokals", 0) or 0
            dfb_pokal_last = t.get("dfb_pokal_last")
            cl = t.get("champions_league", 0) or 0
            cl_last = t.get("cl_last")
            el = t.get("europa_league", 0) or 0
            el_last = t.get("el_last")
            ecl = t.get("conference_league", 0) or 0
            ecl_last = t.get("ecl_last")
            super_cups = t.get("super_cups", 0) or 0

            if bl_titles:
                text += f"🥇 Чемпион Германии: {bl_titles}x"
                if bl_last:
                    text += f" (последний: {bl_last})"
                text += "\n"
            if dfb_pokals:
                text += f"🏆 DFB-Pokal: {dfb_pokals}x"
                if dfb_pokal_last:
                    text += f" (последний: {dfb_pokal_last})"
                text += "\n"
            if cl:
                text += f"⭐ Лига Чемпионов: {cl}x"
                if cl_last:
                    text += f" (последний: {cl_last})"
                text += "\n"
            if el:
                text += f"🌍 Лига Европы: {el}x"
                if el_last:
                    text += f" (последний: {el_last})"
                text += "\n"
            if ecl:
                text += f"🌐 Лига Конференций: {ecl}x"
                if ecl_last:
                    text += f" (последний: {ecl_last})"
                text += "\n"
            if super_cups:
                text += f"🏅 Суперкубок: {super_cups}x\n"

            if not any([bl_titles, dfb_pokals, cl, el, ecl, super_cups]):
                text += "Пока нет крупных достижений\n"
        else:
            text += "Данные о достижениях не найдены\n"

        await callback.message.edit_text(text, reply_markup=club_page_kb(club_name), parse_mode=None)
        await callback.answer()
    except Exception as e:
        logger.error("cb_club_trophies error: %s", e)
        await callback.answer("⚠️ Ошибка загрузки достижений", show_alert=True)


@router.callback_query(F.data.startswith("club_matches:"))
async def cb_club_matches(callback: CallbackQuery):
    try:
        club_name = callback.data.split(":", 1)[1]
        emoji = club_emoji(club_name)
        await callback.message.edit_text(
            f"{emoji} *{club_name}*\n\n"
            f"📅 Расписание матчей\n\n"
            f"*Раздел в разработке*\n\n"
            f"Скоро здесь будет:\n"
            f"• Все матчи клуба в сезоне\n• Результаты\n• Статистика по матчам",
            reply_markup=club_page_kb(club_name),
        )
        await callback.answer()
    except Exception as e:
        logger.error("cb_club_matches error: %s", e)
        await callback.answer("⚠️ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("club_stats:"))
async def cb_club_stats(callback: CallbackQuery):
    try:
        club_name = callback.data.split(":", 1)[1]
        emoji = club_emoji(club_name)
        await callback.message.edit_text(
            f"{emoji} *{club_name}*\n\n"
            f"📈 Статистика\n\n"
            f"*Раздел в разработке*\n\n"
            f"Скоро здесь будет:\n"
            f"• Позиция в таблице\n• Форма (последние 5)\n• Топ-бомбардиры\n• История выступлений",
            reply_markup=club_page_kb(club_name),
        )
        await callback.answer()
    except Exception as e:
        logger.error("cb_club_stats error: %s", e)
        await callback.answer("⚠️ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("club_discuss:"))
async def cb_club_discuss(callback: CallbackQuery):
    try:
        club_name = callback.data.split(":", 1)[1]
        emoji = club_emoji(club_name)
        topic_name = CLUB_TOPIC_NAMES.get(club_name, club_name)
        await callback.message.edit_text(
            f"{emoji} *{club_name}*\n\n"
            f"💬 Обсуждение: *{topic_name}*\n\n"
            f"Переходи в группу @BundLTD\n"
            f"и выбирай топик «{topic_name}»\n\n"
            f"Там можно:\n"
            f"• Обсуждать матчи\n• Делиться мнениями\n• Следить за новостями",
            reply_markup=club_page_kb(club_name),
        )
        await callback.answer()
    except Exception as e:
        logger.error("cb_club_discuss error: %s", e)
        await callback.answer("⚠️ Ошибка", show_alert=True)


@router.callback_query(F.data == "schedule")
async def cb_schedule(callback: CallbackQuery):
    await callback.answer("Загружаю...")
    try:
        data = await get_matchday_formatted()
        await callback.message.edit_text(
            f"📅 *Расписание матчей*\n\n{data}",
            reply_markup=main_menu_kb(),
        )
    except Exception as e:
        logger.error("cb_schedule error: %s", e)
        await callback.message.edit_text("⚠️ Расписание временно недоступно.")


@router.callback_query(F.data == "subs")
async def cb_subs(callback: CallbackQuery):
    db = get_db()
    subs = db.execute(
        "SELECT club FROM subscriptions WHERE user_id=? ORDER BY club",
        (callback.from_user.id,)
    ).fetchall()
    db.close()

    sub_list = "\n".join(f"  ⚽ {s['club']}" for s in subs) if subs else "  Нет подписок"
    text = f"🔔 *Твои подписки:*\n\n{sub_list}\n\nВыбери клуб для подписки/отписки:"
    await callback.message.edit_text(text, reply_markup=clubs_kb("sub"))
    await callback.answer()


@router.callback_query(F.data.startswith("sub_club:"))
async def cb_sub_toggle(callback: CallbackQuery):
    club = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    db = get_db()
    existing = db.execute(
        "SELECT id FROM subscriptions WHERE user_id=? AND club=?",
        (user_id, club)
    ).fetchone()

    if existing:
        db.execute("DELETE FROM subscriptions WHERE id=?", (existing["id"],))
        action_text = f"❌ Отписка от {club}"
    else:
        db.execute(
            "INSERT OR IGNORE INTO subscriptions (user_id, club) VALUES (?, ?)",
            (user_id, club)
        )
        action_text = f"✅ Подписка на {club}"

    db.commit()
    db.close()
    await callback.answer(action_text, show_alert=True)


@router.callback_query(F.data == "favorites")
async def cb_favorites(callback: CallbackQuery):
    db = get_db()
    favs = db.execute(
        "SELECT club FROM favorites WHERE user_id=? ORDER BY club",
        (callback.from_user.id,)
    ).fetchall()
    db.close()

    fav_list = "\n".join(f"  ⭐ {f['club']}" for f in favs) if favs else "  Нет избранных клубов"
    text = f"⭐ *Избранные клубы:*\n\n{fav_list}\n\nВыбери клуб для добавления/удаления:"
    await callback.message.edit_text(text, reply_markup=clubs_kb("fav"))
    await callback.answer()


@router.callback_query(F.data.startswith("fav_club:"))
async def cb_fav_toggle(callback: CallbackQuery):
    club = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    db = get_db()
    existing = db.execute(
        "SELECT id FROM favorites WHERE user_id=? AND club=?",
        (user_id, club)
    ).fetchone()

    if existing:
        db.execute("DELETE FROM favorites WHERE id=?", (existing["id"],))
        action_text = f"❌ Удалено из избранного: {club}"
    else:
        db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, club) VALUES (?, ?)",
            (user_id, club)
        )
        action_text = f"⭐ Добавлено в избранное: {club}"

    db.commit()
    db.close()
    await callback.answer(action_text, show_alert=True)


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery):
    text = textwrap.dedent("""\
        📈 *Статистика*

        _Раздел в разработке._

        Premium-пользователи получат:
        • Детальную статистику команд
        • xG-аналитику матчей
        • Сравнения игроков
        • Историю личных встреч
    """)
    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "premium")
async def cb_premium(callback: CallbackQuery):
    text = textwrap.dedent("""\
        💎 *Bundesliga Today Premium*

        _Возможности:_
        📊 Уведомления о матчах подписанных клубов в реальном времени
        📈 Расширенная статистика и xG-аналитика
        📋 Прогнозы на матчи
        🎯 Оповещения о голах
        💬 Без рекламы

        Выбери тариф:
    """)
    await callback.message.edit_text(text, reply_markup=premium_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("buy_premium:"))
async def cb_buy_premium(callback: CallbackQuery):
    _, label, price = callback.data.split(":")
    price = int(price)
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=f"Bundesliga Today Premium — {label}",
        description=f"Premium-доступ к Bundesliga Today на {label}",
        payload=f"premium_{label}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"Premium {label}", amount=price)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    await message.answer(
        "💎 *Premium активирован!*\n\nСпасибо за подписку!\nВсе функции теперь доступны.",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery):
    text = textwrap.dedent("""\
        🇩🇪 *Bundesliga Today*

        Твой персональный гид по немецкому футболу.

        _Открытая информация:_
        • Таблица и результаты — OpenLigaDB
        • Автор проекта: @enders_pashka
        • Версия: 0.2

        _Контакт для связи:_ @enders_pashka
    """)
    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    await callback.message.edit_text("📍 *Главное меню*", reply_markup=main_menu_kb())
    await callback.answer()


# ── Admin-команды ──────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
    total_subs = db.execute("SELECT COUNT(*) as n FROM subscriptions").fetchone()["n"]
    total_favs = db.execute("SELECT COUNT(*) as n FROM favorites").fetchone()["n"]
    premium_users = db.execute("SELECT COUNT(*) as n FROM users WHERE is_premium=1").fetchone()["n"]
    db.close()

    text = (
        f"🔧 *Админ-панель*\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"🔔 Подписок: {total_subs}\n"
        f"⭐ Избранное: {total_favs}\n"
        f"💎 Premium: {premium_users}\n\n"
        f"📢 *Публикация в канал:*\n"
        f"/post_table — таблица в канал\n"
        f"/post_matchday — текущий тур в канал\n"
        f"/post_schedule — расписание ближайших матчей\n"
        f"/welcome — приветственное сообщение"
    )
    await message.answer(text)


@router.message(Command("post_table"))
async def cmd_post_table(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        table = await get_table_formatted()
        await bot.send_message(CHANNEL_ID, table)
        await message.answer("✅ Таблица опубликована в канал!")
    except Exception as e:
        logger.error("post_table error: %s", e)
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("post_matchday"))
async def cmd_post_matchday(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        data = await get_matchday_formatted()
        await bot.send_message(CHANNEL_ID, data)
        await message.answer("✅ Тур опубликован в канал!")
    except Exception as e:
        logger.error("post_matchday error: %s", e)
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("post_schedule"))
async def cmd_post_schedule(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        data = await get_matchday_formatted()
        await bot.send_message(CHANNEL_ID, f"📅 *Расписание ближайших матчей*\n\n{data}")
        await message.answer("✅ Расписание опубликовано!")
    except Exception as e:
        logger.error("post_schedule error: %s", e)
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("welcome"))
async def cmd_welcome(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    welcome = """🇩🇪 *Добро пожаловать в Bundesliga Today!*

Главный канал о немецком футболе ⚽

• Актуальная таблица Бундеслиги
• Результаты всех матчей
• Расписание туров
• Новости и трансферы

🤖 *Бот:* @BLTD_bot — подписка на клубы, уведомления, аналитика
📢 *Канал:* @BunLTD"""
    try:
        sent = await bot.send_message(CHANNEL_ID, welcome)
        await bot.pin_chat_message(CHANNEL_ID, sent.message_id, disable_notification=True)
        await message.answer("✅ Приветствие опубликовано и закреплено!")
    except Exception as e:
        logger.error("welcome error: %s", e)
        await message.answer(f"❌ Ошибка: {e}")


# ── Получение ID топиков (для отладки) ─────────────────────────

TOPIC_IDS = {}

@router.message(F.chat.id == GROUP_ID)
async def collect_topic_ids(message: Message):
    thread_id = message.message_thread_id
    text = message.text.strip() if message.text else ""
    if thread_id and text:
        TOPIC_IDS[thread_id] = text
        logger.info("Topic collected: '%s' → thread_id=%s", text, thread_id)
        await message.reply(f"✅ Запомнил! Топик '{text}' → ID {thread_id}")


# ── Автообновление новостей ──────────────────────────────────────

async def news_updater():
    """Фоновая задача: обновление новостей каждые 30 минут."""
    # Первый запуск через 10 сек после старта (даём боту инициализироваться)
    await asyncio.sleep(10)
    while True:
        try:
            logger.info("News updater: fetching...")
            items = await fetch_all_news()
            if items:
                added = save_news(items)
                logger.info("News updater: saved %d new items", added)
            cleanup_news(30)
        except Exception as e:
            logger.error("News updater error: %s", e)
        await asyncio.sleep(1800)  # 30 минут


async def table_updater():
    """Фоновая задача: обновление картинки таблицы каждые 60 минут."""
    await asyncio.sleep(15)  # даём боту запуститься
    while True:
        try:
            logger.info("Table updater: generating standings image...")
            result = await generate_tour_image()
            logger.info("Table updater: generated %s", result)
        except Exception as e:
            logger.error("Table updater error: %s", e)
        await asyncio.sleep(3600)  # 60 минут


@router.message(Command("news_refresh"))
async def cmd_news_refresh(message: Message):
    """Принудительное обновление новостей (только админ)."""
    if message.from_user.id not in ADMIN_IDS:
        return
    msg = await message.answer("⏳ Обновляю новости...")
    try:
        items = fetch_all_news_sync()
        if items:
            added = save_news(items)
            await msg.edit_text(f"✅ Обновлено! Новых новостей: {added} (всего собрано: {len(items)})")
        else:
            await msg.edit_text("⚠️ Новостей не найдено.")
    except Exception as e:
        logger.error("news_refresh error: %s", e)
        await msg.edit_text(f"❌ Ошибка: {e}")


@router.message(Command("table_refresh"))
async def cmd_table_refresh(message: Message):
    """Принудительная перегенерация таблицы (только админ)."""
    if message.from_user.id not in ADMIN_IDS:
        return
    msg = await message.answer("⏳ Генерирую таблицу...")
    try:
        result = await generate_tour_image()
        await msg.edit_text(f"✅ Таблица обновлена: `{result}`")
    except Exception as e:
        logger.error("table_refresh error: %s", e)
        await msg.edit_text(f"❌ Ошибка: {e}")

async def main():
    init_db()
    logger.info("Bundesliga Today Bot starting...")
    # Запускаем фоновое обновление новостей и таблицы
    asyncio.create_task(news_updater())
    asyncio.create_task(table_updater())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "pre_checkout_query"],
    )


if __name__ == "__main__":
    asyncio.run(main())
