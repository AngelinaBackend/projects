import vk_api, random, json, logging,  time, re
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Ваши данные
TOKEN = "vk1.a.a_rZKmUKqpX9MtCqcDiFSFm_LYviSHP4DAqxQkVh7ugIqvDzEXD649Y8b6U1F_6a6-53iqnp4NIWau8S6ggxu2FWn8YXnLk_MCbd-mSEkMixpcmPs5oczHsRejNTKM5hE0zbD3VVLwqs-cSqAdgRzgZA-zrsISObGxy-atVd4FaJ6qwkQ2j0760qbPU14qO-RzESknpRowFzM0iYLwc9Tw"
GROUP_ID = '226604314'
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# Клавиатура
keyboard = VkKeyboard(one_time=False)
keyboard.add_button(
    label="Показать команды",
    color=VkKeyboardColor.POSITIVE,
    payload={"command": "show_commands"}
)

# Список РП-команд и стикеров по умолчанию
roleplay_commands = {
    "погладить": ("погладил", 9019),
    "кусь": ("кусьнул", 9019),
    "поцеловать": ("поцеловал", 9019),
    "уебать": ("уебал", 9019),
    "сделать чай ": ("сделал чай", 9019),
    "дать печеньку": ("дал печеньку", 9019),
    "выебать": ("выебал", 9019),
    "дать пять  ": ("дал пять", 9019),
    "записать на ноготочки ": ("записал на ноготочки", 9019),
    "испугать": ("испугал", 9019),
    "изнасиловать": ("изнасиловал", 9019),
    "кастрировать": ("кастрировал", 9019),
    "лизнуть": ("лизнул", 9019),
    "извиниться": ("извинился", 9019),
    "обнять": ("обнял", 9019),
    "отравить": ("отравил", 9019),
    "отдаться": ("отдался", 9019),
    "поздравить": ("поздравил", 9019),
    "прижать": ("прижал", 9019),
    "потрогать": ("потрогал", 9019),
    "пожать руку   ": ("пожал руку", 9019),
    "послать нахуй ": ("послал нахуй", 9019),
    "понюхать": ("понюхал", 9019),
    "пнуть": ("пнул", 9019),
    "расстрелять": ("расстрелял", 9019),
    "секс": ("трахнул", 9019),
    "сжечь": ("сжег", 9019),
    "балалайка": ("поиграл на балалайке", 9019),
    "Лобик": ("поцеловал в лобик", 9019),
    "лечь на колени": ("лег на колени", 9019),
    "минет": ("сделал минет", 9019),
    "раздеть": ("раздел", 9019)
}

user_state = {}
user_stickers = {}  # Хранит стикеры, измененные пользователями


def get_user_info(user_id):
    try:
        user_info = vk.users.get(user_ids=user_id, fields='sex')
        if user_info and len(user_info) > 0:
            return user_info[0]
        else:
            logger.error(f"User info for user_id {user_id} is empty or list index out of range.")
            return None
    except (vk_api.exceptions.VkApiError, IndexError) as e:
        logger.error(f"Error getting user info for user_id {user_id}: {e}")
        return None


def get_gender_action(gender, action):
    words = action.split()
    if gender == 1:
        if words[0] == "сжег":
            words[0] = "сожгла"
        elif words[0] == "лег":
            words[0] = "легла"
        else:
            words[0] += "а"
    return ' '.join(words)


def format_user_link(user_id, name):
    return f"[id{user_id}|{name}]"


def send_message(peer_id, message, keyboard=None):
    try:
        vk.messages.send(
            peer_id=peer_id,
            message=message,
            random_id=random.randint(1, 2 ** 31),
            keyboard=keyboard.get_keyboard() if keyboard else None
        )
    except vk_api.exceptions.VkApiError as e:
        logger.error(f"Error sending message to peer_id {peer_id}: {e}")


def get_user_sticker(user_id, command):
    if user_id in user_stickers and command in user_stickers[user_id]:
        return user_stickers[user_id][command]
    return roleplay_commands[command][1]


