from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


@csrf_exempt
def feedback_send(request):
    """Feedback yuborish - oddiy Django view"""
    from .models import Feedback
    
    # Faqat POST qabul qilish
    if request.method != 'POST':
        return JsonResponse({'error': 'Faqat POST'}, status=405)
    
    # Xabarni olish
    message = ''
    if request.POST:
        message = request.POST.get('message', '')
    if not message and request.body:
        try:
            body = request.body.decode('utf-8')
            for part in body.split('&'):
                if part.startswith('message='):
                    message = part[8:].replace('+', ' ')
                    break
        except:
            pass
    
    if not message:
        return JsonResponse({'error': 'Xabar kerak'}, status=400)
    
    # User ni olish
    user = None
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Token '):
        try:
            token = Token.objects.get(key=auth[6:])
            user = token.user
        except:
            pass
    
    # Rasmni olish
    image = None
    if request.FILES:
        image = request.FILES.get('image')
    
    # Ma'lumotlarni olish
    first_name = 'Mehmon'
    last_name = ''
    user_phone = None
    
    if request.POST:
        first_name = request.POST.get('first_name') or first_name
        last_name = request.POST.get('last_name') or ''
        user_phone = request.POST.get('phone') or None
    
    if user:
        first_name = user.first_name or first_name
        last_name = user.last_name or ''
        user_phone = user.phone or user_phone
    
    user_name = f"{first_name} {last_name}".strip() or 'Mehmon'
    
    # Feedback yaratish
    feedback = Feedback.objects.create(
        user=user,
        user_name=user_name,
        user_phone=user_phone,
        message=message,
        image=image,
    )
    
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