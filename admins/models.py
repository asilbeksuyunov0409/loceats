from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class SuperAdmin(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'password']
    
    class Meta:
        verbose_name = 'Superadmin'
        verbose_name_plural = 'Superadminlar'
    
    def __str__(self):
        return self.username


class RestaurantAdmin(models.Model):
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('pending', 'Kutilmoqda'),
        ('blocked', 'Bloklangan'),
    ]
    
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    restaurant = models.OneToOneField('restaurants.Restaurant', on_delete=models.CASCADE, related_name='admin', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    can_add_promotion = models.BooleanField(default=False, verbose_name='Aksiya qo\'shish ruxsat')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'password', 'full_name']
    
    class Meta:
        verbose_name = 'Restoran Admin'
        verbose_name_plural = 'Restoran Adminlar'
    
    def __str__(self):
        rest_name = self.restaurant.name if self.restaurant else 'Restoran yo\'q'
        return f"{self.full_name} - {rest_name}"


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Kategoriya nomi')
    
    class Meta:
        verbose_name = 'Xarajat kategoriyasi'
        verbose_name_plural = 'Xarajat kategoriyalari'
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Summa')
    description = models.TextField(verbose_name='Izoh')
    date = models.DateField(verbose_name='Sana')
    created_by = models.ForeignKey(RestaurantAdmin, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Xarajat'
        verbose_name_plural = 'Xarajatlar'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.amount} ({self.date})"


class DailyRevenue(models.Model):
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='revenues')
    date = models.DateField(verbose_name='Sana')
    revenue = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Tushum')
    orders_count = models.IntegerField(default=0, verbose_name='Buyurtmalar soni')
    average_check = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='O\'rtacha chek')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Kunlik tushum'
        verbose_name_plural = 'Kunlik tushumlar'
        unique_together = ['restaurant', 'date']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.date}: {self.revenue}"


class Staff(models.Model):
    POSITION_CHOICES = [
        ('manager', 'Menejer'),
        ('cook', 'Oshpaz'),
        ('warehouse', 'Omborxonachi'),
    ]
    
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='staff')
    full_name = models.CharField(max_length=200, verbose_name='To\'liq ism')
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, verbose_name='Lavozim')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    salary = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='Oylik')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    hire_date = models.DateField(auto_now_add=True, verbose_name='Ishga olingan sana')
    
    # Login uchun maydonlar
    username = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='Login')
    password = models.CharField(max_length=255, null=True, blank=True, verbose_name='Parol')
    
    # Huquqlar - role bo'yicha avtomatik
    can_manage_orders = models.BooleanField(default=False, verbose_name='Buyurtmalarni boshqarish')
    can_manage_bookings = models.BooleanField(default=False, verbose_name='Bronlarni boshqarish')
    can_manage_warehouse = models.BooleanField(default=False, verbose_name='Omborni boshqarish')
    
    class Meta:
        verbose_name = 'Xodim'
        verbose_name_plural = 'Xodimlar'
    
    def __str__(self):
        return f"{self.full_name} - {self.get_position_display()}"
    
    def set_password(self, password):
        from django.contrib.auth.hashers import make_password
        self.password = make_password(password)
    
    def check_password(self, password):
        from django.contrib.auth.hashers import check_password
        return check_password(password, self.password)
    
    def save(self, *args, **kwargs):
        # Auto-set permissions based on position
        if self.position == 'cook':
            self.can_manage_orders = True
            self.can_manage_bookings = False
            self.can_manage_warehouse = False
        elif self.position == 'manager':
            self.can_manage_orders = False
            self.can_manage_bookings = True
            self.can_manage_warehouse = False
        elif self.position == 'warehouse':
            self.can_manage_orders = False
            self.can_manage_bookings = False
            self.can_manage_warehouse = True
        super().save(*args, **kwargs)


class TableQR(models.Model):
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='table_qrs')
    table = models.OneToOneField('restaurants.Table', on_delete=models.CASCADE, related_name='qr_code')
    qr_token = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Stol QR kodi'
        verbose_name_plural = 'Stol QR kodlari'
    
    def __str__(self):
        return f"QR - {self.table}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Muvaffaqiyat'),
        ('warning', 'Ogohlantirish'),
        ('error', 'Xato'),
    ]
    
    recipient = models.ForeignKey(RestaurantAdmin, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
