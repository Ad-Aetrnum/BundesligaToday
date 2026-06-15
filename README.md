# Bundesliga Today 🗞️

**Telegram-бот @BLTD_bot** — генерация новостей и статистики Бундеслиги в формате PNG-изображений.

## Возможности

- 📊 **Таблица Бундеслиги** — полная турнирная таблица с зонами (ЛЧ, ЛЕ, вылет)
- ⚽ **Результаты тура** — матчи с результатами
- 🥅 **Топ бомбардиров** — игроки с голами и ассистами (формат: `голы/ассисты`)
- 📰 **Новости** — автопарсинг с football-data.org

## Технологии

- **Python 3.11+** + Pillow (рендеринг)
- **aiogram 3** (Telegram бот)
- **SQLite** (хранение новостей)
- **football-data.org API** (данные о матчах)

## Установка

```bash
# Клонировать репозиторий
git clone git@github.com:Ad-Aeternum/BundesligaToday.git
cd BundesligaToday

# Установить зависимости
pip install -r requirements.txt

# Настроить окружение
cp .env.example .env
# Заполнить BUNDESLIGA_BOT_TOKEN в .env

# Запустить рендер
python render_final.py

# Запустить бота
python bot.py
```

## Структура проекта

| Файл | Описание |
|------|----------|
| `render_final.py` | Основной скрипт рендера (Pillow) |
| `bot.py` | Telegram-бот (aiogram) |
| `config.py` | Конфигурация |
| `database.py` | Работа с SQLite |
| `news_parser.py` | Парсер новостей |
| `assets/` | Шрифты и фоны |
| `output/` | Сгенерированные PNG |

## Рендеринг

Рендер генерирует изображение в трёх секциях:
- **ST** (Standings Table) — левая часть
- **MR** (Matchday Results) — верхний правый угол
- **TS** (Top Scorers) — нижний правый угол

Подробнее о координатах и размерах: [PROJECT_SETTINGS.md](PROJECT_SETTINGS.md)

## Лицензия

MIT
