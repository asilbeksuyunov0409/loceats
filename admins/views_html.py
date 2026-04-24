from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.db.models import Q as DQ
from django.db import models
from django.conf import settings
from datetime import datetime, timedelta
import uuid
import json
import os

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
from .views import generate_qr_token
from restaurants.models import Restaurant, Table, Booking, MenuItem, MenuCategory, Review, Category, Order, OrderItem, EventInvitation
from restaurants.serializers import RestaurantListSerializer


@csrf_exempt
def admin_login_page(request):
    # Clear any cached session
    request.session.flush()
    error = None
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            admin = SuperAdmin.objects.get(username=username)
            if check_password(password, admin.password):
                request.session['admin_token'] = f'super_{admin.id}_{uuid.uuid4().hex}'
                request.session['admin_data'] = {
                    'id': admin.id,
                    'username': admin.username,
                    'email': admin.email,
                    'full_name': admin.full_name,
                    'type': 'superadmin'
                }
                return redirect('/admin-panel/')
            else:
                error = 'Noto\'g\'ri parol!'
        except SuperAdmin.DoesNotExist:
            error = 'Foydalanuvchi topilmadi!'
    
    return render(request, 'admins/login.html', {'error': error})


@csrf_exempt
def restaurant_admin_login_page(request):
    # Clear any cached session
    request.session.flush()
    error = None
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            admin = RestaurantAdmin.objects.get(username=username)
            if check_password(password, admin.password):
                if not admin.is_active:
                    error = 'Sizning profilingiz bloklangan!'
                elif not admin.restaurant:
                    error = 'Sizga restoran biriktirilmagan!'
                else:
                    request.session['admin_token'] = f'rest_{admin.id}_{uuid.uuid4().hex}'
                    request.session['admin_data'] = {
                        'id': admin.id,
                        'username': admin.username,
                        'full_name': admin.full_name,
                        'type': 'restaurant_admin',
                        'restaurant_id': admin.restaurant.id
                    }
                    return redirect(f'/restaurant-admin/{admin.restaurant.id}/')
            else:
                error = 'Noto\'g\'ri parol!'
        except RestaurantAdmin.DoesNotExist:
            error = 'Foydalanuvchi topilmadi!'
    
    return render(request, 'admins/restaurant_login.html', {'error': error})


@csrf_exempt
def staff_login_page(request):
    request.session.flush()
    error = None
    restaurant_id = None
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        restaurant_id = request.POST.get('restaurant_id')
        
        if not restaurant_id:
            error = 'Restoran tanlanmagan!'
        else:
            try:
                staff = Staff.objects.get(username=username, restaurant_id=restaurant_id)
                if not staff.is_active:
                    error = 'Sizning profilingiz faolem!'
                elif staff.check_password(password):
                    request.session['staff_token'] = f'staff_{staff.id}_{uuid.uuid4().hex}'
                    request.session['staff_data'] = {
                        'id': staff.id,
                        'full_name': staff.full_name,
                        'position': staff.position,
                        'can_manage_orders': staff.can_manage_orders,
                        'can_manage_bookings': staff.can_manage_bookings,
                        'can_manage_warehouse': staff.can_manage_warehouse,
                        'restaurant_id': staff.restaurant_id
                    }
                    # Redirect based on position
                    if staff.position == 'warehouse':
                        return redirect(f'/staff/{staff.restaurant_id}/warehouse/')
                    elif staff.position == 'cook':
                        return redirect(f'/staff/{staff.restaurant_id}/orders/')
                    else:
                        return redirect(f'/staff/{staff.restaurant_id}/bookings/')
                else:
                    error = 'Noto\'g\'ri parol!'
            except Staff.DoesNotExist:
                error = 'Foydalanuvchi topilmadi!'
    
    restaurants = Restaurant.objects.filter(is_active=True)
    return render(request, 'admins/staff_login.html', {'error': error, 'restaurants': restaurants})


# Warehouse view for warehouse workers
def staff_warehouse_view(request, restaurant_id):
    if 'staff_token' not in request.session:
        return redirect('/staff-login/')
    
    staff_data = request.session.get('staff_data', {})
    if staff_data.get('restaurant_id') != restaurant_id:
        return redirect('/staff-login/')
    
    if not staff_data.get('can_manage_warehouse'):
        return render(request, 'admins/staff_no_access.html', {'error': 'Sizda ombor huquqi yo\'q'})
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/staff-login/')
    
    from restaurants.models import OrderItem, MenuItem, WarehouseItem, InventoryEntry
    
    if request.method == 'POST':
        action = request.POST.get('action')
        staff_name = staff_data.get('full_name', 'Noma\'lum')
        
        if action == 'add_warehouse_item':
            name = request.POST.get('name')
            category = request.POST.get('category', 'other')
            unit = request.POST.get('unit')
            quantity = request.POST.get('quantity', 0)
            price = request.POST.get('price', 0)
            min_quantity = request.POST.get('min_quantity', 0)
            supplier = request.POST.get('supplier', '')
            
            if name and unit:
                WarehouseItem.objects.create(
                    restaurant=restaurant,
                    name=name,
                    category=category,
                    unit=unit,
                    quantity=quantity,
                    price=price,
                    min_quantity=min_quantity,
                    supplier=supplier
                )
        
        elif action == 'warehouse_in':
            item_id = request.POST.get('item_id')
            quantity = request.POST.get('quantity', 0)
            price = request.POST.get('price', 0)
            note = request.POST.get('note', '')
            
            if item_id and quantity:
                try:
                    item = WarehouseItem.objects.get(id=item_id, restaurant=restaurant)
                    item.quantity += float(quantity)
                    if price:
                        item.price = price
                    item.save()
                    InventoryEntry.objects.create(
                        warehouse_item=item,
                        entry_type='in',
                        quantity=quantity,
                        price=price,
                        note=note,
                        created_by=staff_name
                    )
                except WarehouseItem.DoesNotExist:
                    pass
        
        elif action == 'warehouse_out':
            item_id = request.POST.get('item_id')
            quantity = request.POST.get('quantity', 0)
            price = request.POST.get('price', 0)
            note = request.POST.get('note', '')
            
            if item_id and quantity:
                try:
                    item = WarehouseItem.objects.get(id=item_id, restaurant=restaurant)
                    item.quantity = max(0, item.quantity - float(quantity))
                    item.save()
                    InventoryEntry.objects.create(
                        warehouse_item=item,
                        entry_type='out',
                        quantity=quantity,
                        price=price,
                        note=note,
                        created_by=staff_name
                    )
                except WarehouseItem.DoesNotExist:
                    pass
        
        return redirect(f'/staff/{restaurant_id}/warehouse/')
    
    # Get last orders for inventory reference
    recent_items = OrderItem.objects.filter(order__restaurant=restaurant).order_by('-id')[:50]
    
    # Get menu items for inventory
    menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)
    
    # Get warehouse items with stock status
    warehouse_items = WarehouseItem.objects.filter(restaurant=restaurant)
    
    # Get recent inventory entries
    recent_entries = InventoryEntry.objects.filter(warehouse_item__restaurant=restaurant).order_by('-created_at')[:30]
    
    context = {
        'restaurant': restaurant,
        'recent_items': recent_items,
        'menu_items': menu_items,
        'warehouse_items': warehouse_items,
        'recent_entries': recent_entries,
        'staff': staff_data
    }
    return render(request, 'admins/staff_warehouse.html', context)


# Bookings view for managers
def staff_bookings_view(request, restaurant_id):
    if 'staff_token' not in request.session:
        return redirect('/staff-login/')
    
    staff_data = request.session.get('staff_data', {})
    if staff_data.get('restaurant_id') != restaurant_id:
        return redirect('/staff-login/')
    
    if not staff_data.get('can_manage_bookings'):
        return render(request, 'admins/staff_no_access.html', {'error': 'Sizda bron huquqi yo\'q'})
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/staff-login/')
    
    from restaurants.models import Booking, Table
    bookings = Booking.objects.filter(restaurant=restaurant).order_by('-booking_date', '-booking_time')[:50]
    tables = Table.objects.filter(restaurant=restaurant)
    
    return render(request, 'admins/staff_bookings.html', {
        'restaurant': restaurant,
        'bookings': bookings,
        'tables': tables,
        'staff': staff_data
    })


