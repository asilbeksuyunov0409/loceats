import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loceats.settings')
django.setup()

import json
import requests
from restaurants.models import AppSettings

BOT_TOKEN = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
BOT_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

def get_admin_chat_id():
    setting = AppSettings.objects.filter(key='admin_telegram_chat_id').first()
    if setting and setting.value:
        return setting.value
    return None

def set_admin_chat_id(chat_id):
    AppSettings.objects.update_or_create(key='admin_telegram_chat_id', defaults={'value': str(chat_id)})

def send_message(chat_id, text):
    if not chat_id:
        return False
    try:
        resp = requests.post(f'{BOT_URL}/sendMessage', json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }, timeout=10)
        return resp.status_code == 200
    except:
        return False

def handle_update(update):
    if 'message' in update:
        msg = update['message']
        chat = msg['chat']
        chat_id = chat['id']
        text = msg.get('text', '')
        
        # /start komandasi - admin chat_id ni saqlash
        if text == '/start':
            set_admin_chat_id(chat_id)
            send_message(chat_id, "👋 LocEats Admin botiga xush kelibsiz!\n\nFikr-mulohazalarni ko'rish va javob berish uchun tayyor:")
            return True
        
        # /reply komandasi - javob berish
        if text.startswith('/reply '):
            parts = text[7:].split(' ', 1)
            if len(parts) >= 2:
                feedback_id = parts[0]
                reply_text = parts[1]
                try:
                    from users.models import Feedback
                    feedback = Feedback.objects.get(id=int(feedback_id))
                    feedback.admin_reply = reply_text
                    feedback.is_replied = True
                    feedback.save()
                    send_message(chat_id, f"✅ Javob yozildi (ID: {feedback_id}):\n{reply_text}")
                except:
                    send_message(chat_id, "❌ Xatolik: Feedback topilmadi")
                return True
        
        # Oddiy xabar - adminga bildirish
        if text.startswith('/feedbacks'):
            from users.models import Feedback
            feedbacks = Feedback.objects.filter(is_replied=False).order_by('-created_at')[:5]
            if feedbacks:
                msg = "📋 Oxirgi fikr-mulohazalar:\n\n"
                for fb in feedbacks:
                    msg += f"#{fb.id} - {fb.user_name or 'Nomalum'}\n"
                    msg += f"   {fb.message[:50]}...\n\n"
                send_message(chat_id, msg)
            else:
                send_message(chat_id, "📭 Hali fikr-mulohazalar yo'q")
            return True
        
        # Oddiy xabarni adminga ko'rsatish
        send_message(chat_id, "📩 Xabar qabul qilindi. Boshqa komanda sinab ko'ring:\n/reply [id] [xabar] - javob berish\n/feedbacks - ro'yxat")
        return True
    
    return False

def poll_updates():
    offset = None
    while True:
        try:
            params = {'timeout': 30}
            if offset:
                params['offset'] = offset
            
            resp = requests.get(f'{BOT_URL}/getUpdates', params=params, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('ok'):
                    for update in data['result']:
                        offset = update['update_id'] + 1
                        handle_update(update)
        except Exception as e:
            print(f"Xatolik: {e}")

if __name__ == '__main__':
    print("LocEats Telegram Bot ishga tushdi...")
    poll_updates()