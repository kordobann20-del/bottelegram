import telebot
from telebot import types
import json
import os
import time

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv('TOKEN')
# ID канала для вывода постов
CHANNEL_ID = '-1003740141875' 
# КД на посты
COOLDOWN_SECONDS = 1800 

# Админы по юзернеймам (без @)
ADMIN_USERNAMES = ["nazikrrk", "miha10021"] 

# Старые владельцы (по ID для надежности)
OLD_OWNERS_IDS = {
    6641683745: "Arsenal",
    7908040352: "Inter Milan",
    8169093601: "Bayern Munich",
    8087187813: "Real Madrid",
    7138854880: "Albacete",
    8373009099: "Fiorentina",
    7718973542: "Fiorentina",
    6212776868: "Zenit",
    5739041429: "AC Milan",
    # @nikitos_201064
}
# =============================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

def load_data():
    """Загрузка базы данных."""
    if not os.path.exists(DATA_FILE): 
        return {"config": {"top_clubs_text": "Текст не настроен", "clubs_list_text": "Текст не настроен"}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = json.load(f)
            if "config" not in content:
                content["config"] = {
                    "top_clubs_text": "⭐ **ТОП КЛУБОВ**\n1. Real Madrid\n2. Arsenal\n3. Inter Milan",
                    "clubs_list_text": "🏆 **OFFICIAL TM CLUBS**\n🇵🇹 Sporting — @nikitos_201064\n🇮🇹 Inter Milan — @Banditdontrealme\n🇪🇸 Real Madrid — @Ez_Mbappe\n🇩🇪 Bayern Munich — @EstavaoJr\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 Arsenal — @IlikeMBB"
                }
            return content
    except: 
        return {"config": {"top_clubs_text": "Ошибка", "clubs_list_text": "Ошибка"}}

def save_data(data):
    """Сохранение базы данных."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def get_main_menu(message):
    """Генерация меню кнопок."""
    data = load_data()
    user_id = message.from_user.id
    user_id_str = str(user_id)
    user_info = data.get(user_id_str, {})
    username = (message.from_user.username or "").lower()
    
    if user_info.get("is_banned"):
        return types.ReplyKeyboardRemove()

    is_retired = user_info.get("is_retired", False)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if username in ADMIN_USERNAMES:
        markup.add("👑 Админ Панель")

    if is_retired:
        markup.add("Возвращение карьеры 🔙")
        markup.add("Список клубов 📋", "Топ клубов 🏆")
        markup.add("Профиль 👤")
    else:
        markup.add("Завершение карьеры 🚫")
        markup.add("Свободный агент 🆓", "Свой текст 📝")
        
        # Проверка прав на трансферы (старые влд, новые влд или админы)
        if user_id in OLD_OWNERS_IDS or user_info.get("owned_club") or username in ADMIN_USERNAMES:
            markup.add("Предложить трансфер 🤝")
            
        markup.add("Список клубов 📋", "Топ клубов 🏆")
        markup.add("Профиль 👤", "Изменить ник ✏️")
    
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚫 Забанить", "✅ Разбанить")
    markup.add("🔑 Дать влд", "🗑 Снять влд")
    markup.add("📝 Изменить список", "🔥 Изменить ТОП")
    markup.add("🔙 Назад в меню")
    return markup

def get_cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Отмена 🔙")
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    data = load_data()
    user_id = str(message.from_user.id)
    username = (message.from_user.username or "нет").lower()
    
    if user_id not in data:
        data[user_id] = {"is_retired": False, "is_banned": False, "owned_club": None, "rb_nick": None}
    
    data[user_id]["username"] = username
    save_data(data)

    if data[user_id].get("is_banned"):
        bot.send_message(message.chat.id, "❌ Вы заблокированы.")
        return

    if not data[user_id].get("rb_nick"):
        msg = bot.send_message(message.chat.id, "👋 Привет! Введите ваш Ник в Roblox для регистрации:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, register_user_step)
    else:
        bot.send_message(message.chat.id, "🔘 Главное меню", reply_markup=get_main_menu(message))

def register_user_step(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_main_menu(message))
        return
    data = load_data()
    data[str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник {message.text} сохранен!", reply_markup=get_main_menu(message))

@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    username = (message.from_user.username or "").lower()
    data = load_data()

    if user_id_str in data and data[user_id_str].get("is_banned"): return

    # Админ-панель
    if message.text == "👑 Админ Панель" and username in ADMIN_USERNAMES:
        bot.send_message(message.chat.id, "🛠 Админ-меню:", reply_markup=get_admin_menu())
        return

    if message.text == "🔙 Назад в меню":
        bot.send_message(message.chat.id, "🏠 Главное меню", reply_markup=get_main_menu(message))
        return

    # Функции админа
    if username in ADMIN_USERNAMES:
        if message.text == "🚫 Забанить":
            msg = bot.send_message(message.chat.id, "Введите @username игрока для бана:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_ban_step)
            return
        elif message.text == "🔑 Дать влд":
            msg = bot.send_message(message.chat.id, "Введите через пробел '@username Клуб':", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_give_club_step)
            return
        elif message.text == "📝 Изменить список":
            msg = bot.send_message(message.chat.id, "Введите новый текст списка клубов:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_set_clubs_text)
            return
        elif message.text == "🔥 Изменить ТОП":
            msg = bot.send_message(message.chat.id, "Введите новый текст ТОП-клубов:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_set_top_text)
            return

    # Логика обычного пользователя
    user_info = data.get(user_id_str, {})
    is_retired = user_info.get("is_retired", False)

    if message.text == "Список клубов 📋":
        bot.send_message(message.chat.id, data["config"]["clubs_list_text"])

    elif message.text == "Топ клубов 🏆":
        bot.send_message(message.chat.id, data["config"]["top_clubs_text"])

    elif message.text == "Профиль 👤":
        status_text = "На пенсии ❌" if is_retired else "Активен ✅"
        club_name = user_info.get("owned_club") or OLD_OWNERS_IDS.get(user_id) or "Нет клуба"
        bot.send_message(message.chat.id, f"👤 **ПРОФИЛЬ**\n\n🎮 Roblox: `{user_info.get('rb_nick')}`\n📊 Статус: {status_text}\n🏢 Владение: {club_name}")

    # Блокировка действий при пенсии
    if is_retired and message.text in ["Свободный агент 🆓", "Свой текст 📝", "Предложить трансфер 🤝"]:
        bot.send_message(message.chat.id, "❌ Функция заблокирована, пока вы на пенсии!")
        return

    # Предложение трансфера (поиск по юзернейму)
    if message.text == "Предложить трансфер 🤝":
        club = user_info.get("owned_club") or OLD_OWNERS_IDS.get(user_id)
        if not club and username not in ADMIN_USERNAMES: return
        msg = bot.send_message(message.chat.id, "🎯 Введите @username игрока, которому хотите предложить контракт:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_transfer_target, club if club else "Admin Control")

    elif message.text == "Завершение карьеры 🚫" and not is_retired:
        msg = bot.send_message(message.chat.id, "Напишите причину завершения карьеры:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_retirement_step)

    elif message.text == "Возвращение карьеры 🔙" and is_retired:
        data[user_id_str]["is_retired"] = False
        save_data(data)
        bot.send_message(message.chat.id, "✅ С возвращением в футбол!", reply_markup=get_main_menu(message))

    elif message.text == "Свой текст 📝" and not is_retired:
        msg = bot.send_message(message.chat.id, "Введите текст для канала:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, post_custom_text)

    elif message.text == "Свободный агент 🆓" and not is_retired:
        msg = bot.send_message(message.chat.id, "Введите П.С.:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, post_sa_status)

# --- ТРАНСФЕРНАЯ ЛОГИКА ---

def find_id_by_username(username_to_find):
    """Поиск ID пользователя по его юзернейму."""
    username_to_find = username_to_find.replace("@", "").lower().strip()
    data = load_data()
    for uid, info in data.items():
        if isinstance(info, dict) and info.get("username") == username_to_find:
            return uid
    return None

def process_transfer_target(message, club):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "Отмена.", reply_markup=get_main_menu(message))
        return
    
    target_id = find_id_by_username(message.text)
    if not target_id:
        bot.send_message(message.chat.id, "❌ Игрок с таким юзернеймом не найден в базе бота.")
        return
    
    owner_username = f"@{message.from_user.username}" if message.from_user.username else "Владелец"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"tr_acc_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ Отклонить", callback_data=f"tr_dec_{message.from_user.id}"))
    
    bot.send_message(target_id, f"⚽️ **НОВОЕ ПРЕДЛОЖЕНИЕ!**\n🏢 Клуб: **{club}**\n👤 Отправитель: {owner_username}\n\nВы принимаете предложение?", reply_markup=markup)
    bot.send_message(message.chat.id, f"🚀 Предложение успешно отправлено пользователю {message.text}!", reply_markup=get_main_menu(message))

@bot.callback_query_handler(func=lambda call: call.data.startswith("tr_"))
def callback_transfer(call):
    data = load_data()
    owner_id_int = int(call.data.split("_")[2])
    player_id_str = str(call.from_user.id)
    player_nick = data.get(player_id_str, {}).get("rb_nick", "Игрок")
    
    # Клуб владельца
    club = data.get(str(owner_id_int), {}).get("owned_club") or OLD_OWNERS_IDS.get(owner_id_int, "Клуб")
    
    if "acc" in call.data:
        bot.edit_message_text("✅ Вы приняли трансферное предложение!", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id_int, f"🔥 Игрок {player_nick} ПРИНЯЛ ваш контракт в {club}!")
        bot.send_message(CHANNEL_ID, f"🏠 **ТРАНСФЕР ПОДТВЕРЖДЕН**\n🎮 Ник: {player_nick}\n🏢 Новый клуб: {club}")
    else:
        bot.edit_message_text("❌ Вы отклонили предложение.", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id_int, f"❌ Игрок {player_nick} отклонил запрос в {club}.")

# --- ПОСТЫ И АДМИНКА ---

def post_custom_text(message):
    if message.text == "Отмена 🔙": return
    data = load_data()
    nick = data[str(message.from_user.id)].get("rb_nick", "Игрок")
    bot.send_message(CHANNEL_ID, f"📝 **СООБЩЕНИЕ**\n👤 {nick}\n💬 {message.text}")
    bot.send_message(message.chat.id, "✅ Отправлено!", reply_markup=get_main_menu(message))

def post_sa_status(message):
    if message.text == "Отмена 🔙": return
    data = load_data()
    nick = data[str(message.from_user.id)].get("rb_nick", "Игрок")
    bot.send_message(CHANNEL_ID, f"🆓 **СВОБОДНЫЙ АГЕНТ**\n👤 {nick}\n🖋 П.С.: {message.text}")
    bot.send_message(message.chat.id, "✅ Опубликовано!", reply_markup=get_main_menu(message))

def process_retirement_step(message):
    if message.text == "Отмена 🔙": return
    data = load_data()
    user_id_str = str(message.from_user.id)
    data[user_id_str]["is_retired"] = True
    save_data(data)
    nick = data[user_id_str].get("rb_nick", "Игрок")
    bot.send_message(CHANNEL_ID, f"🚫 **ЗАВЕРШЕНИЕ КАРЬЕРЫ**\n👤 {nick}\n🖋 Причина: {message.text}")
    bot.send_message(message.chat.id, "❌ Вы ушли на пенсию.", reply_markup=get_main_menu(message))

def admin_ban_step(message):
    target_id = find_id_by_username(message.text)
    if target_id:
        data = load_data()
        data[target_id]["is_banned"] = True
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Пользователь {message.text} забанен.")
    else: bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def admin_give_club_step(message):
    try:
        parts = message.text.split(" ", 1)
        target_id = find_id_by_username(parts[0])
        if target_id:
            data = load_data()
            data[target_id]["owned_club"] = parts[1]
            save_data(data)
            bot.send_message(message.chat.id, f"✅ Клуб {parts[1]} выдан пользователю {parts[0]}.")
        else: bot.send_message(message.chat.id, "❌ Пользователь не найден.")
    except: bot.send_message(message.chat.id, "❌ Неверный формат.")

def admin_set_clubs_text(message):
    if message.text == "Отмена 🔙": return
    data = load_data()
    data["config"]["clubs_list_text"] = message.text
    save_data(data)
    bot.send_message(message.chat.id, "✅ Список обновлен.", reply_markup=get_admin_menu())

def admin_set_top_text(message):
    if message.text == "Отмена 🔙": return
    data = load_data()
    data["config"]["top_clubs_text"] = message.text
    save_data(data)
    bot.send_message(message.chat.id, "✅ ТОП обновлен.", reply_markup=get_admin_menu())

if __name__ == "__main__":
    bot.infinity_polling()
