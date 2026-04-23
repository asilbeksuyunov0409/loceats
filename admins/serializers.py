from rest_framework import serializers
from .models import (
    SuperAdmin, RestaurantAdmin, ExpenseCategory, 
    Expense, DailyRevenue, Staff, TableQR, Notification
)

class SuperAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperAdmin
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'is_active', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}


class RestaurantAdminSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = RestaurantAdmin
        fields = [
            'id', 'username', 'email', 'full_name', 'phone', 
            'restaurant', 'restaurant_name', 'status', 'is_active', 
            'created_at', 'last_login'
        ]
        extra_kwargs = {'password': {'write_only': True}}


class RestaurantAdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = RestaurantAdmin
        fields = ['username', 'email', 'password', 'full_name', 'phone', 'restaurant']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        admin = RestaurantAdmin(**validated_data)
        admin.set_password(password)
        admin.save()
        return admin


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    admin_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'restaurant', 'category', 'category_name', 
            'amount', 'description', 'date', 'created_by', 
            'admin_name', 'created_at'
        ]


class DailyRevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyRevenue
        fields = [
            'id', 'restaurant', 'date', 'revenue', 
            'orders_count', 'average_check', 'created_at'
        ]


class StaffSerializer(serializers.ModelSerializer):
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'id', 'restaurant', 'full_name', 'position', 
            'position_display', 'phone', 'salary', 
            'is_active', 'hire_date'
        ]


class TableQRSerializer(serializers.ModelSerializer):
    table_number = serializers.CharField(source='table.table_number', read_only=True)
    
    class Meta:
        model = TableQR
        fields = ['id', 'restaurant', 'table', 'table_number', 'qr_token', 'is_active', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'is_read', 'created_at']
