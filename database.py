import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "leads.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id INTEGER,
                chat_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (message_id, chat_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                sender_username TEXT,
                sender_name TEXT,
                chat_title TEXT,
                chat_username TEXT,
                message_text TEXT,
                ai_summary TEXT,
                ai_pitch TEXT,
                relevance_score INTEGER,
                message_link TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def is_message_processed(message_id: int, chat_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM processed_messages WHERE message_id = ? AND chat_id = ?",
            (message_id, chat_id)
        )
        row = await cursor.fetchone()
        return row is not None

async def mark_message_processed(message_id: int, chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO processed_messages (message_id, chat_id) VALUES (?, ?)",
            (message_id, chat_id)
        )
        await db.commit()

async def save_lead(
    sender_id: int,
    sender_username: str,
    sender_name: str,
    chat_title: str,
    chat_username: str,
    message_text: str,
    ai_summary: str,
    ai_pitch: str,
    relevance_score: int,
    message_link: str
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO leads (
                sender_id, sender_username, sender_name,
                chat_title, chat_username, message_text,
                ai_summary, ai_pitch, relevance_score, message_link
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sender_id, sender_username, sender_name,
            chat_title, chat_username, message_text,
            ai_summary, ai_pitch, relevance_score, message_link
        ))
        await db.commit()
        return cursor.lastrowid
