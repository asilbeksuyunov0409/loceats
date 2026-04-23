from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDay, TruncMonth
from datetime import datetime, timedelta
import uuid
import hashlib

from .models import (
    SuperAdmin, RestaurantAdmin, ExpenseCategory, 
    Expense, DailyRevenue, Staff, TableQR, Notification
)
from .serializers import (
    SuperAdminSerializer, RestaurantAdminSerializer, 
    RestaurantAdminCreateSerializer, ExpenseCategorySerializer,
    ExpenseSerializer, DailyRevenueSerializer, StaffSerializer,
    TableQRSerializer, NotificationSerializer
)
from restaurants.models import Restaurant, Table, Booking, MenuItem, Review
from restaurants.serializers import RestaurantListSerializer


def hash_password(password):
    return make_password(password)


def verify_password(password, hashed):
    return check_password(password, hashed)


def generate_qr_token():
    return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:12]


# ============= AUTH VIEWS =============

@api_view(['POST'])
def superadmin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username va password kerak'}, status=400)
    
    try:
        admin = SuperAdmin.objects.get(username=username)
        if verify_password(password, admin.password):
            admin.save()
            return Response({
                'success': True,
                'admin': SuperAdminSerializer(admin).data,
                'token': f'super_{admin.id}_{uuid.uuid4().hex}'
            })
        return Response({'error': 'Noto\'g\'ri parol'}, status=401)
    except SuperAdmin.DoesNotExist:
        return Response({'error': 'Foydalanuvchi topilmadi'}, status=404)


@api_view(['POST'])
def restaurant_admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username va password kerak'}, status=400)
    
    try:
        admin = RestaurantAdmin.objects.get(username=username)
        if not admin.is_active:
            return Response({'error': 'Akkaunt bloklangan'}, status=403)
        if verify_password(password, admin.password):
            admin.last_login = timezone.now()
            admin.save()
            return Response({
                'success': True,
                'admin': RestaurantAdminSerializer(admin).data,
                'token': f'rest_{admin.id}_{uuid.uuid4().hex}'
            })
        return Response({'error': 'Noto\'g\'ri parol'}, status=401)
    except RestaurantAdmin.DoesNotExist:
        return Response({'error': 'Foydalanuvchi topilmadi'}, status=404)


# ============= STAFF LOGIN =============

@api_view(['POST'])
def staff_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    restaurant_id = request.data.get('restaurant_id')
    
    if not username or not password:
        return Response({'error': 'Username va password kerak'}, status=400)
    
    try:
        staff = Staff.objects.get(username=username, restaurant_id=restaurant_id)
        if not staff.is_active:
            return Response({'error': 'Akkaunt faolemas'}, status=403)
        if staff.check_password(password):
            return Response({
                'success': True,
                'staff': {
                    'id': staff.id,
                    'full_name': staff.full_name,
                    'position': staff.position,
                    'can_manage_orders': staff.can_manage_orders,
                    'can_manage_bookings': staff.can_manage_bookings,
                    'can_manage_warehouse': staff.can_manage_warehouse,
                    'restaurant_id': staff.restaurant_id,
                },
                'token': f'staff_{staff.id}_{uuid.uuid4().hex}'
            })
        return Response({'error': 'Noto\'g\'ri parol'}, status=401)
    except Staff.DoesNotExist:
        return Response({'error': 'Foydalanuvchi topilmadi'}, status=404)


# ============= BOOKING API =============

@api_view(['GET', 'PATCH', 'DELETE'])
def booking_detail(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)
    
    if request.method == 'GET':
        return Response({
            'id': booking.id,
            'customer_name': booking.customer_name,
            'customer_phone': booking.customer_phone,
            'table': booking.table.table_number if booking.table else None,
            'guests': booking.guests,
            'booking_date': booking.booking_date,
            'booking_time': booking.booking_time,
            'status': booking.status,
        })
    
    elif request.method in ['PATCH', 'PUT']:
        new_status = request.data.get('status')
        if new_status:
            booking.status = new_status
            booking.save()
            return Response({'success': True, 'status': new_status})
        return Response({'error': 'Status kerak'}, status=400)
    
    elif request.method == 'DELETE':
        booking.delete()
        return Response({'success': True})


# ============= SUPERADMIN VIEWS =============

