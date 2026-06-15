"""Send the actual background file used in the template"""
import asyncio
from aiogram import Bot
from aiogram.types import FSInputFile
from config import BOT_TOKEN

async def send():
    bot = Bot(token=BOT_TOKEN)
    try:
        # Отправляем сам файл фона
        await bot.send_photo(
            chat_id=1999236552,
            photo=FSInputFile("/home/hermes/.hermes/BundesligaToday/assets/your_bg_v1_resized.jpg"),
            caption="🖼️ *Фон, который используется в шаблоне*\n\nРазмер: 1080×1350 px\nФайл: `your_bg_v1_resized.jpg`",
            parse_mode="Markdown"
        )
        print("✅ Фон отправлен")
    except Exception as e:
        print(f"❌ {e}")
    finally:
        await bot.session.close()

asyncio.run(send())