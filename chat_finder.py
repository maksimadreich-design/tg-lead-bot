import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import Channel
from telethon.errors import FloodWaitError
from alert_bot import notify_admin, STATS

logger = logging.getLogger("CHAT_FINDER")

# Затримка між вступами: мінімум 5 хвилин (300 секунд) для повного захисту від банів
JOIN_DELAY_SECONDS = 300

UA_SEARCH_QUERIES = [
    "робота it україна", "вакансії україна it", "фріланс україна", 
    "замовлення сайти україна", "it чат україна", "потрібен розробник київ", 
    "робота фріланс україна", "веб розробка замовлення україна", 
    "потрібен бот україна", "айтішники україни", "замовлення ботів україна",
    "digital україна", "маркетинг україна замовлення"
]

CURATED_UA_CHATS = [
    "robota_itszp",
    "freelanceukraine",
    "it_jobs_ua",
    "itvacanciesukraine",
    "dev_ua_chat",
    "freelance_ua_orders",
    "ua_it_chat",
    "python_ua",
    "frontend_ukraine",
    "jobs_it_ua",
    "fl_ua_chat"
]

RU_MARKERS = [
    "avito", "авито", "россия", "москва", "питер", "спб", "рф", "рублей", 
    "руб", "яндекс", "wildberries", "вайлдберриз", "тинькофф", "сбер"
]

def is_russian_chat(title: str, username: str = "") -> bool:
    content = f"{title} {username}".lower()
    return any(marker in content for marker in RU_MARKERS)

async def clean_russian_chats(client: TelegramClient):
    logger.info("🧹 Очищення від руснявих чатів...")
    removed_count = 0
    try:
        dialogs = await client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_channel or dialog.is_group:
                title = dialog.title or ""
                entity = dialog.entity
                username = getattr(entity, 'username', '') or ''
                if is_russian_chat(title, username):
                    logger.info(f"🚫 Виходимо з руснявого чату: {title}")
                    try:
                        await client(LeaveChannelRequest(entity))
                        removed_count += 1
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.warning(f"Не вдалося вийти з {title}: {e}")
        if removed_count > 0:
            await notify_admin(f"🧹 **Очищення:** видалено руснявих чатів: {removed_count}")
    except Exception as e:
        logger.error(f"Помилка очищення: {e}")

async def try_join_chat(client: TelegramClient, peer_or_tag) -> bool:
    """Безпечний вступ у чат з обробкою FloodWait."""
    try:
        entity = await client.get_entity(peer_or_tag)
        if isinstance(entity, Channel) and getattr(entity, 'left', True):
            title = entity.title or "Без назви"
            uname = f"@{entity.username}" if entity.username else "приватний"
            
            if is_russian_chat(title, uname):
                return False

            await client(JoinChannelRequest(entity))
            STATS["joined_chats"] += 1
            await notify_admin(
                f"🇺🇦 **Вступив у новий UA-чат:**\n*{title}* ({uname})\n"
                f"Всього чатів у системі: {STATS['joined_chats']}\n"
                f"⏳ Наступний вступ через 5 хвилин (захист акаунта)."
            )
            logger.info(f"✅ Вступив у {title}. Чекаємо {JOIN_DELAY_SECONDS}с перед наступним...")
            await asyncio.sleep(JOIN_DELAY_SECONDS)
            return True
    except FloodWaitError as e:
        wait_min = round(e.seconds / 60, 1)
        logger.warning(f"FloodWait від Telegram: очікуємо {wait_min} хв.")
        await notify_admin(f"⏳ **Telegram ліміт:** пауза на {wait_min} хв перед наступним вступом у групи.")
        await asyncio.sleep(e.seconds + 5)
    except Exception as e:
        logger.debug(f"Пропуск {peer_or_tag}: {e}")
        await asyncio.sleep(5)
    return False

async def auto_discover_and_join_chats(client: TelegramClient, target_chats_count: int = 30):
    await clean_russian_chats(client)
    
    STATS["last_action"] = "Плавне підключення українських чатів (інтервал 5 хв)..."
    await notify_admin("🇺🇦 **Запущено безпечний авто-вступ в українські чати (інтервал: 1 чат раз на 5 хвилин).**")

    # 1. По черзі додаємо кураторські чати
    for chat_tag in CURATED_UA_CHATS:
        if STATS["joined_chats"] >= target_chats_count:
            break
        await try_join_chat(client, chat_tag)

    # 2. Глобальний пошук нових чатів
    for query in UA_SEARCH_QUERIES:
        if STATS["joined_chats"] >= target_chats_count:
            break
        try:
            res = await client(SearchRequest(q=query, limit=10))
            for peer in res.chats:
                if STATS["joined_chats"] >= target_chats_count:
                    break
                if isinstance(peer, Channel) and (peer.megagroup or peer.gigagroup):
                    await try_join_chat(client, peer)
        except Exception as err:
            logger.error(f"Помилка пошуку '{query}': {err}")
            await asyncio.sleep(10)

    STATS["last_action"] = f"Моніторинг {STATS['joined_chats']} українських чатів у реальному часі."
    await notify_admin(f"✅ **Пул цільових груп сформовано!** Всього чатів: {STATS['joined_chats']}.")
