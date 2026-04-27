from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db import IntegrityError
from .models import User

class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    
    def create(self, validated_data):
        email = validated_data['email']
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone=validated_data.get('phone', ''),
            )
            return user
        except IntegrityError:
            raise serializers.ValidationError({'email': 'Bu email allaqachon ro\'yxatdan o\'tgan'})

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        email = data['email']
        username = email.split('@')[0]
        user = authenticate(username=username, password=data['password'])
        if not user:
            raise serializers.ValidationError('Email yoki parol noto\'g\'ri')
        if not user.is_active:
            raise serializers.ValidationError('Hisob faol emas')
        data['user'] = user
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone']
