import logging
import time
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from asyncio import Lock

API_TOKEN = 7543816231:"AAHRGV5Kq4OK2PmiPGdLN82laZSdXLFnBxc"
ADMIN_CHAT_ID = "7888045216"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

survey_counter = 1
user_last_submission = {}
user_locks = {}

class Form(StatesGroup):
    language = State()
    name = State()
    age = State()
    parameter = State()
    role = State()
    city = State()
    goal = State()
    about = State()
    photo_upload = State()
    partner_age = State()
    partner_role = State()
    partner_city = State()
    partner_about = State()
    confirmation = State()

MESSAGES = {
    "O'zbek": {
        "start": "Assalomu alaykum! Anketani to'ldirish uchun tilni tanlang.",
        "name": "Ismingizni kiriting:",
        "age": "Yoshingizni kiriting:",
        "parameter": "Parametrlaringizni kiriting:",
        "role": "Rolingizni kiriting:",
        "city": "Shahringizni kiriting:",
        "goal": "Maqsadingizni kiriting:",
        "about": "O'zingiz haqingizda qisqacha yozing:",
        "photo_upload": "Iltimos, rasmingizni yuklang yoki 'Keyingisi' deb yozing:",
        "partner_age": "Hamkoringizning yosh diapazonini kiriting:",
        "partner_role": "Hamkoringizning rolini kiriting:",
        "partner_city": "Hamkoringizning shahrini kiriting:",
        "partner_about": "Hamkoringiz haqida qisqacha yozing:",
        "confirmation": "Ma'lumotlaringizni tasdiqlaysizmi? (Ha/Yo'q)",
        "survey_number": "Anketa raqami",
        "about_me": "Men haqimda",
        "name": "Ism",
        "age": "Yosh",
        "parameters": "Parametrlar",
        "role": "Rol",
        "location": "Shahar",
        "goal": "Maqsad",
        "about": "O'zim haqimda",
        "profile_link": "Profilga havola",
        "partner": "Hamkor haqida",
        "partner_age": "Yosh diapazoni",
        "partner_role": "Rol",
        "partner_location": "Shahar",
        "partner_about": "Qisqacha ma'lumot",
        "survey_accepted": "Anketangiz qabul qilindi!",
        "survey_cancelled": "Anketa bekor qilindi.",
        "invalid_choice": "Iltimos, berilgan variantlardan birini tanlang."
    },
    "Русский": {
        "start": "Здравствуйте! Пожалуйста, выберите язык для заполнения анкеты.",
        "name": "Введите ваше имя:",
        "age": "Введите ваш возраст:",
        "parameter": "Введите ваши параметры:",
        "role": "Введите вашу роль:",
        "city": "Введите ваш город:",
        "goal": "Введите вашу цель:",
        "about": "Напишите кратко о себе:",
        "photo_upload": "Пожалуйста, загрузите ваше фото или напишите 'Далее':",
        "partner_age": "Введите возрастной диапазон вашего партнера:",
        "partner_role": "Введите роль вашего партнера:",
        "partner_city": "Введите город вашего партнера:",
        "partner_about": "Напишите кратко о вашем партнере:",
        "confirmation": "Вы подтверждаете введенные данные? (Да/Нет)",
        "survey_number": "Номер анкеты",
        "about_me": "Обо мне",
        "name": "Имя",
        "age": "Возраст",
        "parameters": "Параметры",
        "role": "Роль",
        "location": "Город",
        "goal": "Цель",
        "about": "О себе",
        "profile_link": "Ссылка на профиль",
        "partner": "О партнере",
        "partner_age": "Возрастной диапазон",
        "partner_role": "Роль",
        "partner_location": "Город",
        "partner_about": "Краткая информация",
        "survey_accepted": "Ваша анкета принята!",
        "survey_cancelled": "Анкета отменена.",
        "invalid_choice": "Пожалуйста, выберите один из предложенных вариантов."
    },
    "English": {
        "start": "Hello! Please select a language to fill out the survey.",
        "name": "Enter your name:",
        "age": "Enter your age:",
        "parameter": "Enter your parameters:",
        "role": "Enter your role:",
        "city": "Enter your city:",
        "goal": "Enter your goal:",
        "about": "Write briefly about yourself:",
        "photo_upload": "Please upload your photo or type 'Next':",
        "partner_age": "Enter your partner's age range:",
        "partner_role": "Enter your partner's role:",
        "partner_city": "Enter your partner's city:",
        "partner_about": "Write briefly about your partner:",
        "confirmation": "Do you confirm the entered data? (Yes/No)",
        "survey_number": "Survey number",
        "about_me": "About me",
        "name": "Name",
        "age": "Age",
        "parameters": "Parameters",
        "role": "Role",
        "location": "City",
        "goal": "Goal",
        "about": "About me",
        "profile_link": "Profile link",
        "partner": "About partner",
        "partner_age": "Age range",
        "partner_role": "Role",
        "partner_location": "City",
        "partner_about": "Brief information",
        "survey_accepted": "Your survey has been accepted!",
        "survey_cancelled": "Survey cancelled.",
        "invalid_choice": "Please choose one of the provided options."
    }
}

def get_lock(user_id):
    if user_id not in user_locks:
        user_locks[user_id] = Lock()
    return user_locks[user_id]

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        await state0