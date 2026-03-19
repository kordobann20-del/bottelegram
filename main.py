import telebot
from telebot import types
import json
import os
import datetime

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = '-1003740141875' 
NICK_LIMIT_DAYS = 7 
RETIRE_LIMIT_DAYS = 5  # Ограничение на возврат (5 дней)
ADMIN_ID = 5845609895  
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

def get_main_menu(user_id):
    data = load_data()
    user_id_str = str(user_id)
    is_retired = data.get(user_id_str, {}).get("is_retired", False)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Если админ — видит всё. Если не на пенсии — видит завершение.
    if user_id == ADMIN_ID or not is_retired:
        markup.add("Завершение карьеры")
    
    # Кнопка возвращения видна всегда, если человек на пенсии (или админу)
    if user_id == ADMIN_ID or is_retired:
        markup.add("Возвращение карьеры")
        
    markup.add("Свободный агент", "Переход в клуб")
    markup.add("Свой текст", "Профиль")
    markup.add("Изменить ник")
    return markup

def get_back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⬅️ Назад")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or "rb_nick" not in data[user_id]:
        msg = bot.send_message(message.chat.id, "👋 Привет! Введите ваш **Ник в РБ** для регистрации:")
        bot.register_next_step_handler(msg, register_user)
    else:
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu(message.from_user.id))

def register_user(message):
    rb_nick = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id] = {
        "rb_nick": rb_nick,
        "last_nick_change": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_retired": False
    }
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник **{rb_nick}** сохранен!", reply_markup=get_main_menu(message.from_user.id))

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

    if message.text == "Завершение карьеры":
        msg = bot.send_message(message.chat.id, "🚫 Напишите П.С. для завершения карьеры:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, process_retirement, user_info)

    elif message.text == "Возвращение карьеры":
        # Проверка таймера для обычных игроков
        if message.from_user.id != ADMIN_ID:
            last_retire_str = data[user_id].get("retire_date")
            if last_retire_str:
                last_retire = datetime.datetime.strptime(last_retire_str, "%Y-%m-%d %H:%M:%S")
                days_passed = (datetime.datetime.now() - last_retire).days
                if days_passed < RETIRE_LIMIT_DAYS:
                    bot.send_message(message.chat.id, f"❌ Вернуться можно только через 5 дней!\nОсталось ждать: **{RETIRE_LIMIT_DAYS - days_passed} дн.**")
                    return

        msg = bot.send_message(message.chat.id, "🔙 Напишите П.С. для возвращения:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, process_return, user_info)

    elif message.text == "Изменить ник":
        if message.from_user.id == ADMIN_ID:
            msg = bot.send_message(message.chat.id, "👑 Без очереди: вводи новый ник:", reply_markup=get_back_menu())
            bot.register_next_step_handler(msg, process_nick_change)
            return
        # Обычная проверка ника...
        last_change_str = data[user_id].get("last_nick_change")
        if last_change_str:
            last_change = datetime.datetime.strptime(last_change_str, "%Y-%m-%d %H:%M:%S")
            if (datetime.datetime.now() - last_change).days < NICK_LIMIT_DAYS:
                bot.send_message(message.chat.id, "❌ Рано менять ник!")
                return
        msg = bot.send_message(message.chat.id, "Вводи новый ник:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, process_nick_change)

    elif message.text == "Свободный агент":
        msg = bot.send_message(message.chat.id, "🆓 Напишите П.С.:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, send_to_channel, "Свободный агент", user_info)

    elif message.text == "Свой текст":
        msg = bot.send_message(message.chat.id, "📝 Введите текст:", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, send_to_channel, "Свой текст", user_info)

    elif message.text == "Переход в клуб":
        msg = bot.send_message(message.chat.id, "🏠 Введите: `Клуб, П.С.`", reply_markup=get_back_menu())
        bot.register_next_step_handler(msg, process_club, user_info)

    elif message.text == "Профиль":
        status = "На пенсии ❌" if data[user_id].get("is_retired") else "Активен ✅"
        bot.send_message(message.chat.id, f"👤 **Профиль**\n\n🎮 Ник: `{rb_nick}`\n📊 Статус: {status}")

# --- СПЕЦИАЛЬНАЯ ЛОГИКА ---

def process_retirement(message, user_info):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    user_id = str(message.from_user.id)
    data[user_id]["is_retired"] = True
    data[user_id]["retire_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    
    report = f"📢 **ЗАВЕРШЕНИЕ КАРЬЕРЫ**\n\n{user_info}\n🖋 П.С.: {message.text}"
    bot.send_message(CHANNEL_ID, report, parse_mode='Markdown')
    bot.send_message(message.chat.id, "✅ Карьера завершена. Кнопка скрыта на 5 дней.", reply_markup=get_main_menu(message.from_user.id))

def process_return(message, user_info):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    user_id = str(message.from_user.id)
    data[user_id]["is_retired"] = False
    save_data(data)
    
    report = f"📢 **ВОЗВРАЩЕНИЕ В КАРЬЕРУ**\n\n{user_info}\n🖋 П.С.: {message.text}"
    bot.send_message(CHANNEL_ID, report, parse_mode='Markdown')
    bot.send_message(message.chat.id, "✅ С возвращением! Кнопка 'Завершение' снова доступна.", reply_markup=get_main_menu(message.from_user.id))

def process_nick_change(message):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message.from_user.id))
        return
    new_nick = message.text.strip()
    data = load_data()
    user_id = str(message.from_user.id)
    data[user_id]["rb_nick"] = new_nick
    data[user_id]["last_nick_change"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник изменен на: **{new_nick}**", reply_markup=get_main_menu(message.from_user.id))

def send_to_channel(message, status, user_info):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message.from_user.id))
        return
    report = f"📢 **{status.upper()}**\n\n{user_info}\n🖋 П.С.: {message.text}"
    bot.send_message(CHANNEL_ID, report, parse_mode='Markdown')
    bot.send_message(message.chat.id, "✅ Опубликовано!", reply_markup=get_main_menu(message.from_user.id))

def process_club(message, user_info):
    if message.text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message.from_user.id))
        return
    try:
        parts = message.text.split(',')
        report = f"🏠 **ПЕРЕХОД В КЛУБ**\n\n{user_info}\n🏢 Клуб: {parts[0].strip()}\n📝 П.С.: {parts[1].strip()}"
        bot.send_message(CHANNEL_ID, report, parse_mode='Markdown')
        bot.send_message(message.chat.id, "✅ Опубликовано!", reply_markup=get_main_menu(message.from_user.id))
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка! Пиши через запятую.", reply_markup=get_main_menu(message.from_user.id))

if __name__ == "__main__":
    bot.infinity_polling()
