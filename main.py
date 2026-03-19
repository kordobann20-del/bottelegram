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

# Владельцы клубов (ID: Название клуба)
CLUB_OWNERS = {
    7932332909: "Arsenal",
    7908040352: "Inter Milan",
    8169093601: "Bayern Munich",
    7138854880: "Albacete",
    7710520171: "Qarabağ",
    8087187813: "ФК Террор"
}
# =============================================

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

def load_data():
    """Загрузка данных из файла, чтобы ники не пропадали"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return {}
    return {}

def save_data(data):
    """Сохранение данных в файл"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def get_main_menu(user_id):
    """Создание адаптивной клавиатуры"""
    data = load_data()
    user_id_str = str(user_id)
    is_retired = data.get(user_id_str, {}).get("is_retired", False)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Кнопки карьеры (зависят от статуса)
    if user_id == ADMIN_ID or not is_retired:
        markup.add(types.KeyboardButton("Завершение карьеры 🚫"))
    if user_id == ADMIN_ID or is_retired:
        markup.add(types.KeyboardButton("Возвращение карьеры 🔙"))
        
    markup.add(types.KeyboardButton("Свободный агент 🆓"), types.KeyboardButton("Свой текст 📝"))
    
    # Кнопка для владельцев
    if user_id in CLUB_OWNERS or user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("Предложить трансфер 🤝"))
        
    markup.add(types.KeyboardButton("Список клубов 📋"), types.KeyboardButton("Профиль 👤"))
    markup.add(types.KeyboardButton("Изменить ник ✏️"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.from_user.id)
    username = message.from_user.username.lower() if message.from_user.username else "нет_юзернейма"
    
    if user_id not in data:
        data[user_id] = {"is_retired": False}
    
    # Обновляем юзернейм в базе, если он сменился в ТГ
    data[user_id]["username"] = username
    save_data(data)

    if "rb_nick" not in data[user_id]:
        msg = bot.send_message(message.chat.id, "👋 **Добро пожаловать!**\nВведите ваш **Ник в Roblox** для регистрации в базе:")
        bot.register_next_step_handler(msg, register_user)
    else:
        nick = data[user_id]["rb_nick"]
        bot.send_message(message.chat.id, f"✅ С возвращением, **{nick}**!\nВаш профиль активен.", reply_markup=get_main_menu(message.from_user.id))

def register_user(message):
    rb_nick = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id]["rb_nick"] = rb_nick
    data[user_id]["last_nick_change"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(message.chat.id, f"🎉 Регистрация успешна! Ваш ник: **{rb_nick}**", reply_markup=get_main_menu(message.from_user.id))

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

    if message.text == "Список клубов 📋":
        text = (
            "🏆 **ОФИЦИАЛЬНЫЕ ТМ КЛУБЫ**\n━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇹 Inter Milan — @Banditdontrealme\n"
            "🇩🇪 Bayern Munich — @EstavaoJr\n"
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Arsenal — @Nagisls\n\n"
            "🔥 **КАСТОМНЫЕ ТМ КЛУБЫ**\n━━━━━━━━━━━━━━━━━━━━\n"
            "🇪🇸 Albacete — @Eoupapa\n"
            "🇦🇿 Qarabağ — @Suleyman1453638\n"
            "💀 ФК Террор — @Ez_Mbappe"
        )
        bot.send_message(message.chat.id, text)

    elif message.text == "Свой текст 📝":
        msg = bot.send_message(message.chat.id, "💬 Введите текст для публикации в канале:")
        bot.register_next_step_handler(msg, send_custom_text, rb_nick, tg_user)

    elif message.text == "Предложить трансфер 🤝":
        if user_id not in CLUB_OWNERS and user_id != ADMIN_ID: return
        last_t = data[user_id_str].get("last_transfer_time", 0)
        if time.time() - last_t < 3600 and user_id != ADMIN_ID:
            rem = int((3600 - (time.time() - last_t)) / 60)
            bot.send_message(message.chat.id, f"❌ Подождите ещё {rem} мин. (КД 1 час)")
            return
        msg = bot.send_message(message.chat.id, "🎯 Введите @username игрока, которому хотите предложить контракт:")
        bot.register_next_step_handler(msg, process_transfer_target)

    elif message.text == "Завершение карьеры 🚫":
        msg = bot.send_message(message.chat.id, "🚫 Введите причину завершения карьеры (П.С.):")
        bot.register_next_step_handler(msg, process_retirement, rb_nick, tg_user)

    elif message.text == "Возвращение карьеры 🔙":
        last_r = data[user_id_str].get("retire_date")
        if last_r and user_id != ADMIN_ID:
            diff = (datetime.datetime.now() - datetime.datetime.strptime(last_r, "%Y-%m-%d %H:%M:%S")).days
            if diff < RETIRE_LIMIT_DAYS:
                bot.send_message(message.chat.id, f"❌ Вернуться можно только через 5 дней. Осталось: {RETIRE_LIMIT_DAYS - diff} дн.")
                return
        data[user_id_str]["is_retired"] = False
        save_data(data)
        bot.send_message(message.chat.id, "🔙 Вы официально вернулись в строй!", reply_markup=get_main_menu(user_id))

    elif message.text == "Свободный агент 🆓":
        msg = bot.send_message(message.chat.id, "📝 Напишите ваш П.С. для статуса свободного агента:")
        bot.register_next_step_handler(msg, send_sa_status, rb_nick, tg_user)

    elif message.text == "Профиль 👤":
        status = "На пенсии ❌" if data[user_id_str].get("is_retired") else "Активен ✅"
        bot.send_message(message.chat.id, f"👤 **ВАШ ПРОФИЛЬ**\n\n🎮 Ник: `{rb_nick}`\n📱 ТГ: {tg_user}\n📊 Статус: {status}\n🆔 ID: `{user_id}`")

    elif message.text == "Изменить ник ✏️":
        last_c = data[user_id_str].get("last_nick_change")
        if last_c and user_id != ADMIN_ID:
            diff = (datetime.datetime.now() - datetime.datetime.strptime(last_c, "%Y-%m-%d %H:%M:%S")).days
            if diff < NICK_LIMIT_DAYS:
                bot.send_message(message.chat.id, f"❌ Ник можно менять раз в неделю. Ждите {NICK_LIMIT_DAYS - diff} дн.")
                return
        msg = bot.send_message(message.chat.id, "✏️ Введите новый ник:")
        bot.register_next_step_handler(msg, update_nick)

# --- ФУНКЦИИ ОБРАБОТКИ ---

def send_custom_text(message, nick, tg_user):
    rep = f"📝 **СООБЩЕНИЕ**\n\n👤 От: {nick} ({tg_user})\n💬 Текст: {message.text}"
    bot.send_message(CHANNEL_ID, rep)
    bot.send_message(message.chat.id, "✅ Сообщение отправлено!")

def send_sa_status(message, nick, tg_user):
    rep = f"🆓 **СВОБОДНЫЙ АГЕНТ**\n\n🎮 Ник: {nick}\n📱 Контакт: {tg_user}\n🖋 П.С.: {message.text}"
    bot.send_message(CHANNEL_ID, rep)
    bot.send_message(message.chat.id, "✅ Статус опубликован!")

def process_retirement(message, nick, tg_user):
    data = load_data()
    u_id = str(message.from_user.id)
    data[u_id]["is_retired"] = True
    data[u_id]["retire_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    rep = f"🚫 **ЗАВЕРШЕНИЕ КАРЬЕРЫ**\n\n🎮 Ник: {nick}\n📱 ТГ: {tg_user}\n🖋 Причина: {message.text}"
    bot.send_message(CHANNEL_ID, rep)
    bot.send_message(message.chat.id, "❌ Ваша карьера завершена.", reply_markup=get_main_menu(u_id))

def process_transfer_target(message):
    target_username = message.text.replace("@", "").lower().strip()
    data = load_data()
    target_id = next((uid for uid, udata in data.items() if udata.get("username") == target_username), None)
    if not target_id:
        bot.send_message(message.chat.id, "❌ Игрок не найден. Он должен быть зарегистрирован в боте.")
        return
    owner_tg = f"@{message.from_user.username}" if message.from_user.username else "Владелец"
    club = CLUB_OWNERS.get(message.from_user.id, "Клуб")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"tr_acc_{message.from_user.id}"),
               types.InlineKeyboardButton("❌ Отклонить", callback_data=f"tr_dec_{message.from_user.id}"))
    bot.send_message(target_id, f"⚽️ **ПРЕДЛОЖЕНИЕ!**\n\n🏢 Клуб: **{club}**\n👤 От: {owner_tg}\n\nВы согласны на переход?", reply_markup=markup)
    data[str(message.from_user.id)]["last_transfer_time"] = time.time()
    save_data(data)
    bot.send_message(message.chat.id, "🚀 Предложение отправлено игроку!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("tr_"))
def callback_transfer(call):
    data = load_data()
    owner_id = int(call.data.split("_")[2])
    p_id = str(call.from_user.id)
    p_nick = data.get(p_id, {}).get("rb_nick", "Игрок")
    p_tg = f"@{call.from_user.username}" if call.from_user.username else "ТГ скрыт"
    club = CLUB_OWNERS.get(owner_id, "Клуб")
    if "acc" in call.data:
        bot.edit_message_text("✅ Вы приняли трансфер!", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"🔥 **{p_nick}** ({p_tg}) ПРИНЯЛ ваш контракт!")
        bot.send_message(CHANNEL_ID, f"🏠 **ОФИЦИАЛЬНЫЙ ПЕРЕХОД**\n\n🎮 Игрок: {p_nick} ({p_tg})\n🏢 Клуб: {club}\n✅ Статус: Контракт подписан")
    else:
        bot.edit_message_text("❌ Вы отклонили предложение.", call.message.chat.id, call.message.message_id)
        bot.send_message(owner_id, f"😔 **{p_nick}** отказался от предложения.")

def update_nick(message):
    data = load_data()
    user_id = str(message.from_user.id)
    old_nick = data[user_id].get("rb_nick", "Старый")
    new_nick = message.text.strip()
    data[user_id]["rb_nick"] = new_nick
    data[user_id]["last_nick_change"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Ник успешно изменен с {old_nick} на **{new_nick}**!", reply_markup=get_main_menu(user_id))

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