def process_roleplay_command(command, args, msg):
    peer_id = msg['peer_id']
    from_id = msg['from_id']
    from_user_info = get_user_info(from_id)

    if not from_user_info:
        send_message(peer_id, "Ошибка получения информации о пользователе.", keyboard)
        return

    from_user_name = from_user_info.get('first_name', "Пользователь")
    from_user_gender = from_user_info.get('sex', 2)

    # Проверка на упоминание пользователя или ответ на сообщение
    if 'reply_message' in msg:
        reply_user_id = msg['reply_message']['from_id']
        reply_user_info = get_user_info(reply_user_id)
        if not reply_user_info:
            send_message(peer_id, "Ошибка получения информации о пользователе в ответе.", keyboard)
            return

        user_name = reply_user_info['first_name']
        action = get_gender_action(from_user_gender, roleplay_commands[command][0])
        response = f"{format_user_link(from_id, from_user_name)} {action} {format_user_link(reply_user_id, user_name)}"
    elif args and (args[0].startswith('@') or args[0].startswith('[id')):
        user_name = args[0]
        action = get_gender_action(from_user_gender, roleplay_commands[command][0])
        response = f"{format_user_link(from_id, from_user_name)} {action} {user_name}"
    else:
        send_message(peer_id, "Для выполнения команды нужно ответить на сообщение пользователя или упомянуть его.",
                     keyboard)
        return

    send_message(peer_id, response, keyboard)
    vk.messages.send(peer_id=peer_id, sticker_id=get_user_sticker(from_id, command),
                     random_id=random.randint(1, 2 ** 31))


def send_welcome_message(peer_id):
    welcome_message = (
        """Привет! Спасибо, что добавили меня в группу)"""
    )
    send_message(peer_id, welcome_message, keyboard)


def get_command_from_text(text):
    words = text.lower().split()
    combined_text = ''.join(words)
    command = None

    # Проверка на наличие команды в списке (теперь учитываем пробелы)
    for rp_command in roleplay_commands.keys():
        # Проверяем, начинается ли текст с команды
        if combined_text.startswith(rp_command.lower().replace(" ", "")):
            command = rp_command
            break

    # Если команда найдена, возвращаем её и оставшиеся слова
    if command:
        remaining_text = text[len(command):].strip()
        args = remaining_text.split() if remaining_text else []
        return command, args

    return None, []

def process_change_command(from_id, peer_id, text, msg):
    if from_id not in user_state:
        command, args = get_command_from_text(text)
        if command:
            user_state[from_id] = {'stage': 'awaiting_sticker', 'command': command}
            send_message(peer_id, f"Теперь отправьте новый стикер для команды '{command}'", keyboard)
        else:
            send_message(peer_id, "Неизвестная команда. Пожалуйста, укажите корректную РП-команду.", keyboard)
    else:
        if 'attachments' in msg and msg['attachments'][0]['type'] == 'sticker':
            new_sticker_id = msg['attachments'][0]['sticker']['sticker_id']
            command_to_update = user_state[from_id]['command']
            if from_id not in user_stickers:
                user_stickers[from_id] = {}
            user_stickers[from_id][command_to_update] = new_sticker_id
            del user_state[from_id]
            send_message(peer_id, f"Стикер для команды '{command_to_update}' успешно изменен.", keyboard)
        else:
            send_message(peer_id, "Пожалуйста, отправьте стикер для изменения.", keyboard)
def handle_change_command(from_id, peer_id, text, msg):
    process_change_command(from_id, peer_id, text[7:], msg)  # Передаем текст без 'change'

def handle_id_command(from_id, peer_id, text, msg):
    send_message(peer_id, f"ID сообщества {GROUP_ID}", keyboard)

def handle_start_command(peer_id):
    send_welcome_message(peer_id)

def handle_ping_command(from_id, peer_id, text, msg):
    start_time = time.time()  # Запоминаем время отправки команды
    send_message(peer_id, "Понг!", keyboard)
    end_time = time.time()  # Запоминаем время после получения ответа
    latency = end_time - start_time
    send_message(peer_id, f"Задержка: {latency:.2f} секунд", keyboard)
    logger.debug(f"Ping command processed with latency {latency:.2f} seconds")

