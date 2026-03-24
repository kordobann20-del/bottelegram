import telebot
from telebot import types
import json
import os
import datetime
import time

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = '-1003740141875' 
COOLDOWN_SECONDS = 1800  # 30 минут
ADMIN_ID = 5845609895

# Актуальный список владельцев
CLUB_OWNERS = {
    6641683745: "Arsenal",
    7908040352: "Inter Milan",
    8169093601: "Bayern Munich",
    8087187813: "Real Madrid",
    8435557606: "Barcelona",
    5739041429: "Barcelona",
    7138854880: "Albacete",
    8373009099: "Фиорентина",
    6212776868: "Зенит"
}
# =============================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

def get_main_menu(user_id):
    data = load_data()
    user_id_str = str(user_id)
    is_retired = data.get(user_id_str, {}).get("is_retired", False)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if user_id == ADMIN_ID or not is_retired:
        markup.add("Завершение карьеры 🚫")
    if user_id == ADMIN_ID or is_retired:
        markup.add("Возвращение карьеры 🔙")
        
    markup.add("Свободный агент 🆓", "Свой текст 📝")
    
    if user_id in CLUB_OWNERS or user_id == ADMIN_ID:
        markup.add("Предложить трансфер 🤝")
        
    markup.add("Список клубов 📋", "Профиль 👤")
    markup.add("Изменить ник ✏️")
    return markup

