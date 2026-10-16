import asyncio
import logging
import os
import json
from aiohttp import web
import config
from database import init_db, get_recent_leads
from alert_bot import bot, dp, STATS
from userbot import client as userbot_client
from settings_manager import get_settings, save_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MAIN")

# Веб-панель керування та API
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

async def handle_index(request):
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return web.FileResponse(index_path)
    return web.Response(text="Web App UI ready!")

async def handle_health(request):
    return web.Response(text="OK 200")

async def handle_get_stats(request):
    return web.json_response(STATS)

async def handle_get_leads(request):
    leads = await get_recent_leads(limit=50)
    return web.json_response(leads)

async def handle_get_settings(request):
    settings = await get_settings()
    return web.json_response(settings)

async def handle_save_settings(request):
    try:
        data = await request.json()
        await save_settings(data)
        return web.json_response({"status": "ok", "message": "Налаштування оновлено"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/stats", handle_get_stats)
    app.router.add_get("/api/leads", handle_get_leads)
    app.router.add_get("/api/settings", handle_get_settings)
    app.router.add_post("/api/settings", handle_save_settings)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Повноцінний Web App Dashboard запущено на порту {port}!")

async def main():
    logger.info("Ініціалізація бази даних...")
    await init_db()

    # Запускаємо Web App панель
    await start_web_server()

    logger.info("Запуск Telegram Alert бота...")
    bot_task = asyncio.create_task(dp.start_polling(bot))

    logger.info("Підключення юзербота (Telegram User Client)...")
    await userbot_client.start()
    
    me = await userbot_client.get_me()
    logger.info(f"✅ Юзербот успішно авторизований як: {me.first_name} (@{me.username or me.id})")
    
    # Автоматичний вступ у цільові групи
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
