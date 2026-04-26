from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

# Regular Django view for feedback with file upload
@csrf_exempt
@require_POST
def submit_feedback_simple(request):
    from .models import Feedback
    
    message = request.POST.get('message', '') or ''
    
    if not message:
        return JsonResponse({'error': 'Xabar yoq'}, status=400)
    
    # Get user from token
    auth_header = request.headers.get('Authorization', '')
    user = None
    if auth_header.startswith('Token '):
        token_key = auth_header[6:]
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except:
            pass
    
    image = request.FILES.get('image')
    
    first_name = request.POST.get('first_name') or (user.first_name if user else 'Mehmon')
    last_name = request.POST.get('last_name') or (user.last_name if user else '')
    user_name = f"{first_name} {last_name}".strip()
    user_phone = request.POST.get('phone') or (user.phone if user else None)
    
    feedback = Feedback.objects.create(
        user=user,
        user_name=user_name,
        user_phone=user_phone,
        message=message,
        image=image,
    )
    
    # Telegram botga yuborish
    try:
        admin_chat_id = None
        from restaurants.models import AppSettings
        setting = AppSettings.objects.filter(key='admin_telegram_chat_id').first()
        if setting and setting.value:
            admin_chat_id = setting.value
        
        if admin_chat_id:
            import requests
            bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
            
            user_display = feedback.user_name or "Nomalum"
            phone_display = feedback.user_phone or "Nomalum"
            time_str = feedback.created_at.strftime('%Y-%m-%d %H:%M')
            
            text = f"📩 Yangi Fikr-mulohaza!\n\n"
            text += f"Ism: {user_display}\n"
            text += f"Telefon: {phone_display}\n"
            text += f"Xabar: {message[:200]}\n"
            text += f"Vaqt: {time_str}"
            
            requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json={'chat_id': admin_chat_id, 'text': text},
                timeout=10,
            )
    except:
        pass
    
    return JsonResponse({'success': True, 'id': feedback.id})


@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

# Regular Django view for feedback with file upload
@csrf_exempt
@require_POST
def submit_feedback_simple(request):
    from .models import Feedback
    
    message = request.POST.get('message', '') or ''
    
    if not message:
        return JsonResponse({'error': 'Xabar bo\'sh bo\'lishi mumkin'}, status=400)
    
    # Get message from body if posted as raw text (for multipart)
    if not message and request.body:
        try:
            body_str = request.body.decode('utf-8')
            for line in body_str.split('&'):
                if line.startswith('message='):
                    message = line.split('=')[1]
                    message = message.replace('+', ' ')
                    break
        except:
            pass
    
    # Get user from token
    auth_header = request.headers.get('Authorization', '')
    user = None
    if auth_header.startswith('Token '):
        token_key = auth_header[6:]
        from rest_framework.authtoken.models import Token
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except:
            pass
    
    image = request.FILES.get('image')
    
    first_name = request.POST.get('first_name') or (user.first_name if user else 'Mehmon')
    last_name = request.POST.get('last_name') or (user.last_name if user else '')
    user_name = f"{first_name} {last_name}".strip()
    user_phone = request.POST.get('phone') or (user.phone if user else None)
    
    feedback = Feedback.objects.create(
        user=user,
        user_name=user_name,
        user_phone=user_phone,
        message=message,
        image=image,
    )
    
    # Telegram botga yuborish
    try:
        admin_chat_id = None
        from restaurants.models import AppSettings
        setting = AppSettings.objects.filter(key='admin_telegram_chat_id').first()
        if setting and setting.value:
            admin_chat_id = setting.value
        
        if admin_chat_id:
            import requests
            bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
            
            user_display = feedback.user_name or "Nomalum"
            phone_display = feedback.user_phone or "Nomalum"
            time_str = feedback.created_at.strftime('%Y-%m-%d %H:%M')
            
            text = f"📩 *Yangi Fikr-mulohaza!*\n\n"
            text += f"👤 *Ism:* {user_display}\n"
            text += f"📱 *Telefon:* {phone_display}\n"
            text += f"💬 *Xabar:*\n{feedback.message[:200]}\n\n"
            text += f"🕐 *Vaqt:* {time_str}"
            
            requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json={'chat_id': admin_chat_id, 'text': text, 'parse_mode': 'Markdown'},
                timeout=10,
            )
    except:
        pass
    
    return JsonResponse({'success': True, 'id': feedback.id})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
    from .models import Feedback
    
    message = request.data.get('message') or ''
    user = request.user
    
    if not message:
        return Response({'error': 'Xabar bo\'sh bo\'lishi mumkin'}, status=status.HTTP_400_BAD_REQUEST)
    
    image = request.FILES.get('image') if request.FILES else None
    
    first_name = request.data.get('first_name') or (user.first_name if user else 'Mehmon')
    last_name = request.data.get('last_name') or (user.last_name if user else '')
    user_name = f"{first_name} {last_name}".strip() or (f"{user.first_name} {user.last_name}" if user else None)
    user_phone = request.data.get('phone') or (user.phone if user else None)
    
    feedback = Feedback.objects.create(
        user=user,
        user_name=user_name,
        user_phone=user_phone,
        message=message,
        image=image,
    )
    
    # Telegram botga yuborish
    try:
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            import requests
            bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
            
            user_display = feedback.user_name or "Nomalum"
            phone_display = feedback.user_phone or "Nomalum"
            time_str = feedback.created_at.strftime('%Y-%m-%d %H:%M')
            
            text = f"📩 *Yangi Fikr-mulohaza!*\n\n"
            text += f"👤 *Ism:* {user_display}\n"
            text += f"📱 *Telefon:* {phone_display}\n"
            text += f"💬 *Xabar:*\n{feedback.message}\n\n"
            text += f"🕐 *Vaqt:* {time_str}\n\n"
            text += f"Shu xabarni CHERTING va javob yozing!"
            
            resp = requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json={'chat_id': admin_chat_id, 'text': text, 'parse_mode': 'Markdown'},
                timeout=10,
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get('ok'):
                    msg_id = result.get('result', {}).get('message_id')
                    # JSON faylga saqlash
                    import json as json_module
                    import os
                    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    msg_file = os.path.join(project_dir, 'feedback_msg_ids.json')
                    data = {}
                    try:
                        if os.path.exists(msg_file):
                            with open(msg_file, 'r') as f:
                                data = json_module.load(f)
                    except:
                        pass
                    data[str(msg_id)] = feedback.id
                    try:
                        with open(msg_file, 'w') as f:
                            json_module.dump(data, f)
                    except:
                        pass
    except Exception as e:
        print(f"Telegram xato: {e}")
    
    return Response({'success': True, 'id': feedback.id})

