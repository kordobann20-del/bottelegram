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

# Власники клубів (ID: Назва клубу)
CLUB_OWNERS = {
    7932332909: "Arsenal",
    7908040352: "Inter Milan",
    8169093601: "Bayern Munich",
    7138854880: "Albacete",
    7710520171: "Qarabağ",
    8087187813: "Real Madrid" # Замінено ФК Террор на Real Madrid
}
# =============================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
    data = load_data()
    user_id = str(message.from_user.id)
    username = message.from_user.username.lower() if message.from_user.username else "немає_юзернейма"
    
    if user_id not in data:
        data[user_id] = {"is_retired": False}
    
    data[user_id]["username"] = username
    save_data(data)

    if "rb_nick" not in data[user_id]:
        msg = bot.send_message(message.chat.id, "👋 **Привіт!** Введіть ваш **Нік у Roblox** для реєстрації:")
        bot.register_next_step_handler(msg, register_user)
    else:
        bot.send_message(message.chat.id, f"🔘 **Головне меню**\nВаш нік: {data[user_id]['rb_nick']}", reply_markup=get_main_menu(message.from_user.id))

def register_user(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "❌ Реєстрацію скасовано.", reply_markup=get_main_menu(message.from_user.id))
        return
    rb_nick = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id]["rb_nick"] = rb_nick
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Нік **{rb_nick}** збережено!", reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    data = load_data()

    if user_id_str not in data:
        start(message)
        return

    rb_nick = data[user_id_str].get("rb_nick", "Без ніка")
    tg_user = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"

    if message.text == "Список клубов 📋":
        text = (
            "🏆 **ОФИЦИАЛЬНЫЕ ТМ КЛУБЫ**\n━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇹 Inter Milan — @Banditdontrealme\n"
            "🇪🇸 Real Madrid — @Ez_Mbappe\n"
            "🇩🇪 Bayern Munich — @EstavaoJr\n"
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Arsenal — @Nagisls\n"
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Man City — ❓\n"
            "🇪🇸 Barcelona — ❓\n\n"
            "🔥 **КАСТОМНЫЕ ТМ КЛУБЫ**\n━━━━━━━━━━━━━━━━━━━━\n"
            "🇪🇸 Albacete — @Eoupapa\n"
            "🇦🇿 Qarabağ — @Suleyman1453638"
        )
        bot.send_message(message.chat.id, text)

    elif message.text == "Свой текст 📝":
        msg = bot.send_message(message.chat.id, "💬 Напишіть текст повідомлення:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, send_custom_text, rb_nick, tg_user)

    elif message.text == "Предложить трансфер 🤝":
        if user_id not in CLUB_OWNERS and user_id != ADMIN_ID: return
        msg = bot.send_message(message.chat.id, "🎯 Введіть @username гравця:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_transfer_target)

    elif message.text == "Завершение карьеры 🚫":
        msg = bot.send_message(message.chat.id, "🚫 Напишіть причину виходу на пенсію:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_retirement, rb_nick, tg_user)

    elif message.text == "Свободный агент 🆓":
        msg = bot.send_message(message.chat.id, "📝 Напишіть ваш П.С. до статусу:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, send_sa_status, rb_nick, tg_user)

    elif message.text == "Изменить ник ✏️":
        msg = bot.send_message(message.chat.id, "✏️ Введіть новий нік:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, update_nick)
        
    elif message.text == "Профиль 👤":
        status = "На пенсії ❌" if data[user_id_str].get("is_retired") else "Активний ✅"
        bot.send_message(message.chat.id, f"👤 **Профіль**\n\n🎮 Нік: `{rb_nick}`\n📊 Статус: {status}")

# --- ЛОГІКА З ПЕРЕВІРКОЮ НА ВІДМІНУ ---

def send_custom_text(message, nick, tg_user):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Повернення до меню", reply_markup=get_main_menu(message.from_user.id))
        return
    bot.send_message(CHANNEL_ID, f"📝 **ПОВІДОМЛЕННЯ**\n👤 {nick} ({tg_user})\n💬 {message.text}")
    bot.send_message(message.chat.id, "✅ Відправлено!", reply_markup=get_main_menu(message.from_user.id))

def send_sa_status(message, nick, tg_user):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Повернення до меню", reply_markup=get_main_menu(message.from_user.id))
        return
    bot.send_message(CHANNEL_ID, f"🆓 **СВОБОДНИЙ АГЕНТ**\n👤 {nick} ({tg_user})\n🖋 П.С.: {message.text}")
    bot.send_message(message.chat.id, "✅ Опубліковано!", reply_markup=get_main_menu(message.from_user.id))

def process_retirement(message, nick, tg_user):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Повернення до меню", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    data[str(message.from_user.id)]["is_retired"] = True
    data[str(message.from_user.id)]["retire_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(CHANNEL_ID, f"🚫 **ЗАВЕРШЕННЯ КАР'ЄРИ**\n👤 {nick} ({tg_user})\n🖋 Причина: {message.text}")
    bot.send_message(message.chat.id, "❌ Кар'єру завершено.", reply_markup=get_main_menu(message.from_user.id))

def process_transfer_target(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Повернення до меню", reply_markup=get_main_menu(message.from_user.id))
        return
    target_username = message.text.replace("@", "").lower().strip()
    data = load_data()
    target_id = next((uid for uid, udata in data.items() if udata.get("username") == target_username), None)
    if not target_id:
        bot.send_message(message.chat.id, "❌ Гравця не знайдено.", reply_markup=get_main_menu(message.from_user.id))
        return
    
    owner_tg = f"@{message.from_user.username}" if message.from_user.username else "Власник"
    club = CLUB_OWNERS.get(message.from_user.id, "Клуб")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Прийняти", callback_data=f"tr_acc_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ Відхилити", callback_data=f"tr_dec_{message.from_user.id}"))
    bot.send_message(target_id, f"⚽️ **НОВИЙ ЗАПРОС!**\n🏢 Клуб: **{club}**\n👤 Від: {owner_tg}", reply_markup=markup)
    bot.send_message(message.chat.id, "🚀 Запит відправлено!", reply_markup=get_main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("tr_"))
def callback_transfer(call):
    data = load_data()
    owner_id = int(call.data.split("_")[2])
    p_nick = data.get(str(call.from_user.id), {}).get("rb_nick", "Гравець")
    p_tg = f"@{call.from_user.username}" if call.from_user.username else "Приховано"
    club = CLUB_OWNERS.get(owner_id, "Клуб")
    if "acc" in call.data:
        bot.edit_message_text("✅ Ви прийняли трансфер!", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"🔥 {p_nick} ({p_tg}) ПРИЙНЯВ запит у {club}!")
        bot.send_message(CHANNEL_ID, f"🏠 **ОФІЦІЙНИЙ ПЕРЕХІД**\n🎮 Нік: {p_nick}\n👤 ТГ: {p_tg}\n🏢 Клуб: {club}")
    else:
        bot.edit_message_text("❌ Ви відхилили пропозицію.", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"😔 {p_nick} відмовився від запиту в {club}.")

def update_nick(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Повернення до меню", reply_markup=get_main_menu(message.from_user.id))
        return
    data = load_data()
    data[str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_data(data)
    bot.send_message(message.chat.id, "✅ Нік успішно оновлено!", reply_markup=get_main_menu(message.from_user.id))

if __name__ == "__main__":
    bot.infinity_polling()
