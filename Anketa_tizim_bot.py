import time
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = "7543816231:AAHRGV5Kq4OK2PmiPGdLN82laZSdXLFnBxc"  
ADMIN_CHAT_ID = 7888045216
SESSION_TIMEOUT = 6 * 60 * 60  # 6 soat

# Foydalanuvchi oxirgi yuborgan anketasi haqidagi ma'lumotlar (timestamp va til)
user_last_submission = {}
# Har bir yaratilgan anketaga yagona, ketma-ket ID
survey_counter = 1

# Foydalanuvchi javoblarini bir vaqtning o'zida qayta ishlashni oldini olish uchun lock
user_lock = {}

def get_lock(user_id):
    if user_id not in user_lock:
        user_lock[user_id] = asyncio.Lock()
    return user_lock[user_id]

def format_remaining_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_submission_time(timestamp):
    # Toshkent vaqti UTC+5 hisoblanadi
    return time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime(timestamp + 5 * 3600))

class Form(StatesGroup):
    language = State()
    name = State()
    age = State()
    parameter = State()
    parameter_confirm = State()  # Qo'shimcha tekshiruv
    role = State()
    city = State()
    goal = State()
    about = State()
    photo_choice = State()
    photo_upload = State()
    partner_age = State()
    partner_role = State()
    partner_city = State()
    partner_about = State()
    confirmation = State()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Har bir til uchun matnlar, variantlar va sarlavhalar
