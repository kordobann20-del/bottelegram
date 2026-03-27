import telebot
from telebot import types
import json
import os
import time

# ================= НАСТРОЙКИ =================
# Токен бота из BotFather
TOKEN = os.getenv('TOKEN')
# ID канала для публикаций
CHANNEL_ID = '-1003740141875' 
# КД на сообщения в секундах (30 минут)
COOLDOWN_SECONDS = 1800 

# Список администраторов по именам пользователей (без @, в нижнем регистре)
ADMIN_USERNAMES = ["nazikrrk", "miha10021"] 
# =============================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

def load_data():
    """Загрузка данных пользователей и системных настроек из JSON файла."""
    if not os.path.exists(DATA_FILE): 
        return {"config": {"top_clubs_text": "Текст не настроен", "clubs_list_text": "Текст не настроен"}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = json.load(f)
            # Если в файле нет секции конфига, создаем её с начальными данными
            if "config" not in content:
                content["config"] = {
                    "top_clubs_text": "⭐ **ТОП КЛУБОВ**\n1. Real Madrid\n2. Arsenal\n3. Inter Milan",
                    "clubs_list_text": "🏆 **OFFICIAL TM CLUBS**\n🇵🇹 Sporting — @nikitos_201064\n🇮🇹 Inter Milan — @Banditdontrealme\n🇪🇸 Real Madrid — @Ez_Mbappe\n🇩🇪 Bayern Munich — @EstavaoJr\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 Arsenal — @IlikeMBB"
                }
            return content
    except: 
        return {"config": {"top_clubs_text": "Ошибка загрузки", "clubs_list_text": "Ошибка загрузки"}}

def save_data(data):
    """Сохранение всех данных в JSON файл."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")

def get_main_menu(message):
    """Генерация адаптивного меню в зависимости от статуса игрока."""
    data = load_data()
    user_id_str = str(message.from_user.id)
    user_info = data.get(user_id_str, {})
    username = (message.from_user.username or "").lower()
    
    # Если пользователь забанен, убираем кнопки вообще
    if user_info.get("is_banned"):
        return types.ReplyKeyboardRemove()

    is_retired = user_info.get("is_retired", False)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Кнопка админ-панели для избранных юзеров
    if username in ADMIN_USERNAMES:
        markup.add("👑 Админ Панель")

    if is_retired:
        # Меню для тех, кто завершил карьеру (ограниченное)
        markup.add("Возвращение карьеры 🔙")
        markup.add("Список клубов 📋", "Топ клубов 🏆")
        markup.add("Профиль 👤")
    else:
        # Стандартное меню для активных игроков
        markup.add("Завершение карьеры 🚫")
        markup.add("Свободный агент 🆓", "Свой текст 📝")
        
        # Кнопка трансферов доступна владельцам или админам
        if user_info.get("owned_club") or username in ADMIN_USERNAMES:
            markup.add("Предложить трансфер 🤝")
            
        markup.add("Список клубов 📋", "Топ клубов 🏆")
        markup.add("Профиль 👤", "Изменить ник ✏️")
    
    return markup

def get_admin_menu():
    """Меню администратора."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚫 Забанить", "✅ Разбанить")
    markup.add("🔑 Дать влд", "🗑 Снять влд")
    markup.add("📝 Изменить список", "🔥 Изменить ТОП")
    markup.add("🔙 Назад в меню")
    return markup

