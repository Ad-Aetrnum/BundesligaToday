"""
Script to send image with your custom background
"""
import asyncio
import os
from aiogram import Bot
from aiogram.types import FSInputFile
from config import BOT_TOKEN

async def send_with_bg():
    bot = Bot(token=BOT_TOKEN)
    image_path = "/home/hermes/.hermes/BundesligaToday/output/test_standings.png"
    user_id = 1999236552
    
    try:
        with open(image_path, "rb") as photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=FSInputFile(image_path),
                caption="📊 *Таблица с твоим фоном* _(PNG + HTML → PNG)_",
                parse_mode="Markdown"
            )
        print(f"✅ Отправлено на {user_id}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(send_with_bg())