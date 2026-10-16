import json
import os
import aiofiles

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "app_settings.json")

DEFAULT_SETTINGS = {
    # Режим авто-відповідача (AI Sales Manager)
    "auto_reply_enabled": False,
    "auto_reply_mode": "chat_reply",  # "chat_reply" (у коментар/відповідь у чаті) або "direct_message" (в ЛС)
    "auto_reply_min_score": 85,
    "auto_reply_delay_seconds": 15,  # Затримка перед відповіддю (імітація живої людини)
    
    # Фільтрація ШІ
    "min_relevance_score": 75,
    "services_description": "Розробка Telegram-ботів, створення та доопрацювання сайтів, веб-сервісів, парсерів даних, автоматизація бізнес-процесів, скрипти на Python, інтеграція AI та LLM, веб-розробка під ключ.",
    "ai_temperature": 0.2,
    
    # Ключові слова та стоп-слова
    "required_keywords": [
        "бот", "bot", "сайт", "web", "розроб", "програм", "фриланс", "фріланс", 
        "замовлен", "парсер", "скрипт", "python", "frontend", "backend", "crm"
    ],
    "negative_keywords": [
        "шукаю роботу", "#резюме", "ищу работу", "junior", "готов к работе", 
        "моє резюме", "готовий працювати", "казино", "1win", "крипта", 
        "пасивний дохід", "сигнали", "арбітраж", "темки", "дропи", "карти",
        "біженці", "виплати", "житло", "оренда", "барахолка"
    ],
    
    # Авто-вступ у чати
    "auto_join_enabled": True,
    "auto_join_delay_seconds": 120,
    "target_chats_limit": 50,
    
    # Сповіщення в Telegram
    "notify_on_lead": True,
    "notify_on_chat_join": True,
    "notify_on_error": True
}

async def get_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        await save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        async with aiofiles.open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
            # Доповнюємо дефолтними полями, якщо додались нові
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_SETTINGS.copy()

async def save_settings(new_settings: dict):
    async with aiofiles.open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(new_settings, ensure_ascii=False, indent=2))
