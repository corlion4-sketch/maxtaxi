import os
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

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot tokeni
BOT_TOKEN = "8502586197:AAE68DBK67jTvkiRPTCXjNlZftS6BlVTewE"

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM holatlari
class Form(StatesGroup):
    waiting_for_phone = State()
    waiting_for_comment = State()
    waiting_for_pozivnoy = State()

# Ma'lumotlar bazasi yaratish
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
    
    conn.commit()
    conn.close()
    logger.info("Ma'lumotlar bazasi yaratildi")

# Asosiy menyu
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔢 Raqam + Izoh"), KeyboardButton(text="🚖 Pozivnoylar")],
            [KeyboardButton(text="👤 XODIM")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Raqam + Izoh menyusi
def numbers_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Raqam yozish")],
            [KeyboardButton(text="📅 Bugungi obzvon ro'yxati")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Pozivnoylar menyusi
def pozivnoy_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Pozivnoy qo'shish")],
            [KeyboardButton(text="📅 Bugungi pozivnoy ro'yxati")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Xodim menyusi
def employee_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugungi xodim ro'yxati")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    return keyboard

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await delete_user_message(message)
    user_name = message.from_user.full_name
    await message.answer(
        f"Assalomu alaykum {user_name}! 👋\n"
        "Statistika botiga xush kelibsiz.\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu()
    )

# Asosiy menyu handlerlari
@dp.message(F.text == "🔢 Raqam + Izoh")
async def numbers_section(message: types.Message):
    await delete_user_message(message)
    await message.answer("📊 Raqam + Izoh bo'limi:", reply_markup=numbers_menu())

@dp.message(F.text == "🚖 Pozivnoylar")
async def pozivnoy_section(message: types.Message):
    await delete_user_message(message)
    await message.answer("🚗 Pozivnoylar bo'limi:", reply_markup=pozivnoy_menu())

@dp.message(F.text == "👤 XODIM")
async def employee_section(message: types.Message):
    await delete_user_message(message)
    await message.answer("👨‍💼 XODIM bo'limi:", reply_markup=employee_menu())

@dp.message(F.text == "🔙 Orqaga")
async def back_to_main(message: types.Message):
    await delete_user_message(message)
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu())

# Raqam yozish boshlanishi
@dp.message(F.text == "📝 Raqam yozish")
async def start_number_input(message: types.Message, state: FSMContext):
    await delete_user_message(message)
    await message.answer("📱 Telefon raqamni yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_for_phone)

# Telefon raqam qabul qilish
@dp.message(Form.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await delete_user_message(message)
    phone = message.text.strip()
    
    await state.update_data(phone=phone)
    await message.answer("📝 Izoh yozing:")
    await state.set_state(Form.waiting_for_comment)

# Izoh qabul qilish va saqlash
@dp.message(Form.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    await delete_user_message(message)
    user_data = await state.get_data()
    
    comment = message.text.strip()
    phone = user_data['phone']
    
    # Ma'lumotlarni bazaga saqlash
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO numbers (user_id, username, full_name, phone, comment, region, created_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message.from_user.id, message.from_user.username, message.from_user.full_name, phone, comment, "Viloyat tanlanmagan", datetime.now().strftime("%d.%m.%Y"))
    )
    conn.commit()
    conn.close()
    
    # Yangi raqam so'rash
    await message.answer("✅ Ma'lumot saqlandi! Yangi telefon raqam yuboring:")
    await state.set_state(Form.waiting_for_phone)

# Pozivnoy qo'shish boshlanishi
@dp.message(F.text == "📝 Pozivnoy qo'shish")
async def start_pozivnoy_input(message: types.Message, state: FSMContext):
    await delete_user_message(message)
    await message.answer("🚖 Pozivnoy raqamini yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_for_pozivnoy)

# Pozivnoy qabul qilish
@dp.message(Form.waiting_for_pozivnoy)
async def process_pozivnoy(message: types.Message, state: FSMContext):
    await delete_user_message(message)
    pozivnoy = message.text.strip()
    
    # Ma'lumotlarni bazaga saqlash
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pozivnoy (user_id, username, full_name, pozivnoy, region, created_date) VALUES (?, ?, ?, ?, ?, ?)",
        (message.from_user.id, message.from_user.username, message.from_user.full_name, pozivnoy, "Viloyat tanlanmagan", datetime.now().strftime("%d.%m.%Y"))
    )
    conn.commit()
    conn.close()
    
    # Yangi pozivnoy so'rash
    await message.answer("✅ Pozivnoy saqlandi! Yangi pozivnoy raqamini yuboring:")
    await state.set_state(Form.waiting_for_pozivnoy)

# Bugungi obzvon ro'yxati
@dp.message(F.text == "📅 Bugungi obzvon ro'yxati")
async def today_numbers_list(message: types.Message):
    await delete_user_message(message)
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT phone, comment FROM numbers WHERE user_id = ? AND created_date = ? ORDER BY id DESC",
        (message.from_user.id, datetime.now().strftime("%d.%m.%Y"))
    )
    numbers = cursor.fetchall()
    conn.close()
    
    if not numbers:
        await message.answer("📅 Bugungi obzvon ro'yxati bo'sh", reply_markup=numbers_menu())
        return
    
    response = f"📅 BUGUNGI OBZVON RO'YXATI ({datetime.now().strftime('%d.%m.%Y')})\n\n"
    response += "Viloyat tanlanmagan\n"
    response += f"Xodim: {message.from_user.full_name}\n\n"
    
    for i, (phone, comment) in enumerate(numbers, 1):
        response += f"{i}. {phone} - {comment}\n"
    
    response += "\nViloyat tanlanmagan ✅\n"
    
    await message.answer(response, reply_markup=numbers_menu())

# Bugungi pozivnoy ro'yxati
@dp.message(F.text == "📅 Bugungi pozivnoy ro'yxati")
async def today_pozivnoy_list(message: types.Message):
    await delete_user_message(message)
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT pozivnoy FROM pozivnoy WHERE user_id = ? AND created_date = ? ORDER BY id DESC",
        (message.from_user.id, datetime.now().strftime("%d.%m.%Y"))
    )
    pozivnoys = cursor.fetchall()
    conn.close()
    
    if not pozivnoys:
        await message.answer("📅 Bugungi qo'shilgan pozivnoy ro'yxati bo'sh", reply_markup=pozivnoy_menu())
        return
    
    response = f"📅 BUGUNGI QO'SHILGAN POZIVNOY RO'YXATI ({datetime.now().strftime('%d.%m.%Y')})\n\n"
    response += "Viloyat tanlanmagan\n\n"
    
    for i, (pozivnoy,) in enumerate(pozivnoys, 1):
        response += f"{i}. {pozivnoy}\n"
    
    response += "\nViloyat tanlanmagan ✅\n"
    
    await message.answer(response, reply_markup=pozivnoy_menu())

# Bugungi xodim ro'yxati
@dp.message(F.text == "📅 Bugungi xodim ro'yxati")
async def today_employee_list(message: types.Message):
    await delete_user_message(message)
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Xodimning raqamlari
    cursor.execute(
        "SELECT phone, comment FROM numbers WHERE user_id = ? AND created_date = ? ORDER BY id DESC",
        (message.from_user.id, datetime.now().strftime("%d.%m.%Y"))
    )
    numbers = cursor.fetchall()
    
    conn.close()
    
    response = f"📅 BUGUNGI XODIM RO'YXATI ({datetime.now().strftime('%d.%m.%Y')})\n\n"
    response += "Viloyat tanlanmagan ✅\n"
    response += f"Xodim: {message.from_user.full_name} ✅\n\n"
    
    if numbers:
        for i, (phone, comment) in enumerate(numbers, 1):
            response += f"{i}. {phone} - {comment}\n"
    else:
        response += "Hozircha raqamlar mavjud emas\n"
    
    response += "\nViloyat tanlanmagan ✅\n"
    
    await message.answer(response, reply_markup=employee_menu())

# Foydalanuvchi xabarlarini o'chirish
async def delete_user_message(message: types.Message):
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Xabarni o'chirib bo'lmadi: {e}")

# Asosiy funksiya
async def main():
    # Ma'lumotlar bazasini ishga tushirish
    init_db()
    
    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())