@api_view(['GET', 'POST'])
def superadmin_list(request):
    if request.method == 'GET':
        admins = RestaurantAdmin.objects.all().select_related('restaurant')
        serializer = RestaurantAdminSerializer(admins, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RestaurantAdminCreateSerializer(data=request.data)
        if serializer.is_valid():
            admin = serializer.save()
            return Response(RestaurantAdminSerializer(admin).data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
def superadmin_detail(request, pk):
    try:
        admin = RestaurantAdmin.objects.get(pk=pk)
    except RestaurantAdmin.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)
    
    if request.method == 'GET':
        return Response(RestaurantAdminSerializer(admin).data)
    
    elif request.method == 'PUT':
        serializer = RestaurantAdminSerializer(admin, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        admin.delete()
        return Response(status=204)


@api_view(['GET', 'POST'])
def superadmin_restaurants(request):
    if request.method == 'GET':
        restaurants = Restaurant.objects.all()
        serializer = RestaurantListSerializer(restaurants, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RestaurantListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
def superadmin_restaurant_detail(request, pk):
    try:
        restaurant = Restaurant.objects.get(pk=pk)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)
    
    if request.method == 'GET':
        serializer = RestaurantListSerializer(restaurant)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = RestaurantListSerializer(restaurant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        restaurant.delete()
        return Response(status=204)


@api_view(['GET'])
def app_settings(request):
    from restaurants.models import AppSettings
    settings = {}
    for s in AppSettings.objects.all():
        settings[s.key] = s.value
    return Response(settings)


@api_view(['GET'])
def superadmin_dashboard(request):
    total_restaurants = Restaurant.objects.count()
    total_admins = RestaurantAdmin.objects.count()
    active_admins = RestaurantAdmin.objects.filter(is_active=True).count()
    total_revenue = DailyRevenue.objects.aggregate(Sum('revenue'))['revenue__sum'] or 0
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    return Response({
        'total_restaurants': total_restaurants,
        'total_admins': total_admins,
        'active_admins': active_admins,
        'total_revenue': float(total_revenue),
        'total_expenses': float(total_expenses),
        'net_profit': float(total_revenue) - float(total_expenses),
    })


# ============= RESTAURANT ADMIN VIEWS =============

@api_view(['GET'])
def restaurant_dashboard(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restoran topilmadi'}, status=404)
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    today_revenue = DailyRevenue.objects.filter(
        restaurant=restaurant, date=today
    ).aggregate(Sum('revenue'))['revenue__sum'] or 0
    
    month_revenue = DailyRevenue.objects.filter(
        restaurant=restaurant, date__gte=month_start
    ).aggregate(Sum('revenue'))['revenue__sum'] or 0
    
    month_expenses = Expense.objects.filter(
        restaurant=restaurant, date__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_tables = Table.objects.filter(restaurant=restaurant).count()
    available_tables = Table.objects.filter(restaurant=restaurant, is_available=True).count()
    
    today_bookings = Booking.objects.filter(
        restaurant=restaurant, booking_date=today
    ).count()
    
    avg_rating = Review.objects.filter(restaurant=restaurant).aggregate(Avg('rating'))['rating__avg'] or 0
    
    monthly_data = DailyRevenue.objects.filter(
        restaurant=restaurant, date__gte=month_start.replace(month=month_start.month-2 if month_start.month > 2 else 12)
    ).annotate(day=TruncDay('date')).values('day').annotate(
        revenue=Sum('revenue')
    ).order_by('day')[:30]
    
    return Response({
        'restaurant': {
            'id': restaurant.id,
            'name': restaurant.name,
        },
        'today_revenue': float(today_revenue),
        'month_revenue': float(month_revenue),
        'month_expenses': float(month_expenses),
        'net_profit': float(month_revenue) - float(month_expenses),
        'total_tables': total_tables,
        'available_tables': available_tables,
        'occupied_tables': total_tables - available_tables,
        'today_bookings': today_bookings,
        'avg_rating': float(avg_rating),
        'monthly_data': list(monthly_data),
    })


@api_view(['GET', 'POST'])
def expense_list(request, restaurant_id):
    if request.method == 'GET':
        expenses = Expense.objects.filter(restaurant_id=restaurant_id)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'POST'])
def expense_categories(request):
    if request.method == 'GET':
        categories = ExpenseCategory.objects.all()
        serializer = ExpenseCategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ExpenseCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'POST'])
def revenue_list(request, restaurant_id):
    if request.method == 'GET':
        revenues = DailyRevenue.objects.filter(restaurant_id=restaurant_id).order_by('-date')[:30]
        serializer = DailyRevenueSerializer(revenues, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = DailyRevenueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'POST'])
def staff_list(request, restaurant_id):
    if request.method == 'GET':
        staff = Staff.objects.filter(restaurant_id=restaurant_id)
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
def staff_detail(request, pk):
    try:
        staff = Staff.objects.get(pk=pk)
    except Staff.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)
    
    if request.method == 'GET':
        return Response(StaffSerializer(staff).data)
    
    elif request.method == 'PUT':
        serializer = StaffSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        staff.delete()
        return Response(status=204)


