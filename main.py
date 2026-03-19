import telebot
from telebot import types
import json
import os
import datetime

# ================= НАСТРОЙКИ =================
# Берем токен из настроек Railway
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = '-1003740141875' 
NICK_LIMIT_DAYS = 7 
# =============================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Завершение карьеры", "Возвращение карьеры")
    markup.add("Свободный агент", "Переход в клуб")
    markup.add("Свой текст", "Профиль")
    markup.add("Изменить ник")
    return markup

def get_back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⬅️ Назад")
    return markup

# --- СТАРТ И РЕГИСТРАЦИЯ ---
@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id not in data or "rb_nick" not in data[user_id]:
        msg = bot.send_message(message.chat.id, "👋 Привет! Введите ваш **Ник в РБ** для регистрации:")
        bot.register_next_step_handler(msg, register_user)
    else:
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu())

def register_user(message):
    rb_nick = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id] = {
        "rb_nick": rb_nick,
        "last_nick_change": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник **{rb_nick}** сохранен!", reply_markup=get_main_menu())

# --- ОБРАБОТКА ТЕКСТА ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id not in data:
        start(message)
        return

    rb_nick = data[user_id]["rb_nick"]
    user_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
    user_info = f"🎮 Ник: {rb_nick} | 👤 ТГ: {user_tag}"

    if message.text == "Изменить ник":
        last_change_str = data[user_id].get("last_nick_change")
        if last_change_str:
            last_change = datetime.datetime.strptime(last_change_str, "%Y-%m-%d %H:%M:%S")
            days_passed = (datetime.datetime.now() - last_change).days
            if days_passed < NICK_LIMIT_DAYS:
                bot.send_message(message.chat.id, f"❌ Менять ник можно раз в 7 дней!\nПодождите еще **{NICK_LIMIT_DAYS - days_passed} дн.**")
                return
        msg = bot.send_message(message.chat.id, "Введите новый **Ник в РБ**:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, process_nick_change)

    elif message.text == "Завершение карьеры":
        msg = bot.send_message(message.chat.id, "🚫 Напишите П.С.:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, send_to_channel, "Завершение карьеры", user_info)

    elif message.text == "Возвращение карьеры":
        msg = bot.send_message(message.chat.id, "🔙 Напишите П.С.:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, send_to_channel, "Возвращение карьеры", user_info)

    elif message.text == "Свободный агент":
        msg = bot.send_message(message.chat.id, "🆓 Напишите П.С.:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, send_to_channel, "Свободный агент", user_info)

    elif message.text == "Свой текст":
        msg = bot.send_message(message.chat.id, "📝 Введите ваш текст сообщения:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, send_to_channel, "Свой текст", user_info)

    elif message.text == "Переход в клуб":
        msg = bot.send_message(message.chat.id, "🏠 Введите: `Клуб, П.С.` через запятую", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, process_club, user_info)

    elif message.text == "Профиль":
        bot.send_message(message.chat.id, f"👤 **Профиль**\n\n🎮 Ник РБ: `{rb_nick}`\n🔗 ТГ: {user_tag}")

# --- ЛОГИКА ШАГОВ ---

def process_nick_change(message):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu())
        return
    new_nick = message.text.strip()
    data = load_data()
    user_id = str(message.from_user.id)
    data[user_id]["rb_nick"] = new_nick
    data[user_id]["last_nick_change"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник изменен на: **{new_nick}**", reply_markup=get_main_menu())

def send_to_channel(message, status, user_info):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu())
        return
    report = f"📢 **{status.upper()}**\n\n{user_info}\n🖋 П.С.: {message.text}"
    bot.send_message(CHANNEL_ID, report, parse_mode='Markdown')
    bot.send_message(message.chat.id, "✅ Опубликовано!", reply_markup=get_main_menu())

def process_club(message, user_info):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu())
        return
    try:
        parts = message.text.split(',')
        report = f"🏠 **ПЕРЕХОД В КЛУБ**\n\n{user_info}\n🏢 Клуб: {parts[0].strip()}\n📝 П.С.: {parts[1].strip()}"
        bot.send_message(CHANNEL_ID, report, parse_mode='Markdown')
        bot.send_message(message.chat.id, "✅ Опубликовано!", reply_markup=get_main_menu())
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка! Нужно писать через запятую.", reply_markup=get_main_menu())

if __name__ == "__main__":
    print("Бот Трансфермаркет запущен на Railway!")
    bot.infinity_polling()