def staff_orders_view(request, restaurant_id):
    try:
        print(f"Debug: staff_orders_view called with restaurant_id={restaurant_id}")
    except:
        pass
    
    if 'staff_token' not in request.session:
        return redirect('/staff-login/')
    
    staff_data = request.session.get('staff_data', {})
    if staff_data.get('restaurant_id') != restaurant_id:
        return redirect('/staff-login/')
    
    if not staff_data.get('can_manage_orders'):
        return render(request, 'admins/staff_no_access.html', {'error': 'Sizda buyurtmalarni boshqarish huquqi yo\'q'})
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/staff-login/')
    
    try:
        from restaurants.models import Order, OrderItem
        orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')[:50]
        
        # Get items for each order - handle errors
        for order in orders:
            try:
                order.items_list = list(OrderItem.objects.filter(order=order).select_related('menu_item'))
            except Exception as e:
                print(f"Error loading items for order {order.id}: {e}")
                order.items_list = []
    except Exception as e:
        print(f"Error loading orders: {e}")
        orders = []
    
    # Get items for each order
    for order in orders:
        order.items_list = OrderItem.objects.filter(order=order)
    
    return render(request, 'admins/staff_orders.html', {
        'restaurant': restaurant,
        'orders': orders,
        'staff': staff_data
    })


@csrf_exempt
def staff_update_order(request, restaurant_id, order_id):
    print(f"Debug: staff_update_order called with restaurant_id={restaurant_id}, order_id={order_id}")
    
    if 'staff_token' not in request.session:
        return redirect('/staff-login/')
    
    staff_data = request.session.get('staff_data', {})
    if not staff_data.get('can_manage_orders'):
        return JsonResponse({'error': 'Huquq yo\'q'}, status=403)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        print(f"Updating order {order_id} to status: '{new_status}'")
        
        # Validate status
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled', 'delivered']
        if not new_status or new_status not in valid_statuses:
            print(f"Invalid status: {new_status}")
            return redirect(f'/staff/{restaurant_id}/orders/')
        
        try:
            order = Order.objects.get(id=order_id, restaurant_id=restaurant_id)
            old_status = order.status
            order.status = new_status
            order.save()
            print(f"Order {order_id} status changed from {old_status} to {new_status}")
            return redirect(f'/staff/{restaurant_id}/orders/')
        except Order.DoesNotExist:
            print(f"Order not found: {order_id}")
            return redirect(f'/staff/{restaurant_id}/orders/')
    
    return JsonResponse({'error': 'Noto\'g\'ri so\'rov'}, status=400)


