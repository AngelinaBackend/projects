from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import config
import re
import asyncio
import logging
import json
import os


logging.basicConfig(level=logging.INFO)

Token = config.token

DATA_FILE = 'data.json'

bot = Bot(token=Token)
dp = Dispatcher()

def load_data():

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Ошибка при загрузке данных: {e}")
            return {'users': {}}
    return {'users': {}}

def save_data(data):

    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        logging.error(f"Ошибка при сохранении данных: {e}")

data = load_data()

@dp.message(Command('start'))
async def start_handler(msg: types.Message):
    user_id = msg.from_user.id
    user_data = data['users'].setdefault(user_id, {
        'name': msg.from_user.username,
        'keywords': [],
        'chats': []
    })
    if 'name' not in user_data:
        save_data(data)
        await msg.reply("Ваша учетная запись настроена для получения оповещений.\n Команды: /key")
    else:
        await msg.reply("Ваша учетная запись уже настроена.")

    commands_info = (
        """Доступные команды:
        
    /start - Настроить учетную запись.
    /addchat - Добавить текущий чат в список мониторинга.
    /removechat - Удалить текущий чат из списка мониторинга.
    /listchats - Показать чаты, которые вы мониторите.
    /keywords - Управление ключевыми словами.
    /keywords add <Ключевое слово> - Добавить ключевое слово.
    /keywords remove <Ключевое слово> - Удалить ключевое слово.
    /keywords list - Показать все ключевые слова."""
    )

    await msg.reply(commands_info)

@dp.message(Command('addchat'))
async def add_chat_handler(msg: types.Message):
    if msg.chat.type not in ['group', 'supergroup']:
        await msg.reply("Пожалуйста, используйте эту команду в группе или супергруппе.")
        return

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    user_chats = data['users'].setdefault(user_id, {}).setdefault('chats', [])

    if chat_id not in user_chats:
        user_chats.append(chat_id)
        save_data(data)
        await bot.send_message(user_id, f"Чат {chat_id} был добавлен в список мониторинга.")
    else:
        await bot.send_message(user_id, "Этот чат уже находится в списке мониторинга.")

@dp.message(Command('removechat'))
async def remove_chat_handler(msg: types.Message):
    if msg.chat.type not in ['group', 'supergroup']:
        await msg.reply("Пожалуйста, используйте эту команду в группе или супергруппе.")
        return

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    user_chats = data['users'].setdefault(user_id, {}).setdefault('chats', [])

    if chat_id in user_chats:
        user_chats.remove(chat_id)
        save_data(data)
        await bot.send_message(user_id, f"Чат {chat_id} был удален из списка мониторинга.")
    else:
        await bot.send_message(user_id, "Этот чат не находится в списке мониторинга.")

@dp.message(Command('listchats'))
async def list_chats_handler(msg: types.Message):
    user_id = msg.from_user.id
    chats = data['users'].get(user_id, {}).get('chats', [])
    if chats:
        chat_list = '\n'.join(map(str, chats))
        await msg.reply(f"Текущие чаты для мониторинга:\n{chat_list}")
    else:
        await msg.reply("В данный момент нет чатов для мониторинга.")

@dp.message(Command('keywords'))
async def keywords_handler(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in data['users']:
        await msg.reply("Сначала настройте вашу учетную запись. Используйте команду /start для этого.")
        return

    args = msg.text.split(maxsplit=2)
    if len(args) < 2:
        await msg.reply("Использование: /keywords <add|remove|list> <Ключевое слово>")
        return

    action = args[1].lower()
    keywords = data['users'][user_id].setdefault('keywords', [])

    if action == 'add':
        if len(args) < 3:
            await msg.reply("Пожалуйста, укажите ключевое слово для добавления.")
            return
        keyword = args[2]
        if keyword not in keywords:
            keywords.append(keyword)
            save_data(data)
            await msg.reply(f"Ключевое слово '{keyword}' успешно добавлено.")
        else:
            await msg.reply(f"Ключевое слово '{keyword}' уже существует.")

    elif action == 'remove':
        if len(args) < 3:
            await msg.reply("Пожалуйста, укажите ключевое слово для удаления.")
            return
        keyword = args[2]
        if keyword in keywords:
            keywords.remove(keyword)
            save_data(data)
            await msg.reply(f"Ключевое слово '{keyword}' успешно удалено.")
        else:
            await msg.reply(f"Ключевое слово '{keyword}' не существует.")

    elif action == 'list':
        if keywords:
            keyword_list = '\n'.join(keywords)
            await msg.reply(f"Текущие ключевые слова:\n{keyword_list}")
        else:
            await msg.reply("В данный момент нет отслеживаемых ключевых слов.")

    else:
        await msg.reply("Неверное действие. Используйте /keywords <add|remove|list> <Ключевое слово>.")

@dp.message()
async def message_handler(msg: types.Message):
    monitored_chats = set(chat for user in data['users'].values() for chat in user.get('chats', []))
    if msg.chat.id in monitored_chats:
        for user_id, user_data in data['users'].items():
            keywords = user_data.get('keywords', [])
            for keyword in keywords:
                if re.search(keyword, msg.text, re.IGNORECASE):
                    try:
                        await bot.send_message(
                            user_id,
                            f"Ключевое слово '{keyword}' найдено в чате {msg.chat.id} пользователем {msg.from_user.full_name} (@{msg.from_user.username})."
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
