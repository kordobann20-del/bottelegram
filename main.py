import telebot
from telebot import types
import json
import os
import logging

# =================================================================
# НАСТРОЙКИ И КОНФИГУРАЦИЯ
# =================================================================

# Токен твоего бота (берется из переменных окружения или вставляется строкой)
TOKEN = os.getenv('TOKEN')

# ID канала, куда будут улетать все публикации (трансферы, агентства и т.д.)
CHANNEL_ID = '-1003740141875' 

# Список главных администраторов по юзернеймам (без символа @)
ADMIN_USERNAMES = ["nazikrrk", "miha10021"] 

# ПОЛНЫЙ И ПРОВЕРЕННЫЙ СПИСОК ВЛАДЕЛЬЦЕВ КЛУБОВ (СТРОГО ПО ЮЗЕРНЕЙМАМ)
# Бот будет автоматически давать им права на трансферы при совпадении юза
CLUB_OWNERS_LIST = {
    "banditdontrealme": "Inter Milan 🇮🇹",
    "ez_mbappe": "Real Madrid 🇪🇸",
    "estavaojr": "Bayern Munich 🇩🇪",
    "amojvucu": "Napoli 🇮🇹",
    "nikitos_201064": "Sporting 🇵🇹",
    "ilikembb": "Arsenal 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "pheluix23": "Empoli 🇮🇹",
    "eoupapa": "Albacete 🇪🇸",
    "nurikbro20145": "Zenit 🇷🇺",
    "mbappe_677": "Fiorentina 🇮🇹",
    "o17_misty": "Ac Milan 🇮🇹",
    "suleyman1453638": "Juventus 🇮🇹"
}

# Настройка логирования для отслеживания ошибок в консоли
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Имя файла базы данных
DATA_FILE = "users_database_v3.json"

# =================================================================
# РАБОТА С ДАННЫМИ (JSON)
# =================================================================

def load_all_data():
    """
    Загружает всю базу данных из JSON файла. 
    Если файла нет — создает структуру по умолчанию.
    """
    if not os.path.exists(DATA_FILE):
        default_structure = {
            "users": {},
            "config": {
                "top_clubs_text": "⭐ **ТОП КЛУБОВ ТМ**\n1. Real Madrid\n2. Inter Milan\n3. Bayern Munich",
                "clubs_list_text": "🏆 **СПИСОК ОФИЦИАЛЬНЫХ КЛУБОВ**\n(Отредактируйте через админ-панель)"
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_structure, f, ensure_ascii=False, indent=4)
        return default_structure

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при чтении базы данных: {e}")
        return {"users": {}, "config": {}}

def save_all_data(data):
    """
    Сохраняет текущее состояние данных в JSON файл.
    """
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Ошибка при сохранении базы данных: {e}")

# =================================================================
# КЛАВИАТУРЫ И ИНТЕРФЕЙС
# =================================================================

def get_main_keyboard(user_id, username):
    """
    Генерирует главное меню. Учитывает:
    - Статус админа
    - Статус владельца клуба
    - Статус 'На пенсии'
    - Статус бана
    """
    data = load_all_data()
    user_id_str = str(user_id)
    user_info = data["users"].get(user_id_str, {})
    username_low = (username or "").lower()

    # Проверка бана (Админы всегда имеют доступ)
    if user_info.get("is_banned", False) and username_low not in ADMIN_USERNAMES:
        return types.ReplyKeyboardRemove()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Кнопка админ-панели (только для списка админов)
    if username_low in ADMIN_USERNAMES:
        markup.add(types.KeyboardButton("👑 Админ Панель"))

    # Если игрок завершил карьеру
    if user_info.get("is_retired", False):
        markup.add(types.KeyboardButton("Возвращение карьеры 🔙"))
        markup.add(types.KeyboardButton("Список клубов 📋"), types.KeyboardButton("Топ клубов 🏆"))
        markup.add(types.KeyboardButton("Профиль 👤"))
        return markup

    # Стандартные игровые кнопки
    markup.add(types.KeyboardButton("Свободный агент 🆓"), types.KeyboardButton("Свой текст 📝"))
    
    # Проверка прав на трансферы (В списке CLUB_OWNERS или выдано админом в базе)
    is_owner = (username_low in CLUB_OWNERS_LIST or 
                user_info.get("owned_club") is not None or 
                username_low in ADMIN_USERNAMES)
    
    if is_owner:
        markup.add(types.KeyboardButton("Предложить трансфер 🤝"))

    markup.add(types.KeyboardButton("Список клубов 📋"), types.KeyboardButton("Топ клубов 🏆"))
    markup.add(types.KeyboardButton("Профиль 👤"), types.KeyboardButton("Изменить ник ✏️"))
    markup.add(types.KeyboardButton("Завершение карьеры 🚫"))

    return markup

def get_admin_keyboard():
    """Клавиатура управления для админов."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🚫 Забанить"), types.KeyboardButton("✅ Разбанить"))
    markup.add(types.KeyboardButton("🔑 Дать влд"), types.KeyboardButton("🗑 Снять влд"))
    markup.add(types.KeyboardButton("📝 Изменить список"), types.KeyboardButton("🔥 Изменить ТОП"))
    markup.add(types.KeyboardButton("🔙 Назад в меню"))
    return markup

def get_cancel_keyboard():
    """Клавиатура с одной кнопкой отмены."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Отмена 🔙"))
    return markup

