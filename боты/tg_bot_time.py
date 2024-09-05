import asyncio
import logging
import config
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage



BOT_TOKEN = config.token
CHANNEL_ID = config.id
tasks = {}
async def send_periodic_messages(bot: Bot, user_id: int, text: str, interval: int):
    while True:
        await bot.send_message(chat_id=user_id, text=text)
        await asyncio.sleep(interval)


async def approve_request(event: ChatJoinRequest, bot: Bot):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласиться на периодические сообщения", callback_data=f"agree_{event.from_user.id}")],
        [InlineKeyboardButton(text="Отказаться от периодических сообщений", callback_data=f"disagree_{event.from_user.id}")]
    ])
    await bot.send_message(chat_id=event.from_user.id, text=f'{event.from_user.first_name}, Рада приветствовать тебя в нашем канале!', reply_markup=keyboard)
    await event.approve()


async def button_click_handler(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.data.startswith("agree"):
        await callback_query.message.bot.send_message(chat_id=user_id, text="Вы согласились на получение периодических сообщений.\n\n <b>Чтобы отказаться напишите /stop</b>\n (сообщения каждые 10 сек)", parse_mode='html', reply_markup=generate_keyboard(user_id))
        tasks[user_id] = asyncio.create_task(send_periodic_messages(callback_query.message.bot, user_id, "Сообщение", 10))
    elif callback_query.data.startswith("disagree"):
        await callback_query.message.bot.send_message(chat_id=user_id, text="Вы отказались от получения периодических сообщений.")
        if user_id in tasks:
            tasks[user_id].cancel()
            del tasks[user_id]


def generate_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отказаться от периодических сообщений", callback_data=f"disagree_{user_id}")]
    ])


async def stop_command(message: types.Message):
    await message.answer("Вы можете отказаться от периодических сообщений.", reply_markup=generate_keyboard(message.from_user.id))


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN, session=session)

    dp = Dispatcher(storage=MemoryStorage())
    router = Router()

    router.chat_join_request.register(approve_request)
    router.callback_query.register(button_click_handler, F.data.startswith("agree_") | F.data.startswith("disagree_"))
    router.message.register(stop_command, F.text == "/stop")

    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())