import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter,  ADMINISTRATOR



Token = config.token
logging.basicConfig(level=logging.INFO)

bot = Bot(token=Token)
dp = Dispatcher()

panel = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Добавить в свой чат', url= 'https://t.me/YOUR_bot?startgroup=YOUR&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users')]])

@dp.message(Command('start'))
async def welcome_message(message: types.Message):
    await message.answer(f'Привет!, @{message.from_user.username} можешь меня добавить в чат по кнопке ниже', reply_markup=panel)



@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
async def on_bot_became_admin(event: types.ChatMemberUpdated):
    await event.answer(text="Спасибо, что добавил меня в чат!")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())




