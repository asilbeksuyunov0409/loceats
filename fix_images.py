import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loceats.settings')
django.setup()

from restaurants.models import Restaurant, MenuItem, MenuCategory, Category

# Fix image fields
Restaurant.objects.filter(image='image.png').update(image=None)
MenuItem.objects.filter(image='image.png').update(image=None)
MenuCategory.objects.filter(image='image.png').update(image=None)
Category.objects.filter(image='image.png').update(image=None)

print('Xatolar tozitildi!')
print(f'Restoranlar: {Restaurant.objects.count()}')
print(f'MenuItemlar: {MenuItem.objects.count()}')