MESSAGES = {
    "O'zbek": {
        "welcome_text": "Assalom Aleykum!\nIltimos, menudan anketa tilini tanlang:",
        "ask_name": "1. Ismingizni kiriting:",
        "ask_age": "2. Yoshingizni kiriting (Masalan, 23 yoki 36):",
        "ask_parameter": "3. Parametrlaringizni kiriting (Masalan: 178-65-18):",
        "parameter_confirm": "Siz aminmisiz, rostanam asbobingiz uzunligi 20sm dan kattami? Anketangiz orqali kim bilandir ko'rishganizda uyalib qolmaysizmi?����",
        "ask_role": "4. Ro'lingizni tanlang:",
        "ask_city": "5. Yashash manzilingiz (Viloyat/Shahar):",
        "ask_goal": "6. Tanishuvdan maqsadingiz:",
        "ask_about": "7. O'zingiz haqingizda qisqacha ma'lumot kiriting:",
        "ask_photo_choice": "8. Anketangiz uchun rasmingizni yuklamoqchimisiz?",
        "ask_photo_upload": "Iltimos, rasmingizni yuboring:",
        "ask_partner_age": "9. Tanishmoqchi bo'lgan insoningiz yoshi (Masalan: 25-30):",
        "ask_partner_role": "10. Tanishmoqchi bo'lgan insoningiz roli:",
        "ask_partner_city": "11. Tanishmoqchi bo'lgan insoningiz manzili:",
        "ask_partner_about": "12. Tanishmoqchi bo'lgan insoningiz haqida qisqacha ma'lumot:",
        "ask_confirmation": "13. Anketangiz deyarli tayyor! Agar barcha ma'lumotlar to'g'ri bo'lsa, adminga yuborish uchun tasdiqlang:",
        "invalid_language": "Iltimos, menyudan tilni tanlang!",
        "invalid_age": "Iltimos, yoshingizni to'g'ri formatda kiriting (Masalan, 17 yoki 35):\n(16 yoshdan kichiklardan anketa qabul qilinmaydi)",
        "invalid_parameter": "Iltimos, parametrlaringizni to'g'ri kiriting (Masalan, 182-70-17):",
        "invalid_choice": "Iltimos, menyudan javob variantini tanlang!",
        "invalid_role": "Iltimos, menyudan variant tanlang!",
        "invalid_partner_age": "Iltimos, yosh oralig'ini to'g'ri kiriting (Masalan, 16-23 yoki 25-35):\n(16 yoshdan kichiklarga anketa qo'llanilmaydi)",
        "invalid_photo": "Iltimos, faqat rasm yuboring!",
        "survey_accepted": "��� <b>Anketa qabul qilindi!</b>\nAnketangiz admin tomonidan tekshirilgandan so'ng kanalda e'lon qilinadi va sizga bot orqali habar beriladi.\nYangi anketa uchun /start ni bosing.",
        "survey_cancelled": "��� Anketa bekor qilindi. Yangi anketa uchun /start ni bosing.",
        "time_limit_message": "��� Siz so���nggi marta <b>{date}</b> kuni soat <b>{time}</b> da anketa to���ldirgansiz.\nYangi anketa to���ldirish uchun <b>{remaining}</b> soatdan keyin urinib ko���ring.",
        "survey_number": "Anketa raqami",
        "about_me": "O'zim haqimda",
        "name": "Ism",
        "age": "Yosh",
        "parameters": "Parametrlar",
        "role": "Rol",
        "location": "Manzil",
        "goal": "Maqsad",
        "about": "Haqida",
        "partner": "Tanishmoqchi bo'lgan inson",
        "partner_age": "Yosh",
        "partner_role": "Rol",
        "partner_location": "Manzil",
        "partner_about": "Haqida",
        "profile_link": "Mening profilimga havola",
        "role_options": ["Aktiv", "Uni-Aktiv", "Universal", "Uni-Passiv", "Passiv"],
        "goal_options": ["Do'stlik", "Seks", "Oila qurish", "Virtual aloqa", "Eskort"]
    },
    "��������������": {
        "welcome_text": "������������! ���������� ��������������������!\n��������������������, ���������������� �������� ������������:",
        "ask_name": "1. �������������� �������� ������:",
        "ask_age": "2. �������������� ������ �������������� (����������������, 23 ������ 36):",
        "ask_parameter": "3. �������������� �������� ������������������ (����������������: 178-65-18):",
        "parameter_confirm": "���� ��������������, ������ ���������� ������������ ������������������ ���������� 20 ����? ������ ���� ���������� ������������, �������� ������-���� ������������ ������ ���������� ������������?����",
        "ask_role": "4. ���������������� �������� ��������:",
        "ask_city": "5. ������ ���������� (������������/����������):",
        "ask_goal": "6. �������� �������� ��������������������:",
        "ask_about": "7. �������������������� ������������ �� ��������:",
        "ask_photo_choice": "8. ������������ ������������������ �������������������� ������ ������������?",
        "ask_photo_upload": "��������������������, ������������������ ��������������������:",
        "ask_partner_age": "9. �������������� ����������������, �� �������������� ������������ �������������������������� (����������������, 25-30):",
        "ask_partner_role": "10. �������� ����������������, �� �������������� ������������ ��������������������������:",
        "ask_partner_city": "11. ���������� ����������������, �� �������������� ������������ ��������������������������:",
        "ask_partner_about": "12. �������������������� ������������ �� ����������������, �� �������������� ������������ ��������������������������:",
        "ask_confirmation": "13. �������� ������������ ���������� ������������! �������� ������ ������������ ����������, ���������������������� ���������������� ����������������������������:",
        "invalid_language": "��������������������, ���������������� �������� ���� ��������!",
        "invalid_age": "��������������������, �������������� �������������������� �������������� (����������������, 17 ������ 35):\n(������������ ���� ������ ������������ 16 ������ ���� ����������������������)",
        "invalid_parameter": "��������������������, �������������� ������������������ ������������������ (����������������, 182-70-17):",
        "invalid_choice": "��������������������, ���������������� �������������� ���� ��������!",
        "invalid_role": "��������������������, ���������������� �������������� ���� ��������!",
        "invalid_partner_age": "��������������������, �������������� �������������������� �������������������� ���������������� (����������������, 16-23 ������ 25-35):\n(������������ ������ ������ ������������ 16 ������ ���� ����������������������������)",
        "invalid_photo": "��������������������, ������������������ ��������������������!",
        "survey_accepted": "��� <b>������������ ��������������!</b>\n���������� ���������������� ������������������������������ ������������ ���������� ������������������������, �� ���� ���������������� ���������������������� ���������� ��������.\n������ ���������� ������������ �������������� /start.",
        "survey_cancelled": "��� ������������ ����������������. ������ ���������� ������������ �������������� /start.",
        "time_limit_message": "��� ���� ������������������ ������������ �� <b>{date}</b> �� <b>{time}</b>.\n������������������ �������������������� ���������������� ���������� <b>{remaining}</b>.",
        "survey_number": "���������� ������������",
        "about_me": "�� ��������",
        "name": "������",
        "age": "��������������",
        "parameters": "������������������",
        "role": "��������",
        "location": "����������",
        "goal": "��������",
        "about": "�� ��������",
        "partner": "��������������",
        "partner_age": "��������������",
        "partner_role": "��������",
        "partner_location": "����������",
        "partner_about": "�� ������/������",
        "profile_link": "������������ ���� ������ ��������������",
        "role_options": ["����������", "������-����������", "������������������", "������-������������", "������������"],
        "goal_options": ["������������", "��������", "���������������� ����������", "���������������������� ��������������", "������������"]
    },
    "English": {
        "welcome_text": "Hello! Welcome!\nPlease select the survey language:",
        "ask_name": "1. Please enter your name:",
        "ask_age": "2. Please enter your age (e.g., 23 or 36):",
        "ask_parameter": "3. Please enter your parameters (e.g., 178-65-18):",
        "parameter_confirm": "Are you sure your measurement is more than 20 cm? Won't you be embarrassed if someone sees it via the survey?����",
        "ask_role": "4. Please select your role:",
        "ask_city": "5. Your location (Region/City):",
        "ask_goal": "6. What is your purpose for meeting someone:",
        "ask_about": "7. Please provide a short description about yourself:",
        "ask_photo_choice": "8. Would you like to upload a photo for your survey?",
        "ask_photo_upload": "Please send your photo:",
        "ask_partner_age": "9. Age of the person you want to meet (e.g., 25-30):",
        "ask_partner_role": "10. Role of the person you want to meet:",
        "ask_partner_city": "11. Location of the person you want to meet:",
        "ask_partner_about": "12. Provide a brief description of the person you want to meet:",
        "ask_confirmation": "13. Your survey is almost ready! If all your information is correct, confirm to send it to the admin:",
        "invalid_language": "Please select a language from the menu!",
        "invalid_age": "Please enter a valid age (e.g., 17 or 35):\n(We do not accept surveys from those under 16)",
        "invalid_parameter": "Please enter your parameters correctly (e.g., 182-70-17):",
        "invalid_choice": "Please select an option from the menu!",
        "invalid_role": "Please select an option from the menu!",
        "invalid_partner_age": "Please enter a valid age range (e.g., 16-23 or 25-35):\n(We do not support surveys for users under 16)",
        "invalid_photo": "Please send a photo!",
        "survey_accepted": "��� <b>Survey accepted!</b>\nAfter admin verification, your survey will be published in the channel and you will receive a notification via this bot.\nTo start a new survey, press /start.",
        "survey_cancelled": "��� Survey cancelled. For a new survey, press /start.",
        "time_limit_message": "��� You filled out the survey on <b>{date}</b> at <b>{time}</b>.\nYou can fill out a new survey only after <b>{remaining}</b>.",
        "survey_number": "Survey Number",
        "about_me": "About Me",
        "name": "Name",
        "age": "Age",
        "parameters": "Parameters",
        "role": "Role",
        "location": "Location",
        "goal": "Goal",
        "about": "About",
        "partner": "Partner",
        "partner_age": "Age",
        "partner_role": "Role",
        "partner_location": "Location",
        "partner_about": "About",
        "profile_link": "Profile Link",
        "role_options": ["Active", "Uni-Active", "Universal", "Uni-Passive", "Passive"],
        "goal_options": ["Friendship", "Sex", "Marriage", "Virtual connection", "Escort"]
    }
}

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    if user_id in user_last_submission:
        submission_info = user_last_submission[user_id]
        last_timestamp = submission_info["timestamp"]
        saved_language = submission_info.get("language", "O'zbek")
        if time.time() - last_timestamp < SESSION_TIMEOUT:
            remaining = SESSION_TIMEOUT - (time.time() - last_timestamp)
            last_time = format_submission_time(last_timestamp)
            localized = MESSAGES[saved_language]
            await message.answer(
                localized["time_limit_message"].format(date=last_time.split()[0], time=last_time.split()[1], remaining=format_remaining_time(remaining)),
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML"
            )
            return
    welcome_text = "\n\n".join([
        MESSAGES["O'zbek"]["welcome_text"],
        MESSAGES["��������������"]["welcome_text"],
        MESSAGES["English"]["welcome_text"]
    ])
    lang_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    lang_markup.add(KeyboardButton("O'zbek"), KeyboardButton("��������������"), KeyboardButton("English"))
    await message.reply(welcome_text, reply_markup=lang_markup, parse_mode="Markdown")
    await Form.language.set()

