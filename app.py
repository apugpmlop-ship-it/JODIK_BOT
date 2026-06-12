import requests
import time
import json
import os
import threading
import re
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
    return {
        "users": {},
        "blocked_ids": [],
        "blocked_usernames": [],
        "muted": {},
        "last_update": 0,
        "total_messages": 0,
        "total_users_ever": 0
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()
users_db = data.get("users", {})
blocked_ids = set(data.get("blocked_ids", []))
blocked_usernames = set(data.get("blocked_usernames", []))
muted_users = data.get("muted", {})
last_update_id = data.get("last_update", 0)
total_messages = data.get("total_messages", 0)
total_users_ever = data.get("total_users_ever", 0)

def save_all():
    data["users"] = users_db
    data["blocked_ids"] = list(blocked_ids)
    data["blocked_usernames"] = list(blocked_usernames)
    data["muted"] = muted_users
    data["last_update"] = last_update_id
    data["total_messages"] = total_messages
    data["total_users_ever"] = total_users_ever
    save_data(data)

# ========== ОТПРАВКА ==========
def send_message(chat_id, text, reply_markup=None, reply_to=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def send_photo(chat_id, photo_file_id, caption="", reply_to=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_file_id, "caption": caption}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_video(chat_id, video_file_id, caption="", reply_to=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    payload = {"chat_id": chat_id, "video": video_file_id, "caption": caption}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_audio(chat_id, audio_file_id, caption="", reply_to=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    payload = {"chat_id": chat_id, "audio": audio_file_id, "caption": caption}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_sticker(chat_id, sticker_file_id, reply_to=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendSticker"
    payload = {"chat_id": chat_id, "sticker": sticker_file_id}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def send_document(chat_id, doc_file_id, caption="", reply_to=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    payload = {"chat_id": chat_id, "document": doc_file_id, "caption": caption}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ========== КЛАВИАТУРЫ ==========
def get_admin_keyboard():
    return {
        "keyboard": [
            ["📊 Статистика"],
            ["👑 Список админов", "👥 Список пользователей"],
            ["🚫 Заблокированные"],
            ["➕ Добавить админа", "➖ Удалить админа"],
            ["🚫 Заблокировать", "🔓 Разблокировать"],
            ["🔇 Замутить", "🔊 Размутить"],
            ["💬 Чат админов"],
            ["🚪 Выйти"]
        ],
        "resize_keyboard": True
    }

def get_inline_channel():
    return {
        "inline_keyboard": [
            [{"text": "📢 Наш канал", "url": CHANNEL_URL}],
            [{"text": "➕ Добавить бота в группу", "url": f"https://t.me/{BOT_TOKEN.split(':')[0]}?startgroup=true"}]
        ]
    }

def get_accept_decline_keyboard(admin_id, admin_tag):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ ДА, стать админом", "callback_data": f"accept_{admin_id}"},
                {"text": "❌ НЕТ, отказаться", "callback_data": f"decline_{admin_id}"}
            ]
        ]
    }

# ========== ВСПОМОГАТЕЛЬНЫЕ ==========
def parse_mute_time(text):
    text = text.lower().strip()
    if text.endswith('м'):
        try:
            minutes = int(text[:-1])
            return datetime.now() + timedelta(minutes=minutes), f"{minutes} минут"
        except:
            pass
    elif text.endswith('ч'):
        try:
            hours = int(text[:-1])
            return datetime.now() + timedelta(hours=hours), f"{hours} часов"
        except:
            pass
    elif text.endswith('д'):
        try:
            days = int(text[:-1])
            return datetime.now() + timedelta(days=days), f"{days} дней"
        except:
            pass
    else:
        try:
            hours = int(text)
            return datetime.now() + timedelta(hours=hours), f"{hours} часов"
        except:
            pass
    return None, None

def is_muted(user_id):
    if str(user_id) in muted_users:
        mute_time = datetime.fromisoformat(muted_users[str(user_id)])
        if mute_time > datetime.now():
            return True, mute_time
        else:
            del muted_users[str(user_id)]
            save_all()
    return False, None

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

def notify_all_admins(text, exclude_id=None):
    admin_ids = [uid for uid, d in users_db.items() if d.get("role") == "admin" and uid != exclude_id]
    if admin_ids:
        for admin_id in admin_ids:
            send_message(admin_id, text)
        return True
    return False

def notify_no_admins(chat_id):
    send_message(chat_id, "❌ Администраторов сейчас нет. Как только появится админ — ваше сообщение будет доставлено.")
    return

admin_temp_data = {}
admin_chat_enabled = {}
pending_requests = {}

# ========== ОСНОВНАЯ ЛОГИКА ==========
def process_message(message):
    global last_update_id, admin_chat_enabled, total_messages, total_users_ever

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    user_id = message.get("from", {}).get("id")
    username = message.get("from", {}).get("username") or message.get("from", {}).get("first_name", "Без имени")
    text = message.get("text", "")
    
    photo = message.get("photo")
    video = message.get("video")
    audio = message.get("audio")
    sticker = message.get("sticker")
    document = message.get("document")

    if user_id == OWNER_ID:
        username = OWNER_USERNAME

    if is_blocked(user_id, username) and user_id != OWNER_ID:
        send_message(chat_id, "❌ Вы заблокированы.")
        return

    muted, until = is_muted(user_id)
    if muted and user_id != OWNER_ID:
        time_left = until - datetime.now()
        minutes = int(time_left.total_seconds() // 60)
        send_message(chat_id, f"🔇 Вы замучены на {minutes} минут.")
        return

    if user_id not in users_db:
        users_db[user_id] = {"role": "user", "username": username}
        total_users_ever += 1
        save_all()
    
    total_messages += 1
    save_all()

    # ========== ОБРАБОТКА ВРЕМЕННЫХ ДАННЫХ ==========
    if user_id in admin_temp_data:
        step = admin_temp_data[user_id].get("step")

        if step == "waiting_new_admin_tag":
            admin_temp_data[user_id]["tag"] = text.strip()
            admin_temp_data[user_id]["step"] = "waiting_new_admin_password"
            send_message(chat_id, "Придумайте пароль для входа в админ-панель:")
            return

        if step == "waiting_new_admin_password":
            users_db[user_id]["role"] = "admin"
            users_db[user_id]["admin_tag"] = admin_temp_data[user_id]["tag"]
            users_db[user_id]["password"] = text.strip()
            save_all()
            send_message(chat_id, f"✅ ПОЗДРАВЛЯЮ! Вы стали администратором!\n\n📛 Ваш тег: {admin_temp_data[user_id]['tag']}\n🔐 Ваш пароль: {text.strip()}\n\n👉 Введите /admins и пароль для входа в админ-панель.")
            
            # Уведомление всем админам о новом админе
            sent = notify_all_admins(f"🆕 НОВЫЙ АДМИНИСТРАТОР!\n📛 Тег: {admin_temp_data[user_id]['tag']}\n👤 Юзер: @{username}\n🆔 ID: {user_id}", exclude_id=user_id)
            if not sent:
                send_message(OWNER_ID, f"🆕 НОВЫЙ АДМИНИСТРАТОР!\n📛 Тег: {admin_temp_data[user_id]['tag']}\n👤 Юзер: @{username}\n🆔 ID: {user_id}")
            
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
            target_id_str = admin_temp_data[user_id].get("target_id")
            if not target_id_str:
                admin_temp_data[user_id]["target_id"] = text.strip()
                send_message(chat_id, "Введите время мута:\n30м - 30 минут\n2ч - 2 часа\n1д - 1 день\n24 - 24 часа")
                return
            else:
                mute_time, time_str = parse_mute_time(text)
                if mute_time:
                    target_id = admin_temp_data[user_id]["target_id"]
                    muted_users[target_id] = mute_time.isoformat()
                    save_all()
                    try:
                        send_message(int(target_id), f"🔇 Вас замутили на {time_str}")
                    except:
                        pass
                    send_message(chat_id, f"✅ Замучен ID: {target_id} на {time_str}")
                else:
                    send_message(chat_id, "❌ Неверный формат. Примеры: 30м, 2ч, 1д, 24")
                del admin_temp_data[user_id]
            return

        if step == "waiting_unmute":
            try:
                uid = int(text.strip())
                if str(uid) in muted_users:
                    del muted_users[str(uid)]
                    send_message(chat_id, f"✅ Размучен ID: {uid}")
                    save_all()
                    try:
                        send_message(uid, "🔊 Вас размутили!")
                    except:
                        pass
                else:
                    send_message(chat_id, "❌ Этот пользователь не в муте")
            except:
                send_message(chat_id, "❌ Введите ID")
            del admin_temp_data[user_id]
            return

        if step == "waiting_remove_admin":
            target_tag = text.strip()
            for uid, data_u in users_db.items():
                if data_u.get("admin_tag") == target_tag and data_u.get("role") == "admin" and uid != OWNER_ID:
                    users_db[uid]["role"] = "user"
                    removed_tag = data_u.get("admin_tag")
                    removed_username = data_u.get("username")
                    if "password" in users_db[uid]:
                        del users_db[uid]["password"]
                    if "admin_tag" in users_db[uid]:
                        del users_db[uid]["admin_tag"]
                    send_message(uid, "❌ Вас лишили прав администратора.")
                    send_message(chat_id, f"✅ Администратор {removed_tag} (@{removed_username}) удалён")
                    notify_all_admins(f"❌ Администратор {removed_tag} (@{removed_username}) удалён из админов")
                    save_all()
                    break
            else:
                send_message(chat_id, "❌ Администратор не найден")
            del admin_temp_data[user_id]
            return

    # ========== КОМАНДЫ ==========
    if text == "/start":
        send_message(chat_id, "🤖 <b>БОТ JODIK</b>\n\nОтправь текст, фото, видео, стикеры — всё уйдёт админам.\n\n📢 Подпишись на канал:\n👇 Кнопка ниже", reply_markup=get_inline_channel())
        return

    if text == "/admins":
        if users_db.get(user_id, {}).get("role") == "admin":
            send_message(chat_id, "✅ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:", reply_markup=get_admin_keyboard())
        else:
            send_message(chat_id, "🔐 <b>ВХОД ДЛЯ АДМИНОВ</b>\n\nВведите пароль:")
        return

    if text == OWNER_PASSWORD and users_db.get(user_id, {}).get("role") != "admin":
        users_db[user_id]["role"] = "admin"
        users_db[user_id]["admin_tag"] = OWNER_TAG
        save_all()
        send_message(chat_id, f"✅ <b>ГЛАВНЫЙ АДМИНИСТРАТОР</b>\n\nВаш тег: {OWNER_TAG}", reply_markup=get_admin_keyboard())
        notify_all_admins(f"🔐 ГЛАВНЫЙ АДМИНИСТРАТОР {OWNER_TAG} зашёл в панель")
        return

    if user_id in users_db and users_db[user_id].get("password") == text and users_db[user_id].get("role") != "admin":
        users_db[user_id]["role"] = "admin"
        save_all()
        tag = users_db[user_id].get("admin_tag", "Admin")
        send_message(chat_id, f"✅ <b>АДМИНИСТРАТОР</b>\n\nВаш тег: {tag}", reply_markup=get_admin_keyboard())
        notify_all_admins(f"🟢 АДМИНИСТРАТОР {tag} зашёл в панель", exclude_id=user_id)
        return

    # ========== ЧАТ АДМИНОВ ==========
    if admin_chat_enabled.get(user_id, False):
        if text == "💬 Написать админам":
            send_message(chat_id, "💬 <b>ЧАТ АДМИНОВ</b>\n\nПишите — все админы увидят\n\n🚪 Выйти из чата - кнопка ниже", 
                        reply_markup={"keyboard": [["🚪 Выйти из чата"]], "resize_keyboard": True})
            return
        if text == "🚪 Выйти из чата":
            admin_chat_enabled[user_id] = False
            send_message(chat_id, "🚪 Вы вышли из чата админов", reply_markup=get_admin_keyboard())
            return
        if users_db.get(user_id, {}).get("role") == "admin":
            tag = get_admin_tag(user_id)
            for uid, data_u in users_db.items():
                if data_u.get("role") == "admin" and uid != user_id:
                    if text:
                        send_message(uid, f"💬 <b>[{tag}]</b>: {text}")
                    elif photo:
                        send_photo(uid, photo[-1]["file_id"], f"💬 <b>[{tag}]</b>: фото")
                    elif video:
                        send_video(uid, video["file_id"], f"💬 <b>[{tag}]</b>: видео")
                    elif sticker:
                        send_sticker(uid, sticker["file_id"])
                        send_message(uid, f"💬 <b>[{tag}]</b>: стикер")
            send_message(chat_id, "✅ Отправлено админам")
            return

    # ========== КНОПКИ АДМИНА ==========
    if users_db.get(user_id, {}).get("role") == "admin":

        if text == "📊 Статистика":
            total = len(users_db)
            admins = sum(1 for d in users_db.values() if d.get("role") == "admin")
            blocked = len(blocked_ids) + len(blocked_usernames)
            muted = len(muted_users)
            send_message(chat_id, f"📊 <b>СТАТИСТИКА БОТА</b>\n\n👥 Пользователей сейчас: {total}\n👑 Администраторов: {admins}\n🚫 Заблокировано: {blocked}\n🔇 Замучено: {muted}\n\n📈 Всего пользователей (за всё время): {total_users_ever}\n💬 Всего сообщений: {total_messages}")
            return

        if text == "👑 Список админов":
            admin_list = []
            for uid, data_u in users_db.items():
                if data_u.get("role") == "admin":
                    tag = data_u.get("admin_tag", "Без тега")
                    admin_list.append(f"👑 <b>{tag}</b> — @{data_u.get('username')} (ID: {uid})")
            send_message(chat_id, "📋 <b>АДМИНИСТРАТОРЫ</b>\n\n" + "\n".join(admin_list) if admin_list else "Нет админов")
            return

        if text == "👥 Список пользователей":
            user_list = []
            for uid, data_u in users_db.items():
                if data_u.get("role") != "admin":
                    user_list.append(f"👤 @{data_u.get('username')} (ID: {uid})")
            send_message(chat_id, "📋 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n" + "\n".join(user_list[:50]) if user_list else "Нет пользователей")
            return

        if text == "🚫 Заблокированные":
            items = [f"🚫 ID: {uid}" for uid in blocked_ids] + [f"🚫 @{uname}" for uname in blocked_usernames]
            send_message(chat_id, "🚫 <b>ЗАБЛОКИРОВАННЫЕ</b>\n\n" + "\n".join(items) if items else "Нет")
            return

        if text == "➕ Добавить админа" and user_id == OWNER_ID:
            admin_temp_data[user_id] = {"step": "waiting_username_for_add"}
            send_message(chat_id, "Введите @username или ID пользователя для приглашения в админы:")
            return

        if text == "➕ Добавить админа" and user_id != OWNER_ID:
            send_message(chat_id, "❌ Только главный администратор может добавлять админов")
            return

        if text == "➖ Удалить админа" and user_id == OWNER_ID:
            tags = []
            for uid, data_u in users_db.items():
                if data_u.get("role") == "admin" and uid != OWNER_ID:
                    tags.append(f"{data_u.get('admin_tag', 'Без тега')} — @{data_u.get('username')}")
            if tags:
                admin_temp_data[user_id] = {"step": "waiting_remove_admin"}
                send_message(chat_id, f"Введите ТЕГ админа для удаления:\n\n" + "\n".join(tags))
            else:
                send_message(chat_id, "Нет других админов для удаления")
            return

        if text == "➖ Удалить админа" and user_id != OWNER_ID:
            send_message(chat_id, "❌ Только главный администратор может удалять админов")
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
            admin_temp_data[user_id] = {"step": "waiting_mute", "target_id": None}
            send_message(chat_id, "Введите ID пользователя для мута:")
            return

        if text == "🔊 Размутить":
            admin_temp_data[user_id] = {"step": "waiting_unmute"}
            send_message(chat_id, "Введите ID пользователя для размута:")
            return

        if text == "💬 Чат админов":
            admin_chat_enabled[user_id] = True
            send_message(chat_id, "💬 <b>ВЫ ВОШЛИ В ЧАТ АДМИНОВ</b>\n\nПишите — все админы увидят\n\n🚪 Выйти из чата - кнопка ниже",
                        reply_markup={"keyboard": [["💬 Написать админам"], ["🚪 Выйти из чата"]], "resize_keyboard": True})
            return

        if text == "🚪 Выйти":
            tag = get_admin_tag(user_id)
            send_message(chat_id, "🚪 Вы вышли из админ-панели", reply_markup={"remove_keyboard": True})
            notify_all_admins(f"🔴 АДМИНИСТРАТОР {tag} вышел из панели", exclude_id=user_id)
            admin_chat_enabled[user_id] = False
            return

    # ========== ПРИГЛАШЕНИЕ В АДМИНЫ ==========
    if text.startswith("/add_admin") and user_id == OWNER_ID:
        parts = text.split()
        if len(parts) >= 2:
            target = parts[1].strip()
            target_id = None
            target_username = None
            
            # Проверка: это ID или юзернейм?
            try:
                target_id = int(target)
                for uid, data_u in users_db.items():
                    if uid == target_id:
                        target_username = data_u.get("username")
                        break
            except:
                target_username = target.lstrip('@')
                for uid, data_u in users_db.items():
                    if data_u.get("username") == target_username:
                        target_id = uid
                        break
            
            if target_id and target_id in users_db:
                pending_requests[target_id] = {"admin_id": user_id, "admin_tag": OWNER_TAG, "username": target_username}
                send_message(target_id, f"🔑 <b>ПРИГЛАШЕНИЕ В АДМИНИСТРАТОРЫ</b>\n\nЗдравствуйте, @{target_username}!\n\nВас хочет пригласить в роль администратора бота <b>JODIK</b> администратор <b>{OWNER_TAG}</b>.\n\n<b>Вы согласны стать администратором?</b>",
                            reply_markup=get_accept_decline_keyboard(user_id, OWNER_TAG))
                send_message(chat_id, f"✅ Приглашение отправлено @{target_username} (ID: {target_id})")
            else:
                send_message(chat_id, f"❌ Пользователь не найден. Убедитесь, что он написал /start боту.")
        else:
            send_message(chat_id, "Использование: /add_admin @username\nили\n/add_admin 123456789")
        return

    # ========== ОТВЕТ АДМИНА ПОЛЬЗОВАТЕЛЮ (с reply) ==========
    reply_to_id = message.get("reply_to_message", {}).get("message_id") if message.get("reply_to_message") else None
    if reply_to_id and users_db.get(user_id, {}).get("role") == "admin":
        replied_text = message.get("reply_to_message", {}).get("text", "") or message.get("reply_to_message", {}).get("caption", "")
        match = re.search(r"ID: (\d+)", replied_text)
        if match:
            target_id = int(match.group(1))
            if not is_blocked(target_id, ""):
                tag = get_admin_tag(user_id)
                
                if text:
                    send_message(target_id, f"📨 <b>ОТВЕТ ОТ АДМИНИСТРАТОРА {tag}</b>\n\n{text}", reply_to=reply_to_id)
                elif photo:
                    send_photo(target_id, photo[-1]["file_id"], f"📨 Ответ от {tag}", reply_to=reply_to_id)
                elif video:
                    send_video(target_id, video["file_id"], f"📨 Ответ от {tag}", reply_to=reply_to_id)
                elif audio:
                    send_audio(target_id, audio["file_id"], f"📨 Ответ от {tag}", reply_to=reply_to_id)
                elif sticker:
                    send_sticker(target_id, sticker["file_id"], reply_to=reply_to_id)
                    send_message(target_id, f"📨 Ответ от {tag}: стикер")
                elif document:
                    send_document(target_id, document["file_id"], f"📨 Ответ от {tag}", reply_to=reply_to_id)
                    
                send_message(chat_id, "✅ Ответ отправлен пользователю")
            return

    # ========== ПЕРЕСЫЛКА ПОЛЬЗОВАТЕЛЯ АДМИНАМ ==========
    if users_db.get(user_id, {}).get("role") != "admin":
        admin_ids = [uid for uid, d in users_db.items() if d.get("role") == "admin"]
        if admin_ids:
            for admin_id in admin_ids:
                if text:
                    send_message(admin_id, f"📩 <b>НОВОЕ СООБЩЕНИЕ</b>\n\n👤 @{username} (ID: {user_id})\n💬 Текст: {text}")
                elif photo:
                    send_photo(admin_id, photo[-1]["file_id"], f"📩 @{username} (ID: {user_id})\n📷 Фото")
                elif video:
                    send_video(admin_id, video["file_id"], f"📩 @{username} (ID: {user_id})\n🎬 Видео")
                elif audio:
                    send_audio(admin_id, audio["file_id"], f"📩 @{username} (ID: {user_id})\n🎵 Аудио")
                elif sticker:
                    send_sticker(admin_id, sticker["file_id"])
                    send_message(admin_id, f"📩 @{username} (ID: {user_id})\n🏷 Стикер")
            send_message(chat_id, "✅ Сообщение отправлено администраторам")
        else:
            send_message(chat_id, "❌ Администраторов сейчас нет. Как только появится админ — мы отправим ваше сообщение.")

# ========== ОБРАБОТКА КНОПОК ==========
def process_callback(callback):
    chat_id = callback.get("message", {}).get("chat", {}).get("id")
    user_id = callback.get("from", {}).get("id")
    data = callback.get("data", "")
    
    if data.startswith("accept_"):
        admin_id = int(data.split("_")[1])
        if user_id in pending_requests:
            admin_tag = pending_requests[user_id].get("admin_tag", OWNER_TAG)
            send_message(chat_id, "✅ <b>ПРИГЛАШЕНИЕ ПРИНЯТО</b>\n\nТеперь придумайте свой <b>ТЕГ</b> (любое имя, например: Support, Admin, JODIK):")
            admin_temp_data[user_id] = {"step": "waiting_new_admin_tag"}
            send_message(admin_id, f"✅ ПОЛЬЗОВАТЕЛЬ @{pending_requests[user_id]['username']} СОГЛАСИЛСЯ СТАТЬ АДМИНИСТРАТОРОМ!")
            del pending_requests[user_id]
        else:
            send_message(chat_id, "❌ Запрос уже обработан или устарел.")
        return True
    
    elif data.startswith("decline_"):
        admin_id = int(data.split("_")[1])
        if user_id in pending_requests:
            send_message(chat_id, "❌ <b>ОТКАЗ ОТ ПРИГЛАШЕНИЯ</b>\n\nВы отказались стать администратором бота JODIK.")
            send_message(admin_id, f"❌ ПОЛЬЗОВАТЕЛЬ @{pending_requests[user_id]['username']} ОТКАЗАЛСЯ СТАТЬ АДМИНИСТРАТОРОМ.")
            del pending_requests[user_id]
        else:
            send_message(chat_id, "❌ Запрос уже обработан или устарел.")
        return True
    
    return False

# ========== ЗАПУСК БОТА ==========
def run_bot():
    global last_update_id
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    print("🔄 Бот JODIK запущен...")
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
                    if "callback_query" in update:
                        process_callback(update["callback_query"])
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
    print("✅ Бот JODIK успешно запущен!")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
