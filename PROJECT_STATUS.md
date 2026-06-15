# Bundesliga Today — Статус проекта

## Что это
Telegram-бот @BLTD_bot для фанатов немецкого футбола. Публикует новости, таблицу, результаты тура, новостную ленту в канал.

## Технологии
- **Bot**: aiogram 3.x
- **Rendering**: PIL/Pillow (render_final.py) — рендерит PNG-изображения
- **Playwright**: легаси, использовался раньше для HTML→PNG
- **DB**: SQLite (bundesliga_today.db)
- **Translator**: deep_translator (ru/en)
- **Data sources**: football-data.org API, NewsAPI

## Архитектура рендера (render_final.py)
Пиксельный рендеринг через PIL. Магazine cover стиль.

- **Canvas**: 1360×2048px, фон — `assets/magazine_bg_v1.png`
- **Scaling**: все координаты через `S(ref_x, ref_y)` — масштабирование от референса 2000×2500 к реальному размеру фона

### Разделы (сверху вниз):
1. **Header** — дата, сезон
2. **Standings Table** — основная таблица слева
   - Колонки: # (52px), Club (292px), W/D/L/GF/GA/PTS (32px each). Итого 536px
   - Зоны: CL синий (0,120,255), EL вишнёвый (180,0,80), 7-е зелёный (0,200,80), вылет красный (255,60,60)
   - Шрифты: # и Club — 53/55px; W/D/L/GF/GA/PTS — 40/40px (Oswald)
3. **Matchday Results** — результаты тура (справа-верх)
   - Позиция: S(1129, 759), размер: 543×200px
   - Шрифты: 40px Oswald
4. **Top 5 Scorers** — бомбардиры (справа-низ)
   - Позиция: S(1129, 1619), размер: 543×1665px
   - Шрифты: 40px Oswald
5. **Footer** — «Updated After Matchday N» (самый низ)
   - Позиция: S(87, 2484), размер: 1745×50px
   - Шрифт: 43px Oswald, красный (255,60,60)

## Новостная система
### БД схема:
- `news` — основная таблица (type, topic, priority, title_ru, text_ru, title_en, text_en, published_at, source_url, is_published)
- `news_clubs` — M:N связь новостей с клубами
- `news_entities` — M:N связь с сущностями (игроки, тренеры)

### Типы новостей (type):
match, transfer, injury, contract, interview, coach, standing, rumor, announcement

### Темы (topic):
bundesliga, world_cup, national_team, champions_league, europa_league, dfb_pokal, club, german_abroad

### Правила публикации в канал:
- priority >= 8 → канал
- type IN (match, transfer, coach, standing) AND priority >= 7 → канал
- Иначе → только бот/клуб

## Критические правила
- **НЕЛЬЗЯ** вызывать `fetch_all_news_sync()` в асинхронном контексте — убьёт event loop
- **НЕЛЬЗЯ** отправлять картинки через MEDIA-теги в Telegram — не работает
- **ТОЛЬКО** `aiogram bot.send_photo()` с `FSInputFile` для отправки изображений
- **Шрифты ТОЛЬКО локальные** — Bebas Neue, Inter, Oswald в `assets/fonts/`
- **Фон НЕ сжимать** — PIL загружает как есть

## Что сделано
- [x] Бот работает (Telegram aiogram)
- [x] Парсер новостей (NewsAPI + football-data.org)
- [x] БД с новой схемой (news, news_clubs, news_entities)
- [x] Пил-рендер (render_final.py) — standings + scorers + results + footer
- [x] Авто-обновление по крону (30 мин)
- [x] Перевод новостей (RU)
- [x] Система зон с цветными полосками
- [x] Настройка отправки через двух ботов (BLTD + EPS_A)
- [x] Контуры разделов для отладки макета (DEBUG_BORDERS)

## Что нужно сделать
- [ ] Шаблон новостной карточки (news.html → PNG)
- [ ] Шаблон трансфера (transfer.html → PNG)
- [ ] Классификация новостей (Rule Engine + AI fallback)
- [ ] Webhook-подписки для event-driven архитектуры
- [ ] Логотипы клубов → assets
- [ ] Zone Engine v2 (правила зон в конфиге)
- [ ] Анти-AI-дрифт тесты (unit tests)
- [ ] Рефакторинг bot.py под editorial pipeline

## Запуск
```bash
cd /home/hermes/.hermes/BundesligaToday
python3 render_final.py  # тест рендера
python3 bot.py           # запуск бота
```

## Ключи (в .env)
- BUNDESLIGA_BOT_TOKEN — токен @BLTD_bot (публикации в канал)
- EPS_A_BOT_TOKEN — токен EPS_A_bot (дубликат картинок в чат разработки)
- EPSE1LON_BOT_TOKEN — токен @EPSe1lon_bot (персональный секретарь)
- NEWS_API_KEY
- FOOTBALL_DATA_KEY
- CHANNEL_ID
- ADMIN_IDS

## Отправка изображений
При рендере (`render_final.py`) картинка отправляется в двух местах:
1. **BLTD_bot** → основная отправка (канал/публикация)
2. **EPS_A_bot** → дубликат в чат разработки (для просмотра макета)

Функции:
- `send_to_telegram()` — отправка через BLTD_bot
- `send_duplicate_to_dev_chat()` — дубликат через EPS_A_bot

## Контакты
- Админ: Pavel Enders, Telegram ID 1999236552
- BLTD_bot: @BLTD_bot (Bundesliga Today)
- EPS_A_bot: бот для переписки с Hermes Agent
- EPSe1lon_bot: @EPSe1lon_bot (персональный секретарь)
