import telebot
from telebot import types
import json
import os
import time

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = '-1003740141875' 
COOLDOWN_SECONDS = 1800 

# Список админов по Username
ADMIN_USERNAMES = ["nazikrrk", "miha10021"] 
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

def get_main_menu(message):
    data = load_data()
    user_id_str = str(message.from_user.id)
    user_info = data.get(user_id_str, {})
    username = (message.from_user.username or "").lower()
    
    if user_info.get("is_banned"):
        return types.ReplyKeyboardRemove()

    is_retired = user_info.get("is_retired", False)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Проверка на админа по юзернейму
    if username in ADMIN_USERNAMES:
        markup.add("👑 Админ Панель")

    if not is_retired:
        markup.add("Завершение карьеры 🚫")
    else:
        markup.add("Возвращение карьеры 🔙")
        
    markup.add("Свободный агент 🆓", "Свой текст 📝")
    
    # Кнопка трансфера если есть клуб или админ
    if user_info.get("owned_club") or username in ADMIN_USERNAMES:
        markup.add("Предложить трансфер 🤝")
        
    markup.add("Список клубов 📋", "Профиль 👤")
    markup.add("Изменить ник ✏️")
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚫 Забанить", "✅ Разбанить")
    markup.add("🔑 Дать влд", "🗑 Снять влд")
    markup.add("🔙 Назад в меню")
    return markup

