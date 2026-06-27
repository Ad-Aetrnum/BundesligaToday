# Bundesliga Today — Project Settings

## Repository
- GitHub: https://github.com/Ad-Aetrnum/BundesligaToday (private)
- Bot: @BLTD_bot (Telegram)

## Layout Parameters

### Canvas
- Reference: REF_W=2000, REF_H=2500
- Scale factors: sx, sy

### ST (Standings Table)
- Position: sx0=352, sy0=659
- Column widths: #=52, Club=232, W=42, D=42, L=42, GF=42, GA=42, PTS=42
- Total width: 546px (sum of columns)
- Row height: header=62px, data=42px
- Bottom padding: 30px
- Fonts: Oswald 53px (#, Club), Oswald 40px (stats), Oswald 55px (PTS)
- Contour: black (0,0,0), 2px
- Zone stripes: CL=(0,120,255), EL=(180,0,80), 7th=(0,200,80), Relegation=(255,60,60)
- Club names: shortened via `shorten_tour()` dictionary

### MR (Matchday Results)
- Position: mx=1159 (= tx0), my=sy0 (aligned with ST top)
- Width: 350px
- Columns: Home=140, Score=45, Away=140
- Rows: 9
- Bottom padding: 74px (24px + 50px)
- Title: "Matchday N Results", centered
- Stripe below title: (80,80,80), 75% width, 4px, 20px gap
- Contour: black (0,0,0), 2px
- Club names: shortened via `shorten_tour()`

### TS (Top Scorers)
- Position: tx0=1159, ty0=dynamic (bottom-aligned with ST)
- Width: 523px
- Columns: Rank=25, Name=160, Club=100, Goals=45
- Total data width: 330px
- Rows: 10
- Bottom padding: 50px
- Title: "Top Scorers", centered
- Stripe below title: (80,80,80), 75% width, 4px, 20px gap
- Contour: black (0,0,0), 2px
- Fonts: Name=Inter 40px, Club=Inter 34px, Goals=Inter 36px
- Goals format: "goals/assists" (e.g. "36/12")
- Club names: shortened via `shorten_tour()`

### Separator Line
- Width: 800px
- Thickness: 3px
- Color: (80,80,80) dark gray
- Position: footer_y - 8

## Colors
- Background: white (255,255,255)
- Text: black (0,0,0)
- Contours: black (0,0,0)
- Stripes/separators: dark gray (80,80,80)
- Row alternation: white / (250,250,250)

## Fonts
- Section headings: Bebas Neue 40px
- ST headers: Oswald 53px (#, Club), Oswald 40px (stats)
- ST data: Oswald 55px (#, Club), Oswald 40px (stats), Oswald 55px (PTS)
- MR/TS: Oswald/Inter 43px
- TS: Inter 40px (Name), 34px (Club), 36px (Goals)
- Column headers: Inter SemiBold 32px

## Club Name Shortening Dictionary
Located in `Bundesliga_tour.py` as `TOUR_SHORT_NAMES` and in `render_cup.py` as `SHORTEN`.
Must be kept identical between both renderers.

Key entries:
- "FC Bayern München" → "Bayern"
- "Borussia Dortmund" → "Borussia D"
- "Borussia Mönchengladbach" → "Borussia M"
- "Bayer 04 Leverkusen" → "Bayer 04"
- "Eintracht Frankfurt" → "Eintracht"
- "VfB Stuttgart" → "Stuttgart"
- "TSG 1899 Hoffenheim" → "Hoffenheim"
- "1. FC Heidenheim 1846" → "Heidenheim"
- "1. FC Kaiserslautern" → "K'lautern"
- "1. FC Union Berlin" → "Union"
- "1. FSV Mainz 05" → "Mainz 05"
- "SV Werder Bremen" → "Werder"
- "VfL Wolfsburg" → "Wolfsburg"
- "FC Augsburg" → "Augsburg"
- "SC Freiburg" → "Freiburg"
- "1. FC Köln" → "1. FC Köln"
- "RB Leipzig" → "RB Leipzig"
- "Hamburger SV" → "HSV"
- "FC St. Pauli 1910" → "St. Pauli"
- "VfL Bochum" → "Bochum"
- "SV Darmstadt 98" → "Darmstadt"

## Bot Architecture
- `bot.py`: Telegram bot (aiogram 3, polling)
- `table_generator.py`: Fetches data from football-data.org API, calls `render_full()`, saves `output/bl_today.png`
- `Bundesliga_tour.py`: Pillow renderer (ST + MR + TS)
- `render_cup.py`: DFB-Pokal cup draw renderer

### Commands
- `/start` — welcome + main menu
- `/menu` — show club pages
- `/table` — show current standings table (sends bl_today.png)
- `/matchday` — show latest matchday results
- `/admin` — admin panel
- `/news_refresh` — force news refresh (admin only)
- `/table_refresh` — force table image regeneration (admin only)

### Inline Buttons
- Club page → 📰 Новости, 📋 Информация, 👥 Состав, 📅 Матчи, 📈 Статистика, 🏆 Достижения, 🔔 Подписаться
- 📊 Таблица — sends pre-generated `bl_today.png` instantly

### Key Implementation Notes
- Club squad text: NO Markdown formatting (causes "can't parse entities" errors with | and brackets)
- `generate_tour_image()` is async — must be awaited, not called with asyncio.run()
- Club names stored in DB as `[FCB] FC Bayern München | Бавария`
- Shortened via `shorten_tour()` for tour table, `SHORTEN` dict for cup draw
- Only ONE bot instance must be running per token (TelegramConflictError otherwise)
- Use `BufferedInputFile` for sending photos (not FSInputFile or MEDIA: prefix)

## API
- football-data.org (FOOTBALL_DATA_API_KEY in .env)
- Rate limit: 10 req/min, sleep 7+ sec between requests
- Position mapping: long names → GK/DF/MF/FW

## Environment Variables (.env)
- BUNDESLIGA_BOT_TOKEN: @BLTD_bot token
- FOOTBALL_DATA_API_KEY: football-data.org API key
- ADMIN_IDS: list of admin user IDs
- CHANNEL_ID: channel ID for posting
- GROUP_ID: group ID for monitoring
