#!/usr/bin/env python3
"""
LocEats Telegram Bot
Fikr-mulohazalarni qabul qilish va javob berish

Ishga tushirish:
    python telegram_bot.py

Bot komandalari:
    /start - Botni ishga tushirish
    /feedbacks - Oxirgi fikr-mulohazalar ro'yxati
    /reply [id] [xabar] - Javob berish
"""

import os
import sys
import django
import time
import requests
from datetime import datetime

# Django sozlamalari
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loceats.settings')

# Loyiha papkasiga o'tish
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)
django.setup()

# Telegram Bot sozlamalari
BOT_TOKEN = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
BOT_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

def log(msg):
    """Log xabarlarini chiqarish"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def send_message(chat_id, text, reply_markup=None):
    """Telegramga xabar yuborish"""
    try:
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
        if reply_markup:
            data['reply_markup'] = reply_markup
        resp = requests.post(f'{BOT_URL}/sendMessage', json=data, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        log(f"Xabar yuborishda xato: {e}")
        return False

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
        
        try:
            feedback = Feedback.objects.get(id=int(feedback_id))
        except Feedback.DoesNotExist:
            return False, "Feedback topilmadi"
        
        feedback.admin_reply = reply_text
        feedback.is_replied = True
        feedback.save()
        
        log(f"Feedback #{feedback_id} ga javob berildi: {reply_text[:50]}...")
        return True, "Javob saqlandi"
    except Exception as e:
        return False, f"Xato: {e}"

def list_feedbacks():
    """Oxirgi fikr-mulohazalarni ro'yxatini olish"""
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
            msg += f"#{fb.id} [{time_str}]\n"
            msg += f"👤 {name}\n"
            msg += f"💬 {message}\n\n"
        
        msg += "\n📝 Javob berish: /reply [id] [xabar]"
        return msg
    except Exception as e:
        return f"Xato: {e}"

def handle_command(chat_id, command, args):
    """Bot komandalarini ishga tushirish"""
    command = command.lower()
    
    if command == '/start':
        save_admin_chat_id(chat_id)
        msg = "👋 *LocEats Botga xush kelibsiz!*\n\n"
        msg += "Bu bot fikr-mulohazalarni qabul qiladi va javob berish imkonini beradi.\n\n"
        msg += "📋 *Komandalar:*\n"
        msg += "/feedbacks - Javobsiz fikr-mulohazalar\n"
        msg += "/reply [id] [xabar] - Javob berish\n"
        msg += "/start - Qayta boshlash"
        send_message(chat_id, msg)
        return True
    
    elif command == '/feedbacks':
        msg = list_feedbacks()
        send_message(chat_id, msg)
        return True
    
    elif command == '/reply':
        if len(args) < 2:
            send_message(chat_id, "❌ Format: /reply [id] [xabar]\n\nMasalan: /reply 5 Rahmat, yaxshi ish!")
            return True
        
        feedback_id = args[0]
        reply_text = ' '.join(args[1:])
        
        success, result = reply_to_feedback(feedback_id, reply_text)
        if success:
            send_message(chat_id, f"✅ {result}")
        else:
            send_message(chat_id, f"❌ {result}")
        return True
    
    return False

def handle_message(update):
    """Xabarni qayta ishlash"""
    msg = update.get('message', {})
    chat = msg.get('chat', {})
    text = msg.get('text', '')
    
    chat_id = chat.get('id')
    if not chat_id:
        return False
    
    # Komandani ajratish
    parts = text.strip().split(' ', 1)
    command = parts[0]
    args_text = parts[1] if len(parts) > 1 else ''
    args = args_text.split(' ') if args_text else []
    
    if command.startswith('/'):
        return handle_command(chat_id, command, args)
    
    # Oddiy xabar - admin ekanligini tekshirish
    admin_chat_id = get_admin_chat_id()
    if str(chat_id) != str(admin_chat_id):
        send_message(chat_id, "🤖 Bu bot faqat LocEats adminlari uchun. /start buyrug'ini bering.")
        return True
    
    send_message(chat_id, "📩 Xabar qabul qilindi. /help buyrug'ini berib ko'ring.")
    return True

def poll_updates():
    """Telegram getUpdates ni tekshirib turish"""
    offset = None
    
    admin_id = get_admin_chat_id()
    admin_display = admin_id if admin_id else "Hali o'rnatilmagan"
    
    log("Bot ishga tushdi...")
    log(f"Admin chat_id: {admin_display}")
    
    while True:
        try:
            params = {'timeout': 30}
            if offset:
                params['offset'] = offset
            
            resp = requests.get(f'{BOT_URL}/getUpdates', params=params, timeout=35)
            
            if resp.status_code != 200:
                log(f"API xato: {resp.status_code}")
                time.sleep(5)
                continue
            
            data = resp.json()
            if not data.get('ok'):
                log(f"API xato: {data}")
                time.sleep(5)
                continue
            
            updates = data.get('result', [])
            if not updates:
                continue
            
            for update in updates:
                update_id = update.get('update_id')
                
                # Xabarni qayta ishlash
                if 'message' in update:
                    handle_message(update)
                
                # Keyingi update uchun offset
                offset = update_id + 1
            
            # Ishga tushirilganda barcha pending updatelarni o'qish
            if not offset:
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