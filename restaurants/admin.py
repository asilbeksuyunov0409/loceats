from django.contrib import admin
from .models import Category, Restaurant, Table, Booking, MenuCategory, MenuItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'address', 'rating', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'address']
    list_editable = ['is_active']

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['id', 'restaurant', 'table_number', 'capacity', 'is_available']
    list_filter = ['restaurant', 'is_available']
    search_fields = ['table_number']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'restaurant', 'table', 'booking_date', 'booking_time', 'is_confirmed']
    list_filter = ['restaurant', 'booking_date', 'is_confirmed']
    search_fields = ['customer_name', 'customer_phone']
    list_editable = ['is_confirmed']

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'restaurant', 'price', 'item_type', 'category', 'is_available']
    list_filter = ['restaurant', 'item_type', 'category', 'is_available']
    search_fields = ['name', 'restaurant__name']
    list_editable = ['is_available', 'price']
