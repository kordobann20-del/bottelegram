import telebot
from telebot import types
import json
import os
import datetime
import time

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = '-1003740141875' 
NICK_LIMIT_DAYS = 7 
RETIRE_LIMIT_DAYS = 5
ADMIN_ID = 5845609895

# Владельцы клубов и их данные
CLUB_OWNERS = {
    7932332909: "Arsenal",
    7908040352: "Inter Milan",
    8169093601: "Bayern Munich",
    7138854880: "Albacete"
}
# =============================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_main_menu(user_id):
    data = load_data()
    user_id_str = str(user_id)
    is_retired = data.get(user_id_str, {}).get("is_retired", False)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Кнопки карьеры
    if user_id == ADMIN_ID or not is_retired:
        markup.add("Завершение карьеры")
    if user_id == ADMIN_ID or is_retired:
        markup.add("Возвращение карьеры")
        
    markup.add("Свободный агент") # Кнопка "Переход в клуб" УДАЛЕНА
    
    # Кнопка только для владельцев или админа
    if user_id in CLUB_OWNERS or user_id == ADMIN_ID:
        markup.add("Предложить трансфер 🤝")
        
    markup.add("Список клубов 📋", "Профиль")
    markup.add("Изменить ник")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.from_user.id)
    username = message.from_user.username.lower() if message.from_user.username else None
    
    if user_id not in data:
        data[user_id] = {"is_retired": False}
    
    if username:
        data[user_id]["username"] = username
    
    if "rb_nick" not in data[user_id]:
        save_data(data)
        msg = bot.send_message(message.chat.id, "👋 Привет! Введите ваш **Ник в РБ** для регистрации:")
        bot.register_next_step_handler(msg, register_user)
    else:
        save_data(data)
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu(message.from_user.id))

