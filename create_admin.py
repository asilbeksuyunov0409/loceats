import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loceats.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from admins.models import SuperAdmin

# O'chirish
SuperAdmin.objects.all().delete()

# Yangi superadmin
admin = SuperAdmin.objects.create(
    username='admin',
    full_name='Super Admin',
    email='admin@loceats.uz',
    password=make_password('admin123')
)
print('SuperAdmin yaratildi!')
print(f"Username: admin, Password: admin123")