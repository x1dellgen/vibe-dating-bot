from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# НАСТРОЙКА CORS (Важно!)
# Наш React-сайт будет работать на порту 5173, а Python-сервер — на порту 8000.
# Чтобы браузер разрешил им общаться, нужно включить CORS-политику.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # адрес нашего React-сервера
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Описываем модель данных, которую мы ждем от React (схема анкеты)
class ProfileData(BaseModel):
    telegram_id: int
    name: str
    age: int
    city: str

# Тестовый маршрут для проверки, что сервер вообще живой
@app.get("/")
def home():
    return {"status": "FastAPI работает!"}

# Маршрут для приема анкеты от Mini App
@app.post("/api/register")
def register_user(data: ProfileData):
    print("\n--- ПОЛУЧЕНЫ ДАННЫЕ ОТ MINI APP ---")
    print(f"Telegram ID: {data.telegram_id}")
    print(f"Имя: {data.name}")
    print(f"Возраст: {data.age}")
    print(f"Город: {data.city}")
    print("-----------------------------------\n")
    
    # Здесь на следующем этапе мы вызовем функцию из database.py
    # db.add_user(data.telegram_id, data.name, data.age, data.city)
    
    return {"success": True, "message": "Анкета успешно сохранена в базу!"}