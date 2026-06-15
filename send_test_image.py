"""
Script to send test image directly via Telegram Bot API
"""
import asyncio
import os
from aiogram import Bot
from aiogram.types import FSInputFile
from config import BOT_TOKEN

async def send_test_image():
    # Инициализируем бота
    bot = Bot(token=BOT_TOKEN)
    
    # Путь к тестовому файлу
    image_path = "/home/hermes/.hermes/BundesligaToday/output/test_standings.png"
    
    # Проверяем, существует ли файл
    if not os.path.exists(image_path):
        print(f"Файл не найден: {image_path}")
        return
    
    # ID пользователя (из твоего профиля)
    user_id = 1999236552  # ID из conversation
    
    try:
        # Отправляем фото как FSInputFile
        with open(image_path, "rb") as photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=FSInputFile(image_path),
                caption="📊 *Тестовая таблица Бундеслиги 2025/26* _(сгенерировано через новый движок)_",
                parse_mode="Markdown"
            )
        print(f"✅ Файл успешно отправлен на {user_id}")
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(send_test_image())