@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def me(request):
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data)
    return Response({'error': 'Tizimga kirmagan'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone = request.data.get('phone')
    
    if first_name:
        request.user.first_name = first_name
    if last_name:
        request.user.last_name = last_name
    if phone:
        request.user.phone = phone
    
    request.user.save()
    return Response(UserSerializer(request.user).data)


def get_admin_chat_id():
    """Admin Telegram chat_id sini olish"""
    admin_chat_id = None
    
    # 1. AppSettings dan olish
    try:
        from restaurants.models import AppSettings
        setting = AppSettings.objects.filter(key='admin_telegram_chat_id').first()
        if setting and setting.value:
            admin_chat_id = setting.value
    except:
        pass
    
    # 2. getUpdates dan olish (oxirgi xabar berguvchi)
    if not admin_chat_id:
        try:
            import requests
            bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
            updates = requests.get(f'https://api.telegram.org/bot{bot_token}/getUpdates', timeout=5)
            if updates.status_code == 200:
                for update in updates.json().get('result', []):
                    msg = update.get('message', {})
                    chat = msg.get('chat', {})
                    if chat.get('id') and not chat.get('is_bot'):
                        admin_chat_id = str(chat['id'])
                        # AppSettings ga saqlash
                        try:
                            AppSettings.objects.update_or_create(
                                key='admin_telegram_chat_id',
                                defaults={'value': admin_chat_id}
                            )
                        except:
                            pass
                        break
        except:
            pass
    
    return admin_chat_id


@api_view(['POST'])
def reply_to_feedback(request):
    from .models import Feedback
    
    feedback_id = request.data.get('feedback_id')
    reply = request.data.get('reply', '')
    
    if not feedback_id or not reply:
        return Response({'error': 'feedback_id va reply kerak'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        feedback.admin_reply = reply
        feedback.is_replied = True
        feedback.save()
        
        if feedback.telegram_chat_id:
            try:
                import requests
                bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
                requests.post(
                    f'https://api.telegram.org/bot{bot_token}/sendMessage',
                    json={'chat_id': feedback.telegram_chat_id, 'text': f"📬 *Javob:*\n{reply}", 'parse_mode': 'Markdown'},
                    timeout=10,
                )
            except Exception as e:
                print(f"Telegram xato: {e}")
        
        return Response({'success': True})
    except Feedback.DoesNotExist:
        return Response({'error': 'Feedback topilmadi'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_feedbacks(request):
    from .models import Feedback
    
    user_phone = request.query_params.get('phone')
    if not user_phone:
        user_phone = request.user.phone if hasattr(request.user, 'phone') and request.user.phone else None
    
    feedbacks = Feedback.objects.filter(user=request.user) if request.user.is_authenticated else Feedback.objects.none()
    
    if user_phone and not feedbacks.exists():
        feedbacks = Feedback.objects.filter(user_phone=user_phone)
    
    feedbacks = feedbacks.order_by('-created_at')
    data = []
    for f in feedbacks:
        data.append({
            'id': f.id,
            'message': f.message,
            'admin_reply': f.admin_reply,
            'is_replied': f.is_replied,
            'image': f.image.url if f.image else None,
            'created_at': f.created_at.isoformat(),
        })
    return Response(data)
