import vk_api, random, json, logging, d, time
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Ваши данные
TOKEN = d.Token
GROUP_ID = d.GROUP_ID
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
        "Привет! Спасибо, что добавили меня в группу)\n\n\n"
        "Вот список доступных команд:\n\n"
        "погладить - погладить пользователя\n"
        "кусь - кусьнуть пользователя\n"
        "минет\n"    
        "раздеть\n"
        "погладить - погладить пользователя\n\n"
        "change + 'стикер' - изменить стикер для команды\n"
        "старт - показать список команд\n"
        "id - узнать айди группы\n"
        "пинг - измерить пинг\n\n"
        "Чтобы увидеть список команд снова, нажмите на кнопку ниже."
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


for event in longpoll.listen():
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.message
            text = msg['text']
            peer_id = msg['peer_id']
            from_id = msg['from_id']

            # Проверка на команду change
            if text.lower().startswith('change'):
                process_change_command(from_id, peer_id, text[7:], msg)  # Передаем текст без 'change'
            elif text.lower().startswith( 'id'):

                send_message(peer_id, f"ID сообщества {GROUP_ID}", keyboard)
            elif text.lower().startswith( 'старт'):
                send_welcome_message(peer_id)
            elif text.lower().startswith('пинг'):
                start_time = time.time()  # Запоминаем время отправки команды
                send_message(peer_id, "Понг!", keyboard)
                end_time = time.time()  # Запоминаем время после получения ответа
                latency = end_time - start_time
                send_message(peer_id, f"Задержка: {latency:.2f} секунд", keyboard)
                logger.debug(f"Ping command processed with latency {latency:.2f} seconds")

            if text.lower().startswith('музыка'):
              from_id = event.obj.message['from_id']
              vk_user = vk.users.get(user_ids=from_id)
              username = vk_user[0]['first_name']

            # Список музыкальных плейлистов
              coin_sides = [
                "741758604_44_45db5efe41613d7796",
                "821162530_84/b624c0153288eca499",
                "263841990_70_7fbe4f1e2e925ef370",
                "741758604_51/908c6081d9244cbb14"]
              coin_side = random.choice(coin_sides)

            # Сообщения, которые будут отправлены пользователю
              cmssscs = [
                f"[vk.com/id{from_id}|{username}], слушай музыку!",
                f"[vk.com/id{from_id}|{username}], хочешь добавить свой альбом, пиши создателю сообщества!"]
              cmsssc = random.choice(cmssscs)


              vk.messages.send(
                    peer_id=peer_id,
                    message=cmsssc,
                    attachment=f"audio_playlist{coin_side}",
                    random_id=random.randint(1, 2 ** 31)
                )

            else:
                command, args = get_command_from_text(text)
                if command:
                    process_roleplay_command(command, args, msg)


                # Обработка payload для показа команд
                if 'payload' in msg:
                    payload = json.loads(msg['payload'])
                    if payload.get('command') == 'show_commands':
                        send_welcome_message(peer_id)
                        continue

                # Если пользователь находится в процессе изменения стикера, ждем стикер
                elif from_id in user_state:
                    process_change_command(from_id, peer_id, text, msg)

        elif event.type == VkBotEventType.GROUP_JOIN:
            send_welcome_message(event.object.user_id)
    except Exception as e:
        logger.error(f"Error handling event: {e}")

