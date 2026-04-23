from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

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


@api_view(['POST'])
def submit_feedback(request):
    from .models import Feedback
    
    message = request.data.get('message', '')
    image = request.FILES.get('image')
    user = request.user if request.user.is_authenticated else None
    
    if not message:
        return Response({'error': 'Xabar bo\'sh bo\'lishi mumkin'}, status=status.HTTP_400_BAD_REQUEST)
    
    feedback = Feedback.objects.create(
        user=user,
        user_name=f"{request.data.get('first_name', '')} {request.data.get('last_name', '')}".strip() or (f"{user.first_name} {user.last_name}" if user and (user.first_name or user.last_name) else None),
        user_phone=request.data.get('phone') or (user.phone if user else None),
        message=message,
        image=image,
    )
    
    try:
        import requests
        bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
        chat_id = '8433417347'
        
        user_display = feedback.user_name or "Nomalum"
        phone_display = feedback.user_phone or "Nomalum"
        
        text = f"📩 *Yangi Fikr-mulohaza!*\n\n"
        text += f"👤 *Ism:* {user_display}\n"
        text += f"📱 *Telefon:* {phone_display}\n"
        text += f"💬 *Xabar:*\n{feedback.message}\n\n"
        text += f"🕐 *Vaqt:* {feedback.created_at.strftime('%Y-%m-%d %H:%M')}"
        
        requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
            timeout=10,
        )
    except Exception as e:
        print(f"Telegram xato: {e}")
    
    return Response({'success': True, 'id': feedback.id})


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_feedbacks(request):
    from .models import Feedback
    
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
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
