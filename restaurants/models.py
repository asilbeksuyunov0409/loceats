from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Kategoriya nomi')
    
    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
    
    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='chat_messages')
    sender_type = models.CharField(max_length=20, choices=[
        ('superadmin', 'Super Admin'),
        ('restaurant', 'Restaurant Admin'),
    ])
    sender_name = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat xabari'
        verbose_name_plural = 'Chat xabarlar'
    
    def __str__(self):
        return f"{self.sender_name}: {self.message[:50]}"

class AppSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    
    class Meta:
        verbose_name = 'Sozlama'
        verbose_name_plural = 'Sozlamalar'
    
    def __str__(self):
        return self.key

class Restaurant(models.Model):
    name = models.CharField(max_length=200, verbose_name='Restoran nomi')
    address = models.CharField(max_length=300, verbose_name='Manzil')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    description = models.TextField(verbose_name='Tavsif', blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0, verbose_name='Reyting')
    image = models.ImageField(upload_to='restaurants/', blank=True, null=True, verbose_name='Rasm')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='restaurants')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Restoran'
        verbose_name_plural = 'Restoranlar'
        ordering = ['-rating']
    
    def __str__(self):
        return self.name

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    table_number = models.CharField(max_length=10, verbose_name='Stol raqami')
    capacity = models.IntegerField(default=4, verbose_name='Sig\'im')
    is_available = models.BooleanField(default=True, verbose_name='Bo\'sh')
    
    class Meta:
        verbose_name = 'Stol'
        verbose_name_plural = 'Stollar'
    
    def __str__(self):
        return f"{self.restaurant.name} - Stol {self.table_number}"

class Booking(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='bookings')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=100, verbose_name='Mijoz ismi')
    customer_phone = models.CharField(max_length=20, verbose_name='Telefon')
    booking_date = models.DateField(verbose_name='Sana')
    booking_time = models.TimeField(verbose_name='Vaqt')
    guest_count = models.IntegerField(default=2, verbose_name='Mehmonlar soni')
    note = models.TextField(blank=True, verbose_name='Izoh')
    is_confirmed = models.BooleanField(default=False, verbose_name=' Tasdiqlangan')
    event = models.ForeignKey('QaniKetedikEvent', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Bandlik'
        verbose_name_plural = 'Bandliklar'
        ordering = ['-booking_date', '-booking_time']
    
    def __str__(self):
        return f"{self.customer_name} - {self.restaurant.name} ({self.booking_date})"

class MenuCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Ovqat kategoriyasi')
    
    class Meta:
        verbose_name = 'Ovqat kategoriyasi'
        verbose_name_plural = 'Ovqat kategoriyalari'
    
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    TYPE_CHOICES = [
        ('food', 'Ovqat'),
        ('drink', 'Ichimlik'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=200, verbose_name='Nomi')
    description = models.TextField(verbose_name='Tavsif', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='Narxi (so\'m)')
    image = models.ImageField(upload_to='menu/', blank=True, null=True, verbose_name='Rasm')
    category = models.ForeignKey(MenuCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='menu_items')
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='food', verbose_name='Turi')
    is_available = models.BooleanField(default=True, verbose_name='Mavjud')
    is_promotion = models.BooleanField(default=False, verbose_name='Aksiya')
    promotion_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name='Aksiya narxi')
    promotion_title = models.CharField(max_length=100, blank=True, verbose_name='Aksiya nomi')
    discount_percent = models.IntegerField(default=0, verbose_name='Chegirma %')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Menyu elementi'
        verbose_name_plural = 'Menyu elementlari'
    
    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"
    
    def save(self, *args, **kwargs):
        if self.is_promotion and self.promotion_price and self.price > 0:
            self.discount_percent = int((1 - float(self.promotion_price) / float(self.price)) * 100)
        else:
            self.discount_percent = 0
        super().save(*args, **kwargs)


class Promotion(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='promotions')
    title = models.CharField(max_length=200, verbose_name='Aksiya sarlavhasi')
    description = models.TextField(verbose_name='Tavsif', blank=True)
    image = models.ImageField(upload_to='promotions/', blank=True, null=True, verbose_name='Rasm')
    discount_percent = models.IntegerField(default=10, verbose_name='Chegirma %')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    start_date = models.DateTimeField(verbose_name='Boshlanish sanasi')
    end_date = models.DateTimeField(verbose_name='Tugash sanasi')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Aksiya'
        verbose_name_plural = 'Aksiyalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.restaurant.name}"