def register_user(message):
    rb_nick = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id]["rb_nick"] = rb_nick
    data[user_id]["last_nick_change"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник **{rb_nick}** сохранен!", reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    data = load_data()

    if user_id_str not in data:
        start(message)
        return

    # --- СПИСОК КЛУБОВ ---
    if message.text == "Список клубов 📋":
        text = (
            "❗️❕ОФИЦИАЛЬНЫЕ ТМ КЛУБЫ\n\n"
            "🇮🇹Inter Milan - @Banditdontrealme\n"
            "🇩🇪Bayern Munich - @EstavaoJr\n"
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿Arsenal - @Nagisls\n\n"
            "🔥КАСТОМНЫЕ ТМ КЛУБЫ\n"
            "🇪🇸Albacete - @Eoupapa"
        )
        bot.send_message(message.chat.id, text)

    # --- ЛОГИКА ТРАНСФЕРА ---
    elif message.text == "Предложить трансфер 🤝":
        if user_id not in CLUB_OWNERS and user_id != ADMIN_ID:
            return

        last_transfer = data[user_id_str].get("last_transfer_time", 0)
        if time.time() - last_transfer < 3600 and user_id != ADMIN_ID:
            remain = int((3600 - (time.time() - last_transfer)) / 60)
            bot.send_message(message.chat.id, f"❌ Подождите еще {remain} мин.")
            return

        msg = bot.send_message(message.chat.id, "Введите @username игрока:")
        bot.register_next_step_handler(msg, process_transfer_target)

    elif message.text == "Завершение карьеры":
        msg = bot.send_message(message.chat.id, "🚫 Напишите П.С. для завершения:")
        bot.register_next_step_handler(msg, process_retirement)

    elif message.text == "Возвращение карьеры":
        # Проверка 5 дней для обычных
        if user_id != ADMIN_ID:
            last_retire_str = data[user_id_str].get("retire_date")
            if last_retire_str:
                last_retire = datetime.datetime.strptime(last_retire_str, "%Y-%m-%d %H:%M:%S")
                days_passed = (datetime.datetime.now() - last_retire).days
                if days_passed < RETIRE_LIMIT_DAYS:
                    bot.send_message(message.chat.id, f"❌ Ждите еще {RETIRE_LIMIT_DAYS - days_passed} дн.")
                    return
        
        data[user_id_str]["is_retired"] = False
        save_data(data)
        bot.send_message(message.chat.id, "🔙 Вы вернулись в карьеру!", reply_markup=get_main_menu(user_id))

    elif message.text == "Свободный агент":
        msg = bot.send_message(message.chat.id, "🆓 Напишите П.С.:")
        bot.register_next_step_handler(msg, send_to_channel, "Свободный агент", data[user_id_str].get("rb_nick"))

    elif message.text == "Профиль":
        nick = data[user_id_str].get("rb_nick", "Не указан")
        bot.send_message(message.chat.id, f"👤 Профиль\nНик: {nick}\nID: {user_id}")

    elif message.text == "Изменить ник":
        if user_id == ADMIN_ID:
            msg = bot.send_message(message.chat.id, "Вводи новый ник:")
            bot.register_next_step_handler(msg, process_nick_change)
        else:
            # Обычная проверка ника (7 дней)
            last_change_str = data[user_id_str].get("last_nick_change")
            if last_change_str:
                last_change = datetime.datetime.strptime(last_change_str, "%Y-%m-%d %H:%M:%S")
                if (datetime.datetime.now() - last_change).days < NICK_LIMIT_DAYS:
                    bot.send_message(message.chat.id, "❌ Рано менять ник!")
                    return
            msg = bot.send_message(message.chat.id, "Вводи новый ник:")
            bot.register_next_step_handler(msg, process_nick_change)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def process_transfer_target(message):
    target_username = message.text.replace("@", "").lower().strip()
    data = load_data()
    target_id = None
    for uid, udata in data.items():
        if udata.get("username") == target_username:
            target_id = uid
            break
    if not target_id:
        bot.send_message(message.chat.id, "❌ Игрок не найден в базе бота.")
        return
    club_name = CLUB_OWNERS.get(message.from_user.id, "Сборная")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"tr_acc_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ Отклонить", callback_data=f"tr_dec_{message.from_user.id}"))
    bot.send_message(target_id, f"⚽️ Вам пришел запрос в клуб **{club_name}**!", reply_markup=markup, parse_mode="Markdown")
    data[str(message.from_user.id)]["last_transfer_time"] = time.time()
    save_data(data)
    bot.send_message(message.chat.id, "🚀 Запрос отправлен!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("tr_"))
def callback_transfer(call):
    data = load_data()
    owner_id = call.data.split("_")[2]
    player_nick = data.get(str(call.from_user.id), {}).get("rb_nick", "Игрок")
    club_name = CLUB_OWNERS.get(int(owner_id), "Клуб")
    if "acc" in call.data:
        bot.edit_message_text("✅ Принято!", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"🔥 {player_nick} ПРИНЯЛ переход в {club_name}!")
        bot.send_message(CHANNEL_ID, f"🏠 **ОФИЦИАЛЬНЫЙ ПЕРЕХОД**\n\n🎮 Игрок: {player_nick}\n🏢 Клуб: {club_name}")
    else:
        bot.edit_message_text("❌ Отклонено.", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"😔 {player_nick} ОТКАЗАЛСЯ от перехода.")

def process_retirement(message):
    data = load_data()
    user_id = str(message.from_user.id)
    data[user_id]["is_retired"] = True
    data[user_id]["retire_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(message.chat.id, "❌ Карьера завершена!", reply_markup=get_main_menu(message.from_user.id))

def process_nick_change(message):
    new_nick = message.text.strip()
    data = load_data()
    user_id = str(message.from_user.id)
    data[user_id]["rb_nick"] = new_nick
    data[user_id]["last_nick_change"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник изменен на: {new_nick}", reply_markup=get_main_menu(message.from_user.id))

def send_to_channel(message, status, nick):
    report = f"📢 **{status.upper()}**\n🎮 Ник: {nick}\n🖋 П.С.: {message.text}"
    bot.send_message(CHANNEL_ID, report)
    bot.send_message(message.chat.id, "✅ Опубликовано!", reply_markup=get_main_menu(message.from_user.id))

if __name__ == "__main__":
    bot.infinity_polling()
