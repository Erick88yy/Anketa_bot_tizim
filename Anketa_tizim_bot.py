import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import Throttled

from middlewares.throttling import ThrottlingMiddleware  # Middleware ni import qilish

API_TOKEN = "7543816231:AAHRGV5Kq4OK2PmiPGdLN82laZSdXLFnBxc"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Throttling middleware ni o‘rnatish
dp.middleware.setup(ThrottlingMiddleware(limit=1))  # 1 soniyada 1 marta xabar cheklovi

class Form(StatesGroup):
    language = State()
    name = State()
    age = State()
    parameter = State()
    role = State()
    city = State()
    goal = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("O'zbek"), KeyboardButton("Русский"), KeyboardButton("English"))

    await message.reply(
        "Assalom Aleykum!\nСалам! Добро пожаловать!\nHello! Welcome!\n\n"
        "Anketani boshlash uchun tilni tanlang:",
        reply_markup=keyboard
    )
    await Form.language.set()

@dp.message_handler(lambda message: message.text in ["O'zbek", "Русский", "English"], state=Form.language)
async def language_choice(message: types.Message, state: FSMContext):
    user_language = message.text
    await state.update_data(language=user_language)
    await message.answer("1. Ismingizni kiriting:" if user_language == "O'zbek" else 
                         "1. Введите ваше имя:" if user_language == "Русский" else 
                         "1. Enter your name:", reply_markup=ReplyKeyboardRemove())
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    language = (await state.get_data())['language']
    await message.answer("2. Yoshingizni kiriting (16-100):" if language == "O'zbek" else 
                         "2. Введите ваш возраст (16-100):" if language == "Русский" else 
                         "2. Enter your age (16-100):")
    await Form.age.set()

@dp.message_handler(state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if 16 <= age <= 100:
            await state.update_data(age=age)
            language = (await state.get_data())['language']
            await message.answer("3. Parametringizni kiriting (Masalan: 178-65-18):" if language == "O'zbek" else 
                                 "3. Введите ваш параметр (например: 178-65-18):" if language == "Русский" else 
                                 "3. Enter your parameter (e.g., 178-65-18):")
            await Form.parameter.set()
        else:
            raise ValueError
    except ValueError:
        language = (await state.get_data())['language']
        await message.answer("Iltimos, yoshingizni to'g'ri kiriting (16-100):" if language == "O'zbek" else 
                             "Пожалуйста, введите правильный возраст (от 16 до 100):" if language == "Русский" else 
                             "Please enter a valid age (16-100):")

@dp.message_handler(state=Form.parameter)
async def process_parameter(message: types.Message, state: FSMContext):
    parameter = message.text.strip()
    if re.match(r'^[\d\-\_\.,\*]+$', parameter):
        await state.update_data(parameter=parameter)
        language = (await state.get_data())['language']

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Aktiv"), KeyboardButton("Uni-Aktiv"), KeyboardButton("Universal"),
                     KeyboardButton("Uni-Passiv"), KeyboardButton("Passiv"))

        await message.answer("4. Temadagi ro'lingizni tanlang:" if language == "O'zbek" else 
                             "4. Выберите вашу роль в теме:" if language == "Русский" else 
                             "4. Select your role in the topic:", reply_markup=keyboard)
        await Form.role.set()
    else:
        language = (await state.get_data())['language']
        await message.answer("Iltimos, parametringizni to'g'ri kiriting (Masalan: 178-65-18):" if language == "O'zbek" else 
                             "Пожалуйста, введите правильный параметр (например: 178-65-18):" if language == "Русский" else 
                             "Please enter a valid parameter (e.g., 178-65-18):")

async def anti_flood(*args, **kwargs):
    raise Throttled()

dp.message_handler(anti_flood, rate=1)  # Har bir foydalanuvchiga 1 soniyada 1 marta xabar yuborish

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)