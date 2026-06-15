# Bundesliga Today — Tech Debt & TODO

## Перенос данных в БД

Статические данные о клубах (стадионы, трофеи, новости) сейчас захардкожены в config.py.

План:
1. config.py оставить только базовые данные (название, город, стадион, вместимость)
2. Трофеи, составы, новости перенести в SQLite
3. Динамические данные (позиции, формы, бомбардиры) кэшировать в БД из OpenLigaDB
4. При масштабировании на другие лиги — единая структура таблиц

Когда: при масштабировании на другие лиги или когда потребуется админка для редактирования.

## Установленные библиотеки (2026-05-29)
- deep-translator 1.11.4 — авто-перевод DE/EN → RU
- feedparser 6.0.12 — парсинг RSS новостей

## Проверенные API
- OpenLigaDB — OK (18 команд, данные 2025/26)
- Transfermarkt RSS — OK
- Pillow — OK
- deep-translate — OK
- feedparser — OK

## Требуют бесплатных ключей
- NewsAPI.org (newsapi.org, 100 req/day free)
- Football-Data.org (football-data.org, 10 req/min free)
- Groq API (console.groq.com, free tier для AI)