def get_cancel_menu():
    """Меню отмены для пошаговых действий."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Отмена 🔙")
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработка команды старт и первичная регистрация."""
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    data = load_data()
    user_id = str(message.from_user.id)
    username = (message.from_user.username or "нет").lower()
    
    # Инициализация нового пользователя
    if user_id not in data:
        data[user_id] = {"is_retired": False, "is_banned": False, "owned_club": None, "rb_nick": None}
    
    # Обновляем юзернейм при каждом старте на случай смены
    data[user_id]["username"] = username
    save_data(data)

    if data[user_id].get("is_banned"):
        bot.send_message(message.chat.id, "❌ Вы заблокированы администрацией.")
        return

    # Если ник в роблокс еще не введен
    if not data[user_id].get("rb_nick"):
        msg = bot.send_message(message.chat.id, "👋 Привет! Пожалуйста, введите ваш Ник в Roblox для регистрации:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, register_user_step)
    else:
        bot.send_message(message.chat.id, "🔘 Главное меню", reply_markup=get_main_menu(message))

def register_user_step(message):
    """Сохранение ника игрока."""
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "❌ Регистрация не завершена.", reply_markup=get_main_menu(message))
        return
    data = load_data()
    data[str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник {message.text} успешно привязан!", reply_markup=get_main_menu(message))

@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    """Основной обработчик текстовых кнопок."""
    user_id = message.from_user.id
    user_id_str = str(user_id)
    username = (message.from_user.username or "").lower()
    data = load_data()

    # Проверка на бан
    if user_id_str in data and data[user_id_str].get("is_banned"):
        return

    # Обработка входа в админку
    if message.text == "👑 Админ Панель" and username in ADMIN_USERNAMES:
        bot.send_message(message.chat.id, "🛠 Режим администратора включен:", reply_markup=get_admin_menu())
        return

    if message.text == "🔙 Назад в меню":
        bot.send_message(message.chat.id, "🏠 Возврат в меню игрока...", reply_markup=get_main_menu(message))
        return

    # Логика функций администратора
    if username in ADMIN_USERNAMES:
        if message.text == "🚫 Забанить":
            msg = bot.send_message(message.chat.id, "Введите @username игрока для бана:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_ban_step)
            return
        elif message.text == "✅ Разбанить":
            msg = bot.send_message(message.chat.id, "Введите @username для разбана:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_unban_step)
            return
        elif message.text == "🔑 Дать влд":
            msg = bot.send_message(message.chat.id, "Введите через пробел '@username Название_Клуба':", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_give_club_step)
            return
        elif message.text == "🗑 Снять влд":
            msg = bot.send_message(message.chat.id, "Введите @username, чтобы забрать владение клубом:", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_remove_club_step)
            return
        elif message.text == "📝 Изменить список":
            msg = bot.send_message(message.chat.id, "Введите новый текст для кнопки 'Список клубов':", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_set_clubs_text)
            return
        elif message.text == "🔥 Изменить ТОП":
            msg = bot.send_message(message.chat.id, "Введите новый текст для кнопки 'Топ клубов':", reply_markup=get_cancel_menu())
            bot.register_next_step_handler(msg, admin_set_top_text)
            return

    # Логика кнопок игрока
    user_info = data.get(user_id_str, {})
    is_retired = user_info.get("is_retired", False)

    if message.text == "Список клубов 📋":
        bot.send_message(message.chat.id, data["config"]["clubs_list_text"])

    elif message.text == "Топ клубов 🏆":
        bot.send_message(message.chat.id, data["config"]["top_clubs_text"])

    elif message.text == "Профиль 👤":
        status_text = "На пенсии ❌" if is_retired else "Активен ✅"
        club_name = user_info.get("owned_club") or "Нет клуба"
        bot.send_message(message.chat.id, f"👤 **ВАШ ПРОФИЛЬ**\n\n🎮 Ник: `{user_info.get('rb_nick')}`\n📊 Статус: {status_text}\n🏢 Владение: {club_name}")

    # Блокировка действий для тех, кто на пенсии
    if is_retired and message.text in ["Свободный агент 🆓", "Свой текст 📝", "Предложить трансфер 🤝", "Изменить ник ✏️"]:
        bot.send_message(message.chat.id, "❌ Эта функция недоступна, пока вы не вернетесь в карьеру!")
        return

    if message.text == "Завершение карьеры 🚫" and not is_retired:
        msg = bot.send_message(message.chat.id, "📝 Напишите причину ухода из футбола:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, process_retirement_step)

    elif message.text == "Возвращение карьеры 🔙" and is_retired:
        data[user_id_str]["is_retired"] = False
        save_data(data)
        bot.send_message(message.chat.id, "✅ С возвращением в большой футбол! Все функции разблокированы.", reply_markup=get_main_menu(message))

    elif message.text == "Свой текст 📝" and not is_retired:
        msg = bot.send_message(message.chat.id, "💬 Введите текст для публикации в канал:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, post_custom_text)

    elif message.text == "Свободный агент 🆓" and not is_retired:
        msg = bot.send_message(message.chat.id, "📝 Напишите ваши условия или пожелания:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, post_sa_status)

    elif message.text == "Изменить ник ✏️" and not is_retired:
        msg = bot.send_message(message.chat.id, "✏️ Введите новый Ник в Roblox:", reply_markup=get_cancel_menu())
        bot.register_next_step_handler(msg, update_rb_nick)

# --- ФУНКЦИИ ПУБЛИКАЦИИ ---

def post_custom_text(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message))
        return
    data = load_data()
    user_id_str = str(message.from_user.id)
    nick = data[user_id_str].get("rb_nick", "Игрок")
    bot.send_message(CHANNEL_ID, f"📝 **СООБЩЕНИЕ**\n👤 {nick}\n💬 {message.text}")
    bot.send_message(message.chat.id, "✅ Ваше сообщение отправлено в канал!", reply_markup=get_main_menu(message))

def post_sa_status(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message))
        return
    data = load_data()
    user_id_str = str(message.from_user.id)
    nick = data[user_id_str].get("rb_nick", "Игрок")
    bot.send_message(CHANNEL_ID, f"🆓 **СВОБОДНЫЙ АГЕНТ**\n👤 {nick}\n🖋 П.С.: {message.text}")
    bot.send_message(message.chat.id, "✅ Статус свободного агента опубликован!", reply_markup=get_main_menu(message))

def process_retirement_step(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message))
        return
    data = load_data()
    user_id_str = str(message.from_user.id)
    data[user_id_str]["is_retired"] = True
    save_data(data)
    nick = data[user_id_str].get("rb_nick", "Игрок")
    bot.send_message(CHANNEL_ID, f"🚫 **ЗАВЕРШЕНИЕ КАРЬЕРЫ**\n👤 {nick}\n🖋 Причина: {message.text}")
    bot.send_message(message.chat.id, "❌ Вы завершили карьеру. Игровые функции заблокированы.", reply_markup=get_main_menu(message))

def update_rb_nick(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=get_main_menu(message))
        return
    data = load_data()
    data[str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_data(data)
    bot.send_message(message.chat.id, "✅ Ник обновлен!", reply_markup=get_main_menu(message))

# --- АДМИН-ФУНКЦИИ РЕДАКТИРОВАНИЯ ТЕКСТА ---

def admin_set_clubs_text(message):
    if message.text == "Отмена 🔙": return
    data = load_data()
    data["config"]["clubs_list_text"] = message.text
    save_data(data)
    bot.send_message(message.chat.id, "✅ Список клубов успешно изменен!", reply_markup=get_admin_menu())

def admin_set_top_text(message):
    if message.text == "Отмена 🔙": return
    data = load_data()
    data["config"]["top_clubs_text"] = message.text
    save_data(data)
    bot.send_message(message.chat.id, "✅ ТОП клубов успешно изменен!", reply_markup=get_admin_menu())

# --- УТИЛИТЫ ПОИСКА ПО USERNAME ---

def find_id_by_username(username_to_find):
    username_to_find = username_to_find.replace("@", "").lower().strip()
    data = load_data()
    for uid, info in data.items():
        if isinstance(info, dict) and info.get("username") == username_to_find:
            return uid
    return None

def admin_ban_step(message):
    target_id = find_id_by_username(message.text)
    if target_id:
        data = load_data()
        data[target_id]["is_banned"] = True
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Игрок {message.text} заблокирован.")
    else: bot.send_message(message.chat.id, "❌ Ошибка: Игрок не найден в базе.")

def admin_unban_step(message):
    target_id = find_id_by_username(message.text)
    if target_id:
        data = load_data()
        data[target_id]["is_banned"] = False
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Игрок {message.text} разблокирован.")
    else: bot.send_message(message.chat.id, "❌ Ошибка: Игрок не найден.")

def admin_give_club_step(message):
    try:
        parts = message.text.split(" ", 1)
        target_id = find_id_by_username(parts[0])
        if target_id:
            data = load_data()
            data[target_id]["owned_club"] = parts[1]
            save_data(data)
            bot.send_message(message.chat.id, f"✅ Игроку {parts[0]} выдан клуб: {parts[1]}")
        else: bot.send_message(message.chat.id, "❌ Ошибка: Игрок не найден.")
    except: bot.send_message(message.chat.id, "❌ Ошибка: Используйте формат '@username Название'")

def admin_remove_club_step(message):
    target_id = find_id_by_username(message.text)
    if target_id:
        data = load_data()
        data[target_id]["owned_club"] = None
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Владение клубом у {message.text} аннулировано.")
    else: bot.send_message(message.chat.id, "❌ Ошибка: Игрок не найден.")

if __name__ == "__main__":
    bot.infinity_polling()