def handle_music_command(from_id, peer_id, text, msg):
    vk_user = vk.users.get(user_ids=from_id)
    username = vk_user[0]['first_name']

    # Список музыкальных плейлистов
    coin_sides = [
        "741758604_44_45db5efe41613d7796",
        "821162530_84/b624c0153288eca499",
        "263841990_70_7fbe4f1e2e925ef370",
        "741758604_51/908c6081d9244cbb14"
    ]
    coin_side = random.choice(coin_sides)

    # Сообщения, которые будут отправлены пользователю
    cmssscs = [
        f"{username}, слушай музыку!",
        f"{username}, хочешь добавить свой альбом, пиши создателю сообщества!"
    ]
    cmsssc = random.choice(cmssscs)

    vk.messages.send(
        peer_id=peer_id,
        message=cmsssc,
        attachment=f"audio_playlist{coin_side}",
        random_id=random.randint(1, 2 ** 31)
    )

def handle_online_command(peer_id):
    try:
        chat_members = vk.messages.getConversationMembers(peer_id=peer_id)
        member_ids = [member['member_id'] for member in chat_members['items']]
        user_infos = vk.users.get(user_ids=','.join(map(str, member_ids)), fields='online,screen_name')
        online_members = [f"[vk.com/id{user_info['id']}|{user_info['first_name']} {user_info['last_name']}]" for user_info in user_infos if user_info['online'] == 1]
        online_list = ', '.join(online_members)
        send_message(peer_id, f"Сейчас онлайн: 🌝\n{online_list}", keyboard)
    except Exception as e:
        logger.error(f"Error fetching online members: {e}")
        send_message(peer_id, "Ошибка при получении списка пользователей онлайн.", keyboard)

def handle_calculator_command(peer_id, text):
    calc_input = text[11:].strip()
    allowed_tokens = '1234567890+-*/.() '
    if not re.match('^[' + re.escape(allowed_tokens) + ']+$', calc_input):
        send_message(peer_id, "Недопустимый символ в выражении. Пожалуйста, используйте только цифры и операторы.", keyboard)
    else:
        try:
            result = eval(calc_input)  # Используйте eval для вычисления
            send_message(peer_id, f"Результат: {result}", keyboard)
        except Exception as e:
            send_message(peer_id, f"Ошибка: {e}", keyboard)

def handle_ship_command(peer_id):
    try:
        chat_users = vk.messages.getConversationMembers(peer_id=peer_id)
        all_users = [user['member_id'] for user in chat_users['items']]
        if len(all_users) < 2:
            send_message(peer_id, 'В чате недостаточно пользователей!', keyboard)
        else:
            random_users = random.sample(all_users, 2)
            users_info = vk.users.get(user_ids=','.join(map(str, random_users)), fields='first_name, last_name')
            user1 = users_info[0]
            user2 = users_info[1]
            send_message(peer_id, f"ОУ голубки может у них все сложется? [vk.com/id{user1['id']}|{user1['first_name']} {user1['last_name']}] и [vk.com/id{user2['id']}|{user2['first_name']} {user2['last_name']}]!", keyboard)
    except Exception as e:
        logger.error(f"Error processing ship command: {e}")
        send_message(peer_id, 'Я что-то заснула, извините.', keyboard)

# Словарь, сопоставляющий команды с их обработчиками
command_handlers = {
    'change': handle_change_command,
    'id': handle_id_command,
    'старт': handle_start_command,
    'пинг': handle_ping_command,
    'музыка': handle_music_command,
    'онлайн': handle_online_command,
    'калькулятор': handle_calculator_command,
    'шип': handle_ship_command,
}

# Основной цикл
for event in longpoll.listen():
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.message
            text = msg['text'].lower()
            peer_id = msg['peer_id']
            from_id = msg['from_id']

            command, args = get_command_from_text(text)

            if command in roleplay_commands:
                process_roleplay_command(command, args, msg)
            elif command in command_handlers:
                command_handlers[command](from_id, peer_id, text, msg)
# Если пользователь находится в процессе изменения стикера, ждем стикер
            elif from_id in user_state:
                process_change_command(from_id, peer_id, text, msg)

            # Обработка payload для показа команд
            if 'payload' in msg:
                payload = json.loads(msg['payload'])
                if payload.get('command') == 'show_commands':
                    send_welcome_message(peer_id)

    except Exception as e:
        logger.error(f"Error handling event: {e}")
