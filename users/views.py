from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


@method_decorator(csrf_exempt)
class SubmitFeedbackView(View):
    def post(self, request):
        from .models import Feedback
        
        message = request.POST.get('message', '') or ''
        
        if not message:
            return JsonResponse({'error': 'Xabar yoq'}, status=400)
        
        auth_header = request.headers.get('Authorization', '') or request.META.get('HTTP_AUTHORIZATION', '')
        user = None
        if auth_header.startswith('Token '):
            token_key = auth_header[6:].strip()
            try:
                token = Token.objects.get(key=token_key)
                user = token.user
            except:
                pass
        
        image = request.FILES.get('image') if request.FILES else None
        
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
        
        try:
            admin_chat_id = None
            from restaurants.models import AppSettings
            setting = AppSettings.objects.filter(key='admin_telegram_chat_id').first()
            if setting and setting.value:
                admin_chat_id = setting.value
            
            if admin_chat_id:
                import requests
                bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
                text = f"Yangi Fikr-mulohaza!\nIsm: {user_name}\nTelefon: {user_phone or 'yoq'}\nXabar: {message[:100]}"
                requests.post(
                    f'https://api.telegram.org/bot{bot_token}/sendMessage',
                    json={'chat_id': admin_chat_id, 'text': text},
                    timeout=5,
                )
        except:
            pass
        
        return JsonResponse({'success': True, 'id': feedback.id})


submit_feedback_simple = SubmitFeedbackView.as_view()


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
    admin_chat_id = None
    try:
        from restaurants.models import AppSettings
        setting = AppSettings.objects.filter(key='admin_telegram_chat_id').first()
        if setting and setting.value:
            admin_chat_id = setting.value
    except:
        pass
    return admin_chat_id


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    from .models import Feedback
    
    message = request.data.get('message') or ''
    
    if not message:
        return Response({'error': 'Xabar yoq'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    first_name = request.data.get('first_name') or (user.first_name if user else 'Mehmon')
    last_name = request.data.get('last_name') or (user.last_name if user else '')
    user_name = f"{first_name} {last_name}".strip()
    user_phone = request.data.get('phone') or (user.phone if user else None)
    
    feedback = Feedback.objects.create(
        user=user,
        user_name=user_name,
        user_phone=user_phone,
        message=message,
    )
    
    return Response({'success': True, 'id': feedback.id})


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
            'image': f.image.url if f.image and f.image.name else None,
            'created_at': f.created_at.isoformat(),
        })
    return Response(data)