# =================================================================
# ОБРАБОТЧИКИ КОМАНД И ОСНОВНОЙ ТЕКСТ
# =================================================================

@bot.message_handler(commands=['start'])
def welcome_start(message):
    """
    Стартовая команда. Регистрирует пользователя в базе.
    """
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    data = load_all_data()
    user_id_str = str(message.from_user.id)
    username = (message.from_user.username or "нет").lower()

    # Инициализация нового пользователя
    if user_id_str not in data["users"]:
        data["users"][user_id_str] = {
            "username": username,
            "rb_nick": None,
            "is_retired": False,
            "is_banned": False,
            "owned_club": None
        }
    else:
        # Обновляем юзернейм, если он сменился
        data["users"][user_id_str]["username"] = username
    
    save_all_data(data)

    # Проверка бана
    if data["users"][user_id_str].get("is_banned") and username not in ADMIN_USERNAMES:
        bot.send_message(message.chat.id, "🚫 Доступ к боту заблокирован администрацией.")
        return

    # Если не введен ник Roblox — просим ввести
    if not data["users"][user_id_str].get("rb_nick"):
        msg = bot.send_message(
            message.chat.id, 
            "👋 Добро пожаловать! Для использования системы введите ваш **Ник в Roblox**:", 
            parse_mode="Markdown", 
            reply_markup=get_cancel_keyboard()
        )
        bot.register_next_step_handler(msg, step_register_nickname)
    else:
        bot.send_message(
            message.chat.id, 
            "🔘 Главное меню открыто. Выберите нужное действие:", 
            reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username)
        )

def step_register_nickname(message):
    """Регистрация первого ника."""
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Действие отменено.", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
        return
    
    if not message.text or len(message.text) < 2:
        msg = bot.send_message(message.chat.id, "⚠️ Ник слишком короткий. Введите корректный ник Roblox:")
        bot.register_next_step_handler(msg, step_register_nickname)
        return

    data = load_all_data()
    data["users"][str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_all_data(data)

    bot.send_message(
        message.chat.id, 
        f"✅ Ник **{message.text}** успешно привязан!", 
        parse_mode="Markdown", 
        reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username)
    )

# =================================================================
# ГЛАВНЫЙ ЦИКЛ ОБРАБОТКИ СООБЩЕНИЙ (КНОПКИ)
# =================================================================

