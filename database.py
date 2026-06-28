import aiosqlite

DB_NAME = "dating.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as conn:
        # Таблица пользователей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT,
                age INTEGER,
                city TEXT,
                gender TEXT,
                preference TEXT,
                description TEXT,
                search_scope TEXT,
                registration_complete INTEGER DEFAULT 0
            )
        ''')
        # Таблица фотографий
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                file_id TEXT
            )
        ''')
        # Таблица взаимодействий (лайки и дизлайки), чтобы не крутить анкеты по кругу
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                user_id INTEGER,
                target_id INTEGER,
                action TEXT,
                PRIMARY KEY (user_id, target_id)
            )
        ''')
        await conn.commit()

async def get_user_profile(user_id):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
        user_row = await cursor.fetchone()
        if not user_row:
            return None
        
        cursor = await conn.execute("SELECT file_id FROM photos WHERE telegram_id = ?", (user_id,))
        photo_rows = await cursor.fetchall()
        
        return {
            'info': dict(user_row),
            'photos': [{'file_id': row['file_id']} for row in photo_rows]
        }

async def register_user(user_id, username, name, age, city, gender, preference, description, search_scope):
    """Регистрация нового пользователя. Пригодна для вызова из любого API."""
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute('''
            INSERT OR REPLACE INTO users 
            (telegram_id, username, name, age, city, gender, preference, description, search_scope, registration_complete)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (user_id, username, name, age, city, gender, preference, description, search_scope))
        await conn.commit()

async def update_user_field(user_id, field_name, value):
    """
    Универсальная безопасная функция обновления атомарных полей профиля.
    Идеально подходит для API запросов вида PATCH /api/user/v1/
    """
    allowed_fields = ["name", "age", "city", "description", "preference", "search_scope"]
    if field_name not in allowed_fields:
        raise ValueError(f"Попытка изменения недопустимого поля: {field_name}")
        
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(f"UPDATE users SET {field_name} = ? WHERE telegram_id = ?", (value, user_id))
        await conn.commit()

async def update_user_photos(user_id, photo_list):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute("DELETE FROM photos WHERE telegram_id = ?", (user_id,))
        for file_id in photo_list:
            await conn.execute("INSERT INTO photos (telegram_id, file_id) VALUES (?, ?)", (user_id, file_id))
        await conn.commit()

async def add_interaction(user_id, target_id, action):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute('''
            INSERT OR REPLACE INTO interactions (user_id, target_id, action)
            VALUES (?, ?, ?)
        ''', (user_id, target_id, action))
        await conn.commit()

async def check_match(user_id, target_id):
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute('''
            SELECT action FROM interactions 
            WHERE user_id = ? AND target_id = ? AND action IN ('like', 'superlike')
        ''', (target_id, user_id))
        row = await cursor.fetchone()
        return row is not None

async def get_next_candidate(user_id):
    """
    Чистая функция подбора кандидата. Не зависит от Telegram API, 
    возвращает чистый словарь данных, готовый к сериализации в JSON для Mini App.
    """
    user_profile = await get_user_profile(user_id)
    if not user_profile:
        return None
    
    info = user_profile['info']
    user_gender = info['gender']       
    user_pref = info['preference']     
    user_city = info['city']
    user_scope = info['search_scope']  

    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        
        gender_clause = ""
        params = [user_id, user_id]
        
        if user_pref == "Девушек":
            gender_clause = "AND u.gender = 'Девушка'"
        elif user_pref == "Парней":
            gender_clause = "AND u.gender = 'Парень'"
            
        pref_clause = ""
        if user_gender == "Парень":
            pref_clause = "AND (u.preference = 'Парней' OR u.preference = 'Всех')"
        elif user_gender == "Девушка":
            pref_clause = "AND (u.preference = 'Девушек' OR u.preference = 'Всех')"
            
        scope_clause = ""
        if user_scope == "city":
            scope_clause = "AND u.city = ?"
            params.append(user_city)

        query = f'''
            SELECT u.telegram_id FROM users u
            WHERE u.registration_complete = 1
              AND u.telegram_id != ?
              AND u.telegram_id NOT IN (SELECT target_id FROM interactions WHERE user_id = ?)
              {gender_clause}
              {pref_clause}
              {scope_clause}
            LIMIT 1
        '''
        
        cursor = await conn.execute(query, params)
        row = await cursor.fetchone()
        if row:
            return await get_user_profile(row['telegram_id'])
        return None