def get_cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Отмена 🔙")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    data = load_data()
    user_id = str(message.from_user.id)
    
    if user_id not in data:
        data[user_id] = {"is_retired": False}
    data[user_id]["username"] = message.from_user.username.lower() if message.from_user.username else "нет"
    save_data(data)

    if "rb_nick" not in data[user_id]:
        msg = bot.send_message(message.chat.id, "👋 **Привет!** Введите ваш **Ник в Roblox** для регистрации:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, register_user)
    else:
        bot.send_message(message.chat.id, f"🔘 **Главное меню**\nВаш ник: {data[user_id]['rb_nick']}", reply_markup=get_main_menu(message.from_user.id))

def register_user(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "❌ Регистрация отменена.", reply_markup=get_main_menu(message.from_user.id))
        return
    rb_nick = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id]["rb_nick"] = rb_nick
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник **{rb_nick}** успешно сохранен!", reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    data = load_data()

    if user_id_str not in data:
        start(message)
        return

    rb_nick = data[user_id_str].get("rb_nick", "Без ника")
    tg_user = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
    last_post = data[user_id_str].get("last_post_time", 0)

    # --- КНОПКИ ---

    if message.text == "Список клубов 📋":
        text = (
            "🏆 **ОФИЦИАЛЬНЫЕ ТМ КЛУБЫ**\n━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇹 Inter Milan — @Banditdontrealme\n"
            "🇪🇸 Real Madrid — @Ez_Mbappe\n"
            "🇩🇪 Bayern Munich — @EstavaoJr\n"
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Arsenal — @IlikeMBB\n"
            "🇪🇸 Barcelona — @Romanzik_1717 / @o17_misty\n\n"
            "🔥 **КАСТОМНЫЕ ТМ КЛУБЫ**\n━━━━━━━━━━━━━━━━━━━━\n"
            "🇪🇸 Albacete — @Eoupapa\n"
            "🇮🇹 Фиорентина — @Maldini_756\n"
            "🇷🇺 Зенит — @NURIKBRO20145"
        )
        bot.send_message(message.chat.id, text)

    elif message.text == "Свой текст 📝":
        if time.time() - last_post < COOLDOWN_SECONDS and user_id != ADMIN_ID:
            rem = int((COOLDOWN_SECONDS - (time.time() - last_post)) / 60)
            bot.send_message(message.chat.id, f"⏳ КД! Подождите еще {rem} мин.")
            return
        msg = bot.send_message(message.chat.id, "💬 Напишите текст сообщения:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, send_custom_text, rb_nick, tg_user)

    elif message.text == "Свободный агент 🆓":
        if time.time() - last_post < COOLDOWN_SECONDS and user_id != ADMIN_ID:
            rem = int((COOLDOWN_SECONDS - (time.time() - last_post)) / 60)
            bot.send_message(message.chat.id, f"⏳ КД! Подождите еще {rem} мин.")
            return
        msg = bot.send_message(message.chat.id, "📝 Напишите ваш П.С. к статусу:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, send_sa_status, rb_nick, tg_user)

    elif message.text == "Предложить трансфер 🤝":
        if user_id not in CLUB_OWNERS and user_id != ADMIN_ID: return
        msg = bot.send_message(message.chat.id, "🎯 Введите @username игрока:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_transfer_target)

    elif message.text == "Завершение карьеры 🚫":
        msg = bot.send_message(message.chat.id, "🚫 Напишите причину завершения карьеры:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_retirement, rb_nick, tg_user)

    elif message.text == "Изменить ник ✏️":
        msg = bot.send_message(message.chat.id, "✏️ Введите новый ник:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, update_nick)
        
    elif message.text == "Профиль 👤":
        status = "На пенсии ❌" if data[user_id_str].get("is_retired") else "Активен ✅"
        bot.send_message(message.chat.id, f"👤 **Профиль**\n\n🎮 Ник: `{rb_nick}`\n📊 Статус: {status}")

# --- ЛОГИКА ОБРАБОТКИ ---

def send_custom_text(message, nick, tg_user):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Возврат в меню.", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    data[str(message.from_user.id)]["last_post_time"] = time.time()
    save_data(data)
    bot.send_message(CHANNEL_ID, f"📝 **СООБЩЕНИЕ**\n👤 {nick} ({tg_user})\n💬 {message.text}")
    bot.send_message(message.chat.id, "✅ Отправлено!", reply_markup=get_main_menu(message.from_user.id))

def send_sa_status(message, nick, tg_user):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Возврат в меню.", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    data[str(message.from_user.id)]["last_post_time"] = time.time()
    save_data(data)
    bot.send_message(CHANNEL_ID, f"🆓 **СВОБОДНЫЙ АГЕНТ**\n👤 {nick} ({tg_user})\n🖋 П.С.: {message.text}")
    bot.send_message(message.chat.id, "✅ Опубликовано!", reply_markup=get_main_menu(message.from_user.id))

def process_retirement(message, nick, tg_user):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Возврат в меню.", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    data[str(message.from_user.id)]["is_retired"] = True
    save_data(data)
    bot.send_message(CHANNEL_ID, f"🚫 **ЗАВЕРШЕНИЕ КАРЬЕРЫ**\n👤 {nick} ({tg_user})\n🖋 Причина: {message.text}")
    bot.send_message(message.chat.id, "❌ Карьера завершена.", reply_markup=get_main_menu(message.from_user.id))

def process_transfer_target(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Возврат в меню.", reply_markup=get_main_menu(message.from_user.id))
        return
    target_username = message.text.replace("@", "").lower().strip()
    data = load_data()
    target_id = next((uid for uid, udata in data.items() if udata.get("username") == target_username), None)
    if not target_id:
        bot.send_message(message.chat.id, "❌ Игрок не найден в базе.", reply_markup=get_main_menu(message.from_user.id))
        return
    
    owner_tg = f"@{message.from_user.username}" if message.from_user.username else "Владелец"
    club = CLUB_OWNERS.get(message.from_user.id, "Клуб")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"tr_acc_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ Отклонить", callback_data=f"tr_dec_{message.from_user.id}"))
    bot.send_message(target_id, f"⚽️ **НОВЫЙ ЗАПРОС!**\n🏢 Клуб: **{club}**\n👤 От: {owner_tg}", reply_markup=markup)
    bot.send_message(message.chat.id, "🚀 Запрос отправлен!", reply_markup=get_main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("tr_"))
def callback_transfer(call):
    data = load_data()
    owner_id = int(call.data.split("_")[2])
    p_nick = data.get(str(call.from_user.id), {}).get("rb_nick", "Игрок")
    p_tg = f"@{call.from_user.username}" if call.from_user.username else "Скрыто"
    club = CLUB_OWNERS.get(owner_id, "Клуб")
    if "acc" in call.data:
        bot.edit_message_text("✅ Вы приняли трансфер!", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"🔥 {p_nick} ({p_tg}) ПРИНЯЛ запрос в {club}!")
        bot.send_message(CHANNEL_ID, f"🏠 **ОФИЦИАЛЬНЫЙ ПЕРЕХОД**\n🎮 Ник: {p_nick}\n👤 ТГ: {p_tg}\n🏢 Клуб: {club}")
    else:
        bot.edit_message_text("❌ Вы отклонили предложение.", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"😔 {p_nick} отказался от запроса в {club}.")

def update_nick(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Возврат в меню.", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    data[str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_data(data)
    bot.send_message(message.chat.id, "✅ Ник успешно обновлен!", reply_markup=get_main_menu(message.from_user.id))

if __name__ == "__main__":
    bot.infinity_polling()
