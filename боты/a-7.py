import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Ваши данные
TOKEN = 'vk1.a.zoR_nSm-nD7HsqEBhjpcinGJG1ZVmPdWPnC0Mt_ZMx0BraxhTEpCY1gUK8MSR1gYaVcYpUpnX-K7AsVj3jJXTmheU0FyY-zmwKnI1QoacPJaUpC3Z3sMws2HTgslYS06OM7k_jPTvJoRfCRXr8UkuGxp-tkt7m-ypjej1lByV4O_cWWCwssxNUVCI0h'
GROUP_ID = '226604314'

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# Клавиатура
def get_default_keyboard():
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "payload": json.dumps({"command": "show_commands"}),
                        "label": "Показать команды"
                    },
                    "color": "primary"
                }
            ]
        ]
    }
    return json.dumps(keyboard)

# Список РП-команд и стикеров по умолчанию
rp_commands = {
    "ударить": ("ударил", 9017),
    "поцеловать": ("поцеловал", 9016),
    "обнять": ("обнял", 9018),
    "пнуть": ("пнул", 9019),
    "погладить": ("погладил", 9019)
}

user_state = {}

def get_user_info(user_id):
    try:
        return vk.users.get(user_ids=user_id, fields='sex')[0]
    except (vk_api.exceptions.VkApiError, IndexError) as e:
        logger.error(f"Error getting user info for user_id {user_id}: {e}")
        return None

def get_gender_action(gender, action):
    return action + ('а' if gender == 1 else '')

def format_user_link(user_id, name):
    return f"[id{user_id}|{name}]"

def send_message(peer_id, message):
    try:
        vk.messages.send(
            peer_id=peer_id,
            message=message,
            random_id=random.randint(1, 2 ** 31),
            keyboard=get_default_keyboard()
        )
    except vk_api.exceptions.VkApiError as e:
        logger.error(f"Error sending message to peer_id {peer_id}: {e}")

def handle_command(command, args, msg):
    peer_id = msg['peer_id']
    from_id = msg['from_id']
    from_user_info = get_user_info(from_id)
    from_user_name = from_user_info['first_name'] if from_user_info else "Пользователь"
    from_user_gender = from_user_info['sex'] if from_user_info else 2

    command = command.lower()

    if command in rp_commands:
        response_action, sticker_id = rp_commands[command]
        if 'reply_message' in msg and 'from_id' in msg['reply_message']:
            reply_user_id = msg['reply_message']['from_id']
            reply_user_info = get_user_info(reply_user_id)
            user_name = reply_user_info['first_name'] if reply_user_info else "Пользователь"
            action = get_gender_action(from_user_gender, response_action)
            response = f"{format_user_link(from_id, from_user_name)} {action} {format_user_link(reply_user_id, user_name)}"
        elif args:
            user_name = args[0]
            action = get_gender_action(from_user_gender, response_action)
            response = f"{format_user_link(from_id, from_user_name)} {action} {user_name}"
        else:
            send_message(peer_id, "Пожалуйста, ответьте на сообщение пользователя или укажите имя пользователя для выполнения команды.")
            return

        send_message(peer_id, response)
        vk.messages.send(peer_id=peer_id, sticker_id=sticker_id, random_id=random.randint(1, 2 ** 31))
    elif command == "изменитьстикер":
        if args and args[0].lower() in rp_commands:
            user_state[from_id] = args[0].lower()
            send_message(peer_id, f"Отправьте новый стикер для команды '{args[0].lower()}'")
        else:
            send_message(peer_id, "Неизвестная команда для изменения стикера или команда не указана.")
    else:
        send_message(peer_id, "Неизвестная команда.")

def send_welcome_message(peer_id):
    welcome_message = (
"<b>Привет! Добро пожаловать!</b>\n"
        "Вот список доступных команд:\n"
        "ударить - ударить пользователя\n"
        "поцеловать - поцеловать пользователя\n"
        "обнять - обнять пользователя\n"
        "пнуть - пнуть пользователя\n"
        "погладить - погладить пользователя\n"
        "изменитьстикер - изменить стикер для команды\n"
        "Нажмите на кнопку ниже, чтобы показать список команд снова."
    )
    send_message(peer_id, welcome_message)

# Основной цикл
for event in longpoll.listen():
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.message
            text = msg['text']
            peer_id = msg['peer_id']
            from_id = msg['from_id']

            if any(command in text.lower() for command in rp_commands.keys()) or "изменитьстикер" in text.lower():
                parts = text.split()
                command = parts[0]
                args = parts[1:]
                handle_command(command, args, msg)
            elif from_id in user_state and 'attachments' in msg and msg['attachments'][0]['type'] == 'sticker':
                new_sticker_id = msg['attachments'][0]['sticker']['sticker_id']
                command_to_update = user_state.pop(from_id)
                rp_commands[command_to_update] = (rp_commands[command_to_update][0], new_sticker_id)
                send_message(peer_id, f"Стикер для команды '{command_to_update}' успешно изменен.")
            elif 'payload' in msg:
                payload = json.loads(msg['payload'])
                if payload.get('command') == 'show_commands':
                    send_welcome_message(peer_id)
            else:

                pass
        elif event.type == VkBotEventType.GROUP_JOIN:
            send_welcome_message(event.object.user_id)
    except Exception as e:
        logger.error(f"Error handling event: {e}")
