import asyncio
import logging
import config
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, ADMINISTRATOR
from collections import defaultdict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton




Token = config.token



logging.basicConfig(level=logging.INFO)

bot = Bot(token=Token)
dp = Dispatcher()


banned_users = set()

warnings = defaultdict(int)

WARN_LIMIT = 3

panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить в свой чат', url='https://t.me/YOUR_bot?startgroup=YOUR&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users')]
])

async def get_username(chat_id: int, user_id: int) -> str:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        username = member.user.username
        return f"@{username}" if username else f"ID: {user_id}"
    except Exception as e:
        logging.error(f"Ошибка получения username: {e}")
        return f"ID: {user_id}"
async def is_admin(chat_id: int, user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ['administrator', 'creator']

@dp.message(Command('start'))
async def welcome_message(message: types.Message):
    await message.answer(f'Привет, @{message.from_user.username}! Можешь меня добавить в чат по кнопке ниже.', reply_markup=panel)

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
async def on_bot_became_admin(event: types.ChatMemberUpdated):
    if event.new_chat_member.user.id == bot.id:
        await event.answer(text="""Спасибо, что добавил меня в чат!
Что я умею: 
/warn - предупреждение
/unwarn - снятие предупреждения
/ban - забанить пользователя
/unban - разбанить""")

@dp.message(Command('warn'))
async def warn_user(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение пользователя.")
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("Только администраторы могут использовать эту команду.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    user_username = await get_username(chat_id, user_id)
    warnings[(user_id, chat_id)] += 1

    if warnings[(user_id, chat_id)] >= WARN_LIMIT:
        banned_users.add((user_id, chat_id))
        await message.reply(f"Пользователь {user_username} был забанен за превышение лимита предупреждений.")
    else:
        await message.reply(f"Пользователю {user_username} вынесено предупреждение. Количество предупреждений: {warnings[(user_id, chat_id)]}/{WARN_LIMIT}.")

@dp.message(Command('ban'))
async def ban_user(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение пользователя.")
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("Только администраторы могут использовать эту команду.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    user_username = await get_username(chat_id, user_id)
    banned_users.add((user_id, chat_id))

    await message.reply(f"Пользователь {user_username} был забанен.")

@dp.message(Command('unban'))
async def unban_user(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение пользователя.")
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("Только администраторы могут использовать эту команду.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    user_username = await get_username(chat_id, user_id)
    banned_users.discard((user_id, chat_id))
    warnings[(user_id, chat_id)] = 0

    await message.reply(f"Пользователь {user_username} был разбанен.")

@dp.message(Command('unwarn'))
async def remove_warn(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение пользователя.")
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("Только администраторы могут использовать эту команду.")
        return

    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id
    user_username = await get_username(chat_id, user_id)

    if warnings[(user_id, chat_id)] > 0:
        warnings[(user_id, chat_id)] -= 1

    await message.reply(f"Одно предупреждение было снято с пользователя {user_username}. Количество оставшихся предупреждений: {warnings[(user_id, chat_id)]}.")

@dp.message()
async def handle_message(message: types.Message):
    if (message.from_user.id, message.chat.id) in banned_users:
        await message.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())




