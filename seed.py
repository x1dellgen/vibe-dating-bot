import asyncio
import aiosqlite

DB_NAME = "dating.db" 

async def populate_database():
    test_profiles = [
        (987654321, "anna_rock", "Анна", 21, "Санкт-Петербург", "Девушка", "Парней", "Люблю живую музыку, рок-концерты и Muse 🎸", "City", "", 1),
        (876543210, "masha_art", "Мария", 24, "Москва", "Девушка", "Всех", "Занимаюсь дизайном, ищу приятный вайб для общения ✨", "City", "", 1),
        (765432109, "dima_code", "Дмитрий", 25, "Санкт-Петербург", "Парень", "Девушек", "Пишу код на Python, катаюсь на сноуборде 🏂", "City", "", 1),
        (654321098, "elena_sport", "Елена", 23, "Санкт-Петербург", "Девушка", "Парней", "Фитнес-тренер, обожаю силовые тренировки и правильный движ 💪", "City", "", 1),
        (543210987, "katya_vibe", "Екатерина", 20, "Тверь", "Девушка", "Парней", "Учусь на лингвиста, люблю смотреть аниме и читать книги 📚", "City", "", 1)
    ]
    
    async with aiosqlite.connect(DB_NAME) as conn:
        # Очищаем старые взаимодействия, чтобы начать тесты с чистого листа
        await conn.execute("DELETE FROM interactions")
        
        for profile in test_profiles:
            await conn.execute('''
                INSERT OR REPLACE INTO users (
                    telegram_id, username, name, age, city, gender, preference, description, search_scope, avatar_url, registration_complete
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', profile)
            
        await conn.commit()
    print("🎉 База данных успешно заселена тестовыми анкетками через seed.py! Таблица лайков очищена.")

if __name__ == "__main__":
    asyncio.run(populate_database())