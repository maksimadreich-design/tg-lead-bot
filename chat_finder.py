import asyncio
import logging
import re
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.types import Channel
from telethon.errors import FloodWaitError, UserAlreadyParticipantError
from alert_bot import notify_admin, STATS

logger = logging.getLogger("CHAT_FINDER")

JOIN_DELAY_SECONDS = 120

# Ваші пріоритетні джерела (канали та групи замовлень)
TARGET_SOURCES = [
    "freelance_for_ukraine",        # Український Freelance
    "FreelancehuntProjects",        # Freelancehunt Projects
    "FreelancehuntJobs",            # Freelancehunt Jobs
    "nofluffjobsukraine",           # No Fluff Jobs Ukraine
    "freelance_in_ukraine",         # Freelance in Ukraine
    "work_hub_0",                   # Work Hub
    "https://t.me/+TAnlc22ehOBlOGYy", # Приватний інвайт чат
    # Додаткові топові профільні IT-чати
    "robota_itszp",
    "freelanceukraine",
    "dev_ua_chat",
    "freelance_ua_orders",
    "python_ua",
    "frontend_ukraine"
]

# Стоп-слова: біженці, візи, допомога, оренда, барахолка
JUNK_CHAT_MARKERS = [
    "avito", "авито", "россия", "москва", "питер", "спб", "рф", "рублей", "руб",
    "захист", "біженці", "допомога", "італія", "польща", "німеччина", "віза", 
    "виплати", "житло", "оренда", "попутники", "перевезення", "знайомства",
    "барахолка", "куплю", "продам", "авто", "одяг", "манікюр", "робота в польщі"
]

def is_junk_chat(title: str, username: str = "") -> bool:
    content = f"{title} {username}".lower()
    return any(marker in content for marker in JUNK_CHAT_MARKERS)

async def join_target_source(client: TelegramClient, source: str) -> bool:
    """Універсальне підключення до каналу, групи або приватного інвайт-посилання."""
    try:
        # 1. Якщо це приватне інвайт-посилання (+TAnlc22ehOBlOGYy або joinchat)
        if "+" in source or "joinchat" in source:
            match = re.search(r'(?:\+|\/joinchat\/)([a-zA-Z0-9_-]+)', source)
            if match:
                hash_code = match.group(1)
                try:
                    updates = await client(ImportChatInviteRequest(hash_code))
                    STATS["joined_chats"] += 1
                    chat_name = "Приватний чат"
                    if hasattr(updates, 'chats') and updates.chats:
                        chat_name = updates.chats[0].title
                    await notify_admin(f"🎯 **Успішно приєднався до інвайт-чату:**\n*{chat_name}*")
                    logger.info(f"✅ Вступив по інвайту: {chat_name}")
                    await asyncio.sleep(JOIN_DELAY_SECONDS)
                    return True
                except UserAlreadyParticipantError:
                    logger.info(f"Вже учасник інвайт-чату: {source}")
                    return True
                except Exception as e:
                    logger.warning(f"Не вдалося вступити по інвайту {source}: {e}")
            return False

        # 2. Якщо це публічний username/посилання
        clean_tag = source.replace("https://t.me/s/", "").replace("https://t.me/", "").replace("@", "").split("/")[0]
        entity = await client.get_entity(clean_tag)
        
        title = getattr(entity, 'title', clean_tag)
        uname = f"@{getattr(entity, 'username', clean_tag)}"

        if is_junk_chat(title, uname):
            logger.info(f"Пропуск нецільового чату: {title}")
            return False

        # Якщо ми ще не там
        if getattr(entity, 'left', True):
            await client(JoinChannelRequest(entity))
            STATS["joined_chats"] += 1
            await notify_admin(
                f"💻 **Додано цільове джерело:**\n*{title}* ({uname})\n"
                f"Всього джерел у моніторингу: {STATS['joined_chats']}\n"
                f"⏳ Інтервал: 2 хв."
            )
            logger.info(f"✅ Успішно підключено: {title}. Пауза {JOIN_DELAY_SECONDS}с...")
            await asyncio.sleep(JOIN_DELAY_SECONDS)
            return True
        else:
            logger.info(f"Вже підписані на: {title}")
            return True

    except FloodWaitError as e:
        wait_min = round(e.seconds / 60, 1)
        await notify_admin(f"⏳ **Telegram ліміт:** пауза на {wait_min} хв перед наступним вступом.")
        await asyncio.sleep(e.seconds + 5)
    except Exception as e:
        logger.warning(f"Помилка підключення до {source}: {e}")
        await asyncio.sleep(5)
    return False

async def auto_discover_and_join_chats(client: TelegramClient, target_chats_count: int = 30):
    STATS["last_action"] = "Підключення вказаних користувачем цільових IT-каналів..."
    await notify_admin("🎯 **Починаю підключення до ваших персональних IT/Freelance джерел...**")

    # 1. Підключаємо ваші джерела одне за одним
    for src in TARGET_SOURCES:
        await join_target_source(client, src)

    STATS["last_action"] = f"Моніторинг {STATS['joined_chats']} цільових IT-джерел у реальному часі."
    await notify_admin(f"✅ **Усі ваші джерела підключено!** Моніторинг активний 24/7.")
