import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import config

logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Глобальна статистика в пам'яті
STATS = {
    "scanned": 0,
    "filtered_out": 0,
    "leads_found": 0,
    "joined_chats": 0,
    "last_action": "Запуск системи..."
}

async def notify_admin(text: str):
    """Швидке системне сповіщення адміну про стан, дії або помилки."""
    if not config.ADMIN_TELEGRAM_ID:
        return
    try:
        await bot.send_message(
            chat_id=config.ADMIN_TELEGRAM_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Не вдалося надіслати повідомлення адміну: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if str(message.from_user.id) != str(config.ADMIN_TELEGRAM_ID):
        await message.answer("Доступ заборонено.")
        return
    await message.answer(
        "👋 **Вітаю! Сервіс лідогенерації активовано.**\n\n"
        "Команди керування:\n"
        "📊 `/status` — актуальний стан, що зараз робить бот і скільки опрацьовано повідомлень.\n"
        "🔍 `/find` — запустити пошук нових чатів прямо зараз.\n\n"
        "Я надсилатиму сюди кожен знайдений лід, а також критичні сповіщення/помилки.",
        parse_mode="Markdown"
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    if str(message.from_user.id) != str(config.ADMIN_TELEGRAM_ID):
        return
    text = (
        f"📊 **Поточний стан системи:**\n\n"
        f"⚡ **Остання дія:**\n_{STATS['last_action']}_\n\n"
        f"📥 **Прочитано повідомлень:** {STATS['scanned']}\n"
        f"🗑 **Відсіяно спаму/нерелевантного:** {STATS['filtered_out']}\n"
        f"🎯 **Знайдено гарячих лідів:** {STATS['leads_found']}\n"
        f"📢 **Підключено нових груп:** {STATS['joined_chats']}"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("find"))
async def cmd_find(message: types.Message):
    if str(message.from_user.id) != str(config.ADMIN_TELEGRAM_ID):
        return
    await message.answer("🔍 Запускаю позачерговий пошук нових чатів...")
    from userbot import client as userbot_client
    from chat_finder import auto_discover_and_join_chats
    import asyncio
    asyncio.create_task(auto_discover_and_join_chats(userbot_client, max_chats_to_join=10))

async def send_lead_card(
    lead_id: int,
    sender_id: int,
    sender_username: str,
    sender_name: str,
    chat_title: str,
    message_text: str,
    ai_summary: str,
    ai_pitch: str,
    relevance_score: int,
    message_link: str
):
    if not config.ADMIN_TELEGRAM_ID:
        return

    STATS["leads_found"] += 1

    if sender_username:
        user_url = f"https://t.me/{sender_username}"
        user_tag = f"@{sender_username}"
    else:
        user_url = f"tg://user?id={sender_id}"
        user_tag = f"[{sender_name}]({user_url})"

    text = (
        f"🎯 **НОВИЙ ЛІД (Релевантність: {relevance_score}%)**\n\n"
        f"👤 **Замовник:** {user_tag}\n"
        f"📍 **Джерело (чат):** {chat_title}\n\n"
        f"📝 **Суть запиту:**\n{ai_summary}\n\n"
        f"💬 **Оригінал повідомлення:**\n_{message_text}_\n\n"
        f"🤖 **Згенерована відповідь (Pitch):**\n`{ai_pitch}`\n"
        f"_(натисніть на текст вище, щоб скопіювати)_"
    )

    buttons = []
    buttons.append([InlineKeyboardButton(text="💬 Написати замовнику", url=user_url)])
    if message_link:
        buttons.append([InlineKeyboardButton(text="🔗 Повідомлення в чаті", url=message_link)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await bot.send_message(
            chat_id=config.ADMIN_TELEGRAM_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Не вдалося надіслати картку ліда в Telegram: {e}")
