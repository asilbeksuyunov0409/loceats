# LocEats Backend - Django

## O'rnatish

### 1. Virtual muhit yaratish
```bash
cd LocEats_Backend
python -m venv venv
venv\Scripts\activate
```

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. MySQL bazasini yaratish (OpenServer/phpMyAdmin)
1. phpMyAdmin oching: http://localhost/phpmyadmin
2. `database_setup.sql` faylini import qiling
Yoki MySQL CLI da:
```sql
mysql -u root -p < database_setup.sql
```

### 4. Migration lari ishga tushirish
```bash
python manage.py migrate
```

### 5. Serverni ishga tushirish
```bash
python manage.py runserver
```

Server: http://127.0.0.1:8000
Admin panel: http://127.0.0.1:8000/admin

### 6. Admin yaratish
```bash
python manage.py createsuperuser
```

## API Endpointlar

| Method | Endpoint | Tavsif |
|--------|----------|--------|
| GET | /api/categories/ | Kategoriyalar ro'yxati |
| POST | /api/categories/ | Yangi kategoriya |
| GET | /api/restaurants/ | Restoranlar ro'yxati |
| POST | /api/restaurants/ | Yangi restoran (rasm bilan) |
| GET | /api/restaurants/{id}/ | Restoran tafsilotlari |
| GET | /api/restaurants/{id}/tables/ | Restoran stollari |
| POST | /api/bookings/ | Yangi bandlik |
| GET | /api/bookings/ | Barcha bandliklar |

## Rasm yuklash

Rasmlarni yuklash uchun `multipart/form-data` formatida yuboring:

```javascript
const formData = new FormData();
formData.append('name', 'Yangi Restoran');
formData.append('address', 'Manzil');
formData.append('phone', '+998901234567');
formData.append('rating', '4.5');
formData.append('image', fileInput.files[0]);

fetch('http://127.0.0.1:8000/api/restaurants/', {
    method: 'POST',
    body: formData
});
```

## MySQL sozlamalari

`loceats/settings.py` da MySQL sozlamalari:
- Host: 127.0.0.1
- Port: 3306
- User: root
- Password: (OpenServer MySQL paroli)
- Database: loceats_db

OpenServer da MySQL parolini `Settings > Modules > MySQL` dan o'rnating.
salom
