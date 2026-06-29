import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup 
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, 
                           InlineKeyboardButton, InputMediaPhoto, ReplyKeyboardRemove,
                           WebAppInfo) # 🎯 Шаг 1: Успешно импортировали WebAppInfo

from backend.app import database as db

# Загружаем переменные из файла .env
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN") 

if not API_TOKEN:
    exit("Ошибка: Токен бота не найден в файле .env!")

# 🎯 Шаг 2: Ссылка на твое Mini App из вкладки Ports в VS Code.
# ОБЯЗАТЕЛЬНО замени эту заглушку на свою реальную https-ссылку из VS Code!
MINI_APP_URL = "https://0ffm52n9-5173.euw.devtunnels.ms/"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- СОСТОЯНИЯ ---
class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    description = State()
    gender = State()
    photos = State()
    preference = State()
    scope = State()

class EditProfile(StatesGroup):
    editing_field = State()
    waiting_value = State()
    waiting_photos = State()

class Interaction(StatesGroup):
    superlike_msg = State()

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Смотреть анкеты 🔎")], [KeyboardButton(text="Мой профиль 👤")]], resize_keyboard=True)

def get_edit_menu():
    kb = [
        [InlineKeyboardButton(text="📝 Изменить имя", callback_data="edit_name")],
        [InlineKeyboardButton(text="🔢 Изменить возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="📍 Изменить город", callback_data="edit_city")],
        [InlineKeyboardButton(text="ℹ️ Изменить описание О себе", callback_data="edit_description")],
        [InlineKeyboardButton(text="📸 Обновить все фотографии", callback_data="edit_photos")],
        [InlineKeyboardButton(text="🔍 Изменить кого ищу", callback_data="edit_preference")],
        [InlineKeyboardButton(text="🌍 Изменить радиус поиска", callback_data="edit_scope")],
        [InlineKeyboardButton(text="🔄 Заполнить анкету с нуля", callback_data="start_reg")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def show_profile_card(user_id, target_dict, to_chat_id=None, kb=None, prefix=""):
    info = target_dict['info']
    photos = target_dict['photos']
    to_chat_id = to_chat_id or user_id
    
    caption = f"{prefix}{info['name']}, {info['age']}, {info['city']}\n\n{info['description']}"
    media = [InputMediaPhoto(media=p['file_id'], caption=caption if i == 0 else "") for i, p in enumerate(photos)]
    
    await bot.send_media_group(chat_id=to_chat_id, media=media)
    if kb:
        await bot.send_message(chat_id=to_chat_id, text="Действия:", reply_markup=kb)

async def show_next_candidate(message_or_call, user_id):
    candidate = await db.get_next_candidate(user_id)
    if not candidate:
        text = "Радар пуст! 🌍 Кажется, вы посмотрели все подходящие анкеты. Попробуйте изменить критерии поиска в профиле!"
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.message.answer(text)
        else:
            await message_or_call.answer(text)
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Лайк", callback_data=f"btn_like_{candidate['info']['telegram_id']}"),
            InlineKeyboardButton(text="👎 Пропустить", callback_data=f"btn_dislike_{candidate['info']['telegram_id']}")
        ],
        [
            InlineKeyboardButton(text="📩 Написать суперлайк", callback_data=f"btn_super_{candidate['info']['candidate']['telegram_id']}")
        ]
    ])
    await show_profile_card(user_id, candidate, kb=kb, prefix="✨ Найдена анкета:\n")

# --- РЕГИСТРАЦИЯ ---

# 🎯 Шаг 3: Обновили команду /start под запуск Mini App
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() # Мягко сбрасываем любые старые FSM-состояния, чтобы не было конфликтов
    await db.init_db()
    
    if not message.from_user.username:
        return await message.answer("⚠️ Установи username в настройках Telegram и напиши /start снова!")
    
    # Создаем кнопку-ссылку, которая откроет наше WebApp прямо внутри интерфейса Telegram
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔥 Открыть VibeDating", 
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]
    ])
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в **VibeDating** — дейтинг-сервис нового поколения внутри Telegram.\n"
        "Нажми на кнопку ниже, чтобы открыть приложение, настроить свой профиль и начать поиск! ✨",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "start_reg")
async def start_reg(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Как тебя зовут?")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def reg_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 99):
        return await message.answer("Введи число от 10 до 99:")
    await state.update_data(age=int(message.text))
    await message.answer("Твой город?")
    await state.set_state(Registration.city)

@dp.message(Registration.city)
async def reg_city(message: types.Message, state: FSMContext):
    if not all(c.isalpha() or c in "- " for c in message.text):
        return await message.answer("В названии города только буквы! Попробуй снова:")
    await state.update_data(city=message.text)
    await message.answer("Расскажи о себе (до 300 символов):")
    await state.set_state(Registration.description)

@dp.message(Registration.description)
async def reg_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text[:300])
    await message.answer("Твой пол:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Парень", callback_data="rg_Парень"), InlineKeyboardButton(text="Девушка", callback_data="rg_Девушка")]
    ]))
    await state.set_state(Registration.gender)