@api_view(['GET', 'POST'])
def table_qr_list(request, restaurant_id):
    if request.method == 'GET':
        qrs = TableQR.objects.filter(restaurant_id=restaurant_id)
        serializer = TableQRSerializer(qrs, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        table_id = request.data.get('table_id')
        try:
            table = Table.objects.get(id=table_id, restaurant_id=restaurant_id)
        except Table.DoesNotExist:
            return Response({'error': 'Stol topilmadi'}, status=404)
        
        qr, created = TableQR.objects.get_or_create(
            table=table,
            defaults={'qr_token': generate_qr_token()}
        )
        return Response(TableQRSerializer(qr).data, status=201 if created else 200)


@api_view(['GET'])
def table_qr_detail(request, pk):
    try:
        qr = TableQR.objects.get(pk=pk)
    except TableQR.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)
    
    qr_url = f"http://10.242.199.57:8000/api/table/{qr.qr_token}/"
    return Response({
        **TableQRSerializer(qr).data,
        'qr_url': qr_url,
    })


@api_view(['GET'])
def table_by_token(request, token):
    try:
        qr = TableQR.objects.get(qr_token=token)
        table = qr.table
        restaurant = table.restaurant
        return Response({
            'restaurant': {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'phone': restaurant.phone,
            },
            'table': {
                'id': table.id,
                'number': table.table_number,
                'capacity': table.capacity,
                'is_available': table.is_available,
            }
        })
    except TableQR.DoesNotExist:
        return Response({'error': 'QR kod noto\'g\'ri'}, status=404)


@api_view(['GET'])
def kpi_report(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restoran topilmadi'}, status=404)
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    today_rev = DailyRevenue.objects.filter(restaurant=restaurant, date=today).first()
    month_revs = DailyRevenue.objects.filter(restaurant=restaurant, date__gte=month_start)
    year_revs = DailyRevenue.objects.filter(restaurant=restaurant, date__gte=year_start)
    
    month_expenses = Expense.objects.filter(restaurant=restaurant, date__gte=month_start)
    year_expenses = Expense.objects.filter(restaurant=restaurant, date__gte=year_start)
    
    total_staff = Staff.objects.filter(restaurant=restaurant, is_active=True).count()
    total_salary = Staff.objects.filter(restaurant=restaurant, is_active=True).aggregate(Sum('salary'))['salary__sum'] or 0
    
    month_revenue = month_revs.aggregate(Sum('revenue'))['revenue__sum'] or 0
    month_expense = month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    year_revenue = year_revs.aggregate(Sum('revenue'))['revenue__sum'] or 0
    year_expense = year_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    month_orders = month_revs.aggregate(Sum('orders_count'))['orders_count__sum'] or 0
    year_orders = year_revs.aggregate(Sum('orders_count'))['orders_count__sum'] or 0
    
    month_avg_check = month_revs.aggregate(Avg('average_check'))['average_check__avg'] or 0
    year_avg_check = year_revs.aggregate(Avg('average_check'))['average_check__avg'] or 0
    
    return Response({
        'restaurant': restaurant.name,
        'today': {
            'revenue': float(today_rev.revenue if today_rev else 0),
            'orders': today_rev.orders_count if today_rev else 0,
        },
        'month': {
            'revenue': float(month_revenue),
            'expenses': float(month_expense),
            'profit': float(month_revenue) - float(month_expense),
            'orders': month_orders,
            'avg_check': float(month_avg_check),
            'profit_margin': round(((float(month_revenue) - float(month_expense)) / float(month_revenue) * 100) if month_revenue > 0 else 0, 2),
        },
        'year': {
            'revenue': float(year_revenue),
            'expenses': float(year_expense),
            'profit': float(year_revenue) - float(year_expense),
            'orders': year_orders,
            'avg_check': float(year_avg_check),
            'profit_margin': round(((float(year_revenue) - float(year_expense)) / float(year_revenue) * 100) if year_revenue > 0 else 0, 2),
        },
        'staff': {
            'count': total_staff,
            'total_salary': float(total_salary),
            'salary_percent': round((float(total_salary) / float(month_revenue) * 100) if month_revenue > 0 else 0, 2),
        }
    })


@api_view(['GET'])
def notifications(request, admin_id):
    try:
        admin = RestaurantAdmin.objects.get(id=admin_id)
    except RestaurantAdmin.DoesNotExist:
        return Response({'error': 'Admin topilmadi'}, status=404)
    
    notifications = Notification.objects.filter(recipient=admin)[:20]
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def mark_notification_read(request, pk):
    try:
        notification = Notification.objects.get(pk=pk)
        notification.is_read = True
        notification.save()
        return Response({'success': True})
    except Notification.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)
