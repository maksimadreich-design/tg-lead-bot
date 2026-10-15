import asyncio
import logging
from telethon import TelegramClient
import config
from database import init_db
from alert_bot import bot, dp
from userbot import client as userbot_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MAIN")

async def main():
    logger.info("Ініціалізація бази даних...")
    await init_db()

    logger.info("Запуск Telegram Alert бота...")
    # Запускаємо полінг бота для сповіщень у фоновому таску
    bot_task = asyncio.create_task(dp.start_polling(bot))

    logger.info("Підключення юзербота (Telegram User Client)...")
    await userbot_client.start()
    
    me = await userbot_client.get_me()
    logger.info(f"✅ Юзербот успішно авторизований як: {me.first_name} (@{me.username or me.id})")
    
    # Автоматичний пошук та вступ у цільові українські групи (до 30 чатів)
    from chat_finder import auto_discover_and_join_chats
    asyncio.create_task(auto_discover_and_join_chats(userbot_client, target_chats_count=30))

    logger.info("🚀 СИСТЕМА ЛІДОГЕНЕРАЦІЇ ПРАЦЮЄ ТА СЛУХАЄ ЧАТИ!")

    # Тримаємо процес активним
    try:
        await userbot_client.run_until_disconnected()
    finally:
        await bot.session.close()
        bot_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Роботу сервісу зупинено.")