def get_cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Отмена 🔙")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.from_user.id)
    username = (message.from_user.username or "нет").lower()
    
    if user_id not in data:
        data[user_id] = {"is_retired": False, "is_banned": False, "owned_club": None}
    
    data[user_id]["username"] = username
    save_data(data)

    if data[user_id].get("is_banned"):
        bot.send_message(message.chat.id, "❌ Вы заблокированы в боте.")
        return

    if "rb_nick" not in data[user_id]:
        msg = bot.send_message(message.chat.id, "👋 Привет! Введите ваш Ник в Roblox для регистрации:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, register_user)
    else:
        bot.send_message(message.chat.id, "🔘 Главное меню", reply_markup=get_main_menu(message))

def register_user(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_main_menu(message))
        return
    data = load_data()
    data[str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник {message.text} сохранен!", reply_markup=get_main_menu(message))

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    username = (message.from_user.username or "").lower()
    data = load_data()

    if user_id_str in data and data[user_id_str].get("is_banned"):
        return

    # --- ПРОВЕРКА АДМИНКИ ---
    if message.text == "👑 Админ Панель" and username in ADMIN_USERNAMES:
        bot.send_message(message.chat.id, "🛠 Админ-панель управления:", reply_markup=get_admin_menu())
        return

    if message.text == "🔙 Назад в меню":
        bot.send_message(message.chat.id, "🏠 Возврат...", reply_markup=get_main_menu(message))
        return

    if username in ADMIN_USERNAMES:
        if message.text == "🚫 Забанить":
            msg = bot.send_message(message.chat.id, "Введите @username игрока для бана:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_ban_by_user)
            return
        elif message.text == "✅ Разбанить":
            msg = bot.send_message(message.chat.id, "Введите @username игрока для разбана:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_unban_by_user)
            return
        elif message.text == "🔑 Дать влд":
            msg = bot.send_message(message.chat.id, "Введите @username и Название клуба через пробел (напр: @Pasha Arsenal):", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_give_club_by_user)
            return
        elif message.text == "🗑 Снять влд":
            msg = bot.send_message(message.chat.id, "Введите @username игрока, чтобы забрать клуб:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_remove_club_by_user)
            return

    # --- ОБЫЧНЫЕ КНОПКИ ---
    user_info = data.get(user_id_str, {})
    rb_nick = user_info.get("rb_nick", "Без ника")
    tg_user = f"@{username}" if username else f"ID: {user_id}"

    if message.text == "Список клубов 📋":
        owners_text = ""
        for uid, info in data.items():
            if info.get("owned_club"):
                owners_text += f"🔹 {info['owned_club']} — @{info.get('username', '???')}\n"
        
        text = (
            "🏆 **OFFICIAL TM CLUBS**\n━━━━━━━━━━━━━━━━━━━━\n"
            "🇵🇹 Sporting — @nikitos_201064\n"
            "🇮🇹 Inter Milan — @Banditdontrealme\n"
            "🇪🇸 Real Madrid — @Ez_Mbappe\n"
            "🇩🇪 Bayern Munich — @EstavaoJr\n"
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Arsenal — @IlikeMBB\n\n"
            "🔥 **ALL ACTIVE OWNERS**\n━━━━━━━━━━━━━━━━━━━━\n"
            f"{owners_text if owners_text else 'Пока нет владельцев'}"
        )
        bot.send_message(message.chat.id, text)

    elif message.text == "Предложить трансфер 🤝":
        club = user_info.get("owned_club")
        if not club and username not in ADMIN_USERNAMES: return
        msg = bot.send_message(message.chat.id, "🎯 Введите @username игрока:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_transfer_target, club if club else "Admin Control")

    elif message.text == "Профиль 👤":
        club = user_info.get("owned_club", "Нет")
        status = "На пенсии ❌" if user_info.get("is_retired") else "Активен ✅"
        bot.send_message(message.chat.id, f"👤 **Профиль**\n\n🎮 Ник: `{rb_nick}`\n📊 Статус: {status}\n🏢 Клуб: {club}")

# --- ФУНКЦИИ АДМИНКИ ПО USERNAME ---

def find_id_by_username(username_to_find):
    username_to_find = username_to_find.replace("@", "").lower().strip()
    data = load_data()
    for uid, info in data.items():
        if info.get("username") == username_to_find:
            return uid
    return None

def admin_ban_by_user(message):
    if message.text == "Отмена 🔙": return
    target_id = find_id_by_username(message.text)
    if target_id:
        data = load_data()
        data[target_id]["is_banned"] = True
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Пользователь {message.text} забанен.")
    else: bot.send_message(message.chat.id, "❌ Игрок не найден в базе (он должен нажать /start).")

def admin_unban_by_user(message):
    if message.text == "Отмена 🔙": return
    target_id = find_id_by_username(message.text)
    if target_id:
        data = load_data()
        data[target_id]["is_banned"] = False
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Пользователь {message.text} разбанен.")
    else: bot.send_message(message.chat.id, "❌ Игрок не найден.")

def admin_give_club_by_user(message):
    if message.text == "Отмена 🔙": return
    try:
        parts = message.text.split(" ", 1)
        user_tag, club_name = parts[0], parts[1]
        target_id = find_id_by_username(user_tag)
        if target_id:
            data = load_data()
            data[target_id]["owned_club"] = club_name
            save_data(data)
            bot.send_message(message.chat.id, f"✅ Клуб {club_name} выдан {user_tag}!")
        else: bot.send_message(message.chat.id, "❌ Игрок не найден.")
    except: bot.send_message(message.chat.id, "❌ Формат: @username Название")

def admin_remove_club_by_user(message):
    if message.text == "Отмена 🔙": return
    target_id = find_id_by_username(message.text)
    if target_id:
        data = load_data()
        data[target_id]["owned_club"] = None
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Владение клубом у {message.text} снято.")
    else: bot.send_message(message.chat.id, "❌ Игрок не найден.")

# --- ЛОГИКА ТРАНСФЕРОВ ---

def process_transfer_target(message, club):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🔙 Отмена.", reply_markup=get_main_menu(message))
        return
    target_id = find_id_by_username(message.text)
    if not target_id:
        bot.send_message(message.chat.id, "❌ Игрок не найден.")
        return
    
    owner_tg = f"@{message.from_user.username}" if message.from_user.username else "Владелец"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"tr_acc_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ Отклонить", callback_data=f"tr_dec_{message.from_user.id}"))
    bot.send_message(target_id, f"⚽️ **ЗАПРОС!**\n🏢 Клуб: **{club}**\n👤 От: {owner_tg}", reply_markup=markup)
    bot.send_message(message.chat.id, "🚀 Запрос отправлен!", reply_markup=get_main_menu(message))

@bot.callback_query_handler(func=lambda call: call.data.startswith("tr_"))
def callback_transfer(call):
    data = load_data()
    owner_id = str(call.data.split("_")[2])
    p_nick = data.get(str(call.from_user.id), {}).get("rb_nick", "Игрок")
    club = data.get(owner_id, {}).get("owned_club", "Клуб")
    
    if "acc" in call.data:
        bot.edit_message_text("✅ Вы приняли трансфер!", call.message.chat.id, call.message.message_id)
        bot.send_message(int(owner_id), f"🔥 {p_nick} ПРИНЯЛ запрос в {club}!")
        bot.send_message(CHANNEL_ID, f"🏠 **ОФИЦИАЛЬНЫЙ ПЕРЕХОД**\n🎮 Ник: {p_nick}\n🏢 Клуб: {club}")
    else:
        bot.edit_message_text("❌ Вы отклонили предложение.", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
