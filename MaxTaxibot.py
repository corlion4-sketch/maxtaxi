import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8502586197:AAE68DBK67jTvkiRPTCXjNlZftS6BlVTewE"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM holatlari
class Form(StatesGroup):
    waiting_for_phone = State()
    waiting_for_comment = State()
    waiting_for_pozivnoy = State()

# Ma'lumotlar bazasi
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            comment TEXT,
            region TEXT DEFAULT 'Viloyat tanlanmagan',
            created_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pozivnoy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            pozivnoy TEXT,
            region TEXT DEFAULT 'Viloyat tanlanmagan',
            created_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            region TEXT DEFAULT 'Viloyat tanlanmagan'
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Ma'lumotlar bazasi yaratildi")

# Yordamchi funksiyalar
async def try_delete(chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id, message_id)
        return True
    except:
        return False

def set_user_region(user_id: int, region: str):
    conn = sqlite3.connect('bot_data.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO user_settings (user_id, region) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET region=excluded.region", (user_id, region))
    conn.commit()
    conn.close()

def get_user_region(user_id: int):
    conn = sqlite3.connect('bot_data.db')
    cur = conn.cursor()
    cur.execute("SELECT region FROM user_settings WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "Viloyat tanlanmagan"

# Menyular
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🔢 Raqam + Izoh"), KeyboardButton("🚖 Pozivnoylar")],
            [KeyboardButton("👤 XODIM")]
        ], resize_keyboard=True
    )
    return keyboard

def numbers_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📝 Raqam yozish")],
            [KeyboardButton("📅 Bugungi obzvon ro'yxati")],
            [KeyboardButton("🔙 Orqaga")]
        ], resize_keyboard=True
    )
    return keyboard

def pozivnoy_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📝 Pozivnoy qo'shish")],
            [KeyboardButton("📅 Bugungi pozivnoy ro'yxati")],
            [KeyboardButton("🔙 Orqaga")]
        ], resize_keyboard=True
    )
    return keyboard

def employee_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Andijon"), KeyboardButton("Buxoro"), KeyboardButton("Farg'ona")],
            [KeyboardButton("Jizzax"), KeyboardButton("Qashqadaryo"), KeyboardButton("Navoiy")],
            [KeyboardButton("Namangan"), KeyboardButton("Samarqand"), KeyboardButton("Sirdaryo")],
            [KeyboardButton("Surxondaryo"), KeyboardButton("Toshkent"), KeyboardButton("Urganch")],
            [KeyboardButton("🔙 Orqaga")]
        ], resize_keyboard=True
    )
    return keyboard

VILOYATLAR = {"Andijon","Buxoro","Farg'ona","Jizzax","Qashqadaryo","Navoiy","Namangan","Samarqand","Sirdaryo","Surxondaryo","Toshkent","Urganch"}

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await try_delete(message.chat.id, message.message_id)
    await message.answer(f"Assalomu alaykum {message.from_user.full_name}! 👋\nBotga xush kelibsiz.", reply_markup=main_menu())

# Menyu handlerlari
@dp.message(F.text == "🔢 Raqam + Izoh")
async def numbers_section(message: types.Message):
    await try_delete(message.chat.id, message.message_id)
    await message.answer("📊 Raqam + Izoh bo'limi:", reply_markup=numbers_menu())

@dp.message(F.text == "🚖 Pozivnoylar")
async def pozivnoy_section(message: types.Message):
    await try_delete(message.chat.id, message.message_id)
    await message.answer("🚗 Pozivnoylar bo'limi:", reply_markup=pozivnoy_menu())

@dp.message(F.text == "👤 XODIM")
async def employee_section(message: types.Message):
    await try_delete(message.chat.id, message.message_id)
    await message.answer("👨‍💼 XODIM bo'limi:", reply_markup=employee_menu())

@dp.message(F.text == "🔙 Orqaga")
async def back_to_main(message: types.Message):
    await try_delete(message.chat.id, message.message_id)
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu())

