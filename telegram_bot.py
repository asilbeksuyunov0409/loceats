#!/usr/bin/env python3
"""
LocEats Telegram Bot
Fikr-mulohazalarni qabul qilish va javob berish

Ishga tushirish:
    python telegram_bot.py

Bot komandalari:
    /start - Botni ishga tushirish
    /feedbacks - Oxirgi fikr-mulohazalar ro'yxati
    /reply [id] [xabar] - Javob berish (eski usul)
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

# Xabarlarni saqlash uchun lug'at (keyinchalik database ga o'tkaziladi)
# Key: telegram_message_id, Value: feedback_id
telegram_to_feedback = {}

def log(msg):
    """Log xabarlarini chiqarish"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def send_message(chat_id, text, reply_to_message_id=None):
    """Telegramga xabar yuborish"""
    try:
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
        if reply_to_message_id:
            data['reply_to_message_id'] = reply_to_message_id
        resp = requests.post(f'{BOT_URL}/sendMessage', json=data, timeout=10)
        
        # Bot yuborgan xabarning ID sini olish (javob berish uchun kerak)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                msg_id = result.get('result', {}).get('message_id')
                return msg_id
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

def send_feedback_to_telegram(feedback_id, user_name, phone, message, time_str):
    """Fikr-mulohazani Telegramga yuborish va javob uchun tayyorlash"""
    admin_chat_id = get_admin_chat_id()
    if not admin_chat_id:
        return None
    
    text = f"📩 *Yangi Fikr-mulohaza!*\n\n"
    text += f"👤 *Ism:* {user_name}\n"
    text += f"📱 *Telefon:* {phone}\n"
    text += f"💬 *Xabar:*\n{message}\n\n"
    text += f"🕐 *Vaqt:* {time_str}\n\n"
    text += f"Javob berish uchun shu xabarni cherting!"
    
    msg_id = send_message(admin_chat_id, text)
    
    if msg_id:
        telegram_to_feedback[msg_id] = feedback_id
        log(f"Feedback #{feedback_id} Telegramga yuborildi (msg_id: {msg_id})")
    
    return msg_id

def reply_to_feedback(feedback_id, reply_text):
    """Feedback ga javob berish va foydalanuvchiga yuborish"""
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
        
        msg += "\n📝 Javob berish: xabarni chertib javob yozing, yoki\n"
        msg += "/reply [id] [xabar]"
        return msg
    except Exception as e:
        return f"Xato: {e}"

def handle_command(chat_id, command, args, reply_to_msg_id=None):
    """Bot komandalarini ishga tushirish"""
    command = command.lower()
    
    if command == '/start':
        save_admin_chat_id(chat_id)
        msg = "👋 *LocEats Botga xush kelibsiz!*\n\n"
        msg += "Bu bot fikr-mulohazalarni qabul qiladi va javob berish imkonini beradi.\n\n"
        msg += "📋 *Foydalanish:*\n"
        msg += "• Yangi fikr-mulohaza kelganda, shu xabarni cherting\n"
        msg += "• Va javob yozing - avtomatik saqlanadi!\n\n"
        msg += "📝 *Komandalar:*\n"
        msg += "/feedbacks - Ro'yxat\n"
        msg += "/help - Yordam"
        send_message(chat_id, msg)
        return True
    
    elif command == '/feedbacks':
        msg = list_feedbacks()
        send_message(chat_id, msg)
        return True
    
    elif command == '/help':
        msg = "📖 *Yordam:*\n\n"
        msg += "1. Yangi fikr-mulohaza kelganda shu xabarni CHERTING\n"
        msg += "2. Javob yozing - avtomatik foydalanuvchiga yuboriladi!\n\n"
        msg += "Yoki komanda bilan:\n"
        msg += "/reply [id] [xabar]"
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
    msg_id = msg.get('message_id')
    reply_to = msg.get('reply_to_message')
    
    if not chat_id:
        return False
    
    admin_chat_id = get_admin_chat_id()
    
    # Agar bu admin bo'lmasa
    if str(chat_id) != str(admin_chat_id):
        send_message(chat_id, "🤖 Bu bot LocEats adminlari uchun. /start buyrug'ini bering.")
        return True
    
    # Agar xabar boshqa xabarga javob bo'lsa (eng muhim!)
    if reply_to:
        original_msg_id = reply_to.get('message_id')
        
        # Bu xabar biz yuborgan feedback xabari edimi?
        if original_msg_id in telegram_to_feedback:
            feedback_id = telegram_to_feedback[original_msg_id]
            success, result = reply_to_feedback(feedback_id, text)
            
            if success:
                send_message(chat_id, f"✅ Javob saqlandi va foydalanuvchiga yuborildi!", original_msg_id)
                log(f"Feedback #{feedback_id} ga javob berildi (reply): {text[:50]}...")
            else:
                send_message(chat_id, f"❌ {result}", original_msg_id)
            return True
        else:
            # Bu biz yuborgan xabar emas, lekin reply qilingan
            # ID sini ajratib ko'rishga harakat qilamiz
            original_text = reply_to.get('text', '')
            if '#' in original_text:
                for word in original_text.split():
                    if word.startswith('#') and word[1:].isdigit():
                        feedback_id = int(word[1:])
                        success, result = reply_to_feedback(feedback_id, text)
                        if success:
                            send_message(chat_id, f"✅ Javob saqlandi!", original_msg_id)
                        else:
                            send_message(chat_id, f"❌ {result}", original_msg_id)
                        return True
            
            send_message(chat_id, "❌ Bu xabarga javob berib bo'lmaydi. /help ko'ring.", original_msg_id)
            return True
    
    # Komanda bo'lsa
    if text.startswith('/'):
        parts = text.strip().split(' ', 1)
        command = parts[0]
        args_text = parts[1] if len(parts) > 1 else ''
        args = args_text.split(' ') if args_text else []
        
        return handle_command(chat_id, command, args)
    
    # Oddiy xabar
    send_message(chat_id, "📩 Xabar qabul qilindi.\n\nJavob berish uchun fikr-mulohaza xabarni cherting, yoki /help yozing.")
    return True

def poll_updates():
    """Telegram getUpdates ni tekshirib turish"""
    offset = None
    
    admin_id = get_admin_chat_id()
    admin_display = admin_id if admin_id else "Hali o'rnatilmagan"
    
    log("Bot ishga tushdi...")
    log(f"Admin chat_id: {admin_display}")

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