import asyncio
import logging
import os
from aiohttp import web
import config
from database import init_db
from alert_bot import bot, dp
from userbot import client as userbot_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MAIN")

# Простий веб-сервер для безкоштовного тарифу Render Web Service
async def handle_ping(request):
    return web.Response(text="Lead Bot is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Fake Web Server запущено на порту {port} для Render Free Plan!")

async def main():
    logger.info("Ініціалізація бази даних...")
    await init_db()

    # Запускаємо легкий веб-сервер для безкоштовного Render Free Web Service
    await start_web_server()

    logger.info("Запуск Telegram Alert бота...")
    bot_task = asyncio.create_task(dp.start_polling(bot))

    logger.info("Підключення юзербота (Telegram User Client)...")
    await userbot_client.start()
    
    me = await userbot_client.get_me()
    logger.info(f"✅ Юзербот успішно авторизований як: {me.first_name} (@{me.username or me.id})")
    
    # Автоматичний вступ у цільові українські групи (1 чат раз на 5 хв)
    from chat_finder import auto_discover_and_join_chats
    asyncio.create_task(auto_discover_and_join_chats(userbot_client, target_chats_count=30))

    logger.info("🚀 СИСТЕМА ЛІДОГЕНЕРАЦІЇ ПРАЦЮЄ ТА СЛУХАЄ ЧАТИ 24/7!")

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