@dp.callback_query(Registration.gender)
async def reg_gender(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(gender=call.data.split('_')[1])
    await call.message.answer("Пришли от 1 до 4 фото. Когда закончишь — жми 'Готово'", 
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Готово ✅", callback_data="photos_done")]]))
    await state.update_data(photo_list=[])
    await state.set_state(Registration.photos)

@dp.message(Registration.photos, F.photo)
async def reg_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    plist = data.get('photo_list', [])
    if len(plist) < 4:
        plist.append(message.photo[-1].file_id)
        await state.update_data(photo_list=plist)
        await message.answer(f"Фото {len(plist)}/4 получено.")
    else:
        await message.answer("Максимум 4 фото!")

@dp.callback_query(F.data == "photos_done", Registration.photos)
async def photos_done(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Кого ищем?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Девушек", callback_data="rp_Девушек"), InlineKeyboardButton(text="Парней", callback_data="rp_Парней")],
        [InlineKeyboardButton(text="Всех", callback_data="rp_Всех")]
    ]))
    await state.set_state(Registration.preference)

@dp.callback_query(Registration.preference)
async def reg_pref(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(preference=call.data.split('_')[1])
    await call.message.answer("Где искать анкеты?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 В моем городе", callback_data="rs_city")],
        [InlineKeyboardButton(text="🌍 По всей стране", callback_data="rs_all")]
    ]))
    await state.set_state(Registration.scope)

@dp.callback_query(Registration.scope)
async def reg_final(call: types.CallbackQuery, state: FSMContext):
    scope = call.data.split('_')[1]
    d = await state.get_data()
    
    await db.register_user(
        user_id=call.from_user.id,
        username=call.from_user.username,
        name=d['name'],
        age=d['age'],
        city=d['city'],
        gender=d['gender'],
        preference=d['preference'],
        description=d['description'],
        search_scope=scope
    )
        
    await db.update_user_photos(call.from_user.id, d['photo_list'])
    await state.clear()
    await call.message.answer("Готово!", reply_markup=get_main_menu())
    user = await db.get_user_profile(call.from_user.id)
    await show_profile_card(call.from_user.id, user)

# --- ПРОСМОТР АНКЕТ (ПОИСК) ---

@dp.message(F.text == "Смотреть анкеты 🔎")
async def cmd_browse_profiles(message: types.Message):
    user = await db.get_user_profile(message.from_user.id)
    if not user or not user['info']['registration_complete']:
        return await message.answer("⚠️ Сначала необходимо зарегистрироваться! Нажми /start")
    
    await show_next_candidate(message, message.from_user.id)

@dp.callback_query(F.data.startswith("btn_like_"))
async def handle_like(call: types.CallbackQuery):
    target_id = int(call.data.split('_')[2])
    user_id = call.from_user.id
    
    await db.add_interaction(user_id, target_id, 'like')
    await call.answer("Вы поставили лайк! ❤️")
    
    is_match = await db.check_match(user_id, target_id)
    if is_match:
        user_profile = await db.get_user_profile(user_id)
        target_profile = await db.get_user_profile(target_id)
        
        await call.message.answer(f"🎉 Совпадение! Вы понравились {target_profile['info']['name']}!\nСсылка: @{target_profile['info']['username']}")
        try:
            await bot.send_message(chat_id=target_id, text=f"🎉 Совпадение! Вы понравились {user_profile['info']['name']}!\nСсылка: @{user_profile['info']['username']}")
        except Exception:
            pass
            
    await call.message.edit_reply_markup(reply_markup=None)
    await show_next_candidate(call, user_id)

@dp.callback_query(F.data.startswith("btn_dislike_"))
async def handle_dislike(call: types.CallbackQuery):
    target_id = int(call.data.split('_')[2])
    user_id = call.from_user.id
    
    await db.add_interaction(user_id, target_id, 'dislike')
    await call.answer("Пропущено 👎")
    await call.message.edit_reply_markup(reply_markup=None)
    await show_next_candidate(call, user_id)

@dp.callback_query(F.data.startswith("btn_super_"))
async def handle_super_click(call: types.CallbackQuery, state: FSMContext):
    target_id = int(call.data.split('_')[2])
    await state.update_data(target_id=target_id)
    await state.set_state(Interaction.superlike_msg)
    await call.message.answer("Напиши сообщение для суперлайка (оно доставится вместе с твоей анкетой):")
    await call.message.edit_reply_markup(reply_markup=None)

@dp.message(Interaction.superlike_msg)
async def process_superlike_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("target_id")
    user_id = message.from_user.id
    
    await db.add_interaction(user_id, target_id, 'superlike')
    user_profile = await db.get_user_profile(user_id)
    await message.answer("Суперлайк успешно отправлен! 🚀")
    
    try:
        await bot.send_message(chat_id=target_id, text=f"🔥 Получен СУПЕРЛАЙК от @{user_profile['info']['username']}!\nСообщение: {message.text}")
        await show_profile_card(target_id, user_profile, to_chat_id=target_id)
    except Exception:
        pass
        
    await state.clear()
    await show_next_candidate(message, user_id)

# --- РЕДАКТИРОВАНИЕ ---

