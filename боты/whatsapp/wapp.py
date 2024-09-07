from whatsapp_chatbot_python import GreenAPIBot, Notification
import c

bot = GreenAPIBot(c.api_key, c.api_idInstance)



@bot.router.message()
def message_handler(notification: Notification) -> None:
    text = notification.message_text.lower()
    sender_data = notification.event["senderData"]
    sender_name = sender_data["senderName"]
    if text == 'привет':
        notification.answer(f"Привет, {sender_name}!")
    else:
        notification.answer("Неправильно введена команда. Напишите: 'Привет'")

bot.run_forever()