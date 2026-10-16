import logging
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import config
from database import is_message_processed, mark_message_processed, save_lead
from ai_analyzer import AIAnalyzer
from alert_bot import send_lead_card, notify_admin, STATS

logger = logging.getLogger(__name__)

ai = AIAnalyzer()

# Якщо є TELEGRAM_STRING_SESSION (для хмари Render) — використовуємо її, інакше локальний файл
session_source = StringSession(config.TELEGRAM_STRING_SESSION) if config.TELEGRAM_STRING_SESSION else "userbot_session"

client = TelegramClient(
    session_source,
    config.TELEGRAM_API_ID,
    config.TELEGRAM_API_HASH
)

STOP_WORDS = [
    "шукаю роботу", "#резюме", "ищу работу", "junior", "готов к работе", 
    "моє резюме", "готовий працювати", "казино", "1win", "крипта", 
    "пасивний дохід", "сигнали", "арбітраж трафіку"
]

def fast_filter(text: str) -> bool:
    if not text or len(text.strip()) < 20:
        return False
    lower_text = text.lower()
    for word in STOP_WORDS:
        if word in lower_text:
            return False
    return True

@client.on(events.NewMessage)
async def handle_new_message(event):
    if event.is_private:
        return

    chat = await event.get_chat()
    chat_title = getattr(chat, 'title', 'Невідомий чат')
    chat_username = getattr(chat, 'username', None)
    
    # Фільтр проти руснявих чатів
    from chat_finder import is_russian_chat
    if is_russian_chat(chat_title, chat_username or ""):
        return
    
    msg_id = event.message.id
    chat_id = event.chat_id
    text = event.message.message or ""

    STATS["scanned"] += 1

    if await is_message_processed(msg_id, chat_id):
        return
    await mark_message_processed(msg_id, chat_id)

    # 1. Швидкий фільтр стоп-слів
    if not fast_filter(text):
        STATS["filtered_out"] += 1
        return

    sender = await event.get_sender()
    if getattr(sender, 'bot', False):
        return  # Ігноруємо повідомлення від інших ботів (економить ліміти Gemini)

    sender_id = getattr(sender, 'id', 0)
    sender_username = getattr(sender, 'username', '')
    first_name = getattr(sender, 'first_name', '') or ''
    last_name = getattr(sender, 'last_name', '') or ''
    sender_name = f"{first_name} {last_name}".strip() or "Користувач"

    # Якщо юзер без юзернейма, get_sender() іноді повертає None або Channel
    if not sender_id and event.message.from_id:
        from_id_obj = event.message.from_id
        sender_id = getattr(from_id_obj, 'user_id', 0)

    # Надійне формування посилання на повідомлення в чаті
    if chat_username:
        msg_link = f"https://t.me/{chat_username}/{msg_id}"
    else:
        # Для приватних супергруп (формат c/ID/MSG_ID)
        clean_chat_id = str(chat_id).replace("-100", "").replace("-", "")
        msg_link = f"https://t.me/c/{clean_chat_id}/{msg_id}"

    STATS["last_action"] = f"Аналіз повідомлення від {sender_name} у '{chat_title}'"
    logger.info(f"🔍 Аналізуємо повідомлення з '{chat_title}' від {sender_name}...")

    # 2. ШІ-аналіз через Gemini з динамічними налаштуваннями
    from settings_manager import get_settings
    settings = await get_settings()

    min_score = settings.get("min_relevance_score", 75)

    try:
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(None, ai.analyze_message, text)
    except Exception as err:
        logger.error(f"Помилка аналізу ШІ: {err}")
        return

    # 3. Якщо це замовник із чітким технічним завданням та доступним контактом
    if analysis.is_client_request and analysis.relevance_score >= min_score and sender_id != 0:
        logger.info(f"🔥 ЗНАЙДЕНО ЛІД! Релевантність: {analysis.relevance_score}% | {sender_name}")
        
        lead_id = await save_lead(
            sender_id=sender_id,
            sender_username=sender_username,
            sender_name=sender_name,
            chat_title=chat_title,
            chat_username=chat_username or "",
            message_text=text,
            ai_summary=analysis.summary,
            ai_pitch=analysis.suggested_pitch,
            relevance_score=analysis.relevance_score,
            message_link=msg_link
        )

        await send_lead_card(
            lead_id=lead_id,
            sender_id=sender_id,
            sender_username=sender_username,
            sender_name=sender_name,
            chat_title=chat_title,
            message_text=text,
            ai_summary=analysis.summary,
            ai_pitch=analysis.suggested_pitch,
            relevance_score=analysis.relevance_score,
            message_link=msg_link
        )

        # 4. 🤖 AI SALES MANAGER (Авто-відповідач 1-в-1 як в OSTRO AI)
        if settings.get("auto_reply_enabled", False):
            auto_min = settings.get("auto_reply_min_score", 85)
            if analysis.relevance_score >= auto_min and analysis.suggested_pitch:
                delay = settings.get("auto_reply_delay_seconds", 15)
                logger.info(f"🤖 AI Sales Manager: очікуємо {delay}с перед авто-відповіддю для {sender_name}...")
                await asyncio.sleep(delay)

                reply_mode = settings.get("auto_reply_mode", "chat_reply")
                try:
                    if reply_mode == "chat_reply":
                        # Відповідь реплаєм у чаті під повідомленням клієнта
                        await event.reply(analysis.suggested_pitch)
                        await notify_admin(f"🤖 **AI Sales Manager відповів клієнту в чаті:**\n*Чат:* {chat_title}\n*Клієнт:* {sender_name}\n*Текст:* `{analysis.suggested_pitch}`")
                    elif reply_mode == "direct_message" and sender_id:
                        # Відправка першого повідомлення напряму в ЛС
                        await client.send_message(sender_id, analysis.suggested_pitch)
                        await notify_admin(f"🤖 **AI Sales Manager написав клієнту в ЛС:**\n*Клієнт:* {sender_name} (@{sender_username})\n*Текст:* `{analysis.suggested_pitch}`")
                except Exception as auto_err:
                    logger.warning(f"Не вдалося виконати авто-відповідь: {auto_err}")
    else:
        STATS["filtered_out"] += 1
