import aiosqlite, json, os

DB = "chats.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT UNIQUE,
                messages TEXT
            )
        """)
        await db.commit()

async def load_chat(target):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT messages FROM chats WHERE target=?", (target,))
        row = await cur.fetchone()
        return json.loads(row[0]) if row else []

async def save_message(target, role, text):
    msgs = await load_chat(target)
    msgs.append({"role": role, "text": text})
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT OR REPLACE INTO chats(target, messages)
            VALUES(?, ?)
        """, (target, json.dumps(msgs, ensure_ascii=False)))
        await db.commit()