# Raqam + Izoh handlerlari
@dp.message(F.text == "📝 Raqam yozish")
async def start_number_input(message: types.Message, state: FSMContext):
    await try_delete(message.chat.id, message.message_id)
    bot_msg = await message.answer("📱 Telefon raqamni yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.update_data(bot_prompt_id=bot_msg.message_id)
    await state.set_state(Form.waiting_for_phone)

@dp.message(Form.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_prompt_id = data.get("bot_prompt_id")
    if bot_prompt_id:
        await try_delete(message.chat.id, bot_prompt_id)
    await try_delete(message.chat.id, message.message_id)
    phone = message.text.strip()
    await state.update_data(phone=phone)
    bot_msg = await message.answer("📝 Izoh yozing:")
    await state.update_data(bot_comment_prompt_id=bot_msg.message_id)
    await state.set_state(Form.waiting_for_comment)

@dp.message(Form.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await try_delete(message.chat.id, data.get("bot_comment_prompt_id"))
    await try_delete(message.chat.id, message.message_id)

    phone = data.get("phone")
    comment = message.text.strip()
    region = get_user_region(message.from_user.id)
    today = datetime.now().strftime("%d.%m.%Y")

    conn = sqlite3.connect('bot_data.db')
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO numbers (user_id, username, full_name, phone, comment, region, created_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message.from_user.id, message.from_user.username, message.from_user.full_name, phone, comment, region, today)
    )
    conn.commit()
    conn.close()

    conf = await message.answer("✅ Ma'lumot saqlandi!")
    await asyncio.sleep(1.5)
    await try_delete(message.chat.id, conf.message_id)

    bot_msg = await message.answer("📱 Telefon raqamni yuboring:")
    await state.update_data(bot_prompt_id=bot_msg.message_id)
    await state.set_state(Form.waiting_for_phone)

# Pozivnoy handlerlari
@dp.message(F.text == "📝 Pozivnoy qo'shish")
async def start_pozivnoy_input(message: types.Message, state: FSMContext):
    await try_delete(message.chat.id, message.message_id)
    bot_msg = await message.answer("🚖 Pozivnoy raqamini yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.update_data(pozivnoy_prompt_id=bot_msg.message_id)
    await state.set_state(Form.waiting_for_pozivnoy)

@dp.message(Form.waiting_for_pozivnoy)
async def process_pozivnoy(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await try_delete(message.chat.id, data.get("pozivnoy_prompt_id"))
    await try_delete(message.chat.id, message.message_id)

    poz = message.text.strip()
    region = get_user_region(message.from_user.id)
    today = datetime.now().strftime("%d.%m.%Y")
    conn = sqlite3.connect('bot_data.db')
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pozivnoy (user_id, username, full_name, pozivnoy, region, created_date) VALUES (?, ?, ?, ?, ?, ?)",
        (message.from_user.id, message.from_user.username, message.from_user.full_name, poz, region, today)
    )
    conn.commit()
    conn.close()

    conf = await message.answer("✅ Pozivnoy saqlandi!")
    await asyncio.sleep(1.5)
    await try_delete(message.chat.id, conf.message_id)

    bot_msg = await message.answer("🚖 Pozivnoy raqamini yuboring:")
    await state.update_data(pozivnoy_prompt_id=bot_msg.message_id)
    await state.set_state(Form.waiting_for_pozivnoy)

# Bugungi obzvon ro'yxati
@dp.message(F.text == "📅 Bugungi obzvon ro'yxati")
async def today_numbers_list(message: types.Message):
    await try_delete(message.chat.id, message.message_id)
    today = datetime.now().strftime("%d.%m.%Y")
    region = get_user_region(message.from_user.id)

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT phone, comment FROM numbers WHERE user_id = ? AND created_date = ? ORDER BY id DESC",
        (message.from_user.id, today)
    )
    numbers = cursor.fetchall()
    conn.close()

    if not numbers:
        await message.answer("📅 Bugungi obzvon ro'yxati bo'sh", reply_markup=numbers_menu())
        return

    response = f"📅 BUGUNGI OBZVON RO'YXATI ({today})\n\n{region} ✅\nXodim: {message.from_user.full_name} ✅\n\n"
    for i, (phone, comment) in enumerate(numbers, 1):
        response += f"{i}. {phone} — {comment}\n"
    response += f"\n{region} ✅\n"

    await message.answer(response, reply_markup=numbers_menu())

# Bugungi pozivnoy ro'yxati
@dp.message(F.text == "📅 Bugungi pozivnoy ro'yxati")
async def today_pozivnoy_list(message: types.Message):
    await try_delete(message.chat.id, message.message_id)
    today = datetime.now().strftime("%d.%m.%Y")
    region = get_user_region(message.from_user.id)

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT pozivnoy FROM pozivnoy WHERE user_id = ? AND created_date = ? ORDER BY id DESC",
        (message.from_user.id, today)
    )
    pozivnoys = cursor.fetchall()
    conn.close()

    if not pozivnoys:
        await message.answer("📅 Bugungi qo'shilgan pozivnoy ro'yxati bo'sh", reply_markup=pozivnoy_menu())
        return

    response = f"📅 BUGUNGI QO'SHILGAN POZIVNOY RO'YXATI ({today})\n\n{region} ✅\n\n"
    for i, (pozivnoy,) in enumerate(pozivnoys, 1):
        response += f"{i}. {pozivnoy}\n"
    response += f"\n{region} ✅\n"

    await message.answer(response, reply_markup=pozivnoy_menu())

# Xodim viloyat tanlashi
@dp.message()
async def handle_region_selection(message: types.Message):
    text = message.text.strip()
    if text in VILOYATLAR:
        await try_delete(message.chat.id, message.message_id)
        set_user_region(message.from_user.id, text)
        await send_today_numbers_with_header(message, message.from_user.id)

async def send_today_numbers_with_header(message: types.Message, user_id: int):
    today = datetime.now().strftime("%d.%m.%Y")
    region = get_user_region(user_id)
    conn = sqlite3.connect('bot_data.db')
    cur = conn.cursor()
    cur.execute("SELECT phone, comment FROM numbers WHERE user_id=? AND created_date=? ORDER BY id DESC", (user_id, today))
    rows = cur.fetchall()
    conn.close()

    header = f"📅 BUGUNGI OBZVON RO'YXATI ({today})\n\n{region} ✅\nXodim: {message.from_user.full_name} ✅\n\n"
    body = ""
    if rows:
        for