@bot.message_handler(content_types=['text'])
def main_button_handler(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    username = (message.from_user.username or "").lower()
    data = load_all_data()

    # Проверка на наличие пользователя в базе
    if user_id_str not in data["users"]:
        welcome_start(message)
        return

    user_info = data["users"][user_id_str]

    # Глобальная проверка бана
    if user_info.get("is_banned") and username not in ADMIN_USERNAMES:
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return

    # --- АДМИНИСТРАТИВНЫЙ БЛОК ---
    if message.text == "👑 Админ Панель" and username in ADMIN_USERNAMES:
        bot.send_message(message.chat.id, "⚙️ Панель управления администратора запущена:", reply_markup=get_admin_keyboard())
        return

    if message.text == "🔙 Назад в меню":
        bot.send_message(message.chat.id, "🏠 Возвращаюсь в главное меню...", reply_markup=get_main_keyboard(user_id, username))
        return

    if username in ADMIN_USERNAMES:
        if message.text == "🚫 Забанить":
            msg = bot.send_message(message.chat.id, "👤 Введите @username игрока для блокировки:", reply_markup=get_cancel_keyboard())
            bot.register_next_step_handler(msg, step_admin_ban)
            return
        elif message.text == "✅ Разбанить":
            msg = bot.send_message(message.chat.id, "👤 Введите @username игрока для разблокировки:", reply_markup=get_cancel_keyboard())
            bot.register_next_step_handler(msg, step_admin_unban)
            return
        elif message.text == "🔑 Дать влд":
            msg = bot.send_message(message.chat.id, "📝 Введите через пробел: `@username Клуб`", parse_mode="Markdown", reply_markup=get_cancel_keyboard())
            bot.register_next_step_handler(msg, step_admin_give_club)
            return
        elif message.text == "🗑 Снять влд":
            msg = bot.send_message(message.chat.id, "👤 Введите @username игрока, у которого нужно забрать клуб:", reply_markup=get_cancel_keyboard())
            bot.register_next_step_handler(msg, step_admin_remove_club)
            return
        elif message.text == "📝 Изменить список":
            msg = bot.send_message(message.chat.id, "📎 Отправьте новый текст для списка всех клубов:", reply_markup=get_cancel_keyboard())
            bot.register_next_step_handler(msg, step_admin_edit_clubs_list)
            return
        elif message.text == "🔥 Изменить ТОП":
            msg = bot.send_message(message.chat.id, "📎 Отправьте новый текст для ТОП-клубов:", reply_markup=get_cancel_keyboard())
            bot.register_next_step_handler(msg, step_admin_edit_top)
            return

    # --- ПОЛЬЗОВАТЕЛЬСКИЙ БЛОК ---
    
    # Кнопки, доступные ВСЕМ (даже на пенсии)
    if message.text == "Список клубов 📋":
        bot.send_message(message.chat.id, data["config"].get("clubs_list_text", "Пусто"))
        return

    elif message.text == "Топ клубов 🏆":
        bot.send_message(message.chat.id, data["config"].get("top_clubs_text", "Пусто"))
        return

    elif message.text == "Профиль 👤":
        status_label = "На пенсии ❌" if user_info.get("is_retired") else "Активен ✅"
        current_club = CLUB_OWNERS_LIST.get(username) or user_info.get("owned_club") or "Отсутствует"
        profile_text = (
            f"👤 **ВАШ ИГРОВОЙ ПРОФИЛЬ**\n\n"
            f"🎮 Roblox: `{user_info.get('rb_nick')}`\n"
            f"🆔 Telegram ID: `{user_id}`\n"
            f"📊 Статус: {status_label}\n"
            f"🏢 Владение клубом: **{current_club}**"
        )
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")
        return

    # Логика выхода с пенсии
    if user_info.get("is_retired") and message.text == "Возвращение карьеры 🔙":
        data["users"][user_id_str]["is_retired"] = False
        save_all_data(data)
        bot.send_message(message.chat.id, "✅ С возвращением в строй! Все функции снова доступны.", reply_markup=get_main_keyboard(user_id, username))
        return

    # Блокировка остальных кнопок, если пользователь на пенсии
    if user_info.get("is_retired"):
        bot.send_message(message.chat.id, "⚠️ Вы находитесь на пенсии. Для выполнения этого действия нужно вернуться в карьеру.")
        return

    # Кнопки активного игрока
    if message.text == "Изменить ник ✏️":
        msg = bot.send_message(message.chat.id, "✏️ Введите новый ник для Roblox:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, step_update_nickname)

    elif message.text == "Свой текст 📝":
        msg = bot.send_message(message.chat.id, "💬 Введите текст сообщения, который будет опубликован в канале:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, step_post_custom_text)

    elif message.text == "Свободный агент 🆓":
        msg = bot.send_message(message.chat.id, "📝 Опишите кратко ваши условия или П.С. для поиска клуба:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, step_post_free_agent)

    elif message.text == "Завершение карьеры 🚫":
        msg = bot.send_message(message.chat.id, "❓ Укажите причину завершения карьеры:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, step_post_retirement)

    elif message.text == "Предложить трансфер 🤝":
        # Проверка прав (Владелец или Админ)
        club_name = CLUB_OWNERS_LIST.get(username) or user_info.get("owned_club")
        if not club_name and username not in ADMIN_USERNAMES:
            bot.send_message(message.chat.id, "❌ У вас нет прав на предложение трансферов.")
            return
        
        msg = bot.send_message(message.chat.id, "🎯 Введите @username игрока, которому хотите предложить контракт:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, step_transfer_target, club_name if club_name else "Администрация")

# =================================================================
# ФУНКЦИИ ШАГОВ (NEXT STEP HANDLERS)
# =================================================================

def util_find_user_by_username(target_username):
    """Вспомогательная функция поиска ID по юзу."""
    target_username = target_username.replace("@", "").lower().strip()
    data = load_all_data()
    for uid, info in data["users"].items():
        if info.get("username") == target_username:
            return uid
    return None

# --- ПОЛЬЗОВАТЕЛЬСКИЕ ШАГИ ---

def step_update_nickname(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
        return
    
    data = load_all_data()
    data["users"][str(message.from_user.id)]["rb_nick"] = message.text.strip()
    save_all_data(data)
    bot.send_message(message.chat.id, "✅ Ник успешно обновлен!", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))

def step_post_custom_text(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
        return
    
    data = load_all_data()
    nick = data["users"][str(message.from_user.id)].get("rb_nick", "Игрок")
    user_tag = f"@{message.from_user.username}" if message.from_user.username else "нет юзернейма"
    
    try:
        post_text = f"📝 **НОВОЕ СООБЩЕНИЕ**\n👤 Отправитель: {nick} ({user_tag})\n\n💬 Текст: {message.text}"
        bot.send_message(CHANNEL_ID, post_text, parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ Ваше сообщение успешно опубликовано в канале!", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка публикации: {e}", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))

def step_post_free_agent(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
        return

    data = load_all_data()
    nick = data["users"][str(message.from_user.id)].get("rb_nick", "Игрок")
    user_tag = f"@{message.from_user.username}" if message.from_user.username else "нет юзернейма"

    try:
        post_text = (
            f"🆓 **СВОБОДНЫЙ АГЕНТ**\n\n"
            f"🎮 Roblox Ник: {nick}\n"
            f"👤 Telegram: {user_tag}\n"
            f"🖋 П.С.: {message.text}"
        )
        bot.send_message(CHANNEL_ID, post_text, parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ Ваша анкета опубликована!", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка публикации: {e}")

def step_post_retirement(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
        return

    data = load_all_data()
    user_id_str = str(message.from_user.id)
    data["users"][user_id_str]["is_retired"] = True
    save_all_data(data)

    nick = data["users"][user_id_str].get("rb_nick", "Игрок")
    user_tag = f"@{message.from_user.username}" if message.from_user.username else "нет юзернейма"

    try:
        post_text = (
            f"🚫 **ЗАВЕРШЕНИЕ КАРЬЕРЫ**\n\n"
            f"👤 Игрок: {nick} ({user_tag})\n"
            f"🖋 Причина: {message.text}"
        )
        bot.send_message(CHANNEL_ID, post_text, parse_mode="Markdown")
        bot.send_message(message.chat.id, "❌ Вы ушли на пенсию. Статус обновлен.", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Статус изменен локально, но произошла ошибка при публикации в канал.")

# --- ТРАНСФЕРНАЯ СИСТЕМА ---

def step_transfer_target(message, sender_club):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
        return
    
    target_id = util_find_user_by_username(message.text)
    if not target_id:
        bot.send_message(message.chat.id, "❌ Ошибка: пользователь не найден. Убедитесь, что он запустил бота и введите @username правильно.")
        return
    
    # Создаем инлайн-кнопки для выбора игрока
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("✅ Принять", callback_data=f"contract_accept_{message.from_user.id}")
    btn_no = types.InlineKeyboardButton("❌ Отклонить", callback_data=f"contract_decline_{message.from_user.id}")
    markup.add(btn_yes, btn_no)

    sender_tag = f"@{message.from_user.username}" if message.from_user.username else "Владелец"
    
    try:
        bot.send_message(
            target_id, 
            f"⚽️ **ВАМ ПРЕДЛОЖИЛИ КОНТРАКТ!**\n\n"
            f"🏢 Клуб: **{sender_club}**\n"
            f"👤 Отправитель: {sender_tag}\n\n"
            f"Вы принимаете предложение о переходе?", 
            parse_mode="Markdown", 
            reply_markup=markup
        )
        bot.send_message(message.chat.id, f"✅ Предложение успешно отправлено игроку {message.text}!", reply_markup=get_main_keyboard(message.from_user.id, message.from_user.username))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Не удалось отправить сообщение (возможно, бот заблокирован игроком): {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("contract_"))
def handle_contract_callback(call):
    """Обработка ответов на трансферы."""
    data = load_all_data()
    # Извлекаем ID того, кто отправил запрос
    sender_id_int = int(call.data.split("_")[2])
    player_id_str = str(call.from_user.id)
    player_nick = data["users"].get(player_id_str, {}).get("rb_nick", "Игрок")
    player_tag = f"@{call.from_user.username}" if call.from_user.username else "скрыт"

    # Определяем название клуба отправителя
    sender_username = (data["users"].get(str(sender_id_int), {}).get("username", "")).lower()
    club_title = CLUB_OWNERS_LIST.get(sender_username) or data["users"].get(str(sender_id_int), {}).get("owned_club", "Клуб")

    if "accept" in call.data:
        # Уведомляем игрока
        bot.edit_message_text("✅ Вы приняли предложение! Трансфер опубликован в канале.", call.message.chat.id, call.message.message_id)
        # Уведомляем владельца клуба
        bot.send_message(sender_id_int, f"🔥 ОТЛИЧНЫЕ НОВОСТИ! Игрок **{player_nick}** принял ваш контракт в **{club_title}**!", parse_mode="Markdown")
        # Публикуем в канал
        bot.send_message(CHANNEL_ID, f"🏠 **ОФИЦИАЛЬНЫЙ ТРАНСФЕР**\n\n🎮 Игрок: {player_nick} ({player_tag})\n🏢 Новый клуб: **{club_title}**\n✅ Сделка подтверждена!", parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Вы отклонили это предложение.", call.message.chat.id, call.message.message_id)
        bot.send_message(sender_id_int, f"❌ Игрок **{player_nick}** отклонил ваше предложение в **{club_title}**.", parse_mode="Markdown")

# --- АДМИНИСТРАТИВНЫЕ ШАГИ ---

def step_admin_ban(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_admin_keyboard())
        return
    
    target_id = util_find_user_by_username(message.text)
    if target_id:
        data = load_all_data()
        # Защита от бана админов
        if data["users"][target_id].get("username") in ADMIN_USERNAMES:
            bot.send_message(message.chat.id, "❌ Ошибка: нельзя забанить администратора системы!")
            return
        
        data["users"][target_id]["is_banned"] = True
        save_all_data(data)
        bot.send_message(message.chat.id, f"✅ Игрок {message.text} успешно заблокирован!", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: пользователь не найден в базе данных.")

def step_admin_unban(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_admin_keyboard())
        return
    
    target_id = util_find_user_by_username(message.text)
    if target_id:
        data = load_all_data()
        data["users"][target_id]["is_banned"] = False
        save_all_data(data)
        bot.send_message(message.chat.id, f"✅ Игрок {message.text} успешно разблокирован!", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def step_admin_give_club(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_admin_keyboard())
        return
    
    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            raise ValueError
        
        target_username = parts[0]
        club_name = parts[1]
        target_id = util_find_user_by_username(target_username)
        
        if target_id:
            data = load_all_data()
            data["users"][target_id]["owned_club"] = club_name
            save_all_data(data)
            bot.send_message(message.chat.id, f"✅ Игроку {target_username} выданы права владения клубом **{club_name}**!", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден.")
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка формата! Используйте: `@username Название`", parse_mode="Markdown")

def step_admin_remove_club(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_admin_keyboard())
        return
    
    target_id = util_find_user_by_username(message.text)
    if target_id:
        data = load_all_data()
        data["users"][target_id]["owned_club"] = None
        save_all_data(data)
        bot.send_message(message.chat.id, f"✅ У игрока {message.text} сняты права владения клубом.", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Не найден.")

def step_admin_edit_clubs_list(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_admin_keyboard())
        return
    
    data = load_all_data()
    data["config"]["clubs_list_text"] = message.text
    save_all_data(data)
    bot.send_message(message.chat.id, "✅ Список всех клубов успешно обновлен!", reply_markup=get_admin_keyboard())

def step_admin_edit_top(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=get_admin_keyboard())
        return
    
    data = load_all_data()
    data["config"]["top_clubs_text"] = message.text
    save_all_data(data)
    bot.send_message(message.chat.id, "✅ Текст ТОП-клубов обновлен!", reply_markup=get_admin_keyboard())

# =================================================================
# ЗАПУСК БОТА
# =================================================================

if __name__ == "__main__":
    print("-----------------------------------------")
    print("ТМ БОТ СИСТЕМА ЗАПУЩЕНА...")
    print("Администраторы:", ADMIN_USERNAMES)
    print("-----------------------------------------")
    bot.infinity_polling()
