import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import Channel
from telethon.errors import FloodWaitError
from alert_bot import notify_admin, STATS

logger = logging.getLogger("CHAT_FINDER")

# Інтервал вступу: 2 хвилини
JOIN_DELAY_SECONDS = 120

# Суто комерційні, розробницькі та фріланс-запити
DEV_SEARCH_QUERIES = [
    "замовлення ботів", "розробка ботів", "потрібен розробник",
    "замовлення сайтів", "веб розробка замовлення", "it замовлення",
    "фріланс розробка", "потрібен програміст", "створення сайтів замовлення",
    "парсер telegram замовлення", "python розробка замовлення", "it проекти фріланс"
]

# Топові цільові українські чати розробки та бірж завдань
CURATED_DEV_CHATS = [
    "robota_itszp",
    "freelanceukraine",
    "dev_ua_chat",
    "freelance_ua_orders",
    "itvacanciesukraine",
    "python_ua",
    "frontend_ukraine",
    "jobs_it_ua",
    "fl_ua_chat",
    "it_orders_ukraine",
    "webdev_ua",
    "telegram_bots_ua"
]

# Стоп-слова для груп: біженці, візи, допомога, оренда, побутові теми
JUNK_CHAT_MARKERS = [
    "avito", "авито", "россия", "москва", "питер", "спб", "рф", "рублей", "руб",
    "захист", "біженці", "допомога", "італія", "польща", "німеччина", "віза", 
    "виплати", "житло", "оренда", "попутники", "перевезення", "знайомства",
    "барахолка", "куплю", "продам", "авто", "одяг", "манікюр", "робота в польщі"
]

# Обов'язкові ключові слова: група має бути пов'язана з IT / розробкою
REQUIRED_KEYWORDS = [
    "it", "dev", "бот", "bot", "сайт", "web", "розроб", "програм", "фриланс", 
    "фріланс", "freelance", "замовлен", "code", "python", "frontend", "backend"
]

def is_junk_or_non_it_chat(title: str, username: str = "") -> bool:
    content = f"{title} {username}".lower()
    
    # 1. Відсікаємо будь-яке сміття (біженці, оренда, країни, барахолки, ру-чати)
    if any(marker in content for marker in JUNK_CHAT_MARKERS):
        return True
        
    # 2. Якщо в назві або юзернеймі взагалі немає жодного натяку на IT/розробку/сайти
    if not any(req in content for req in REQUIRED_KEYWORDS):
        return True
        
    return False

async def clean_junk_chats(client: TelegramClient):
    """Виходить з усіх лівих груп (біженці, допомога, ру-чати, барахолки)."""
    logger.info("🧹 Очищення від нецільових груп...")
    removed_count = 0
    try:
        dialogs = await client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_channel or dialog.is_group:
                title = dialog.title or ""
                entity = dialog.entity
                username = getattr(entity, 'username', '') or ''
                if is_junk_or_non_it_chat(title, username):
                    logger.info(f"🚫 Виходимо з нецільового чату: {title}")
                    try:
                        await client(LeaveChannelRequest(entity))
                        removed_count += 1
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.warning(f"Не вдалося вийти з {title}: {e}")
        if removed_count > 0:
            await notify_admin(f"🧹 **Очищення:** видалено {removed_count} нерелевантних чатів (біженці/барахолки).")
    except Exception as e:
        logger.error(f"Помилка очищення: {e}")

async def try_join_chat(client: TelegramClient, peer_or_tag) -> bool:
    try:
        entity = await client.get_entity(peer_or_tag)
        if isinstance(entity, Channel) and getattr(entity, 'left', True):
            title = entity.title or "Без назви"
            uname = f"@{entity.username}" if entity.username else "приватний"
            
            # Жорстка перевірка: тільки IT, сайти, боти, фріланс
            if is_junk_or_non_it_chat(title, uname):
                logger.info(f"Пропуск нецільового чату: {title}")
                return False

            await client(JoinChannelRequest(entity))
            STATS["joined_chats"] += 1
            await notify_admin(
                f"💻 **Додано цільовий IT/Dev чат:**\n*{title}* ({uname})\n"
                f"Всього чатів у системі: {STATS['joined_chats']}\n"
                f"⏳ Наступний вступ через 2 хвилини."
            )
            logger.info(f"✅ Вступив у {title}. Пауза {JOIN_DELAY_SECONDS}с...")
            await asyncio.sleep(JOIN_DELAY_SECONDS)
            return True
    except FloodWaitError as e:
        wait_min = round(e.seconds / 60, 1)
        await notify_admin(f"⏳ **Telegram ліміт:** пауза на {wait_min} хв перед наступним вступом.")
        await asyncio.sleep(e.seconds + 5)
    except Exception as e:
        logger.debug(f"Пропуск {peer_or_tag}: {e}")
        await asyncio.sleep(4)
    return False

async def auto_discover_and_join_chats(client: TelegramClient, target_chats_count: int = 30):
    await clean_junk_chats(client)
    
    STATS["last_action"] = "Підключення профільних IT-чатів із замовленнями..."
    await notify_admin("💻 **Запущено пошук СУТО IT/WEB/DEV чатів (сайти, боти, автоматизація, фріланс).**")

    # 1. Додаємо перевірені IT-спільноти
    for chat_tag in CURATED_DEV_CHATS:
        if STATS["joined_chats"] >= target_chats_count:
            break
        await try_join_chat(client, chat_tag)

    # 2. Пошук виключно за комерційними IT-запитами
    for query in DEV_SEARCH_QUERIES:
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

    STATS["last_action"] = f"Моніторинг {STATS['joined_chats']} IT-чатів у реальному часі."
    await notify_admin(f"✅ **Пул IT-чатів зібрано!** Всього профільних чатів: {STATS['joined_chats']}.")
