import json
import asyncio
import logging
import config
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


API_TOKEN = config.token


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

JSON_FILE = "data.json"

try:
    with open(JSON_FILE, 'r') as file:
        users = json.load(file)
except FileNotFoundError:
    users = {}

user_data = {}


@router.message(Command("start"))
async def send_welcome(message: types.Message):
    user_first_name = message.from_user.first_name
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Регистрация", callback_data="register")
    keyboard.button(text="Показать пользователей", callback_data="show_users")
    keyboard.adjust(1)
    await message.answer(f"Привет, {user_first_name}! Выберите действие:", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "register")
async def start_registration(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in users:
        await callback_query.message.answer("Вы уже зарегистрированы.")
        return


    user_data[user_id] = {'step': 1, 'username': callback_query.from_user.username}
    await callback_query.message.answer("Введите ваше имя:")


@router.message()
async def handle_registration(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        logging.warning(f"Received message from unregistered user: {user_id}")
        return

    steps = {1: "name", 2: "surname", 3: "age"}
    next_step = {1: "Введите вашу фамилию:", 2: "Введите ваш возраст:", 3: "Регистрация завершена."}

    step = user_data[user_id]['step']
    user_data[user_id][steps[step]] = message.text

    if step == 3:
        if not message.text.isdigit():
            await message.answer("Возраст должен быть числом. Пожалуйста, введите ваш возраст снова:")
            return

        users[user_id] = {key: user_data[user_id].get(key, 'Unknown') for key in ['username', 'name', 'surname', 'age']}
        with open(JSON_FILE, 'w') as file:
            json.dump(users, file, indent=4)
        user_name = user_data[user_id]['name']
        del user_data[user_id]
        await message.answer(f"Вы успешно зарегистрированы, {user_name}!")
    else:
        user_data[user_id]['step'] += 1
        await message.answer(next_step[step])


@router.callback_query(F.data == "show_users")
async def list_users(callback_query: CallbackQuery):
    if users:
        user_list = "\n\n".join(
            [f"ID: {uid}\nUsername: @{info['username']}\nФИ: {info['name']} {info['surname']}\nВозраст: {info['age']}"
             for uid, info in users.items()])
        await callback_query.message.answer(f"<b>Зарегистрированные пользователи:</b>\n\n{user_list}\n",
                                            parse_mode='html')
    else:
        await callback_query.message.answer("Нет зарегистрированных пользователей.")
    await callback_query.answer()


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())