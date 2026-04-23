from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from datetime import timedelta
from .models import Category, Restaurant, Table, Booking, MenuCategory, MenuItem, Review, Order, OrderItem, AppSettings
from .serializers import (
    CategorySerializer, 
    RestaurantListSerializer, 
    RestaurantDetailSerializer,
    RestaurantWithMenuSerializer,
    TableSerializer,
    BookingSerializer,
    MenuCategorySerializer,
    MenuItemSerializer,
    ReviewSerializer,
    SearchResultSerializer,
    OrderSerializer,
    OrderCreateSerializer
)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def restaurant_list(request):
    if request.method == 'GET':
        restaurants = Restaurant.objects.filter(is_active=True)
        serializer = RestaurantListSerializer(restaurants, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RestaurantDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RestaurantDetailView(viewsets.ModelViewSet):
    queryset = Restaurant.objects.filter(is_active=True)
    serializer_class = RestaurantDetailSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_queryset(self):
        queryset = Restaurant.objects.filter(is_active=True)
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = RestaurantWithMenuSerializer(instance)
        return Response(serializer.data)

@api_view(['GET', 'POST'])
def category_list(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def menu_category_list(request):
    if request.method == 'GET':
        categories = MenuCategory.objects.all()
        serializer = MenuCategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = MenuCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def menu_item_list(request, restaurant_id=None):
    if request.method == 'GET':
        if restaurant_id:
            items = MenuItem.objects.filter(restaurant_id=restaurant_id, is_available=True)
        else:
            items = MenuItem.objects.filter(is_available=True)
        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        try:
            name = request.data.get('name')
            price = request.data.get('price')
            description = request.data.get('description', '')
            category_id = request.data.get('category')
            item_type = request.data.get('item_type', 'food')
            image = request.data.get('image')
            
            if not name or not price:
                return Response({'error': 'Name and price are required'}, status=400)
            
            restaurant = None
            if restaurant_id:
                restaurant = Restaurant.objects.get(id=restaurant_id)
            
            category = None
            if category_id:
                category = MenuCategory.objects.get(id=category_id)
            
            item = MenuItem.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                price=price,
                category=category,
                item_type=item_type,
                image=image,
                is_available=True
            )
            
            return Response({
                'id': item.id,
                'name': item.name,
                'price': str(item.price),
                'message': 'Success'
            }, status=201)
            
        except Restaurant.DoesNotExist:
            return Response({'error': 'Restaurant not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

@api_view(['GET', 'POST'])
def table_list(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restoran topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        tables = Table.objects.filter(restaurant=restaurant)
        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(restaurant=restaurant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def booking_list(request):
    if request.method == 'GET':
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def booking_detail(request, pk):
    try:
        booking = Booking.objects.get(pk=pk)
    except Booking.DoesNotExist:
        return Response({'error': 'Bandlik topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = BookingSerializer(booking)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = BookingSerializer(booking, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        booking.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def check_table_booking(request):
    restaurant_id = request.query_params.get('restaurant_id')
    table_id = request.query_params.get('table_id')
    phone = request.query_params.get('phone')
    
    if not restaurant_id or not table_id:
        return Response({'error': 'restaurant_id va table_id kerak'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        table = Table.objects.get(id=table_id, restaurant=restaurant)
    except (Restaurant.DoesNotExist, Table.DoesNotExist):
        return Response({'error': 'Restoran yoki stol topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    now = timezone.now()
    thirty_minutes_ago = now - timedelta(minutes=30)
    today = now.date()
    
    recent_bookings = Booking.objects.filter(
        restaurant=restaurant,
        table=table,
        booking_date=today,
        is_confirmed=True,
        booking_time__gte=thirty_minutes_ago.time()
    )
    
    if recent_bookings.exists():
        booking = recent_bookings.first()
        is_own_booking = phone and booking.customer_phone == phone
        
        return Response({
            'status': 'occupied',
            'booked': True,
            'is_own_booking': is_own_booking,
            'booking_id': booking.id,
            'customer_name': booking.customer_name,
            'customer_phone': booking.customer_phone,
            'guest_count': booking.guest_count,
            'booking_time': booking.booking_time.strftime('%H:%M'),
            'message': 'Bu stol yaqinda bron qilingan' if is_own_booking else 'Bu stol band'
        })
    
    if phone:
        user_bookings = Booking.objects.filter(
            restaurant=restaurant,
            booking_date=today,
            is_confirmed=True,
            customer_phone=phone
        )
        
        if user_bookings.exists():
            user_booking = user_bookings.first()
            if user_booking.table_id == int(table_id):
                return Response({
                    'status': 'confirmed',
                    'booked': True,
                    'is_own_booking': True,
                    'booking_id': user_booking.id,
                    'customer_name': user_booking.customer_name,
                    'booking_time': user_booking.booking_time.strftime('%H:%M'),
                    'message': 'Sizning broningiz tasdiqlandi'
                })
            else:
                return Response({
                    'status': 'different_table',
                    'booked': True,
                    'is_own_booking': True,
                    'booking_id': user_booking.id,
                    'booking_table_id': user_booking.table_id,
                    'booking_table_number': user_booking.table.table_number,
                    'scanned_table_id': int(table_id),
                    'scanned_table_number': table.table_number,
                    'message': f'Siz {user_booking.table.table_number} stolni bron qilgansiz'
                })
    
    return Response({
        'status': 'available',
        'booked': False,
        'message': 'Stol bo\'sh'
    })


@api_view(['GET', 'POST'])
def event_list(request):
    user_id = request.query_params.get('user_id')
    
    if request.method == 'GET':
        if user_id:
            events = QaniKetedikEvent.objects.filter(host_user_id=user_id)
            serializer = EventSerializer(events, many=True)
            return Response(serializer.data)
        
        events = QaniKetedikEvent.objects.all()[:20]
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        try:
            restaurant = Restaurant.objects.get(id=data.get('restaurant'))
            table = None
            if data.get('table'):
                table = Table.objects.get(id=data.get('table'), restaurant=restaurant)
            
            event = QaniKetedikEvent.objects.create(
                host_user_id=data.get('host_user_id'),
                host_name=data.get('host_name'),
                host_phone=data.get('host_phone'),
                title=data.get('title'),
                description=data.get('description', ''),
                restaurant=restaurant,
                table=table,
                event_date=data.get('event_date'),
                event_time=data.get('event_time'),
                max_guests=data.get('max_guests', 10),
            )
            
            # Bron yaratish
            booking = Booking.objects.create(
                restaurant=restaurant,
                table=table,
                customer_name=data.get('host_name'),
                customer_phone=data.get('host_phone'),
                booking_date=data.get('event_date'),
                booking_time=data.get('event_time'),
                guest_count=data.get('max_guests', 10),
                note=f"QaniKetdik: {event.title}",
                event=event,
            )
            
            return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def event_invite(request):
    event_id = request.data.get('event_id')
    guests = request.data.get('guests', [])
    
    try:
        event = QaniKetedikEvent.objects.get(id=event_id)
        created = []
        
        for guest in guests:
            invitation, is_new = EventInvitation.objects.get_or_create(
                event=event,
                guest_phone=guest.get('phone'),
                defaults={
                    'guest_name': guest.get('name'),
                    'guest_user_id': guest.get('user_id'),
                }
            )
            if is_new:
                created.append(invitation)
        
        return Response({
            'event_id': event.id,
            'invited_count': len(created)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def event_checkin(request):
    event_id = request.data.get('event_id')
    user_id = request.data.get('user_id')
    
    try:
        event = QaniKetedikEvent.objects.get(id=event_id)
        
        if event.is_checked_in:
            return Response({'error': 'Allaqachon check-in qilingan'}, status=status.HTTP_400_BAD_REQUEST)
        
        event.is_checked_in = True
        event.status = 'in_progress'
        event.checked_in_at = timezone.now()
        event.save()
        
        event.invitations.update(can_order_food=True)
        
        return Response({'success': True, 'checked_in': True})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def group_order_list(request, event_id=None):
    if request.method == 'GET':
        if not event_id:
            return Response({'error': 'event_id kerak'}, status=status.HTTP_400_BAD_REQUEST)
        
        orders = GroupOrder.objects.filter(event_id=event_id)
        serializer = GroupOrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        event_id = request.data.get('event_id')
        user_id = request.data.get('user_id')
        user_name = request.data.get('user_name')
        items = request.data.get('items', [])
        
        try:
            event = QaniKetedikEvent.objects.get(id=event_id)
            
            existing = GroupOrder.objects.filter(event=event, is_submitted=False).first()
            if existing:
                existing.items = existing.items + items
                existing.save()
                serializer = GroupOrderSerializer(existing)
            else:
                order = GroupOrder.objects.create(
                    event=event,
                    items=items,
                )
                serializer = GroupOrderSerializer(order)
            
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def submit_group_order(request):
    event_id = request.data.get('event_id')
    
    try:
        event = QaniKetedikEvent.objects.get(id=event_id)
        order = GroupOrder.objects.filter(event=event, is_submitted=False).first()
        
        if not order:
            return Response({'error': 'Buyurtma topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        
        order.is_submitted = True
        order.submitted_at = timezone.now()
        order.save()
        
        return Response({'success': True, 'order_id': order.id})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def my_invitations(request):
    user_id = request.query_params.get('user_id')
    phone = request.query_params.get('phone')
    
    if not user_id and not phone:
        return Response({'error': 'user_id yoki phone kerak'}, status=status.HTTP_400_BAD_REQUEST)
    
    invitations = EventInvitation.objects.filter(
        Q(guest_user_id=user_id) | Q(guest_phone=phone)
    ).select_related('event', 'event__restaurant')
    
    serializer = InvitationSerializer(invitations, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def respond_invitation(request):
    invitation_id = request.data.get('invitation_id')
    response = request.data.get('response')
    
    try:
        invitation = EventInvitation.objects.get(id=invitation_id)
        
        if response == 'accept':
            invitation.status = 'accepted'
        elif response == 'decline':
            invitation.status = 'declined'
        elif response == 'arrived':
            invitation.status = 'arrived'
            invitation.arrived_at = timezone.now()
        
        invitation.save()
        return Response({'success': True})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def review_list(request, restaurant_id=None):
    if request.method == 'GET':
        if restaurant_id:
            reviews = Review.objects.filter(restaurant_id=restaurant_id)
        else:
            reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PUT':
        review_id = request.data.get('id') or request.query_params.get('id')
        if not review_id:
            return Response({'error': 'Review ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Allow update if user owns the review or is restaurant admin
        try:
            review = Review.objects.get(id=review_id)
            
            # Check ownership or admin
            user_id = request.data.get('user_id', 0)
            if review.user_id != user_id and user_id != 0:
                # Check if user is restaurant admin
                from admins.models import RestaurantAdmin
                if not RestaurantAdmin.objects.filter(restaurant=review.restaurant, is_active=True).exists():
                    return Response({'error': 'Sizga ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)
            
            review.comment = request.data.get('comment', review.comment)
            review.rating = request.data.get('rating', review.rating)
            review.save()
            
            serializer = ReviewSerializer(review)
            return Response(serializer.data)
        except Review.DoesNotExist:
            return Response({'error': 'Sharh topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'DELETE':
        review_id = request.query_params.get('id')
        if not review_id:
            return Response({'error': 'Review ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            review = Review.objects.get(id=review_id)
            
            # Check ownership
            user_id = request.query_params.get('user_id', 0)
            if str(review.user_id) != str(user_id) and str(user_id) != '0':
                return Response({'error': 'Sizga ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)
            
            review.delete()
            return Response({'success': True})
        except Review.DoesNotExist:
            return Response({'error': 'Sharh topilmadi'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def search_all(request):
    query = request.query_params.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({'restaurants': [], 'menu_items': []})
    
    query_lower = query.lower()
    
    restaurants = Restaurant.objects.filter(
        is_active=True
    ).filter(
        Q(name__icontains=query) | 
        Q(address__icontains=query) |
        Q(category__name__icontains=query)
    ).distinct()[:20]
    
    menu_items = MenuItem.objects.filter(
        is_available=True
    ).filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query)
    ).select_related('restaurant').distinct()[:30]
    
    restaurant_results = []
    for r in restaurants:
        restaurant_results.append({
            'type': 'restaurant',
            'id': r.id,
            'name': r.name,
            'description': r.description or '',
            'price': None,
            'image': r.image.url if r.image else None,
            'restaurant_id': r.id,
            'restaurant_name': r.name,
            'rating': float(r.rating) if r.rating else 0,
            'address': r.address,
        })
    
    menu_results = []
    for item in menu_items:
        menu_results.append({
            'type': 'menu',
            'id': item.id,
            'name': item.name,
            'description': item.description or '',
            'price': float(item.price) if item.price else 0,
            'image': item.image.url if item.image else None,
            'restaurant_id': item.restaurant.id if item.restaurant else None,
            'restaurant_name': item.restaurant.name if item.restaurant else '',
            'rating': float(item.restaurant.rating) if item.restaurant and item.restaurant.rating else 0,
            'address': item.restaurant.address if item.restaurant else '',
        })
    
    return Response({
        'restaurants': restaurant_results,
        'menu_items': menu_results
    })


@api_view(['GET', 'POST'])
def order_list(request, restaurant_id=None):
    if request.method == 'GET':
        if restaurant_id:
            orders = Order.objects.filter(restaurant_id=restaurant_id)
        else:
            orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            restaurant_id = data.get('restaurant_id')
            table_id = data.get('table_id')
            table_token = data.get('table_token')
            user_name = data.get('user_name', 'Mehmon')
            user_id = data.get('user_id', 0)
            phone = data.get('phone', '')
            note = data.get('note', '')
            items_data = data.get('items', [])
            booking_date_time_str = data.get('booking_date_time')
            
            booking_date_time = None
            if booking_date_time_str:
                from datetime import datetime
                try:
                    booking_date_time = datetime.fromisoformat(booking_date_time_str.replace('Z', '+00:00'))
                except:
                    pass
            
            if not restaurant_id:
                return Response({'error': 'Restaurant ID required'}, status=400)
            
            restaurant = Restaurant.objects.get(id=restaurant_id)
            
            table = None
            if table_id:
                try:
                    table = Table.objects.get(id=table_id)
                except Table.DoesNotExist:
                    pass
            
            order = Order.objects.create(
                restaurant=restaurant,
                table=table,
                table_token=table_token or '',
                user_name=user_name,
                user_id=user_id,
                phone=phone,
                note=note,
                status='pending',
                total_amount=0,
                booking_date_time=booking_date_time
            )
            
            total = 0
            for item_data in items_data:
                menu_item_id = item_data.get('menu_item_id')
                quantity = int(item_data.get('quantity', 1))
                
                try:
                    menu_item = MenuItem.objects.get(id=menu_item_id)
                    item_total = int(menu_item.price) * quantity
                    total += item_total
                    
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        menu_item_name=menu_item.name,
                        quantity=quantity,
                        price=menu_item.price,
                        total_price=item_total
                    )
                except MenuItem.DoesNotExist:
                    continue
            
            order.total_amount = total
            order.save()
            
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=201)
            
        except Restaurant.DoesNotExist:
            return Response({'error': 'Restaurant topilmadi'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


@api_view(['GET', 'PUT'])
def order_detail(request, pk):
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return Response({'error': 'Buyurtma topilmadi'}, status=404)
    
    if request.method == 'GET':
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        new_status = request.data.get('status')
        if new_status:
            order.status = new_status
            order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)


@api_view(['GET'])
def order_by_token(request, token):
    try:
        order = Order.objects.get(table_token=token)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({'error': 'Buyurtma topilmadi'}, status=404)


@api_view(['GET'])
def user_orders(request, user_id):
    phone = request.query_params.get('phone', '')
    
    if user_id and user_id > 0:
        orders = Order.objects.filter(user_id=user_id).order_by('-created_at')
    elif phone:
        # Clean phone number for comparison
        clean_phone = ''.join(filter(str.isdigit, phone))
        orders = Order.objects.filter(
            phone__icontains=clean_phone
        ).order_by('-created_at')
    else:
        orders = Order.objects.none()
    
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def order_status_check(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return Response({
            'id': order.id,
            'status': order.status,
            'updated_at': order.updated_at.isoformat()
        })
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)


# Promotion Views
@api_view(['GET', 'POST'])
def promotion_list(request, restaurant_id=None):
    from .models import Promotion
    from django.utils import timezone
    
    if request.method == 'GET':
        now = timezone.now()
        if restaurant_id:
            promotions = Promotion.objects.filter(
                restaurant_id=restaurant_id,
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            )
        else:
            promotions = Promotion.objects.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            )
        serializer = PromotionSerializer(promotions, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = PromotionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def all_promotions(request):
    from .models import Promotion
    from django.utils import timezone
    
    now = timezone.now()
    promotions = Promotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).select_related('restaurant')
    
    # Also get promotions from menu items
    promotion_items = MenuItem.objects.filter(
        is_promotion=True,
        is_available=True,
        promotion_price__isnull=False
    ).select_related('restaurant')
    
    # Combine data
    result = []
    for p in promotions:
        result.append({
            'id': p.id,
            'type': 'promotion',
            'restaurant_id': p.restaurant.id,
            'restaurant_name': p.restaurant.name,
            'title': p.title,
            'description': p.description,
            'image': p.restaurant.image.url if p.restaurant.image else None,
            'discount_percent': p.discount_percent,
            'start_date': p.start_date.isoformat(),
            'end_date': p.end_date.isoformat()
        })
    
    for item in promotion_items:
        result.append({
            'id': item.id,
            'type': 'menu_promotion',
            'restaurant_id': item.restaurant.id,
            'restaurant_name': item.restaurant.name,
            'title': item.promotion_title or f"{item.name} - {item.discount_percent}% chegirma!",
            'description': item.description,
            'image': item.image.url if item.image else None,
            'menu_item_id': item.id,
            'original_price': str(item.price),
            'promotion_price': str(item.promotion_price),
            'discount_percent': int((1 - item.promotion_price / item.price) * 100) if item.promotion_price else 0
        })
    
    return Response(result)


@api_view(['GET'])
def app_settings(request):
    from .models import AppSettings
    
    about_us = AppSettings.objects.filter(key='about_us').first()
    search_background = AppSettings.objects.filter(key='search_background').first()
    app_name = AppSettings.objects.filter(key='app_name').first()
    contact_phone = AppSettings.objects.filter(key='contact_phone').first()
    contact_email = AppSettings.objects.filter(key='contact_email').first()
    instagram_url = AppSettings.objects.filter(key='instagram_url').first()
    telegram_url = AppSettings.objects.filter(key='telegram_url').first()
    facebook_url = AppSettings.objects.filter(key='facebook_url').first()
    youtube_url = AppSettings.objects.filter(key='youtube_url').first()
    app_logo_url = AppSettings.objects.filter(key='app_logo_url').first()
    app_version = AppSettings.objects.filter(key='app_version').first()
    home_background = AppSettings.objects.filter(key='home_background').first()
    
    def get_full_url(path):
        if not path:
            return ''
        if path.startswith('http'):
            return path
        return request.build_absolute_uri(path)
    
    return Response({
        'about_us': about_us.value if about_us else '',
        'search_background': search_background.value if search_background else '#e74c3c',
        'app_name': app_name.value if app_name else 'LocEats',
        'contact_phone': contact_phone.value if contact_phone else '',
        'contact_email': contact_email.value if contact_email else '',
        'instagram_url': instagram_url.value if instagram_url else '',
        'telegram_url': telegram_url.value if telegram_url else '',
        'facebook_url': facebook_url.value if facebook_url else '',
        'youtube_url': youtube_url.value if youtube_url else '',
        'app_logo_url': get_full_url(app_logo_url.value) if app_logo_url else '',
        'app_version': app_version.value if app_version else '1.0.0',
        'home_background': get_full_url(home_background.value) if home_background else '',
    })
