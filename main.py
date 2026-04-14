import telebot
from telebot import types
import json
import os
import time
import logging
import re

# =================================================================
# КОНФИГУРАЦИЯ И НАСТРОЙКИ
# =================================================================

TOKEN = os.getenv('TOKEN') # Убедись, что токен вставлен правильно
CHANNEL_ID = '-1003740141875' 

# ГЛАВНЫЙ АДМИНИСТРАТОР
SUPER_ADMIN = "nazikrrk" 

# СПИСОК ВЛАДЕЛЬЦЕВ КЛУБОВ (КОНСТАНТА)
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

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "transfer_market_database.json"
logging.basicConfig(level=logging.INFO)

# =================================================================
# СИСТЕМА ХРАНЕНИЯ ДАННЫХ
# =================================================================

def load_all_data():
    """Загрузка всей базы данных из файла"""
    if not os.path.exists(DATA_FILE):
        default_data = {
            "users": {},
            "admins": [SUPER_ADMIN],
            "config": {
                "top_clubs_text": "⭐ **ТОП КЛУБОВ ТМ**\n\nМесто 1: Bayern Munich\nМесто 2: Real Madrid",
                "clubs_list_text": "🏆 **СПИСОК ОФИЦИАЛЬНЫХ КЛУБОВ**\n\n1. Inter Milan\n2. Real Madrid\n3. Bayern Munich"
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка чтения базы: {e}")
        return {"users": {}, "admins": [SUPER_ADMIN], "config": {}}

def save_all_data(data):
    """Сохранение всей базы данных в файл"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения базы: {e}")

# =================================================================
# СИСТЕМА КУЛДАУНОВ (ОГРАНИЧЕНИЕ ПО ВРЕМЕНИ)
# =================================================================

def check_action_cooldown(user_id, action_name, cooldown_seconds):
    """Проверяет, прошло ли нужное время с последнего действия"""
    data = load_all_data()
    uid = str(user_id)
    
    if uid not in data["users"]:
        return True, 0
    
    last_time = data["users"][uid].get("cooldown_timers", {}).get(action_name, 0)
    elapsed = time.time() - last_time
    
    if elapsed < cooldown_seconds:
        remaining = int(cooldown_seconds - elapsed)
        return False, remaining
    return True, 0

def register_action_time(user_id, action_name):
    """Записывает время совершения действия"""
    data = load_all_data()
    uid = str(user_id)
    
    if "cooldown_timers" not in data["users"][uid]:
        data["users"][uid]["cooldown_timers"] = {}
    
    data["users"][uid]["cooldown_timers"][action_name] = time.time()
    save_all_data(data)

# =================================================================
# КЛАВИАТУРЫ (ИНТЕРФЕЙС)
# =================================================================

def main_menu_keyboard(user_id, username):
    data = load_all_data()
    uid_str = str(user_id)
    u_info = data["users"].get(uid_str, {})
    uname_low = (username or "").lower()
    is_bot_admin = uname_low in data["admins"]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Кнопка админа (если есть права)
    if is_bot_admin:
        markup.add(types.KeyboardButton("👑 Админ Панель"))

    # Если игрок завершил карьеру
    if u_info.get("is_retired", False):
        markup.add(types.KeyboardButton("Возвращение карьеры 🔙"))
        markup.add(types.KeyboardButton("Написать админам 📩"))
        markup.add(types.KeyboardButton("Список клубов 📋"), types.KeyboardButton("Топ клубов 🏆"))
        markup.add(types.KeyboardButton("Профиль 👤"))
        return markup

    # Стандартные кнопки для активных игроков
    markup.add(types.KeyboardButton("Свободный агент 🆓"), types.KeyboardButton("Свой текст 📝"))
    
    # Проверка на владение клубом (для кнопки трансферов)
    is_club_boss = (uname_low in CLUB_OWNERS_LIST or u_info.get("owned_club") is not None or is_bot_admin)
    if is_club_boss:
        markup.add(types.KeyboardButton("Предложить трансфер 🤝"))

    markup.add(types.KeyboardButton("Список клубов 📋"), types.KeyboardButton("Топ клубов 🏆"))
    markup.add(types.KeyboardButton("Профиль 👤"), types.KeyboardButton("Изменить ник ✏️"))
    markup.add(types.KeyboardButton("Написать админам 📩"), types.KeyboardButton("Завершение карьеры 🚫"))
    
    return markup

def admin_panel_keyboard(username):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🚫 Забанить"), types.KeyboardButton("✅ Разбанить"))
    markup.add(types.KeyboardButton("🔑 Дать влд"), types.KeyboardButton("🗑 Снять влд"))
    
    # Только Супер Админ видит управление админ-составом
    if username.lower() == SUPER_ADMIN:
        markup.add(types.KeyboardButton("⭐ Дать админку"), types.KeyboardButton("❌ Снять админку"))
    
    markup.add(types.KeyboardButton("📝 Изменить список"), types.KeyboardButton("🔥 Изменить ТОП"))
    markup.add(types.KeyboardButton("🔙 Назад в меню"))
    return markup

def cancel_action_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Отмена 🔙"))
    return markup

# =================================================================
# ВСПОМОГАТЕЛЬНЫЕ ИНСТРУМЕНТЫ
# =================================================================

def get_user_id_by_tag(tag):
    """Поиск ID пользователя в базе по его @username"""
    tag = tag.replace("@", "").lower().strip()
    data = load_all_data()
    for uid, info in data["users"].items():
        if info.get("username") == tag:
            return uid
    return None

# =================================================================
# ЛОГИКА ШАГОВ (NEXT STEP HANDLERS)
# =================================================================

def process_nickname_registration(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "❌ Регистрация отменена. Используйте /start.", reply_markup=types.ReplyKeyboardRemove())
        return
    if not message.text or len(message.text) < 2:
        msg = bot.send_message(message.chat.id, "⚠️ Ник слишком короткий. Введите заново:")
        bot.register_next_step_handler(msg, process_nickname_registration)
        return
    
    data = load_all_data()
    uid = str(message.from_user.id)
    data["users"][uid]["rb_nick"] = message.text.strip()
    save_all_data(data)
    
    bot.send_message(message.chat.id, f"✅ Ваш ник {message.text} успешно привязан!", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))

def process_nickname_update(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))
        return
    
    # Кулдаун 7 дней (604800 секунд)
    can_act, wait_time = check_action_cooldown(message.from_user.id, "nickname_change", 604800)
    if not can_act:
        days_left = wait_time // 86400
        bot.send_message(message.chat.id, f"⚠️ Слишком часто! Изменить ник можно будет через {days_left} дн.")
        return

    data = load_all_data()
    uid = str(message.from_user.id)
    data["users"][uid]["rb_nick"] = message.text.strip()
    save_all_data(data)
    register_action_time(message.from_user.id, "nickname_change")
    
    bot.send_message(message.chat.id, "✅ Ник успешно обновлен!", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))

def process_message_to_support(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))
        return
    
    # Кулдаун 20 минут (1200 секунд)
    can_act, wait_time = check_action_cooldown(message.from_user.id, "support_ticket", 1200)
    if not can_act:
        bot.send_message(message.chat.id, f"⚠️ Вы уже писали админам. Подождите {wait_time // 60} мин.")
        return

    data = load_all_data()
    sender_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID {message.from_user.id}"
    
    admin_alert = f"📩 **НОВОЕ ОБРАЩЕНИЕ**\n👤 Отправитель: {sender_tag}\n💬 Сообщение: {message.text}"
    
    # Отправка всем админам из списка
    count = 0
    for admin_username in data["admins"]:
        target_admin_id = get_user_id_by_tag(admin_username)
        if target_admin_id:
            try:
                bot.send_message(target_admin_id, admin_alert, parse_mode="Markdown")
                count += 1
            except: pass
    
    if count > 0:
        register_action_time(message.from_user.id, "support_ticket")
        bot.send_message(message.chat.id, "✅ Ваше сообщение передано администрации!", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: в данный момент админы недоступны.")

def process_channel_custom_post(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))
        return
    
    # Кулдаун 12 часов (43200 секунд)
    can_act, wait_time = check_action_cooldown(message.from_user.id, "channel_post", 43200)
    if not can_act:
        bot.send_message(message.chat.id, f"⚠️ Лимит! Вы сможете отправить текст через {wait_time // 3600} ч.")
        return

    data = load_all_data()
    uid = str(message.from_user.id)
    nick = data["users"][uid].get("rb_nick", "Игрок")
    tag = f"@{message.from_user.username}" if message.from_user.username else "Юзернейм скрыт"
    
    try:
        # Отправляем БЕЗ Markdown во избежание ошибки 400
        final_text = f"📝 НОВОЕ СООБЩЕНИЕ\n👤 Игрок: {nick} ({tag})\n\n💬 Текст:\n{message.text}"
        bot.send_message(CHANNEL_ID, final_text)
        register_action_time(message.from_user.id, "channel_post")
        bot.send_message(message.chat.id, "✅ Ваш пост успешно опубликован!", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка публикации: Бот не админ или канал недоступен.")

def process_transfer_offer(message, sender_club_name):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))
        return
    
    # Кулдаун 3 минуты (180 секунд)
    can_act, wait_time = check_action_cooldown(message.from_user.id, "transfer_offer", 180)
    if not can_act:
        bot.send_message(message.chat.id, f"⚠️ Подождите {wait_time} сек. перед следующим предложением.")
        return

    target_uid = get_user_id_by_tag(message.text)
    if not target_uid:
        bot.send_message(message.chat.id, "❌ Этот игрок не найден. Он должен зайти в бота хотя бы раз.")
        return

    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"contract_ok_{message.from_user.id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"contract_no_{message.from_user.id}")
    )
    
    try:
        bot.send_message(target_uid, f"⚽️ **ВАМ ПРЕДЛОЖИЛИ КОНТРАКТ!**\n🏢 Клуб: {sender_club_name}\n👤 Отправитель: @{message.from_user.username}", reply_markup=inline_kb, parse_mode="Markdown")
        register_action_time(message.from_user.id, "transfer_offer")
        bot.send_message(message.chat.id, "✅ Контракт успешно отправлен игроку!", reply_markup=main_menu_keyboard(message.from_user.id, message.from_user.username))
    except:
        bot.send_message(message.chat.id, "❌ Не удалось отправить сообщение (возможно, игрок заблокировал бота).")

# =================================================================
# АДМИНИСТРАТИВНЫЕ ШАГИ (ОБРАБОТКА)
# =================================================================

def admin_step_ban_user(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=admin_panel_keyboard(message.from_user.username))
        return
    target_id = get_user_id_by_tag(message.text)
    if target_id:
        data = load_all_data()
        data["users"][target_id]["is_banned"] = True
        save_all_data(data)
        bot.send_message(message.chat.id, f"✅ Пользователь {message.text} забанен!")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def admin_step_unban_user(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=admin_panel_keyboard(message.from_user.username))
        return
    target_id = get_user_id_by_tag(message.text)
    if target_id:
        data = load_all_data()
        data["users"][target_id]["is_banned"] = False
        save_all_data(data)
        bot.send_message(message.chat.id, f"✅ Пользователь {message.text} разбанен!")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def admin_step_give_admin_rights(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=admin_panel_keyboard(SUPER_ADMIN))
        return
    data = load_all_data()
    clean_tag = message.text.replace("@", "").lower().strip()
    if clean_tag not in data["admins"]:
        data["admins"].append(clean_tag)
        save_all_data(data)
        bot.send_message(message.chat.id, f"✅ @{clean_tag} назначен администратором!")
    else:
        bot.send_message(message.chat.id, "⚠️ Пользователь уже администратор.")

def admin_step_remove_admin_rights(message):
    if message.text == "Отмена 🔙":
        bot.send_message(message.chat.id, "🏠 Отменено.", reply_markup=admin_panel_keyboard(SUPER_ADMIN))
        return
    data = load_all_data()
    clean_tag = message.text.replace("@", "").lower().strip()
    if clean_tag == SUPER_ADMIN:
        bot.send_message(message.chat.id, "❌ Нельзя лишить прав главного админа!")
        return
    if clean_tag in data["admins"]:
        data["admins"].remove(clean_tag)
        save_all_data(data)
        bot.send_message(message.chat.id, f"✅ @{clean_tag} больше не администратор.")
    else:
        bot.send_message(message.chat.id, "⚠️ Его нет в списке админов.")

# =================================================================
# ОБРАБОТКА КОМАНД И ГЛАВНОЕ МЕНЮ
# =================================================================

@bot.message_handler(commands=['start'])
def command_start_handler(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    data = load_all_data()
    uid = str(message.from_user.id)
    uname = (message.from_user.username or "none").lower()
    
    # Инициализация нового пользователя
    if uid not in data["users"]:
        data["users"][uid] = {
            "username": uname,
            "rb_nick": None,
            "is_retired": False,
            "is_banned": False,
            "owned_club": None,
            "cooldown_timers": {}
        }
    else:
        data["users"][uid]["username"] = uname
    
    save_all_data(data)

    if data["users"][uid].get("is_banned") and uname != SUPER_ADMIN:
        bot.send_message(message.chat.id, "🚫 Доступ заблокирован администрацией.")
        return

    # Если ник не задан — просим ввести
    if not data["users"][uid].get("rb_nick"):
        msg = bot.send_message(message.chat.id, "👋 Добро пожаловать!\nВведите ваш **Ник в Roblox** для продолжения:", parse_mode="Markdown", reply_markup=cancel_action_keyboard())
        bot.register_next_step_handler(msg, process_nickname_registration)
    else:
        bot.send_message(message.chat.id, "🔘 Вы в главном меню:", reply_markup=main_menu_keyboard(message.from_user.id, uname))

@bot.message_handler(content_types=['text'])
def general_text_handler(message):
    uid = str(message.from_user.id)
    uname = (message.from_user.username or "").lower()
    data = load_all_data()
    
    if uid not in data["users"]: return
    user_info = data["users"][uid]
    is_admin = uname in data["admins"]

    if user_info.get("is_banned") and uname != SUPER_ADMIN: return

    # --- СЕКЦИЯ АДМИНИСТРАТОРА ---
    if message.text == "👑 Админ Панель" and is_admin:
        bot.send_message(message.chat.id, "⚙️ Панель управления:", reply_markup=admin_panel_keyboard(uname))
        return

    if message.text == "🔙 Назад в меню":
        bot.send_message(message.chat.id, "🏠 Возвращаю в меню:", reply_markup=main_menu_keyboard(message.from_user.id, uname))
        return

    if is_admin:
        if message.text == "🚫 Забанить":
            msg = bot.send_message(message.chat.id, "Введите @username для бана:", reply_markup=cancel_action_keyboard())
            bot.register_next_step_handler(msg, admin_step_ban_user)
            return
        if message.text == "✅ Разбанить":
            msg = bot.send_message(message.chat.id, "Введите @username для разбана:", reply_markup=cancel_action_keyboard())
            bot.register_next_step_handler(msg, admin_step_unban_user)
            return
        if message.text == "⭐ Дать админку" and uname == SUPER_ADMIN:
            msg = bot.send_message(message.chat.id, "Кому дать админку? (@username):", reply_markup=cancel_action_keyboard())
            bot.register_next_step_handler(msg, admin_step_give_admin_rights)
            return
        if message.text == "❌ Снять админку" and uname == SUPER_ADMIN:
            msg = bot.send_message(message.chat.id, "У кого снять права? (@username):", reply_markup=cancel_action_keyboard())
            bot.register_next_step_handler(msg, admin_step_remove_admin_rights)
            return
        # (Остальные админ-механики по аналогии)

    # --- СЕКЦИЯ ПОЛЬЗОВАТЕЛЯ ---
    if message.text == "Написать админам 📩":
        msg = bot.send_message(message.chat.id, "✍️ Опишите ваш вопрос (Лимит: 1 раз в 20 мин):", reply_markup=cancel_action_keyboard())
        bot.register_next_step_handler(msg, process_message_to_support)

    elif message.text == "Изменить ник ✏️":
        msg = bot.send_message(message.chat.id, "✏️ Введите новый ник в Roblox (Лимит: раз в 7 дней):", reply_markup=cancel_action_keyboard())
        bot.register_next_step_handler(msg, process_nickname_update)

    elif message.text == "Свой текст 📝":
        msg = bot.send_message(message.chat.id, "💬 Введите текст сообщения для канала (Раз в 12 часов):", reply_markup=cancel_action_keyboard())
        bot.register_next_step_handler(msg, process_channel_custom_post)

    elif message.text == "Предложить трансфер 🤝":
        owner_club = CLUB_OWNERS_LIST.get(uname) or user_info.get("owned_club") or (is_admin and "Администрация")
        if owner_club:
            msg = bot.send_message(message.chat.id, "🎯 Введите @username игрока, которому хотите предложить контракт:", reply_markup=cancel_action_keyboard())
            bot.register_next_step_handler(msg, process_transfer_offer, owner_club)

    elif message.text == "Профиль 👤":
        status = "Пенсия ❌" if user_info.get("is_retired") else "Актив ✅"
        club = CLUB_OWNERS_LIST.get(uname) or user_info.get("owned_club") or "Нет"
        bot.send_message(message.chat.id, f"👤 **ВАШ ПРОФИЛЬ**\n\n🎮 Roblox: `{user_info.get('rb_nick')}`\n📈 Статус: {status}\n🏢 Клуб: {club}", parse_mode="Markdown")

    elif message.text == "Список клубов 📋":
        bot.send_message(message.chat.id, data["config"]["clubs_list_text"])

    elif message.text == "Топ клубов 🏆":
        bot.send_message(message.chat.id, data["config"]["top_clubs_text"])

    elif message.text == "Завершение карьеры 🚫":
        data["users"][uid]["is_retired"] = True
        save_all_data(data)
        bot.send_message(message.chat.id, "🚫 Ваша карьера завершена. Вы перешли в список неактивных игроков.", reply_markup=main_menu_keyboard(message.from_user.id, uname))

    elif message.text == "Возвращение карьеры 🔙":
        data["users"][uid]["is_retired"] = False
        save_all_data(data)
        bot.send_message(message.chat.id, "✅ С возвращением! Вы снова в списке активных игроков.", reply_markup=main_menu_keyboard(message.from_user.id, uname))

# =================================================================
# ОБРАБОТКА ОБРАТНЫХ ВЫЗОВОВ (CALLBACKS)
# =================================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("contract_"))
def handle_contract_callback(call):
    data = load_all_data()
    action = call.data.split("_")[1] # "ok" или "no"
    sender_uid = str(call.data.split("_")[2])
    
    player_id = str(call.from_user.id)
    player_nick = data["users"].get(player_id, {}).get("rb_nick", "Игрок")
    
    sender_info = data["users"].get(sender_uid, {})
    sender_uname = sender_info.get("username", "").lower()
    club_name = CLUB_OWNERS_LIST.get(sender_uname) or sender_info.get("owned_club", "Клуб")

    if action == "ok":
        bot.edit_message_text(f"✅ Вы приняли предложение от клуба {club_name}!", call.message.chat.id, call.message.message_id)
        bot.send_message(sender_uid, f"🔥 Игрок {player_nick} ПРИНЯЛ ваш контракт!")
        # Пост в канал
        bot.send_message(CHANNEL_ID, f"🏠 **ТРАНСФЕР СОСТОЯЛСЯ**\n\n🎮 Игрок: {player_nick}\n🏢 Новый клуб: {club_name}\n🤝 Желаем успехов!")
    else:
        bot.edit_message_text(f"❌ Вы отклонили предложение от {club_name}.", call.message.chat.id, call.message.message_id)
        bot.send_message(sender_uid, f"❌ Игрок {player_nick} отклонил ваш контракт.")

# =================================================================
# ЗАПУСК
# =================================================================

if __name__ == "__main__":
    print("Бот успешно запущен...")
    bot.infinity_polling()
