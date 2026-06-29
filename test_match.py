import asyncio
import aiosqlite

DB_NAME = "dating.db" 

async def simulate_incoming_like():
    async with aiosqlite.connect(DB_NAME) as conn:
        # 1. Стираем твои старые действия в бэкенде, чтобы карточки обновились
        await conn.execute("DELETE FROM interactions WHERE user_id = 123456")
        
        # 2. Имитируем, что Анна (ID 987654321) лайкнула ТЕБЯ (ID 123456)
        await conn.execute('''
            INSERT OR REPLACE INTO interactions (user_id, target_id, action)
            VALUES (987654321, 123456, 'like')
        ''')
        await conn.commit()
    print("⚡ Симуляция через test_match.py успешна! Анна тайно поставила лайк твоему профилю (ID 123456).")

if __name__ == "__main__":
    asyncio.run(simulate_incoming_like())