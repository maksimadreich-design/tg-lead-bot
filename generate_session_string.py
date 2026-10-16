import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import config

async def main():
    print("\n--- ГЕНЕРАТОР STRING SESSION ДЛЯ RENDER ---")
    async with TelegramClient(StringSession(), config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH) as client:
        session_str = client.session.save()
        print("\n" + "="*60)
        print("ВАШ РЯДОК СЕСІЇ (скопіюйте його повністю):")
        print("="*60)
        print(session_str)
        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
