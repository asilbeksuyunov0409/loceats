#!/usr/bin/env python3
"""
LocEats Telegram Bot
Fikr-mulohazalarni qabul qilish va javob berish
"""

import os
import sys
import json
import django
import time
import requests
from datetime import datetime

# Django sozlamalari
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loceats.settings')

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)
django.setup()

# Telegram Bot sozlamalari
BOT_TOKEN = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
BOT_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# JSON fayl orqali message ID larni saqlash
MSG_ID_FILE = os.path.join(project_dir, 'feedback_msg_ids.json')

def load_msg_ids():
    """JSON dan message ID larni o'qish"""
    try:
        if os.path.exists(MSG_ID_FILE):
            with open(MSG_ID_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_msg_ids(data):
    """JSON ga message ID larni saqlash"""
    try:
        with open(MSG_ID_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def add_msg_id(telegram_msg_id, feedback_id):
    """Yangi message ID qo'shish"""
    data = load_msg_ids()
    data[str(telegram_msg_id)] = feedback_id
    save_msg_ids(data)

def get_feedback_id(telegram_msg_id):
    """Telegram message ID dan feedback ID olish"""
    data = load_msg_ids()
    return data.get(str(telegram_msg_id))

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def send_message(chat_id, text, reply_to_message_id=None):
    """Telegramga xabar yuborish"""
    try:
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
        if reply_to_message_id:
            data['reply_to_message_id'] = reply_to_message_id
        resp = requests.post(f'{BOT_URL}/sendMessage', json=data, timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                return result.get('result', {}).get('message_id')
        return None
    except Exception as e:
        log(f"Xabar yuborishda xato: {e}")
        return None

def save_admin_chat_id(chat_id):
    """Admin chat_id ni bazaga saqlash"""
    try:
        from restaurants.models import AppSettings
        AppSettings.objects.update_or_create(
            key='admin_telegram_chat_id',
            defaults={'value': str(chat_id)}
        )
        log(f"Admin chat_id saqlandi: {chat_id}")
        return True
    except Exception as e:
        log(f"Chat ID saqlashda xato: {e}")
        return False

def get_admin_chat_id():
    """Admin chat_id ni bazadan olish"""
    try:
        from restaurants.models import AppSettings
        setting = AppSettings.objects.filter(key='admin_telegram_chat_id').first()
        return setting.value if setting and setting.value else None
    except:
        return None

def reply_to_feedback(feedback_id, reply_text):
    """Feedback ga javob berish"""
    try:
        from users.models import Feedback
        feedback = Feedback.objects.get(id=int(feedback_id))
        feedback.admin_reply = reply_text
        feedback.is_replied = True
        feedback.save()
        log(f"Feedback #{feedback_id} ga javob berildi: {reply_text[:50]}...")
        return True, "Javob saqlandi!"
    except Exception as e:
        return False, f"Xato: {e}"

def send_feedback_to_telegram(feedback_id, user_name, phone, message, time_str):
    """Fikr-mulohazani Telegramga yuborish"""
    admin_chat_id = get_admin_chat_id()
    if not admin_chat_id:
        log("Admin chat_id topilmadi")
        return None
    
    text = f"📩 *Yangi Fikr-mulohaza!*\n\n"
    text += f"👤 *Ism:* {user_name}\n"
    text += f"📱 *Telefon:* {phone}\n"
    text += f"💬 *Xabar:*\n{message}\n\n"
    text += f"🕐 *Vaqt:* {time_str}\n\n"
    text += f"Shu xabarni CHERTING va javob yozing!"
    
    msg_id = send_message(admin_chat_id, text)
    
    if msg_id:
        add_msg_id(msg_id, feedback_id)
        log(f"Feedback #{feedback_id} Telegramga yuborildi (msg_id: {msg_id})")
    
    return msg_id

def list_feedbacks():
    """Oxirgi fikr-mulohazalar ro'yxati"""
    try:
        from users.models import Feedback
        feedbacks = Feedback.objects.filter(is_replied=False).order_by('-created_at')[:10]
        
        if not feedbacks:
            return "📭 Hali javobsiz fikr-mulohazalar yo'q"
        
        msg = "📋 *Javobsiz Fikr-mulohazalar:*\n\n"
        for fb in feedbacks:
            name = fb.user_name or "Nomalum"
            message = fb.message[:60] + "..." if len(fb.message) > 60 else fb.message
            time_str = fb.created_at.strftime('%d.%m %H:%M')
            msg += f"#{fb.id} [{time_str}]\n👤 {name}\n💬 {message}\n\n"
        
        msg += "\nJavob berish: xabarni cherting yoki /reply [id] [xabar]"
        return msg
    except Exception as e:
        return f"Xato: {e}"

def handle_message(update):
    """Xabarni qayta ishlash"""
    msg = update.get('message', {})
    chat = msg.get('chat', {})
    text = msg.get('text', '')
    
    chat_id = chat.get('id')
    msg_id = msg.get('message_id')
    reply_to = msg.get('reply_to_message')
    
    if not chat_id:
        return False
    
    admin_chat_id = get_admin_chat_id()
    
    # Admin ekanligini tekshirish
    if str(chat_id) != str(admin_chat_id):
        if text == '/start':
            save_admin_chat_id(chat_id)
            send_message(chat_id, "👋 *LocEats Botga xush kelibsiz!*\n\nFikr-mulohazalarni shu yerdan ko'rishingiz va javob berishingiz mumkin.")
        else:
            send_message(chat_id, "🤖 Bu bot LocEats adminlari uchun. /start buyrug'ini bering.")
        return True
    
    # Reply (xabarni chertish)
    if reply_to:
        original_msg_id = reply_to.get('message_id')
        feedback_id = get_feedback_id(original_msg_id)
        
        if feedback_id:
            success, result = reply_to_feedback(feedback_id, text)
            if success:
                send_message(chat_id, "✅ Javob saqlandi!", original_msg_id)
            else:
                send_message(chat_id, f"❌ {result}", original_msg_id)
        else:
            send_message(chat_id, "❌ Bu xabarni aniqlab bo'lmaydi.", original_msg_id)
        return True
    
    # Komandalar
    if text.startswith('/'):
        if text == '/start':
            save_admin_chat_id(chat_id)
            msg = "👋 *LocEats Botga xush kelibsiz!*\n\n"
            msg += "📋 *Foydalanish:*\n"
            msg += "• Yangi fikr-mulohaza kelganda shu xabarni CHERTING\n"
            msg += "• Va javob yozing!\n\n"
            msg += "/feedbacks - Ro'yxat\n"
            msg += "/help - Yordam"
            send_message(chat_id, msg)
        elif text == '/feedbacks':
            send_message(chat_id, list_feedbacks())
        elif text == '/help':
            msg = "📖 *Yordam:*\n\n"
            msg += "1. Yangi xabar kelganda shu xabarni CHERTING (Reply)\n"
            msg += "2. Javob yozing - avtomatik saqlanadi!\n\n"
            msg += "Yoki: /reply [id] [xabar]"
            send_message(chat_id, msg)
        elif text.startswith('/reply '):
            parts = text[7:].split(' ', 1)
            if len(parts) >= 2:
                feedback_id, reply_text = parts
                success, result = reply_to_feedback(feedback_id, reply_text)
                send_message(chat_id, f"{'✅' if success else '❌'} {result}")
            else:
                send_message(chat_id, "❌ Format: /reply [id] [xabar]")
        return True
    
    # Oddiy xabar
    send_message(chat_id, "📩 Xabar qabul qilindi.\n\nJavob berish uchun fikr-mulohaza xabarni cherting.")
    return True

def poll_updates():
    """Telegram getUpdates ni tekshirib turish"""
    offset = None
    
    admin_id = get_admin_chat_id()
    log("Bot ishga tushdi...")
    log(f"Admin chat_id: {admin_id or 'Hali o\\'rnatilmagan'}")
    
    while True:
        try:
            params = {'timeout': 30}
            if offset:
                params['offset'] = offset
            
            resp = requests.get(f'{BOT_URL}/getUpdates', params=params, timeout=35)
            
            if resp.status_code != 200:
                time.sleep(5)
                continue
            
            data = resp.json()
            if not data.get('ok'):
                time.sleep(5)
                continue
            
            updates = data.get('result', [])
            if not updates:
                continue
            
            for update in updates:
                update_id = update.get('update_id')
                
                if 'message' in update:
                    handle_message(update)
                
                offset = update_id + 1
            
            if not offset and updates:
                offset = updates[-1].get('update_id', 0) + 1
            
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            log(f"Xato: {e}")
            time.sleep(5)

if __name__ == '__main__':
    print("=" * 50)
    print("LocEats Telegram Bot")
    print("=" * 50)
    print()
    print("To'xtatish uchun: Ctrl+C")
    print()
    
    try:
        poll_updates()
    except KeyboardInterrupt:
        print("\n\nBot to'xtatildi.")
        sys.exit(0)