def superadmin_dashboard_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    from users.models import User
    from restaurants.models import Order
    
    total_restaurants = Restaurant.objects.count()
    total_admins = RestaurantAdmin.objects.count()
    active_admins = RestaurantAdmin.objects.filter(is_active=True).count()
    pending_admins = RestaurantAdmin.objects.filter(status='pending').count()
    
    # User statistics
    total_registered_users = User.objects.count()
    users_with_orders = Order.objects.exclude(user_id=0).values('user_id').distinct().count()
    total_orders = Order.objects.count()
    total_order_value = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get registered users list - prepare for display
    recent_users_raw = User.objects.order_by('-date_joined')[:10]
    recent_users = []
    for user in recent_users_raw:
        order_count = Order.objects.filter(user_id=user.id).count()
        recent_users.append({
            'id': user.id,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'email': user.email or '',
            'phone': user.phone or '-',
            'date_joined': user.date_joined,
            'order_count': order_count,
        })
    
    # Get recent restaurants
    recent_restaurants = Restaurant.objects.order_by('-created_at')[:10]
    
    month_revenue = DailyRevenue.objects.filter(
        date__gte=timezone.now().replace(day=1)
    ).aggregate(Sum('revenue'))['revenue__sum'] or 0
    
    month_expenses = Expense.objects.filter(
        date__gte=timezone.now().replace(day=1)
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    recent_admins = RestaurantAdmin.objects.select_related('restaurant').order_by('-created_at')[:5]
    
    context = {
        'page': 'dashboard',
        'stats': {
            'total_restaurants': total_restaurants,
            'total_admins': total_admins,
            'active_admins': active_admins,
            'pending_admins': pending_admins,
            'month_revenue': float(month_revenue),
            'month_expenses': float(month_expenses),
            'net_profit': float(month_revenue) - float(month_expenses),
            'total_registered_users': total_registered_users,
            'users_with_orders': users_with_orders,
            'total_orders': total_orders,
            'total_order_value': float(total_order_value),
        },
        'recent_admins': recent_admins,
        'recent_restaurants': recent_restaurants,
        'recent_users': recent_users,
    }
    return render(request, 'admins/dashboard.html', context)


def superadmin_restaurants_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        rating = request.POST.get('rating', 4.0)
        latitude = request.POST.get('latitude', 39.6542)
        longitude = request.POST.get('longitude', 66.9597)
        description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        
        try:
            category = None
            if category_id:
                category = Category.objects.get(id=category_id)
            
            restaurant = Restaurant(
                name=name,
                address=address,
                phone=phone,
                rating=rating,
                latitude=latitude,
                longitude=longitude,
                description=description,
                category=category
            )
            
            if request.FILES.get('image'):
                restaurant.image = request.FILES.get('image')
            
            restaurant.save()
        except Exception as e:
            pass
        
        return redirect('/admin-panel/restaurants/')
    
    search = request.GET.get('search', '')
    restaurants = Restaurant.objects.all().order_by('-rating')
    
    if search:
        restaurants = restaurants.filter(
            DQ(name__icontains=search) |
            DQ(address__icontains=search) |
            DQ(phone__icontains=search) |
            DQ(category__name__icontains=search)
        )
    
    categories = Category.objects.all()
    admins = RestaurantAdmin.objects.filter(is_active=True)
    context = {
        'page': 'restaurants',
        'restaurants': restaurants,
        'categories': categories,
        'admins': admins,
        'search': search,
    }
    return render(request, 'admins/restaurants.html', context)


def superadmin_admins_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    search = request.GET.get('search', '')
    admins = RestaurantAdmin.objects.select_related('restaurant').all()
    
    if search:
        admins = admins.filter(
            DQ(full_name__icontains=search) |
            DQ(username__icontains=search) |
            DQ(email__icontains=search) |
            DQ(phone__icontains=search) |
            DQ(restaurant__name__icontains=search)
        )
    
    restaurants = Restaurant.objects.all()
    context = {
        'page': 'admins',
        'admins': admins,
        'restaurants': restaurants,
        'search': search,
    }
    return render(request, 'admins/admins.html', context)


def create_restaurant_admin(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        from django.contrib.auth.hashers import make_password
        
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        restaurant_id = request.POST.get('restaurant')
        status = request.POST.get('status', 'active')
        can_add_promotion = request.POST.get('can_add_promotion') == '1'
        
        try:
            restaurant = None
            if restaurant_id:
                restaurant = Restaurant.objects.get(id=restaurant_id)
            
            admin = RestaurantAdmin.objects.create(
                full_name=full_name,
                username=username,
                email=email,
                phone=phone,
                password=make_password(password),
                restaurant=restaurant,
                status=status,
                is_active=(status == 'active'),
                can_add_promotion=can_add_promotion
            )
            return redirect('/admin-panel/admins/')
        except Exception as e:
            admins = RestaurantAdmin.objects.select_related('restaurant').all()
            restaurants = Restaurant.objects.all()
            return render(request, 'admins/admins.html', {
                'page': 'admins',
                'admins': admins,
                'restaurants': restaurants,
                'error': str(e)
            })
    
    return redirect('/admin-panel/admins/')


def delete_restaurant_admin(request, pk):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    try:
        admin = RestaurantAdmin.objects.get(pk=pk)
        admin.delete()
    except RestaurantAdmin.DoesNotExist:
        pass
    
    return redirect('/admin-panel/admins/')


def update_restaurant_admin(request, pk):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        try:
            admin = RestaurantAdmin.objects.get(pk=pk)
            
            admin.full_name = request.POST.get('full_name', admin.full_name)
            admin.username = request.POST.get('username', admin.username)
            admin.email = request.POST.get('email', admin.email)
            admin.phone = request.POST.get('phone', admin.phone)
            admin.status = request.POST.get('status', admin.status)
            admin.is_active = (admin.status == 'active')
            admin.can_add_promotion = request.POST.get('can_add_promotion') == '1'
            
            restaurant_id = request.POST.get('restaurant')
            if restaurant_id:
                admin.restaurant = Restaurant.objects.get(id=restaurant_id)
            else:
                admin.restaurant = None
            
            new_password = request.POST.get('password')
            if new_password and len(new_password) >= 6:
                admin.password = make_password(new_password)
            
            admin.save()
        except Exception as e:
            pass
    
    return redirect('/admin-panel/admins/')


def update_restaurant(request, pk):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(pk=pk)
            
            restaurant.name = request.POST.get('name', restaurant.name)
            restaurant.phone = request.POST.get('phone', restaurant.phone)
            restaurant.address = request.POST.get('address', restaurant.address)
            restaurant.description = request.POST.get('description', restaurant.description)
            
            rating = request.POST.get('rating')
            if rating:
                try:
                    restaurant.rating = float(rating)
                except:
                    pass
            
            latitude = request.POST.get('latitude')
            if latitude:
                try:
                    restaurant.latitude = float(latitude)
                except:
                    pass
            
            longitude = request.POST.get('longitude')
            if longitude:
                try:
                    restaurant.longitude = float(longitude)
                except:
                    pass
            
            category_id = request.POST.get('category')
            if category_id:
                try:
                    restaurant.category = Category.objects.get(id=category_id)
                except:
                    restaurant.category = None
            else:
                restaurant.category = None
            
            admin_id = request.POST.get('admin')
            if admin_id:
                try:
                    admin = RestaurantAdmin.objects.get(id=admin_id)
                    admin.restaurant = restaurant
                    admin.save()
                except:
                    pass
            
            if request.FILES.get('image'):
                restaurant.image = request.FILES.get('image')
            
            restaurant.save()
            
        except Restaurant.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error updating restaurant: {e}")
            import traceback
            traceback.print_exc()
    
    return redirect('/admin-panel/restaurants/')


def delete_restaurant(request, pk):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(pk=pk)
            restaurant.delete()
        except Restaurant.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error deleting restaurant: {e}")
    
    return redirect('/admin-panel/restaurants/')


def superadmin_expenses_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant')
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        date = request.POST.get('date')
        
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            category = None
            if category_id:
                category = ExpenseCategory.objects.get(id=category_id)
            
            Expense.objects.create(
                restaurant=restaurant,
                category=category,
                amount=amount,
                description=description,
                date=date or timezone.now().date()
            )
        except Exception as e:
            pass
        
        return redirect('/admin-panel/expenses/')
    
    expenses = Expense.objects.select_related('restaurant', 'category').order_by('-date')[:50]
    categories = ExpenseCategory.objects.all()
    restaurants = Restaurant.objects.all()
    
    context = {
        'page': 'expenses',
        'expenses': expenses,
        'categories': categories,
        'restaurants': restaurants,
    }
    return render(request, 'admins/expenses.html', context)


def superadmin_kpi_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    total_restaurants = Restaurant.objects.count()
    total_admins = RestaurantAdmin.objects.filter(is_active=True).count()
    
    month_revenues = DailyRevenue.objects.filter(date__gte=month_start)
    year_revenues = DailyRevenue.objects.filter(date__gte=year_start)
    month_expenses = Expense.objects.filter(date__gte=month_start)
    
    month_revenue = month_revenues.aggregate(Sum('revenue'))['revenue__sum'] or 0
    month_expense = month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    year_revenue = year_revenues.aggregate(Sum('revenue'))['revenue__sum'] or 0
    
    month_orders = month_revenues.aggregate(Sum('orders_count'))['orders_count__sum'] or 0
    month_avg_check = month_revenues.aggregate(Avg('average_check'))['average_check__avg'] or 0
    
    total_staff = Staff.objects.filter(is_active=True).count()
    total_salary = Staff.objects.filter(is_active=True).aggregate(Sum('salary'))['salary__sum'] or 0
    
    restaurant_kpis = []
    for restaurant in Restaurant.objects.all():
        rest_month_rev = DailyRevenue.objects.filter(restaurant=restaurant, date__gte=month_start).aggregate(Sum('revenue'))['revenue__sum'] or 0
        rest_month_exp = Expense.objects.filter(restaurant=restaurant, date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0
        avg_rating = Review.objects.filter(restaurant=restaurant).aggregate(Avg('rating'))['rating__avg'] or 0
        restaurant_kpis.append({
            'restaurant': restaurant,
            'month_revenue': float(rest_month_rev),
            'month_expenses': float(rest_month_exp),
            'profit': float(rest_month_rev) - float(rest_month_exp),
            'rating': float(avg_rating),
        })
    
    context = {
        'page': 'kpi',
        'kpi': {
            'total_restaurants': total_restaurants,
            'total_admins': total_admins,
            'month_revenue': float(month_revenue),
            'month_expenses': float(month_expense),
            'month_profit': float(month_revenue) - float(month_expense),
            'month_profit_margin': round(((float(month_revenue) - float(month_expense)) / float(month_revenue) * 100) if month_revenue > 0 else 0, 1),
            'year_revenue': float(year_revenue),
            'month_orders': month_orders,
            'month_avg_check': float(month_avg_check),
            'total_staff': total_staff,
            'total_salary': float(total_salary),
            'salary_percent': round((float(total_salary) / float(month_revenue) * 100) if month_revenue > 0 else 0, 1),
        },
        'restaurant_kpis': restaurant_kpis,
    }
    return render(request, 'admins/superadmin_kpi.html', context)


def superadmin_settings_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    from users.models import User
    from restaurants.models import Review, AppSettings
    
    # Get all settings
    about_us = AppSettings.objects.filter(key='about_us').first()
    search_background = AppSettings.objects.filter(key='search_background').first()
    app_name = AppSettings.objects.filter(key='app_name').first()
    contact_phone = AppSettings.objects.filter(key='contact_phone').first()
    contact_email = AppSettings.objects.filter(key='contact_email').first()
    terms_url = AppSettings.objects.filter(key='terms_url').first()
    privacy_url = AppSettings.objects.filter(key='privacy_url').first()
    instagram_url = AppSettings.objects.filter(key='instagram_url').first()
    telegram_url = AppSettings.objects.filter(key='telegram_url').first()
    facebook_url = AppSettings.objects.filter(key='facebook_url').first()
    youtube_url = AppSettings.objects.filter(key='youtube_url').first()
    app_logo_url = AppSettings.objects.filter(key='app_logo_url').first()
    app_version = AppSettings.objects.filter(key='app_version').first()
    home_background = AppSettings.objects.filter(key='home_background').first()
    superadmin = SuperAdmin.objects.first()
    superadmin_username = superadmin.username if superadmin else ''
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_all':
            # App Info
            AppSettings.objects.update_or_create(key='app_name', defaults={'value': request.POST.get('app_name', '')})
            AppSettings.objects.update_or_create(key='contact_phone', defaults={'value': request.POST.get('contact_phone', '')})
            AppSettings.objects.update_or_create(key='contact_email', defaults={'value': request.POST.get('contact_email', '')})
            
            # About Us
            AppSettings.objects.update_or_create(key='about_us', defaults={'value': request.POST.get('about_us', '')})
            
            # Search Background
            AppSettings.objects.update_or_create(key='search_background', defaults={'value': request.POST.get('search_background', '')})
            
            # Social Links
            AppSettings.objects.update_or_create(key='instagram_url', defaults={'value': request.POST.get('instagram_url', '')})
            AppSettings.objects.update_or_create(key='telegram_url', defaults={'value': request.POST.get('telegram_url', '')})
            AppSettings.objects.update_or_create(key='facebook_url', defaults={'value': request.POST.get('facebook_url', '')})
            AppSettings.objects.update_or_create(key='youtube_url', defaults={'value': request.POST.get('youtube_url', '')})
            
            # Legal Links
            AppSettings.objects.update_or_create(key='terms_url', defaults={'value': request.POST.get('terms_url', '')})
            AppSettings.objects.update_or_create(key='privacy_url', defaults={'value': request.POST.get('privacy_url', '')})
            
            # Logo & Version
            AppSettings.objects.update_or_create(key='app_version', defaults={'value': request.POST.get('app_version', '')})
            AppSettings.objects.update_or_create(key='app_logo_url', defaults={'value': request.POST.get('app_logo_url', '')})
            AppSettings.objects.update_or_create(key='home_background', defaults={'value': request.POST.get('home_background', '')})
            
            # Theme & Language
            AppSettings.objects.update_or_create(key='auto_dark_mode', defaults={'value': request.POST.get('auto_dark_mode', '')})
            AppSettings.objects.update_or_create(key='default_language', defaults={'value': request.POST.get('default_language', 'uz')})
            
            # Developer Card
            AppSettings.objects.update_or_create(key='developer_card', defaults={'value': request.POST.get('developer_card', '')})
            AppSettings.objects.update_or_create(key='developer_name', defaults={'value': request.POST.get('developer_name', '')})
            
            return redirect('/admin-panel/settings/')
        
        elif action == 'save_superadmin':
            content = request.POST.get('about_us', '')
            AppSettings.objects.update_or_create(key='about_us', defaults={'value': content})
        elif action == 'save_search_bg':
            bg_value = request.POST.get('search_background', '')
            AppSettings.objects.update_or_create(key='search_background', defaults={'value': bg_value})
        elif action == 'save_app_info':
            AppSettings.objects.update_or_create(key='app_name', defaults={'value': request.POST.get('app_name', '')})
            AppSettings.objects.update_or_create(key='contact_phone', defaults={'value': request.POST.get('contact_phone', '')})
            AppSettings.objects.update_or_create(key='contact_email', defaults={'value': request.POST.get('contact_email', '')})
            AppSettings.objects.update_or_create(key='app_logo_url', defaults={'value': request.POST.get('app_logo_url', '')})
            AppSettings.objects.update_or_create(key='app_version', defaults={'value': request.POST.get('app_version', '')})
            AppSettings.objects.update_or_create(key='home_background', defaults={'value': request.POST.get('home_background', '')})
            AppSettings.objects.update_or_create(key='developer_name', defaults={'value': request.POST.get('developer_name', '')})
            AppSettings.objects.update_or_create(key='developer_card', defaults={'value': request.POST.get('developer_card', '')})
            AppSettings.objects.update_or_create(key='auto_dark_mode', defaults={'value': request.POST.get('auto_dark_mode', '')})
            AppSettings.objects.update_or_create(key='default_language', defaults={'value': request.POST.get('default_language', 'uz')})
        elif action == 'save_links':
            AppSettings.objects.update_or_create(key='terms_url', defaults={'value': request.POST.get('terms_url', '')})
            AppSettings.objects.update_or_create(key='privacy_url', defaults={'value': request.POST.get('privacy_url', '')})
        elif action == 'save_social':
            AppSettings.objects.update_or_create(key='instagram_url', defaults={'value': request.POST.get('instagram_url', '')})
            AppSettings.objects.update_or_create(key='telegram_url', defaults={'value': request.POST.get('telegram_url', '')})
            AppSettings.objects.update_or_create(key='facebook_url', defaults={'value': request.POST.get('facebook_url', '')})
            AppSettings.objects.update_or_create(key='youtube_url', defaults={'value': request.POST.get('youtube_url', '')})
        elif action == 'save_superadmin':
            admin_data = request.session.get('admin_data')
            if admin_data and admin_data.get('type') == 'superadmin':
                current_pass = request.POST.get('current_password', '')
                new_password = request.POST.get('new_password', '')
                confirm_password = request.POST.get('confirm_password', '')
                
                superadmin = SuperAdmin.objects.first()
                if superadmin and current_pass and new_password and confirm_password:
                    if not check_password(current_pass, superadmin.password):
                        return render(request, 'admins/settings.html', {'error': 'Joriy parol noto\'g\'ri'})
                    if new_password != confirm_password:
                        return render(request, 'admins/settings.html', {'error': 'Yangi parollar mos kelmadi'})
                    if len(new_password) < 4:
                        return render(request, 'admins/settings.html', {'error': 'Parol kamida 4 ta belgi bo\'lishi kerak'})
                    superadmin.password = make_password(new_password)
                    superadmin.save()
        
        elif action == 'upload_logo':
            uploaded_file = request.FILES.get('logo_file')
            if uploaded_file:
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'app')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                file_name = f"logo_{int(uuid.uuid4().time)}{os.path.splitext(uploaded_file.name)[1]}"
                file_path = os.path.join(upload_dir, file_name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                file_url = f"/media/app/{file_name}"
                AppSettings.objects.update_or_create(key='app_logo_url', defaults={'value': file_url})
        
        elif action == 'upload_home_bg':
            uploaded_file = request.FILES.get('home_bg_file')
            if uploaded_file:
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'app')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                file_name = f"home_bg_{int(uuid.uuid4().time)}{os.path.splitext(uploaded_file.name)[1]}"
                file_path = os.path.join(upload_dir, file_name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                file_url = f"/media/app/{file_name}"
                AppSettings.objects.update_or_create(key='home_background', defaults={'value': file_url})
        
        return redirect('/admin-panel/settings/')
    
    auto_dark_mode = AppSettings.objects.filter(key='auto_dark_mode').first()
    default_language = AppSettings.objects.filter(key='default_language').first()
    developer_card = AppSettings.objects.filter(key='developer_card').first()
    developer_name = AppSettings.objects.filter(key='developer_name').first()
    
    context = {
        'page': 'settings',
        'stats': {
            'total_restaurants': Restaurant.objects.count(),
            'total_admins': RestaurantAdmin.objects.count(),
            'total_users': User.objects.count(),
            'total_reviews': Review.objects.count(),
        },
        'about_us': about_us.value if about_us else '',
        'search_background': search_background.value if search_background else '',
        'app_name': app_name.value if app_name else 'LocEats',
        'contact_phone': contact_phone.value if contact_phone else '',
        'contact_email': contact_email.value if contact_email else '',
        'terms_url': terms_url.value if terms_url else '',
        'privacy_url': privacy_url.value if privacy_url else '',
        'instagram_url': instagram_url.value if instagram_url else '',
        'telegram_url': telegram_url.value if telegram_url else '',
        'facebook_url': facebook_url.value if facebook_url else '',
        'youtube_url': youtube_url.value if youtube_url else '',
        'app_logo_url': app_logo_url.value if app_logo_url else '',
        'app_version': app_version.value if app_version else '1.0.0',
        'home_background': home_background.value if home_background else '',
        'superadmin_username': superadmin_username,
        'auto_dark_mode': auto_dark_mode.value if auto_dark_mode else '',
        'default_language': default_language.value if default_language else 'uz',
        'developer_card': developer_card.value if developer_card else '',
        'developer_name': developer_name.value if developer_name else '',
    }
    return render(request, 'admins/settings.html', context)


def superadmin_chat_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    from restaurants.models import ChatMessage, AppSettings
    
    restaurant_id = request.GET.get('restaurant_id')
    messages = []
    restaurants = []
    
    if restaurant_id:
        messages = ChatMessage.objects.filter(
            restaurant_id=restaurant_id
        ).order_by('created_at')
        # Mark messages as read
        ChatMessage.objects.filter(
            restaurant_id=restaurant_id,
            sender_type='restaurant',
            is_read=False
        ).update(is_read=True)
    
    restaurants = Restaurant.objects.all().order_by('name')
    
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        message = request.POST.get('message')
        if restaurant_id and message:
            ChatMessage.objects.create(
                restaurant_id=restaurant_id,
                sender_type='superadmin',
                sender_name='Super Admin',
                message=message,
            )
        return redirect(f'/admin-panel/chat/?restaurant_id={restaurant_id}')
    
    unread_counts = {}
    for rest in restaurants:
        count = ChatMessage.objects.filter(
            restaurant_id=rest.id,
            sender_type='restaurant',
            is_read=False
        ).count()
        if count > 0:
            unread_counts[rest.id] = count
    
    selected_restaurant_name = ''
    if restaurant_id:
        try:
            selected_restaurant_name = Restaurant.objects.get(id=restaurant_id).name
        except:
            selected_restaurant_name = ''
    
    context = {
        'page': 'chat',
        'messages': messages,
        'restaurants': restaurants,
        'selected_restaurant_id': int(restaurant_id) if restaurant_id else None,
        'selected_restaurant_name': selected_restaurant_name,
        'unread_counts': unread_counts,
    }
    return render(request, 'admins/chat.html', context)


def superadmin_feedbacks_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    from users.models import Feedback
    
    if request.method == 'POST':
        feedback_id = request.POST.get('feedback_id')
        reply = request.POST.get('reply', '')
        
        if feedback_id and reply:
            try:
                feedback = Feedback.objects.get(id=feedback_id)
                feedback.admin_reply = reply
                feedback.is_replied = True
                feedback.save()
                
                try:
                    import telegram
                    bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
                    chat_id = '8433417347'
                    bot = telegram.Bot(token=bot_token)
                    
                    text = f"📩 *Admin javobi!*\n\n"
                    text += f"💬 *Javob:*\n{reply}\n\n"
                    text += f"🕐 *Vaqt:* {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                    
                    import asyncio
                    async def send_msg():
                        await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
                    asyncio.run(send_msg())
                except Exception as e:
                    print(f"Telegram reply xato: {e}")
            except:
                pass
    
    feedbacks = Feedback.objects.all().order_by('-created_at')
    unread = feedbacks.filter(is_replied=False).count()
    
    context = {
        'page': 'feedbacks',
        'feedbacks': feedbacks,
        'unread_count': unread,
    }
    return render(request, 'admins/feedbacks.html', context)


def superadmin_users_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    from users.models import User
    from restaurants.models import Order
    
    # Search and filter
    search = request.GET.get('search', '')
    users_list = User.objects.all().order_by('-date_joined')
    
    if search:
        users_list = users_list.filter(
            DQ(first_name__icontains=search) |
            DQ(last_name__icontains=search) |
            DQ(email__icontains=search) |
            DQ(phone__icontains=search)
        )
    
    # Get user statistics
    total_users = User.objects.count()
    users_with_orders_count = Order.objects.exclude(user_id=0).values('user_id').distinct().count()
    users_without_orders = total_users - users_with_orders_count
    
    # Get orders per user
    user_ids = list(users_list.values_list('id', flat=True))
    user_order_counts = {}
    for uid in user_ids:
        count = Order.objects.filter(user_id=uid).count()
        user_order_counts[uid] = count
    
    # Prepare users for template
    users_list_prepared = []
    for user in users_list:
        users_list_prepared.append({
            'id': user.id,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'email': user.email or '',
            'phone': user.phone or '-',
            'date_joined': user.date_joined,
            'order_count': user_order_counts.get(user.id, 0),
        })
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    paginated_users = users_list_prepared[start:end]
    
    total_pages = (total_users + per_page - 1) // per_page
    
    context = {
        'page': 'users',
        'users': paginated_users,
        'stats': {
            'total_users': total_users,
            'users_with_orders_count': users_with_orders_count,
            'users_without_orders': users_without_orders,
        },
        'search': search,
        'current_page': page,
        'total_pages': total_pages,
    }
    return render(request, 'admins/users.html', context)


def superadmin_orders_view(request):
    if not _check_superadmin_auth(request):
        return redirect('/admin-login/')
    
    from restaurants.models import Order
    
    # Filter by restaurant
    restaurant_id = request.GET.get('restaurant_id')
    status_filter = request.GET.get('status')
    
    orders = Order.objects.select_related('restaurant', 'table').order_by('-created_at')
    
    if restaurant_id:
        orders = orders.filter(restaurant_id=restaurant_id)
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    orders = orders[:100]
    
    # Get all restaurants for filter
    restaurants = Restaurant.objects.all()
    
    context = {
        'page': 'orders',
        'orders': orders,
        'restaurants': restaurants,
        'selected_restaurant': int(restaurant_id) if restaurant_id else None,
        'selected_status': status_filter,
    }
    return render(request, 'admins/orders.html', context)


def restaurant_chat_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    from restaurants.models import ChatMessage
    
    restaurant = Restaurant.objects.get(id=restaurant_id)
    
    # First handle POST - save message BEFORE loading messages
    chat_success = None
    chat_error = None
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        admin = RestaurantAdmin.objects.filter(restaurant_id=restaurant_id).first()
        if message and admin:
            # Get sender name safely
            try:
                sender_name = admin.username
                if hasattr(admin, 'user') and admin.user:
                    if admin.user.first_name:
                        sender_name = admin.user.first_name
            except:
                sender_name = admin.username
            
            # Check for duplicate
            last_msg = ChatMessage.objects.filter(
                restaurant_id=restaurant_id,
                sender_type='restaurant'
            ).order_by('-created_at').first()
            
            # Only create if different from last
            try:
                if not last_msg or last_msg.message != message:
                    ChatMessage.objects.create(
                        restaurant_id=restaurant_id,
                        sender_type='restaurant',
                        sender_name=sender_name,
                        message=message,
                    )
                    chat_success = 'Xabar muvaffaqiyatli yuborildi!'
                else:
                    chat_success = 'Xabar qayta yuborilmadi (bir xil xabar)!'
            except Exception as e:
                chat_error = f'Xatolik: {str(e)}'
    
    # NOW load messages after POST is handled
    messages = ChatMessage.objects.filter(
        restaurant_id=restaurant_id
    ).order_by('created_at')
    
    ChatMessage.objects.filter(
        restaurant_id=restaurant_id,
        sender_type='superadmin',
        is_read=False
    ).update(is_read=True)
    
    context = {
        'restaurant': restaurant,
        'page': 'chat',
        'messages': messages,
    }
    if chat_error:
        context['chat_error'] = chat_error
    elif chat_success:
        context['chat_success'] = chat_success
    return render(request, 'admins/restaurant_chat.html', context)


def _check_superadmin_auth(request):
    admin_data = request.session.get('admin_data')
    if not admin_data:
        return False
    return admin_data.get('type') == 'superadmin'


def _check_restaurant_admin_auth(request, restaurant_id):
    admin_data = request.session.get('admin_data')
    if not admin_data:
        return False
    restaurant_val = admin_data.get('restaurant_id') or admin_data.get('restaurant')
    return str(restaurant_val) == str(restaurant_id)


# Restaurant Admin Views
def restaurant_admin_dashboard(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/admin-login/')
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    today_revenue = DailyRevenue.objects.filter(restaurant=restaurant, date=today).first()
    
    month_revenues = DailyRevenue.objects.filter(restaurant=restaurant, date__gte=month_start)
    month_revenue = month_revenues.aggregate(Sum('revenue'))['revenue__sum'] or 0
    month_expenses = Expense.objects.filter(restaurant=restaurant, date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_tables = Table.objects.filter(restaurant=restaurant).count()
    available_tables = Table.objects.filter(restaurant=restaurant, is_available=True).count()
    
    today_bookings = Booking.objects.filter(restaurant=restaurant, booking_date=today).count()
    
    avg_rating = Review.objects.filter(restaurant=restaurant).aggregate(Avg('rating'))['rating__avg'] or 0
    
    menu_items = MenuItem.objects.filter(restaurant=restaurant).count()
    staff_count = Staff.objects.filter(restaurant=restaurant, is_active=True).count()
    
    context = {
        'restaurant': restaurant,
        'stats': {
            'today_revenue': float(today_revenue.revenue if today_revenue else 0),
            'today_orders': today_revenue.orders_count if today_revenue else 0,
            'month_revenue': float(month_revenue),
            'month_expenses': float(month_expenses),
            'net_profit': float(month_revenue) - float(month_expenses),
            'total_tables': total_tables,
            'available_tables': available_tables,
            'occupied_tables': total_tables - available_tables,
            'today_bookings': today_bookings,
            'avg_rating': float(avg_rating),
            'menu_items': menu_items,
            'staff_count': staff_count,
        }
    }
    return render(request, 'admins/restaurant_dashboard.html', context)


def restaurant_orders_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/restaurant-admin-login/')
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        
        try:
            order = Order.objects.get(id=order_id, restaurant=restaurant)
            old_status = order.status
            
            if action == 'confirm':
                order.status = 'confirmed'
                order.save()
                _create_order_notification(order, 'Qabul qilindi', 'Buyurtmangiz qabul qilindi!')
            elif action == 'preparing':
                order.status = 'preparing'
                order.save()
                _create_order_notification(order, 'Tayyorlanmoqda', 'Buyurtmangiz tayyorlanmoqda!')
            elif action == 'ready':
                order.status = 'ready'
                order.save()
                _create_order_notification(order, 'Tayyor!', 'Buyurtmangiz tayyor! Yetkazib olishingiz mumkin.')
            elif action == 'delivered':
                order.status = 'delivered'
                order.save()
                _create_order_notification(order, 'Yetkazildi', 'Buyurtmangiz yetkazildi!')
            elif action == 'cancelled':
                order.status = 'cancelled'
                order.save()
                _create_order_notification(order, 'Bekor qilindi', 'Buyurtmangiz bekor qilindi.')
        except Exception as e:
            pass
        
        return redirect(f'/restaurant-admin/{restaurant_id}/orders/')
    
    orders = Order.objects.filter(restaurant=restaurant).select_related('table').order_by('-created_at')[:50]
    
    pending_count = Order.objects.filter(restaurant=restaurant, status='pending').count()
    confirmed_count = Order.objects.filter(restaurant=restaurant, status='confirmed').count()
    preparing_count = Order.objects.filter(restaurant=restaurant, status='preparing').count()
    ready_count = Order.objects.filter(restaurant=restaurant, status='ready').count()
    
    context = {
        'restaurant': restaurant,
        'page': 'orders',
        'orders': orders,
        'pending_orders': pending_count,
        'confirmed_orders': confirmed_count,
        'preparing_orders': preparing_count,
        'ready_orders': ready_count,
    }
    return render(request, 'admins/restaurant_orders.html', context)


def _create_order_notification(order, title, message):
    try:
        Notification.objects.create(
            admin=RestaurantAdmin.objects.filter(restaurant=order.restaurant).first(),
            title=f'Buyurtma #{order.id}: {title}',
            message=f'{order.user_name} - {message}',
            notification_type='order',
            related_id=order.id
        )
    except:
        pass


def restaurant_bookings_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/restaurant-admin-login/')
    
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        
        try:
            booking = Booking.objects.get(id=booking_id, restaurant=restaurant)
            
            if action == 'confirm':
                booking.is_confirmed = True
                booking.save()
                table = booking.table
                table.is_available = False
                table.save()
                
                # Eventga bog'liq bron bo'lsa, taklifnomalar yuborish
                if booking.event:
                    event = booking.event
                    event.status = 'active'
                    event.save()
                    
                    # Taklifnomalar yuborish
                    invitations = EventInvitation.objects.filter(event=event)
                    for inv in invitations:
                        try:
                            import requests
                            bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
                            text = f"🎉 *Tasdiqlandi!* 🎉\n\n"
                            text += f"Tadbir: {event.title}\n"
                            text += f"📍 Restoran: {event.restaurant.name}\n"
                            text += f"📅 Sana: {event.event_date}\n"
                            text += f"⏰ Vaqt: {event.event_time}\n"
                            text += f"👥 Joylar soni: {event.max_guests}\n\n"
                            text += "Sizning taklifnomaingiz tasdiqlandi!"
                            
                            requests.post(
                                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                                json={'chat_id': inv.guest_phone.replace('+', ''), 'text': text, 'parse_mode': 'Markdown'},
                                timeout=10,
                            )
                        except Exception as e:
                            print(f"Taklifnoma yuborish xato: {e}")
            elif action == 'cancel':
                table = booking.table
                table.is_available = True
                table.save()
                booking.delete()
            elif action == 'complete':
                booking.is_confirmed = False
                booking.save()
                table = booking.table
                table.is_available = True
                table.save()
        except Exception as e:
            pass
        
        return redirect(f'/restaurant-admin/{restaurant_id}/bookings/')


def confirm_booking(request, restaurant_id, booking_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        booking = Booking.objects.get(id=booking_id, restaurant_id=restaurant_id)
        booking.is_confirmed = True
        booking.save()
        
        table = booking.table
        table.is_available = False
        table.save()
        
        if booking.event:
            event = booking.event
            event.status = 'active'
            event.save()
            
            invitations = EventInvitation.objects.filter(event=event)
            for inv in invitations:
                try:
                    import requests
                    bot_token = '8433417347:AAHtctEF2mDuhdUpbV43cw_cQoho4-keOk4'
                    text = f"🎉 *Tasdiqlandi!* 🎉\n\n"
                    text += f"Tadbir: {event.title}\n"
                    text += f"📍 Restoran: {event.restaurant.name}\n"
                    text += f"📅 Sana: {event.event_date}\n"
                    text += f"⏰ Vaqt: {event.event_time}\n"
                    text += f"👥 Joylar soni: {event.max_guests}\n\n"
                    text += "Sizning taklifnomaingiz tasdiqlandi!"
                    
                    requests.post(
                        f'https://api.telegram.org/bot{bot_token}/sendMessage',
                        json={'chat_id': inv.guest_phone.replace('+', ''), 'text': text, 'parse_mode': 'Markdown'},
                        timeout=10,
                    )
                except Exception as e:
                    print(f"Taklifnoma yuborish xato: {e}")
    except Exception as e:
        print(f"Booking confirm xato: {e}")
    
    return redirect(f'/restaurant-admin/{restaurant_id}/bookings/')


def cancel_booking(request, restaurant_id, booking_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        booking = Booking.objects.get(id=booking_id, restaurant_id=restaurant_id)
        
        table = booking.table
        table.is_available = True
        table.save()
        
        booking.delete()
    except Exception as e:
        print(f"Booking cancel xato: {e}")
    
    return redirect(f'/restaurant-admin/{restaurant_id}/bookings/')


def restaurant_bookings_view(request, restaurant_id):
    
    today = timezone.now().date()
    
    # Booking modelidan bronlar
    upcoming_bookings = Booking.objects.filter(
        restaurant=restaurant, 
        booking_date__gte=today
    ).select_related('table').order_by('booking_date', 'booking_time')
    
    today_bookings = Booking.objects.filter(
        restaurant=restaurant, 
        booking_date=today
    ).select_related('table').order_by('booking_time')
    
    # Order modelidan bronlar (stol bron qilinganda)
    today_orders = Order.objects.filter(
        restaurant=restaurant,
        booking_date_time__isnull=False
    ).order_by('-booking_date_time')[:50]
    
    # Bugungi bronlar va buyurtmalarni birlashtirish
    all_bookings = []
    
    # Booking larni qo'shish
    for b in today_bookings:
        booking_data = {
            'type': 'booking',
            'id': b.id,
            'user_name': b.customer_name,
            'phone': b.customer_phone,
            'guest_count': b.guest_count,
            'date_time': f"{b.booking_date} {b.booking_time}" if b.booking_time else b.booking_date,
            'table': b.table.table_number if b.table else '-',
            'status': 'confirmed' if b.is_confirmed else 'pending',
            'is_event': b.event is not None,
            'event_title': b.event.title if b.event else None,
            'note': b.note or '',
        }
        all_bookings.append(booking_data)
    
    # Order larni qo'shish
    for o in today_orders:
        all_bookings.append({
            'type': 'order',
            'id': o.id,
            'user_name': o.user_name,
            'phone': o.phone,
            'guest_count': 1,
            'date_time': o.booking_date_time,
            'table': o.table.table_number if o.table else '-',
            'status': o.status,
            'note': o.note or '',
        })
    
    context = {
        'restaurant': restaurant,
        'page': 'bookings',
        'today_bookings': today_bookings,
        'upcoming_bookings': upcoming_bookings,
        'all_bookings': all_bookings,
    }
    return render(request, 'admins/restaurant_bookings.html', context)


def restaurant_tables_view(request, restaurant_id):
    from django.contrib import messages
    
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/restaurant-admin-login/')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_table':
            table_number = request.POST.get('table_number')
            capacity = request.POST.get('capacity', 4)
            
            try:
                Table.objects.create(
                    restaurant=restaurant,
                    table_number=table_number,
                    capacity=capacity,
                    is_available=True
                )
            except Exception as e:
                pass
        
        elif action == 'generate_qr':
            table_id = request.POST.get('table_id')
            try:
                table = Table.objects.get(id=table_id, restaurant=restaurant)
                TableQR.objects.get_or_create(
                    table=table,
                    defaults={'qr_token': generate_qr_token()}
                )
            except Exception as e:
                pass
        
        elif action == 'generate_all_qr':
            tables = Table.objects.filter(restaurant=restaurant)
            for table in tables:
                TableQR.objects.get_or_create(
                    table=table,
                    defaults={'qr_token': generate_qr_token()}
                )
        
        elif action == 'download_qr_pdf':
            from io import BytesIO
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            from reportlab.lib import colors
            import qrcode
            import tempfile
            import os
            
            tables = Table.objects.filter(restaurant=restaurant)
            if not tables:
                return redirect(f'/restaurant-admin/{restaurant_id}/tables/')
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            cols = 4
            rows = 5
            per_page = cols * rows
            
            margin_x = 15
            margin_y = 15
            cell_width = (width - 2 * margin_x) / cols
            cell_height = (height - 2 * margin_y - 30) / rows
            
            qr_size = 70
            
            page_num = 0
            rest_name = restaurant.name
            
            green_color = colors.Color(0, 0.7, 0)
            blue_color = colors.Color(0, 0.5, 0.9)
            orange_color = colors.Color(1, 0.5, 0)
            
            for idx, table in enumerate(tables):
                if idx % per_page == 0:
                    if idx > 0:
                        c.showPage()
                    page_num += 1
                    c.setFont("Helvetica", 8)
                    c.drawString(30, height - 15, f"{rest_name} - Sahifa {page_num}")
                
                col = idx % cols
                row = idx // cols % rows
                
                x = margin_x + col * cell_width + 3
                y = height - margin_y - 20 - (row + 1) * cell_height + 3
                
                c.setLineWidth(0.5)
                c.setLineWidth(0.5)
                c.rect(x, y, cell_width - 6, cell_height - 6)
                
                qr_data = f"LOCEATS:{restaurant.id}:{table.id}"
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(qr_data)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                img_buffer = BytesIO()
                qr_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                qr_x = x + (cell_width - 6) / 2 - qr_size / 2
                qr_y = y + cell_height - 6 - qr_size - 15
                c.drawImage(ImageReader(img_buffer), qr_x, qr_y, width=qr_size, height=qr_size)
                
                loc_y = qr_y - 10
                c.setFont("Helvetica-Bold", 11)
                center_x = x + cell_width / 2 - 3 + 5
                c.setFillColor(orange_color)
                c.drawCentredString(center_x - 22, loc_y, "Loc")
                c.setFillColor(blue_color)
                c.drawCentredString(center_x + 3, loc_y, "Eats")
                c.setFillColor(colors.black)
                
                name_y = loc_y - 18
                c.setFont("Helvetica", 8)
                c.drawCentredString(x + cell_width / 2 - 3, name_y, rest_name)
                
                table_y = name_y - 20
                c.setFont("Helvetica-Bold", 12)
                c.drawCentredString(x + cell_width / 2 - 3, table_y, f"Stol {table.table_number}")
            
            c.save()
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{restaurant.name.replace(" ", "_")}_QR_codes.pdf"'
            return response
        
        return redirect(f'/restaurant-admin/{restaurant_id}/tables/')
    
    tables = Table.objects.filter(restaurant=restaurant)
    qrs = TableQR.objects.filter(restaurant=restaurant)
    
    context = {
        'restaurant': restaurant,
        'tables': tables,
        'qrs': qrs,
    }
    return render(request, 'admins/restaurant_tables.html', context)


def restaurant_menu_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_availability':
            item_id = request.POST.get('item_id')
            try:
                menu_item = MenuItem.objects.get(id=item_id, restaurant=restaurant)
                menu_item.is_available = not menu_item.is_available
                menu_item.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'edit':
            item_id = request.POST.get('item_id')
            try:
                menu_item = MenuItem.objects.get(id=item_id, restaurant=restaurant)
                menu_item.name = request.POST.get('name')
                menu_item.price = request.POST.get('price')
                menu_item.description = request.POST.get('description', '')
                menu_item.item_type = request.POST.get('item_type', 'food')
                category_id = request.POST.get('category')
                menu_item.category = MenuCategory.objects.get(id=category_id) if category_id else None
                menu_item.is_available = request.POST.get('is_available') == 'on'
                
                if request.FILES.get('image'):
                    menu_item.image = request.FILES.get('image')
                
                menu_item.save()
            except Exception as e:
                pass
            
        elif action == 'promotion':
            item_id = request.POST.get('item_id')
            promo_enabled = request.POST.get('promo_enabled') == '1'
            
            try:
                menu_item = MenuItem.objects.get(id=item_id, restaurant=restaurant)
                
                if promo_enabled:
                    menu_item.is_promotion = True
                    menu_item.promotion_title = request.POST.get('promotion_title', 'Aksiya')
                    menu_item.promotion_price = request.POST.get('promotion_price')
                    menu_item.discount_percent = request.POST.get('discount_percent', 10)
                else:
                    menu_item.is_promotion = False
                    menu_item.promotion_title = ''
                    menu_item.promotion_price = None
                    menu_item.discount_percent = 0
                
                menu_item.save()
            except Exception as e:
                pass
            
        else:
            name = request.POST.get('name')
            price = request.POST.get('price')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category')
            item_type = request.POST.get('item_type', 'food')
            
            try:
                category = None
                if category_id:
                    category = MenuCategory.objects.get(id=category_id)
                
                menu_item = MenuItem(
                    restaurant=restaurant,
                    name=name,
                    description=description,
                    price=price,
                    category=category,
                    item_type=item_type,
                    is_available=True
                )
                
                if request.FILES.get('image'):
                    menu_item.image = request.FILES.get('image')
                
                menu_item.save()
            except Exception as e:
                pass
        
        return redirect(f'/restaurant-admin/{restaurant_id}/menu/')
    
    # Check if restaurant admin has promotion permission
    # First check from session, then fallback to restaurant's admin
    can_add_promo = False
    
    # Get admin from session
    admin_data = request.session.get('admin_data')
    if admin_data:
        admin_id = admin_data.get('id')
        if admin_id:
            try:
                admin = RestaurantAdmin.objects.get(id=admin_id)
                can_add_promo = admin.can_add_promotion
            except RestaurantAdmin.DoesNotExist:
                pass
    
    # Fallback: check restaurant's admin
    if not can_add_promo and restaurant.admin:
        can_add_promo = restaurant.admin.can_add_promotion
    
    items = MenuItem.objects.filter(restaurant=restaurant).select_related('category')
    categories = MenuCategory.objects.all()
    
    context = {
        'restaurant': restaurant,
        'menu_items': items,
        'categories': categories,
        'can_add_promotion': can_add_promo,
    }
    return render(request, 'admins/restaurant_menu.html', context)


def restaurant_reviews_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/admin-login/')
    
    from restaurants.models import Review
    from django.utils import timezone
    
    if request.method == 'POST':
        action = request.POST.get('action')
        review_id = request.POST.get('review_id')
        
        try:
            review = Review.objects.get(id=review_id, restaurant=restaurant)
            
            if action == 'delete':
                review.delete()
            elif action == 'respond':
                response_text = request.POST.get('response', '').strip()
                if response_text:
                    review.admin_response = response_text
                    review.save()
        except Review.DoesNotExist:
            pass
        
        return redirect(f'/restaurant-admin/{restaurant_id}/reviews/')
    
    reviews = Review.objects.filter(restaurant=restaurant).order_by('-created_at')
    
    # Statistics
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    five_stars = reviews.filter(rating=5).count()
    four_stars = reviews.filter(rating=4).count()
    three_stars = reviews.filter(rating=3).count()
    two_stars = reviews.filter(rating=2).count()
    one_star = reviews.filter(rating=1).count()
    
    context = {
        'restaurant': restaurant,
        'page': 'reviews',
        'reviews': reviews,
        'stats': {
            'total': total_reviews,
            'avg_rating': round(avg_rating, 1),
            'five_stars': five_stars,
            'four_stars': four_stars,
            'three_stars': three_stars,
            'two_stars': two_stars,
            'one_star': one_star,
        }
    }
    return render(request, 'admins/restaurant_reviews.html', context)


def restaurant_staff_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_staff':
            full_name = request.POST.get('full_name')
            position = request.POST.get('position')
            phone = request.POST.get('phone')
            salary = request.POST.get('salary')
            username = request.POST.get('username')
            password = request.POST.get('password')
            can_manage_orders = request.POST.get('can_manage_orders') == 'on'
            can_manage_bookings = request.POST.get('can_manage_bookings') == 'on'
            can_manage_warehouse = request.POST.get('can_manage_warehouse') == 'on'
            
            import random
            import string
            
            # Auto-generate username if not provided
            if not username:
                base_username = full_name.lower().replace(' ', '_')[:10]
                if len(base_username) < 3:
                    base_username = f"staff_{random.randint(100, 999)}"
                username = base_username
                # Ensure unique per restaurant
                counter = 1
                while Staff.objects.filter(restaurant=restaurant, username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
            
            # Auto-generate password if not provided
            if not password:
                password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            
            plain_password = password  # Save plain for display
            
            try:
                staff = Staff.objects.create(
                    restaurant=restaurant,
                    full_name=full_name,
                    position=position,
                    phone=phone,
                    salary=salary,
                    username=username,
                    can_manage_orders=can_manage_orders,
                    can_manage_bookings=can_manage_bookings,
                    can_manage_warehouse=can_manage_warehouse,
                    is_active=True
                )
                staff.set_password(plain_password)
                staff.save()
                
                # Store plain for display in session
                request.session['last_staff_credentials'] = {
                    'username': username,
                    'password': plain_password
                }
            except Exception as e:
                pass
        
        # Edit staff
        if action == 'edit_staff':
            staff_id = request.POST.get('staff_id')
            full_name = request.POST.get('full_name')
            position = request.POST.get('position')
            phone = request.POST.get('phone')
            salary = request.POST.get('salary')
            can_manage_orders = request.POST.get('can_manage_orders') == 'on'
            can_manage_bookings = request.POST.get('can_manage_bookings') == 'on'
            can_manage_warehouse = request.POST.get('can_manage_warehouse') == 'on'
            new_password = request.POST.get('new_password')
            is_active = request.POST.get('is_active') == 'on'
            
            try:
                staff = Staff.objects.get(id=staff_id, restaurant=restaurant)
                staff.full_name = full_name
                staff.position = position
                staff.phone = phone
                staff.salary = salary
                staff.can_manage_orders = can_manage_orders
                staff.can_manage_bookings = can_manage_bookings
                staff.can_manage_warehouse = can_manage_warehouse
                staff.is_active = is_active
                if new_password:
                    import random
                    import string
                    staff.set_password(new_password)
                    request.session['last_staff_credentials'] = {
                        'username': staff.username,
                        'password': new_password
                    }
                staff.save()
            except Exception as e:
                pass
        
        # Delete staff
        if action == 'delete_staff':
            staff_id = request.POST.get('staff_id')
            try:
                Staff.objects.filter(id=staff_id, restaurant=restaurant).delete()
            except Exception as e:
                pass
        
        return redirect(f'/restaurant-admin/{restaurant_id}/staff/')
    
    staff = Staff.objects.filter(restaurant=restaurant)
    total_salary = staff.filter(is_active=True).aggregate(Sum('salary'))['salary__sum'] or 0
    
    # Get last created staff credentials if exists
    new_staff = request.session.pop('last_staff_credentials', None)
    
    context = {
        'restaurant': restaurant,
        'staff': staff,
        'total_salary': float(total_salary),
        'new_staff': new_staff,
    }
    return render(request, 'admins/restaurant_staff.html', context)


def restaurant_expenses_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/admin-login/')
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        date = request.POST.get('date')
        
        try:
            category = None
            if category_id:
                category = ExpenseCategory.objects.get(id=category_id)
            
            Expense.objects.create(
                restaurant=restaurant,
                category=category,
                amount=amount,
                description=description,
                date=date or timezone.now().date()
            )
        except Exception as e:
            pass
        
        return redirect(f'/restaurant-admin/{restaurant_id}/expenses/')
    
    expenses = Expense.objects.filter(restaurant=restaurant).select_related('category').order_by('-date')[:50]
    categories = ExpenseCategory.objects.all()
    
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'restaurant': restaurant,
        'expenses': expenses,
        'categories': categories,
        'total_expenses': float(total_expenses),
    }
    return render(request, 'admins/restaurant_expenses.html', context)


def restaurant_revenue_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/restaurant-admin-login/')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        revenue = request.POST.get('revenue')
        orders_count = request.POST.get('orders_count', 0)
        
        try:
            DailyRevenue.objects.create(
                restaurant=restaurant,
                date=date or timezone.now().date(),
                revenue=revenue,
                orders_count=orders_count,
                average_check=int(revenue) // int(orders_count) if orders_count and int(orders_count) > 0 else 0
            )
        except Exception as e:
            pass
        
        return redirect(f'/restaurant-admin/{restaurant_id}/revenue/')
    
    revenues = DailyRevenue.objects.filter(restaurant=restaurant).order_by('-date')[:30]
    
    context = {
        'restaurant': restaurant,
        'revenues': revenues,
    }
    return render(request, 'admins/restaurant_revenue.html', context)


def restaurant_kpi_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/restaurant-admin-login/')
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    month_revenues = DailyRevenue.objects.filter(restaurant=restaurant, date__gte=month_start)
    year_revenues = DailyRevenue.objects.filter(restaurant=restaurant, date__gte=year_start)
    month_expenses = Expense.objects.filter(restaurant=restaurant, date__gte=month_start)
    
    month_revenue = month_revenues.aggregate(Sum('revenue'))['revenue__sum'] or 0
    month_expense = month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    year_revenue = year_revenues.aggregate(Sum('revenue'))['revenue__sum'] or 0
    
    month_orders = month_revenues.aggregate(Sum('orders_count'))['orders_count__sum'] or 0
    month_avg_check = month_revenues.aggregate(Avg('average_check'))['average_check__avg'] or 0
    
    total_staff = Staff.objects.filter(restaurant=restaurant, is_active=True).count()
    total_salary = Staff.objects.filter(restaurant=restaurant, is_active=True).aggregate(Sum('salary'))['salary__sum'] or 0
    
    context = {
        'restaurant': restaurant,
        'kpi': {
            'month_revenue': float(month_revenue),
            'month_expenses': float(month_expense),
            'month_profit': float(month_revenue) - float(month_expense),
            'month_profit_margin': round(((float(month_revenue) - float(month_expense)) / float(month_revenue) * 100) if month_revenue > 0 else 0, 1),
            'year_revenue': float(year_revenue),
            'month_orders': month_orders,
            'month_avg_check': float(month_avg_check),
            'total_staff': total_staff,
            'total_salary': float(total_salary),
            'salary_percent': round((float(total_salary) / float(month_revenue) * 100) if month_revenue > 0 else 0, 1),
        }
    }
    return render(request, 'admins/restaurant_kpi.html', context)


def restaurant_attendance_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/restaurant-admin-login/')
    
    from restaurants.models import Employee, Attendance
    from datetime import date, timedelta
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    if request.method == 'POST':
        if 'add_employee' in request.POST:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone = request.POST.get('phone')
            role = request.POST.get('role')
            salary = request.POST.get('salary', 0)
            hire_date = request.POST.get('hire_date')
            
            Employee.objects.create(
                restaurant=restaurant,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role,
                salary=salary,
                hire_date=hire_date,
            )
        
        elif 'check_in' in request.POST:
            employee_id = request.POST.get('employee_id')
            try:
                emp = Employee.objects.get(id=employee_id)
                Attendance.objects.create(
                    employee=emp,
                    date=today,
                    check_in=timezone.now().time(),
                    status='present',
                )
            except Employee.DoesNotExist:
                pass
        
        elif 'check_out' in request.POST:
            employee_id = request.POST.get('employee_id')
            att = Attendance.objects.filter(employee_id=employee_id, date=today, check_out__isnull=True).first()
            if att:
                att.check_out = timezone.now().time()
                check_in_dt = timezone.now().replace(hour=att.check_in.hour, minute=att.check_in.minute)
                check_out_dt = timezone.now()
                hours = (check_out_dt - check_in_dt.replace(second=0, microsecond=0)).seconds / 3600
                att.hours_worked = round(hours, 1)
                att.save()
        
        return redirect(f'/restaurant-admin/{restaurant_id}/attendance/')
    
    employees = Employee.objects.filter(restaurant=restaurant, status='active')
    today_attendances = Attendance.objects.filter(employee__restaurant=restaurant, date=today)
    
    # Oylik statistika
    month_attendances = Attendance.objects.filter(employee__restaurant=restaurant, date__gte=month_start)
    
    # Har bir xodim uchun oylik stats
    employee_stats = []
    for emp in employees:
        emp_att = month_attendances.filter(employee=emp)
        total_hours = sum([float(a.hours_worked or 0) for a in emp_att])
        days_worked = emp_att.count()
        emp_salary = float(emp.salary or 0)
        
        employee_stats.append({
            'id': emp.id,
            'name': f"{emp.first_name} {emp.last_name}",
            'role': emp.role,
            'phone': emp.phone,
            'salary': emp_salary,
            'days_worked': days_worked,
            'total_hours': round(total_hours, 1),
        })
    
    context = {
        'restaurant': restaurant,
        'page': 'attendance',
        'employees': employees,
        'today_attendances': today_attendances,
        'employee_stats': employee_stats,
        'today': today,
    }
    return render(request, 'admins/restaurant_attendance.html', context)


def restaurant_warehouse_view(request, restaurant_id):
    if not _check_restaurant_admin_auth(request, restaurant_id):
        return redirect('/restaurant-admin-login/')
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return redirect('/restaurant-admin-login/')
    
    from restaurants.models import WarehouseItem, InventoryEntry
    
    if request.method == 'POST':
        if 'add_item' in request.POST:
            name = request.POST.get('name')
            category = request.POST.get('category')
            unit = request.POST.get('unit')
            quantity = request.POST.get('quantity', 0)
            min_quantity = request.POST.get('min_quantity', 0)
            price = request.POST.get('price', 0)
            supplier = request.POST.get('supplier', '')
            
            WarehouseItem.objects.create(
                restaurant=restaurant,
                name=name,
                category=category,
                unit=unit,
                quantity=quantity,
                min_quantity=min_quantity,
                price=price,
                supplier=supplier,
            )
        
        elif 'add_entry' in request.POST:
            item_id = request.POST.get('item_id')
            entry_type = request.POST.get('entry_type')
            entry_quantity = request.POST.get('entry_quantity')
            entry_price = request.POST.get('entry_price', 0)
            
            item = WarehouseItem.objects.get(id=item_id)
            InventoryEntry.objects.create(
                warehouse_item=item,
                entry_type=entry_type,
                quantity=entry_quantity,
                price=entry_price,
                created_by=request.session.get('admin_data', {}).get('username', 'Admin'),
            )
            
            if entry_type == 'in':
                item.quantity = float(item.quantity) + float(entry_quantity)
            elif entry_type == 'out':
                item.quantity = max(0, float(item.quantity) - float(entry_quantity))
            item.save()
        
        return redirect(f'/restaurant-admin/{restaurant_id}/warehouse/')
    
    items = WarehouseItem.objects.filter(restaurant=restaurant)
    low_stock_items = [item for item in items if float(item.quantity) <= float(item.min_quantity)]
    recent_entries = InventoryEntry.objects.filter(warehouse_item__restaurant=restaurant)[:20]
    
    context = {
        'restaurant': restaurant,
        'page': 'warehouse',
        'items': items,
        'low_stock_items': low_stock_items,
        'recent_entries': recent_entries,
    }
    return render(request, 'admins/restaurant_warehouse.html', context)


# Simple order update for staff
def simple_update_order(request, restaurant_id, order_id):
    if request.method != 'POST':
        return redirect(f'/staff/{restaurant_id}/orders/')
    
    if 'staff_token' not in request.session:
        return redirect('/staff-login/')
    
    staff_data = request.session.get('staff_data', {})
    if str(staff_data.get('restaurant_id')) != str(restaurant_id):
        return redirect('/staff-login/')
    
    if not staff_data.get('can_manage_orders'):
        return redirect(f'/staff/{restaurant_id}/orders/')
    
    new_status = request.POST.get('status')
    valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed']
    
    if new_status in valid_statuses:
        try:
            from restaurants.models import Order
            order = Order.objects.get(id=order_id, restaurant_id=restaurant_id)
            order.status = new_status
            order.save()
        except:
            pass
    
    return redirect(f'/staff/{restaurant_id}/orders/')
