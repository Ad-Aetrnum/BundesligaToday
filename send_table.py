"""Send standings PNG via bot"""
import asyncio
from aiogram import Bot
from aiogram.types import FSInputFile
from config import BOT_TOKEN

async def send():
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_photo(
            chat_id=1999236552,
            photo=FSInputFile("/home/hermes/.hermes/BundesligaToday/output/test_standings.png"),
            caption="📊 *Таблица — компактный вид* _(уменьшенная, на твоём фоне)_",
            parse_mode="Markdown"
        )
        print("✅ Отправлено")
    except Exception as e:
        print(f"❌ {e}")
    finally:
        await bot.session.close()

asyncio.run(send())