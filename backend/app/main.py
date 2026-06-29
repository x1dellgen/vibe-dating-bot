from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import aiosqlite
import sqlite3

DB_NAME = "dating.db"

app = FastAPI()

# Надежная настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Полная модель регистрации (теперь с поддержкой аватарки)
class UserRegister(BaseModel):
    telegram_id: int
    username: str
    name: str
    age: int
    city: str
    gender: str
    preference: str
    description: Optional[str] = ""
    search_scope: str = "City"
    avatar_url: Optional[str] = ""  # Учли пустое или заполненное поле фото

class ActionModel(BaseModel):
    user_id: int
    target_id: int
    action: str
    message: Optional[str] = None

# Автоматическое исправление структуры БД при запуске
@app.on_event("startup")
async def startup_event():
    async with aiosqlite.connect(DB_NAME) as conn:
        # 1. Базовое создание таблиц
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT,
                age INTEGER,
                city TEXT,
                gender TEXT,
                preference TEXT,
                description TEXT
            )
        ''')
        
        # 2. Умная миграция: добавляем колонки в users, если файл базы данных уже существовал
        missing_columns = [
            ("search_scope", "TEXT DEFAULT 'City'"),
            ("avatar_url", "TEXT DEFAULT ''"),
            ("registration_complete", "INTEGER DEFAULT 0")
        ]
        for col_name, col_type in missing_columns:
            try:
                await conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass  # Колонка уже есть, пропускаем
                
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                target_id INTEGER,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        try:
            await conn.execute("ALTER TABLE interactions ADD COLUMN message TEXT")
        except sqlite3.OperationalError:
            pass
            
        await conn.commit()
    print("\n==================================================")
    print("🚀 БАЗА ДАННЫХ И КОЛОНКИ УСПЕШНО СИНХРОНИЗИРОВАНЫ!")
    print("==================================================\n")

# --- ЭНДПОИНТЫ ---

@app.post("/api/register")
async def register_user(data: UserRegister):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute('''
            INSERT OR REPLACE INTO users (
                telegram_id, username, name, age, city, gender, preference, description, search_scope, avatar_url, registration_complete
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (data.telegram_id, data.username, data.name, data.age, data.city, data.gender, data.preference, data.description, data.search_scope, data.avatar_url))
        await conn.commit()
    return {"success": True, "message": "Профиль успешно сохранен"}

@app.get("/api/catalog")
async def get_catalog(current_user_id: Optional[int] = None, city: Optional[str] = None, age_from: Optional[int] = None, age_to: Optional[int] = None):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM users WHERE registration_complete = 1"
        params = []
        
        if current_user_id:
            query += " AND telegram_id != ?"
            params.append(current_user_id)
        if city:
            query += " AND city LIKE ?"
            params.append(f"%{city}%")
        if age_from:
            query += " AND age >= ?"
            params.append(age_from)
        if age_to:
            query += " AND age <= ?"
            params.append(age_to)
            
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return {"profiles": [dict(r) for r in rows]}

@app.get("/api/user/{user_id}")
async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        async with conn.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if user:
                return dict(user)
            raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/match/next/{user_id}")
async def get_next_candidate(user_id: int):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        async with conn.execute("SELECT gender, preference FROM users WHERE telegram_id = ?", (user_id,)) as cursor:
            current_user = await cursor.fetchone()
            if not current_user:
                return {"candidate": None, "message": "Сначала создайте анкету!"}
        
        async with conn.execute("SELECT target_id FROM interactions WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            voted_ids = [r['target_id'] for r in rows]
            voted_ids.append(user_id)
            
        query = "SELECT * FROM users WHERE registration_complete = 1 AND telegram_id NOT IN ({})".format(",".join(["?"] * len(voted_ids)))
        params = list(voted_ids)
        
        if current_user['preference'] != 'Всех':
            target_gender = 'Парень' if current_user['preference'] == 'Парней' else 'Девушка'
            query += " AND gender = ?"
            params.append(target_gender)
            
        query += " LIMIT 1"
        
        async with conn.execute(query, params) as cursor:
            candidate = await cursor.fetchone()
            if candidate:
                return {"candidate": dict(candidate)}
            return {"candidate": None, "message": "Анкеты закончились!"}

@app.post("/api/match/action")
async def match_action(data: ActionModel):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute('''
            INSERT INTO interactions (user_id, target_id, action, message)
            VALUES (?, ?, ?, ?)
        ''', (data.user_id, data.target_id, data.action, data.message))
        await conn.commit()
        
        if data.action in ['like', 'superlike']:
            async with conn.execute('''
                SELECT id FROM interactions 
                WHERE user_id = ? AND target_id = ? AND action IN ('like', 'superlike')
            ''', (data.target_id, data.user_id)) as cursor:
                match = await cursor.fetchone()
                if match:
                    return {"success": True, "is_match": True}
                    
        return {"success": True, "is_match": False}

@app.get("/api/interactions/liked-you/{user_id}")
async def get_liked_you(user_id: int):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        query = '''
            SELECT u.* FROM users u
            JOIN interactions i ON i.user_id = u.telegram_id
            WHERE i.target_id = ? AND i.action IN ('like', 'superlike')
            AND u.telegram_id NOT IN (SELECT target_id FROM interactions WHERE user_id = ?)
        '''
        async with conn.execute(query, (user_id, user_id)) as cursor:
            rows = await cursor.fetchall()
            return {"profiles": [dict(r) for r in rows]}

@app.get("/api/interactions/matches/{user_id}")
async def get_matches(user_id: int):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        query = '''
            SELECT u.* FROM users u
            WHERE u.telegram_id IN (
                SELECT i1.target_id FROM interactions i1
                JOIN interactions i2 ON i1.user_id = i2.target_id AND i1.target_id = i2.user_id
                WHERE i1.user_id = ? AND i1.action IN ('like', 'superlike') AND i2.action IN ('like', 'superlike')
            )
        '''
        async with conn.execute(query, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return {"matches": [dict(r) for r in rows]}