class Review(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100, verbose_name='Foydalanuvchi ismi')
    user_id = models.IntegerField(default=0, verbose_name='Foydalanuvchi ID')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Baholash')
    comment = models.TextField(verbose_name='Sharh matni', blank=True)
    admin_response = models.TextField(verbose_name='Admin javobi', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Sharh'
        verbose_name_plural = 'Sharhlar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_name} - {self.restaurant.name} ({self.rating}⭐)"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('confirmed', 'Qabul qilingan'),
        ('preparing', 'Tayyorlanmoqda'),
        ('ready', 'Tayyor'),
        ('delivered', 'Yetkazildi'),
        ('cancelled', 'Bekor qilingan'),
    ]
    DELIVERY_CHOICES = [
        ('pickup', 'Olib ketish'),
        ('delivery', 'Yetkazib berish'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    table_token = models.CharField(max_length=100, blank=True, null=True, verbose_name='Stol Token')
    user_name = models.CharField(max_length=100, verbose_name='Mijoz ismi')
    user_id = models.IntegerField(default=0, verbose_name='Mijoz ID')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup', verbose_name='Yetkazish turi')
    address = models.TextField(blank=True, verbose_name='Manzil')
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Umumiy summa')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Holati')
    note = models.TextField(blank=True, verbose_name='Izoh')
    booking_date_time = models.DateTimeField(null=True, blank=True, verbose_name='Bron vaqti')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Buyurtma #{self.id} - {self.user_name} - {self.restaurant.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='order_items')
    menu_item_name = models.CharField(max_length=200, verbose_name='Taom nomi')
    quantity = models.IntegerField(default=1, verbose_name='Soni')
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='Narxi')
    total_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Jami summa')
    
    class Meta:
        verbose_name = 'Buyurtma elementi'
        verbose_name_plural = 'Buyurtma elementlari'
    
    def __str__(self):
        return f"{self.menu_item_name} x{self.quantity}"


class Employee(models.Model):
    ROLE_CHOICES = [
        ('boss', 'Boshqaruvchi'),
        ('chef', 'oshpaz'),
        ('waiter', 'ofitsiant'),
        ('cashier', 'kassir'),
        ('courier', 'yetkazuvchi'),
        ('cleaner', 'tozalovchi'),
    ]
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('on_leave', 'Ta\'til'),
        ('fired', 'Ishdan ketgan'),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='employees')
    first_name = models.CharField(max_length=100, verbose_name='Ism')
    last_name = models.CharField(max_length=100, verbose_name='Familiya')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='Lavozim')
    salary = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Ish haqi')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name='Soatlik stavka')
    hire_date = models.DateField(verbose_name='Ishga qabul sanasi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Holati')
    notes = models.TextField(blank=True, verbose_name='Izohlar')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Xodim'
        verbose_name_plural = 'Xodimlar'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.restaurant.name}"


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(verbose_name='Sana')
    check_in = models.TimeField(null=True, blank=True, verbose_name='Kirish vaqti')
    check_out = models.TimeField(null=True, blank=True, verbose_name='Chiqish vaqti')
    hours_worked = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='Ishlagan soat')
    status = models.CharField(max_length=20, choices=[
        ('present', 'Kelgan'),
        ('absent', 'Kelmagan'),
        ('late', 'Kechikgan'),
        ('day_off', 'Ta\'til'),
    ], default='present', verbose_name='Holati')
    note = models.TextField(blank=True, verbose_name='Izoh')
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Davomat'
        verbose_name_plural = 'Davomat'
    
    def __str__(self):
        return f"{self.employee} - {self.date}"


class WarehouseItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='warehouse_items')
    name = models.CharField(max_length=200, verbose_name='Nomi')
    category = models.CharField(max_length=50, choices=[
        ('food', 'Oziq-ovqat'),
        ('drink', 'Ichimliklar'),
        ('packaging', 'Qadoqlash'),
        ('cleaning', 'Tozalash'),
        ('other', 'Boshqa'),
    ], default='other', verbose_name='Kategoriya')
    unit = models.CharField(max_length=20, verbose_name='Birlik (kg, dona, l...)')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Miqdori')
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Minimal miqdori')
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='Narxi')
    supplier = models.CharField(max_length=200, blank=True, verbose_name='Yetkazuvchi')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='Yaroqlilik sanasi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Ombor elementi'
        verbose_name_plural = 'Ombor'
    
    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"


class InventoryEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('in', 'Kirim'),
        ('out', 'Chiqim'),
        ('adjust', 'Korreksiya'),
    ]
    warehouse_item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE, related_name='entries')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES, verbose_name='Turi')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Miqdori')
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='Narxi')
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_by = models.CharField(max_length=100, verbose_name='Kim qo\'shdi')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ombor yozuvi'
        verbose_name_plural = 'Ombor yozuvlari'
    
    def __str__(self):
        return f"{self.entry_type} - {self.warehouse_item.name}"


class DailyReport(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='daily_reports')
    date = models.DateField(verbose_name='Sana')
    revenue = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Tushum')
    expenses = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Xarajat')
    profit = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Foyda')
    orders_count = models.IntegerField(default=0, verbose_name='Buyurtmalar soni')
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='O\'rtacha buyurtma')
    customers_count = models.IntegerField(default=0, verbose_name='Mijozlar soni')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Kunlik hisobot'
        verbose_name_plural = 'Kunlik hisobotlar'
    
    def __str__(self):
        return f"{self.date} - {self.restaurant.name}"


class TableSession(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Boshlanish vaqti')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='Tugash vaqti')
    guest_count = models.IntegerField(default=1, verbose_name='Mehmonlar soni')
    order_total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Buyurtma summasi')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Faol'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ], default='active', verbose_name='Holati')
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Stol sessiyasi'
        verbose_name_plural = 'Stol sessiyalari'
    
    def __str__(self):
        return f"Stol {self.table.number} - {self.started_at}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)


class QaniKetedikEvent(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Qoralamada'),
        ('active', 'Faol'),
        ('in_progress', 'Davom etmoqda'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    
    host_user_id = models.IntegerField(verbose_name='Tashkilotchi ID')
    host_name = models.CharField(max_length=100, verbose_name='Tashkilotchi ismi')
    host_phone = models.CharField(max_length=20, verbose_name='Tashkilotchi telefon')
    
    title = models.CharField(max_length=200, verbose_name='Tadbir nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='events')
    table = models.ForeignKey('Table', on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    
    event_date = models.DateField(verbose_name='Tadbir sanasi')
    event_time = models.TimeField(verbose_name='Tadbir vaqti')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    max_guests = models.IntegerField(default=10, verbose_name='Maksimal mehmonlar')
    
    is_checked_in = models.BooleanField(default=False, verbose_name='Check-in qilingan')
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Qani Ketdik tadbiri'
        verbose_name_plural = 'Qani Ketdik tadbirlari'
    
    def __str__(self):
        return f"{self.title} - {self.host_name}"


class EventInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('declined', 'Rad etildi'),
        ('arrived', 'Keldi'),
    ]
    
    event = models.ForeignKey(QaniKetedikEvent, on_delete=models.CASCADE, related_name='invitations')
    
    guest_user_id = models.IntegerField(null=True, blank=True)
    guest_phone = models.CharField(max_length=20, verbose_name='Mehmon telefoni')
    guest_name = models.CharField(max_length=100, verbose_name='Mehmon ismi')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    can_order_food = models.BooleanField(default=False, verbose_name='Taom tanlash huquqi')
    
    arrived_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Taklifnoma'
        verbose_name_plural = 'Taklifnomalar'
    
    def __str__(self):
        return f"{self.guest_name} - {self.event.title}"


class GroupOrder(models.Model):
    event = models.ForeignKey(QaniKetedikEvent, on_delete=models.CASCADE, related_name='group_orders')
    
    items = models.JSONField(default=list, verbose_name='Buyurtmalar ro\'yxati')
    is_submitted = models.BooleanField(default=False, verbose_name='Yuborilgan')
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Guruh buyurtmasi'
        verbose_name_plural = 'Guruh buyurtmalari'
    
    def __str__(self):
        return f"Event #{self.event.id} - GroupOrder"


class EventPayment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('click', 'Click'),
        ('payme', 'Payme'),
    ]
    
    group_order = models.ForeignKey(GroupOrder, on_delete=models.CASCADE, related_name='payments')
    
    payer_user_id = models.IntegerField(verbose_name='To\'lovchi ID')
    payer_name = models.CharField(max_length=100, verbose_name='To\'lovchi ismi')
    
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Summa')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name='To\'lov usuli')
    
    is_settled = models.BooleanField(default=False, verbose_name='Hisob-kitob qilingan')
    settled_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
    
    def __str__(self):
        return f"{self.payer_name} - {self.amount}"