@dp.message(F.text == "Мой профиль 👤")
async def my_profile(message: types.Message):
    user = await db.get_user_profile(message.from_user.id)
    if not user or not user['info']['registration_complete']:
        return await message.answer("⚠️ Сначала пройдите регистрацию через /start")
    await show_profile_card(message.from_user.id, user, kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отредактировать 📝", callback_data="edit_menu")]]))

@dp.callback_query(F.data == "edit_menu")
async def edit_menu_call(call: types.CallbackQuery):
    await call.message.answer("Что изменить?", reply_markup=get_edit_menu())

@dp.callback_query(F.data.startswith("edit_"))
async def edit_field(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split('_')[1]
    
    if field in ["name", "age", "city", "description"]:
        await state.update_data(editing_field=field)
        await state.set_state(EditProfile.waiting_value)
        
        if field == "name": await call.message.answer("Введи новое имя:")
        elif field == "age": await call.message.answer("Введи новый возраст:")
        elif field == "city": await call.message.answer("Введи новый город:")
        elif field == "description": await call.message.answer("Введи новое описание:")
        
    elif field == "photos":
        await call.message.answer("Пришли новые фото (1-4). Нажми 'Готово'", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Готово ✅", callback_data="edit_photos_done")]]))
        await state.update_data(photo_list=[])
        return await state.set_state(EditProfile.waiting_photos)
        
    elif field == "preference":
        return await call.message.answer(
            text="Кого ищем?", 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👩 Девушек", callback_data="up_Девушек")],
                [InlineKeyboardButton(text="👨 Парней", callback_data="up_Парней")],
                [InlineKeyboardButton(text="🌍 Всех", callback_data="up_Всех")]
            ])
        )
        
    elif field == "scope":
        return await call.message.answer(
            text="Где искать анкеты?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📍 В моем городе", callback_data="us_city")],
                [InlineKeyboardButton(text="🌍 По всей стране", callback_data="us_all")]
            ])
        )

# --- ОБРАБОТЧИКИ ДЛЯ ИЗМЕНЕНИЙ (FSM EDIT) ---

@dp.message(EditProfile.waiting_value)
async def process_edit_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("editing_field")
    value = message.text

    if field == "age":
        if not value.isdigit() or not (10 <= int(value) <= 99):
            return await message.answer("Введи число от 10 до 99:")
        value = int(value)
    elif field == "city":
        if not all(c.isalpha() or c in "- " for c in value):
            return await message.answer("В названии города только буквы! Попробуй снова:")

    await db.update_user_field(message.from_user.id, field, value)

    await state.clear()
    await message.answer("Данные успешно изменены! ✨", reply_markup=get_main_menu())
    user = await db.get_user_profile(message.from_user.id)
    await show_profile_card(message.from_user.id, user)

@dp.callback_query(F.data.startswith("up_"))
async def process_edit_preference(call: types.CallbackQuery, state: FSMContext):
    pref = call.data.split('_')[1]
    
    await db.update_user_field(call.from_user.id, "preference", pref)
        
    await call.message.answer(f"Предпочтения обновлены на: {pref} 👌", reply_markup=get_main_menu())
    user = await db.get_user_profile(call.from_user.id)
    await show_profile_card(call.from_user.id, user)

@dp.callback_query(F.data.startswith("us_"))
async def process_edit_scope(call: types.CallbackQuery, state: FSMContext):
    scope = call.data.split('_')[1]
    
    await db.update_user_field(call.from_user.id, "search_scope", scope)
        
    text_scope = "В моем городе 📍" if scope == "city" else "По всей стране 🌍"
    await call.message.answer(f"Радиус поиска обновлен на: {text_scope}", reply_markup=get_main_menu())
    user = await db.get_user_profile(call.from_user.id)
    await show_profile_card(call.from_user.id, user)

@dp.message(EditProfile.waiting_photos, F.photo)
async def edit_photos_rcv(message: types.Message, state: FSMContext):
    data = await state.get_data()
    plist = data.get('photo_list', [])
    if len(plist) < 4:
        plist.append(message.photo[-1].file_id)
        await state.update_data(photo_list=plist)
        await message.answer(f"Фото {len(plist)}/4 загружено.")
    else:
        await message.answer("Максимум 4 фотографии!")

@dp.callback_query(F.data == "edit_photos_done", EditProfile.waiting_photos)
async def edit_photos_final(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    plist = data.get('photo_list', [])
    if not plist:
        return await call.message.answer("Пришли хотя бы одно фото перед тем как нажать 'Готово'!")
        
    await db.update_user_photos(call.from_user.id, plist)
    await state.clear()
    await call.message.answer("Фотографии профиля обновлены! 📸", reply_markup=get_main_menu())
    user = await db.get_user_profile(call.from_user.id)
    await show_profile_card(call.from_user.id, user)

@dp.callback_query(F.data == "cancel_edit")
async def cancel_profile_edit(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Редактирование отменено ↩️", reply_markup=get_main_menu())

# --- ТОЧКА ВХОДА ---
async def main():
    print("Бот успешно запущен и слушает сервера Telegram...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())