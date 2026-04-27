from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


@csrf_exempt
@require_POST
def feedback_send(request):
    from users.models import Feedback
    
    message = ''
    if request.POST:
        message = request.POST.get('message', '')
    
    if not message:
        return JsonResponse({'error': 'Xabar kerak'}, status=400)
    
    user = None
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Token '):
        try:
            token = Token.objects.get(key=auth[6:])
            user = token.user
        except:
            pass
    
    image = None
    if request.FILES:
        image = request.FILES.get('image')
    
    first_name = request.POST.get('first_name', 'Mehmon')
    last_name = request.POST.get('last_name', '')
    user_phone = request.POST.get('phone', '')
    
    if user:
        first_name = user.first_name or first_name
        last_name = user.last_name or last_name
        user_phone = user.phone or user_phone
    
    feedback = Feedback.objects.create(
        user=user,
        user_name=f"{first_name} {last_name}".strip(),
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
        }, status=201)
    return Response({'error': serializer.errors}, status=400)


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
    return Response({'error': serializer.errors}, status=400)


@api_view(['GET'])
def me(request):
    if request.user.is_authenticated:
        return Response(UserSerializer(request.user).data)
    return Response({'error': 'Tizimga kirmagan'}, status=401)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user(request):
    if request.data.get('first_name'):
        request.user.first_name = request.data['first_name']
    if request.data.get('last_name'):
        request.user.last_name = request.data['last_name']
    if request.data.get('phone'):
        request.user.phone = request.data['phone']
    request.user.save()
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
def reply_to_feedback(request):
    from users.models import Feedback
    feedback_id = request.data.get('feedback_id')
    reply = request.data.get('reply', '')
    
    if not feedback_id or not reply:
        return Response({'error': 'Kerakli maydonlar yoq'}, status=400)
    
    try:
        feedback = Feedback.objects.get(id=feedback_id)
        feedback.admin_reply = reply
        feedback.is_replied = True
        feedback.save()
        return Response({'success': True})
    except Feedback.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_feedbacks(request):
    from users.models import Feedback
    
    phone = request.query_params.get('phone')
    feedbacks = Feedback.objects.filter(user=request.user)
    
    if phone and not feedbacks.exists():
        feedbacks = Feedback.objects.filter(user_phone=phone)
    
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