@dp.message_handler(state=Form.language)
async def process_language(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lock = get_lock(user_id)
    async with lock:
        if message.text not in ["O'zbek", "��������������", "English"]:
            error_msg = "\n".join([
                MESSAGES["O'zbek"]["invalid_language"],
                MESSAGES["��������������"]["invalid_language"],
                MESSAGES["English"]["invalid_language"]
            ])
            await message.answer(error_msg, reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
                KeyboardButton("O'zbek"), KeyboardButton("��������������"), KeyboardButton("English")
            ), parse_mode="Markdown")
            return
        await state.update_data(language=message.text)
        await Form.next()
        localized = MESSAGES[message.text]
        await message.answer(localized["ask_name"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lock = get_lock(user_id)
    async with lock:
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        await state.update_data(name=message.text)
        await Form.next()
        await message.answer(localized["ask_age"], parse_mode="Markdown")

@dp.message_handler(state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lock = get_lock(user_id)
    async with lock:
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        if not message.text.isdigit() or not (16 <= int(message.text) <= 100):
            await message.answer(localized["invalid_age"], reply_markup=ReplyKeyboardRemove())
            return
        await state.update_data(age=message.text)
        await Form.next()
        await message.answer(localized["ask_parameter"], parse_mode="Markdown")

@dp.message_handler(state=Form.parameter)
async def process_parameter(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lock = get_lock(user_id)
    async with lock:
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        if not re.match(r'^\d{2,3}[-+]\d{2,3}[-+]\d{1,3}$', message.text):
            await message.answer(localized["invalid_parameter"], reply_markup=ReplyKeyboardRemove())
            return
        await state.update_data(parameter=message.text)
        parts = re.split(r'[-_+]', message.text)
        try:
            third_value = int(parts[2])
        except (IndexError, ValueError):
            await message.answer(localized["invalid_parameter"], reply_markup=ReplyKeyboardRemove())
            return
        if third_value > 20:
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            if language == "O'zbek":
                kb.add(KeyboardButton("Ha, ma'lumot to'g'ri"), KeyboardButton("Yo'q, adashibman unchalik uzun emas"))
            elif language == "��������������":
                kb.add(KeyboardButton("����, �������������������� ����������"), KeyboardButton("������, �� ������������, ���� ���������� ����������"))
            else:
                kb.add(KeyboardButton("Yes, the information is correct"), KeyboardButton("No, I made a mistake"))
            await Form.parameter_confirm.set()
            await message.answer(localized["parameter_confirm"], reply_markup=kb, parse_mode="Markdown")
        elif 1 <= third_value <= 20:
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for role in localized["role_options"]:
                kb.add(KeyboardButton(role))
            await Form.role.set()
            await message.answer(localized["ask_role"], reply_markup=kb, parse_mode="Markdown")
        else:
            await message.answer(localized["invalid_parameter"], reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=Form.parameter_confirm)
async def process_parameter_confirm(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lock = get_lock(user_id)
    async with lock:
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        valid_pos = {
            "O'zbek": "Ha, ma'lumot to'g'ri",
            "��������������": "����, �������������������� ����������",
            "English": "Yes, the information is correct"
        }
        valid_neg = {
            "O'zbek": "Yo'q, adashibman unchalik uzun emas",
            "��������������": "������, �� ������������, ���� ���������� ����������",
            "English": "No, I made a mistake"
        }
        if message.text not in [valid_pos[language], valid_neg[language]]:
            await message.answer(localized["invalid_choice"], parse_mode="Markdown")
            return
        if message.text == valid_pos[language]:
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for role in localized["role_options"]:
                kb.add(KeyboardButton(role))
            await Form.next()
            await message.answer(localized["ask_role"], reply_markup=kb, parse_mode="Markdown")
        else:
            await message.answer(localized["survey_cancelled"], reply_markup=ReplyKeyboardRemove())
            await state.finish()

@dp.message_handler(state=Form.role)
async def process_role(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lock = get_lock(user_id)
    async with lock:
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        if message.text not in localized["role_options"]:
            await message.answer(localized["invalid_role"], parse_mode="Markdown")
            return
        await state.update_data(role=message.text)
        await Form.next()
        await message.answer(localized["ask_city"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message_handler(state=Form.city)
async def process_city(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        await state.update_data(city=message.text)
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for goal in localized["goal_options"]:
            kb.add(KeyboardButton(goal))
        await Form.next()
        await message.answer(localized["ask_goal"], reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(state=Form.goal)
async def process_goal(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        if message.text not in localized["goal_options"]:
            await message.answer(localized["invalid_choice"], parse_mode="Markdown")
            return
        await state.update_data(goal=message.text)
        await Form.next()
        await message.answer(localized["ask_about"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message_handler(state=Form.about)
async def process_about(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        await state.update_data(about=message.text)
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        if language == "O'zbek":
            kb.add(KeyboardButton("Ha"), KeyboardButton("Yo'q"))
        elif language == "��������������":
            kb.add(KeyboardButton("����"), KeyboardButton("������"))
        else:
            kb.add(KeyboardButton("Yes"), KeyboardButton("No"))
        await Form.next()
        await message.answer(localized["ask_photo_choice"], reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(state=Form.photo_choice)
async def process_photo_choice(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        valid = {
            "O'zbek": ["Ha", "Yo'q"],
            "��������������": ["����", "������"],
            "English": ["Yes", "No"]
        }
        if message.text not in valid[language]:
            await message.answer(localized["invalid_choice"], parse_mode="Markdown")
            return
        if message.text == valid[language][0]:
            await Form.next()
            await message.answer(localized["ask_photo_upload"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
        else:
            await state.update_data(photo_upload=None)
            await Form.partner_age.set()
            await message.answer(localized["ask_partner_age"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message_handler(state=Form.photo_upload, content_types=types.ContentType.ANY)
async def process_photo_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        if message.content_type != types.ContentType.PHOTO:
            data = await state.get_data()
            language = data.get("language", "O'zbek")
            localized = MESSAGES[language]
            await message.answer(localized["invalid_photo"], reply_markup=ReplyKeyboardRemove())
            return
        await state.update_data(photo_upload=message.photo[-1].file_id)
        await Form.next()
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        await message.answer(localized["ask_partner_age"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message_handler(state=Form.partner_age)
async def process_partner_age(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        if not re.match(r'^\d{2,3}[-+]\d{2,3}$', message.text):
            await message.answer(localized["invalid_partner_age"], reply_markup=ReplyKeyboardRemove())
            return
        try:
            ages = re.split(r'[-+]', message.text)
            age1, age2 = int(ages[0]), int(ages[1])
            if not (16 <= age1 <= 99 and 16 <= age2 <= 99):
                raise ValueError
        except:
            await message.answer(localized["invalid_partner_age"], reply_markup=ReplyKeyboardRemove())
            return
        await state.update_data(partner_age=message.text)
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for role in localized["role_options"]:
            kb.add(KeyboardButton(role))
        await Form.next()
        await message.answer(localized["ask_partner_role"], reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(state=Form.partner_role)
async def process_partner_role(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        if message.text not in localized["role_options"]:
            await message.answer(localized["invalid_role"], reply_markup=ReplyKeyboardRemove())
            return
        await state.update_data(partner_role=message.text)
        await Form.next()
        await message.answer(localized["ask_partner_city"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message_handler(state=Form.partner_city)
async def process_partner_city(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        await state.update_data(partner_city=message.text)
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        await Form.next()
        await message.answer(localized["ask_partner_about"], reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@dp.message_handler(state=Form.partner_about)
async def process_partner_about(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        await state.update_data(partner_about=message.text)
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        if language == "O'zbek":
            kb.add(KeyboardButton("Ha"), KeyboardButton("Yo'q"))
        elif language == "��������������":
            kb.add(KeyboardButton("����"), KeyboardButton("������"))
        else:
            kb.add(KeyboardButton("Yes"), KeyboardButton("No"))
        await Form.next()
        await message.answer(localized["ask_confirmation"], reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(state=Form.confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with get_lock(user_id):
        data = await state.get_data()
        language = data.get("language", "O'zbek")
        localized = MESSAGES[language]
        valid = {
            "O'zbek": ["Ha", "Yo'q"],
            "��������������": ["����", "������"],
            "English": ["Yes", "No"]
        }
        if message.text not in valid[language]:
            await message.answer(localized["invalid_choice"], reply_markup=ReplyKeyboardRemove())
            return
        if message.text == valid[language][0]:
            global survey_counter
            current_id = survey_counter
            survey_counter += 1
            user_last_submission[user_id] = {"timestamp": time.time(), "language": language}
            result_text = (
                f"<b>{localized['survey_number']}:</b> {current_id}\n\n"
                f"<b>{localized['about_me']}:</b>\n"
                f"<b>{localized['name']}:</b> {data.get('name')}\n"
                f"<b>{localized['age']}:</b> {data.get('age')}\n"
                f"<b>{localized['parameters']}:</b> {data.get('parameter')}\n"
                f"<b>{localized['role']}:</b> {data.get('role')}\n"
                f"<b>{localized['location']}:</b> {data.get('city')}\n"
                f"<b>{localized['goal']}:</b> {data.get('goal')}\n"
                f"<b>{localized['about']}:</b>\n{data.get('about')}\n"
                f"<a href=\"tg://user?id={user_id}\">{localized['profile_link']}</a>\n\n"
                f"<b>{localized['partner']}:</b>\n"
                f"<b>{localized['partner_age']}:</b> {data.get('partner_age')}\n"
                f"<b>{localized['partner_role']}:</b> {data.get('partner_role')}\n"
                f"<b>{localized['partner_location']}:</b> {data.get('partner_city')}\n"
                f"<b>{localized['partner_about']}:</b> {data.get('partner_about')}\n"
            )
            if data.get("photo_upload"):
                await message.answer_photo(
                    data.get("photo_upload"),
                    caption=result_text,
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await message.answer(result_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
            await message.answer(localized["survey_accepted"], parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
            # ADMIN: agar rasm bo'lsa rasm bilan, aks holda matn bilan yuborilsin
            if data.get("photo_upload"):
                await bot.send_photo(
                    ADMIN_CHAT_ID,
                    photo=data.get("photo_upload"),
                    caption=result_text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    result_text,
                    parse_mode="HTML"
                )
        else:
            await message.answer(localized["survey_cancelled"], reply_markup=ReplyKeyboardRemove())
        await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)