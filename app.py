import requests
import time
import json
import os
import threading
from flask import Flask
from datetime import datetime, timedelta

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = '8899088892:AAF4GHhH8xvD7ZdPW9-n01ptIy41vWZ8noE'
CHANNEL_URL = 'https://t.me/ваш_канал'
OWNER_PASSWORD = "JODIK_OFISAL091"
OWNER_TAG = "JODIK"
OWNER_ID = 8074739624
OWNER_USERNAME = "AAAP4GPMX"

DATA_FILE = "bot_data.json"

# ========== ЗАГРУЗКА ДАННЫХ ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": {}, "blocked_ids": [], "blocked_usernames": [], "muted": {}, "requests": [], "last_update": 0}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()
users_db = data.get("users", {})
blocked_ids = set(data.get("blocked_ids", []))
blocked_usernames = set(data.get("blocked_usernames", []))
muted_users = data.get("muted", {})
admin_requests = data.get("requests", [])
last_update_id = data.get("last_update", 0)

def save_all():
    data["users"] = users_db
    data["blocked_ids"] = list(blocked_ids)
    data["blocked_usernames"] = list(blocked_usernames)
    data["muted"] = muted_users
    data["requests"] = admin_requests
    data["last_update"] = last_update_id
    save_data(data)

# ========== ОТПРАВКА СООБЩЕНИЙ ==========
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def send_photo(chat_id, photo_url, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        requests.post(url, json={"chat_id": chat_id, "photo": photo_url, "caption": caption}, timeout=10)
    except:
        pass

def send_video(chat_id, video_url, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    try:
        requests.post(url, json={"chat_id": chat_id, "video": video_url, "caption": caption}, timeout=10)
    except:
        pass

def send_audio(chat_id, audio_url, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    try:
        requests.post(url, json={"chat_id": chat_id, "audio": audio_url, "caption": caption}, timeout=10)
    except:
        pass

# ========== КЛАВИАТУРЫ ==========
def get_admin_keyboard():
    return {
        "keyboard": [
            ["📊 Статистика"],
            ["👑 Список админов", "👥 Список пользователей"],
            ["🚫 Заблокированные", "🔇 Мут"],
            ["➕ Добавить админа", "➖ Удалить админа"],
            ["🚫 Заблокировать", "🔓 Разблокировать"],
            ["🔇 Замутить", "🔊 Размутить"],
            ["💬 Чат админов", "📝 Заявки"],
            ["🚪 Выйти"]
        ],
        "resize_keyboard": True
    }

def get_inline_channel():
    return {"inline_keyboard": [[{"text": "📢 Наш канал", "url": CHANNEL_URL}]]}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def is_muted(user_id):
    if str(user_id) in muted_users:
        mute_time = datetime.fromisoformat(muted_users[str(user_id)])
        if mute_time > datetime.now():
            return True
        else:
            del muted_users[str(user_id)]
            save_all()
    return False

def is_blocked(user_id, username):
    if user_id in blocked_ids:
        return True
    if username in blocked_usernames:
        return True
    return False

def get_admin_tag(user_id):
    if user_id == OWNER_ID:
        return OWNER_TAG
    return users_db.get(user_id, {}).get("admin_tag", "Admin")

admin_temp_data = {}
admin_chat_enabled = {}

# ========== ОСНОВНАЯ ЛОГИКА ==========
def process_message(message):
    global last_update_id, admin_chat_enabled

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    user_id = message.get("from", {}).get("id")
    username = message.get("from", {}).get("username") or message.get("from", {}).get("first_name", "Без имени")
    text = message.get("text", "")

    if user_id == OWNER_ID:
        username = OWNER_USERNAME

    if is_blocked(user_id, username) and user_id != OWNER_ID:
        send_message(chat_id, "❌ Вы заблокированы.")
        return

    if is_muted(user_id) and user_id != OWNER_ID:
        send_message(chat_id, "🔇 Вы замучены на 24 часа.")
        return

    if user_id not in users_db:
        users_db[user_id] = {"role": "user", "username": username}
        save_all()

    # ========== ОБРАБОТКА ВРЕМЕННЫХ ДАННЫХ (добавление админа и т.д.) ==========
    if user_id in admin_temp_data:
        step = admin_temp_data[user_id].get("step")

        if step == "waiting_new_admin_tag":
            admin_temp_data[user_id]["tag"] = text.strip()
            admin_temp_data[user_id]["step"] = "waiting_new_admin_password"
            send_message(chat_id, "Придумайте пароль:")
            return

        if step == "waiting_new_admin_password":
            users_db[user_id]["role"] = "admin"
            users_db[user_id]["admin_tag"] = admin_temp_data[user_id]["tag"]
            users_db[user_id]["password"] = text.strip()
            save_all()
            send_message(chat_id, f"✅ Вы стали администратором!\nТег: {admin_temp_data[user_id]['tag']}\nПароль: {text.strip()}\n\nВведите /admins")
            send_message(OWNER_ID, f"🆕 Новый админ: {admin_temp_data[user_id]['tag']} (@{username})")
            del admin_temp_data[user_id]
            return

        if step == "waiting_username_for_add" and user_id == OWNER_ID:
            target_username = text.strip().lstrip('@')
            target_id = None
            for uid, data_u in users_db.items():
                if data_u.get("username") == target_username:
                    target_id = uid
                    break
            if target_id:
                admin_temp_data[target_id] = {"step": "waiting_new_admin_tag"}
                send_message(target_id, "🔑 Вас хотят сделать администратором!\nПридумайте свой ТЕГ:")
                send_message(chat_id, f"✅ Запрос отправлен @{target_username}")
            else:
                send_message(chat_id, f"❌ Пользователь @{target_username} не найден")
            del admin_temp_data[user_id]
            return

        if step == "waiting_tag_for_remove" and user_id == OWNER_ID:
            target_tag = text.strip()
            for uid, data_u in users_db.items():
                if data_u.get("admin_tag") == target_tag and data_u.get("role") == "admin" and uid != OWNER_ID:
                    users_db[uid]["role"] = "user"
                    removed_tag = data_u.get("admin_tag")
                    if "password" in users_db[uid]:
                        del users_db[uid]["password"]
                    if "admin_tag" in users_db[uid]:
                        del users_db[uid]["admin_tag"]
                    send_message(uid, "❌ Вас лишили прав администратора.")
                    send_message(chat_id, f"✅ Админ {removed_tag} удалён")
                    save_all()
                    break
            else:
                send_message(chat_id, "❌ Админ не найден")
            del admin_temp_data[user_id]
            return

        if step == "waiting_block":
            target = text.strip()
            try:
                uid = int(target)
                blocked_ids.add(uid)
                send_message(chat_id, f"✅ Заблокирован ID: {uid}")
            except:
                blocked_usernames.add(target.lstrip('@'))
                send_message(chat_id, f"✅ Заблокирован @{target.lstrip('@')}")
            save_all()
            del admin_temp_data[user_id]
            return

        if step == "waiting_unblock":
            target = text.strip()
            try:
                uid = int(target)
                blocked_ids.discard(uid)
                send_message(chat_id, f"✅ Разблокирован ID: {uid}")
            except:
                blocked_usernames.discard(target.lstrip('@'))
                send_message(chat_id, f"✅ Разблокирован @{target.lstrip('@')}")
            save_all()
            del admin_temp_data[user_id]
            return

        if step == "waiting_mute":
            try:
                uid = int(text.strip())
                mute_time = datetime.now() + timedelta(hours=24)
                muted_users[str(uid)] = mute_time.isoformat()
                send_message(chat_id, f"✅ Замучен ID: {uid} на 24 часа")
                save_all()
            except:
                send_message(chat_id, "❌ Некорректный ID")
            del admin_temp_data[user_id]
            return

        if step == "waiting_unmute":
            try:
                uid = int(text.strip())
                if str(uid) in muted_users:
                    del muted_users[str(uid)]
                    send_message(chat_id, f"✅ Размучен ID: {uid}")
                    save_all()
                else:
                    send_message(chat_id, "❌ Не в муте")
            except:
                send_message(chat_id, "❌ Некорректный ID")
            del admin_temp_data[user_id]
            return

    # ========== КОМАНДЫ ПОЛЬЗОВАТЕЛЯ ==========
    if text == "/start":
        send_message(chat_id, "🤖 Бот JODIK\nОтправь сообщение — оно уйдёт админам.", reply_markup=get_inline_channel())
        return

    if text == "/admins":
        if users_db.get(user_id, {}).get("role") == "admin":
            send_message(chat_id, "✅ Админ-панель", reply_markup=get_admin_keyboard())
        else:
            send_message(chat_id, "🔐 Введите пароль:")
        return

    if text == OWNER_PASSWORD and users_db.get(user_id, {}).get("role") != "admin":
        users_db[user_id]["role"] = "admin"
        users_db[user_id]["admin_tag"] = OWNER_TAG
        save_all()
        send_message(chat_id, f"✅ Главный админ {OWNER_TAG}!", reply_markup=get_admin_keyboard())
        send_message(OWNER_ID, "🔐 Главный админ зашёл в панель")
        return

    if user_id in users_db and users_db[user_id].get("password") == text and users_db[user_id].get("role") != "admin":
        users_db[user_id]["role"] = "admin"
        save_all()
        tag = users_db[user_id].get("admin_tag", "Admin")
        send_message(chat_id, f"✅ Админ {tag}!", reply_markup=get_admin_keyboard())
        for uid, data_u in users_db.items():
            if data_u.get("role") == "admin" and uid != user_id:
                send_message(uid, f"🟢 Админ {tag} зашёл в панель")
        return

    # ========== ЧАТ АДМИНОВ ==========
    if admin_chat_enabled.get(user_id, False):
        if text == "💬 Написать админам":
            send_message(chat_id, "💬 Режим чата включён", reply_markup={"keyboard": [["🚪 Выйти из чата"]], "resize_keyboard": True})
            return
        if text == "🚪 Выйти из чата":
            admin_chat_enabled[user_id] = False
            send_message(chat_id, "🚪 Вы вышли из чата", reply_markup=get_admin_keyboard())
            return
        if users_db.get(user_id, {}).get("role") == "admin":
            tag = get_admin_tag(user_id)
            for uid, data_u in users_db.items():
                if data_u.get("role") == "admin" and uid != user_id:
                    send_message(uid, f"💬 [{tag}]: {text}")
            send_message(chat_id, f"✅ Отправлено: {text}")
            return

    # ========== КНОПКИ АДМИНА ==========
    if users_db.get(user_id, {}).get("role") == "admin":

        if text == "📊 Статистика":
            total = len(users_db)
            admins = sum(1 for d in users_db.values() if d.get("role") == "admin")
            blocked = len(blocked_ids) + len(blocked_usernames)
            muted = len(muted_users)
            send_message(chat_id, f"📊 СТАТИСТИКА\n👥 Пользователей: {total}\n👑 Админов: {admins}\n🚫 Заблокировано: {blocked}\n🔇 Замучено: {muted}")
            return

        if text == "👑 Список админов":
            admin_list = []
            for uid, data_u in users_db.items():
                if data_u.get("role") == "admin":
                    tag = data_u.get("admin_tag", "Без тега")
                    admin_list.append(f"👑 {tag} (ID: {uid})")
            send_message(chat_id, "📋 АДМИНЫ:\n" + "\n".join(admin_list) if admin_list else "Нет админов")
            return

        if text == "👥 Список пользователей":
            user_list = []
            for uid, data_u in users_db.items():
                if data_u.get("role") != "admin":
                    user_list.append(f"👤 {data_u.get('username')} (ID: {uid})")
            send_message(chat_id, "📋 ПОЛЬЗОВАТЕЛИ:\n" + "\n".join(user_list[:50]) if user_list else "Нет пользователей")
            return

        if text == "🚫 Заблокированные":
            items = [f"🚫 ID: {uid}" for uid in blocked_ids] + [f"🚫 @{uname}" for uname in blocked_usernames]
            send_message(chat_id, "🚫 ЗАБЛОКИРОВАННЫЕ:\n" + "\n".join(items) if items else "Нет")
            return

        if text == "🔇 Мут":
            items = [f"🔇 ID: {uid} до {mute_time[:16]}" for uid, mute_time in muted_users.items()]
            send_message(chat_id, "🔇 ЗАМУЧЕННЫЕ:\n" + "\n".join(items) if items else "Нет")
            return

        if text == "➕ Добавить админа" and user_id == OWNER_ID:
            admin_temp_data[user_id] = {"step": "waiting_username_for_add"}
            send_message(chat_id, "Введите @username для добавления в админы:")
            return

        if text == "➖ Удалить админа" and user_id == OWNER_ID:
            tags = []
            for uid, data_u in users_db.items():
                if data_u.get("role") == "admin" and uid != OWNER_ID:
                    tags.append(data_u.get("admin_tag", "Без тега"))
            if tags:
                admin_temp_data[user_id] = {"step": "waiting_tag_for_remove"}
                send_message(chat_id, f"Введите ТЕГ админа для удаления:\n{', '.join(tags)}")
            else:
                send_message(chat_id, "Нет других админов")
            return

        if text == "🚫 Заблокировать":
            admin_temp_data[user_id] = {"step": "waiting_block"}
            send_message(chat_id, "Введите ID или @username для блокировки:")
            return

        if text == "🔓 Разблокировать":
            admin_temp_data[user_id] = {"step": "waiting_unblock"}
            send_message(chat_id, "Введите ID или @username для разблокировки:")
            return

        if text == "🔇 Замутить":
            admin_temp_data[user_id] = {"step": "waiting_mute"}
            send_message(chat_id, "Введите ID для мута на 24 часа:")
            return

        if text == "🔊 Размутить":
            admin_temp_data[user_id] = {"step": "waiting_unmute"}
            send_message(chat_id, "Введите ID для размута:")
            return

        if text == "💬 Чат админов":
            admin_chat_enabled[user_id] = True
            send_message(chat_id, "💬 Добро пожаловать в чат админов", reply_markup={"keyboard": [["💬 Написать админам"], ["🚪 Выйти из чата"]], "resize_keyboard": True})
            return

        if text == "📝 Заявки" and user_id == OWNER_ID:
            pending = [r for r in admin_requests if r.get("status") == "pending"]
            if pending:
                req_list = [f"👤 @{r['username']} (ID: {r['user_id']})" for r in pending]
                send_message(chat_id, "📝 ЗАЯВКИ:\n" + "\n".join(req_list) + "\n\n/accept ID - принять\n/decline ID - отказать")
            else:
                send_message(chat_id, "Нет заявок")
            return

        if text == "🚪 Выйти":
            tag = get_admin_tag(user_id)
            send_message(chat_id, "🚪 Выход", reply_markup={"remove_keyboard": True})
            for uid, data_u in users_db.items():
                if data_u.get("role") == "admin" and uid != user_id:
                    send_message(uid, f"🔴 Админ {tag} вышел")
            return

    # ========== ОТВЕТ АДМИНА ПОЛЬЗОВАТЕЛЮ ==========
    reply_to_id = message.get("reply_to_message", {}).get("message_id") if message.get("reply_to_message") else None
    if reply_to_id and users_db.get(user_id, {}).get("role") == "admin":
        replied_text = message.get("reply_to_message", {}).get("text", "") or message.get("reply_to_message", {}).get("caption", "")
        import re
        match = re.search(r"ID: (\d+)", replied_text)
        if match:
            target_id = int(match.group(1))
            if not is_blocked(target_id, ""):
                tag = get_admin_tag(user_id)
                send_message(target_id, f"📨 Ответ от {tag}: {text}")
                send_message(chat_id, "✅ Ответ отправлен")
            return

    # ========== ПЕРЕСЫЛКА ПОЛЬЗОВАТЕЛЯ АДМИНАМ ==========
    if users_db.get(user_id, {}).get("role") != "admin":
        admin_ids = [uid for uid, d in users_db.items() if d.get("role") == "admin"]
        if admin_ids:
            for admin_id in admin_ids:
                send_message(admin_id, f"📩 Юзер: {username} (ID: {user_id})\nТекст: {text}")
            send_message(chat_id, "✅ Отправлено админам")
        else:
            send_message(chat_id, "❌ Админов нет. Сообщим когда появится.")
        return

# ========== ЗАПУСК БОТА ==========
def run_bot():
    global last_update_id
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    print("🔄 Бот запущен...")
    while True:
        try:
            params = {"timeout": 30, "offset": last_update_id + 1}
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            if data.get("ok"):
                for update in data.get("result", []):
                    last_update_id = update.get("update_id")
                    if "message" in update:
                        process_message(update["message"])
                save_all()
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(1)

app = Flask(__name__)

@app.route('/')
def index():
    return "Бот JODIK работает!", 200

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    print("✅ Бот JODIK запущен!")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
