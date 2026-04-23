from rest_framework import serializers
from django.db import models
from .models import (Category, Restaurant, Table, Booking, MenuCategory, MenuItem, 
                   Review, Order, OrderItem, Promotion, QaniKetedikEvent, 
                   EventInvitation, GroupOrder, EventPayment)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class RestaurantListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'phone', 'rating', 'image', 'category_name', 'latitude', 'longitude']
    
    def get_rating(self, obj):
        reviews = Review.objects.filter(restaurant=obj)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0, 1)
        return 0
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image:
            data['image'] = instance.image.url
        else:
            data['image'] = None
        return data

class RestaurantDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    admin_phone = serializers.SerializerMethodField()
    admin_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'phone', 'description', 'rating', 'image', 
                  'category_name', 'category', 'latitude', 'longitude', 'is_active', 'created_at',
                  'admin_phone', 'admin_username']
    
    def get_admin_phone(self, obj):
        if hasattr(obj, 'admin'):
            return obj.admin.phone if obj.admin else ''
        return ''
    
    def get_admin_username(self, obj):
        if hasattr(obj, 'admin'):
            return obj.admin.username if obj.admin else ''
        return ''
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image:
            data['image'] = instance.image.url
        else:
            data['image'] = None
        return data

class PromotionSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Promotion
        fields = ['id', 'restaurant', 'restaurant_name', 'title', 'description', 'image', 
                  'discount_percent', 'is_active', 'start_date', 'end_date']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image:
            data['image'] = instance.image.url
        else:
            data['image'] = None
        return data

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'table_number', 'capacity', 'is_available']

class BookingSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'restaurant', 'restaurant_name', 'table', 'table_number',
                  'customer_name', 'customer_phone', 'booking_date', 'booking_time',
                  'guest_count', 'note', 'is_confirmed', 'created_at']

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name']

class EventSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True)
    guest_count = serializers.SerializerMethodField()
    
    class Meta:
        model = QaniKetedikEvent
        fields = ['id', 'host_user_id', 'host_name', 'host_phone', 'title', 'description',
                'restaurant', 'restaurant_name', 'table', 'table_number',
                'event_date', 'event_time', 'status', 'max_guests',
                'is_checked_in', 'checked_in_at', 'guest_count', 'created_at']
    
    def get_guest_count(self, obj):
        return obj.invitations.count()


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventInvitation
        fields = ['id', 'event', 'guest_user_id', 'guest_phone', 'guest_name',
                'status', 'can_order_food', 'arrived_at', 'created_at']


class GroupOrderSerializer(serializers.ModelSerializer):
    total_amount = serializers.SerializerMethodField()
    items_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupOrder
        fields = ['id', 'event', 'items', 'is_submitted', 'submitted_at',
                'total_amount', 'items_summary', 'created_at']
    
    def get_total_amount(self, obj):
        total = 0
        for item in (obj.items or []):
            total += (item.get('price', 0) * item.get('quantity', 0))
        return total
    
    def get_items_summary(self, obj):
        summary = {}
        for item in (obj.items or []):
            name = item.get('name', 'Noma\'lum')
            qty = item.get('quantity', 0)
            summary[name] = summary.get(name, 0) + qty
        return summary


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPayment
        fields = ['id', 'group_order', 'payer_user_id', 'payer_name', 'amount',
                'method', 'is_settled', 'settled_at', 'created_at']


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = ['id', 'restaurant', 'name', 'description', 'price', 
                  'category', 'category_name', 'item_type', 'is_available',
                  'is_promotion', 'promotion_price', 'promotion_title', 'discount_percent']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image:
            data['image'] = instance.image.url
        else:
            data['image'] = None
        return data

class RestaurantWithMenuSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    menu_items = MenuItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'phone', 'description', 'rating', 'image', 
                  'category_name', 'latitude', 'longitude', 'menu_items']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image:
            data['image'] = instance.image.url
        else:
            data['image'] = None
        return data

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'restaurant', 'user_name', 'user_id', 'rating', 'comment', 'admin_response', 'created_at']
        read_only_fields = ['created_at']

class SearchResultSerializer(serializers.Serializer):
    type = serializers.CharField()
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=0, allow_null=True)
    image = serializers.CharField(allow_null=True)
    restaurant_id = serializers.IntegerField(allow_null=True)
    restaurant_name = serializers.CharField(allow_null=True)
    rating = serializers.DecimalField(max_digits=2, decimal_places=1, allow_null=True)
    address = serializers.CharField(allow_null=True)

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'quantity', 'price', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True, allow_null=True)
    table_id = serializers.IntegerField(source='table.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Order
        fields = ['id', 'restaurant', 'restaurant_name', 'table_id', 'table_number', 
                  'table_token', 'user_name', 'user_id', 'phone', 'total_amount', 
                  'status', 'note', 'booking_date_time', 'items', 'created_at', 'updated_at']

class OrderCreateSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    table_id = serializers.IntegerField(required=False, allow_null=True)
    table_token = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    user_name = serializers.CharField(max_length=100)
    user_id = serializers.IntegerField(default=0)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    booking_date_time = serializers.DateTimeField(required=False, allow_null=True)
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(allow_blank=True)
        )
    )
