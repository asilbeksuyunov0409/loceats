from django.core.management.base import BaseCommand
from restaurants.models import Category, Restaurant, Table, MenuCategory, MenuItem
import urllib.request
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Adds sample restaurants with images and menu items'

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        media_dir = base_dir / 'media' / 'menu'
        media_dir.mkdir(parents=True, exist_ok=True)

        categories_data = [
            {'name': 'Milliy oshxona'},
            {'name': 'Evropa oshxona'},
            {'name': 'Fast Food'},
            {'name': 'Kafe'},
        ]

        categories = []
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(name=cat_data['name'])
            categories.append(cat)
            if created:
                self.stdout.write(f"Created category: {cat.name}")

        menu_categories_data = [
            {'name': 'Suyuq taomlar'},
            {'name': 'Qovurma taomlar'},
            {'name': 'Non va pishiriqlar'},
            {'name': 'Salatlar'},
            {'name': 'Shirinliklar'},
            {'name': 'Hojatxona ichimliklar'},
            {'name': 'Sovuq ichimliklar'},
            {'name': 'Issiq ichimliklar'},
        ]

        menu_categories = {}
        for cat_data in menu_categories_data:
            cat, created = MenuCategory.objects.get_or_create(name=cat_data['name'])
            menu_categories[cat_data['name']] = cat
            if created:
                self.stdout.write(f"Created menu category: {cat.name}")

        restaurants_data = [
            {
                'name': 'Samarqand Registon Oshxonasi',
                'address': 'Registon ko\'chasi 15, Samarqand',
                'phone': '+998662345678',
                'description': 'Samarqandning eng mashhur milliy oshxonasida Registon yaqinida.',
                'rating': 4.9,
                'category': categories[0],
                'latitude': 39.6542,
                'longitude': 66.9597,
                'image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800',
                'tables': ['1', '2', '3', '4', '5', '6']
            },
            {
                'name': 'Bibixonim Kafe',
                'address': 'Islom Karimov ko\'chasi 45, Samarqand',
                'phone': '+998662345679',
                'description': 'An\'anaviy manti va shashlik. Oilaviy tadbirlar uchun qulay muhit.',
                'rating': 4.7,
                'category': categories[0],
                'latitude': 39.6500,
                'longitude': 66.9750,
                'image_url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800',
                'tables': ['1', '2', '3', '4']
            },
            {
                'name': 'Empire Restaurant',
                'address': 'Dagbitskaya ko\'chasi 8, Samarqand',
                'phone': '+998662345680',
                'description': 'Zamonaviy yevropacha dizayn va yuqori sifatli taomlar.',
                'rating': 4.6,
                'category': categories[1],
                'latitude': 39.6520,
                'longitude': 66.9600,
                'image_url': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800',
                'tables': ['1', '2', '3', '4', '5']
            },
            {
                'name': 'Samarqand Shashlik',
                'address': 'Beruniy ko\'chasi 22, Samarqand',
                'phone': '+998662345681',
                'description': 'Eng sifatli go\'sht va an\'anaviy usullarda tayyorlangan shashlik.',
                'rating': 4.5,
                'category': categories[0],
                'latitude': 39.6510,
                'longitude': 66.9650,
                'image_url': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800',
                'tables': ['1', '2', '3']
            },
            {
                'name': 'Burger King Samarqand',
                'address': 'Shota Rustaveli ko\'chasi 10, Samarqand',
                'phone': '+998662345682',
                'description': 'Xalqaro fast food tarmog\'i. Tez va mazali taomlar.',
                'rating': 4.2,
                'category': categories[2],
                'latitude': 39.6530,
                'longitude': 66.9700,
                'image_url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800',
                'tables': ['1', '2', '3', '4', '5', '6', '7', '8']
            },
            {
                'name': 'Coffee House',
                'address': 'Universitetskaya ko\'chasi 5, Samarqand',
                'phone': '+998662345683',
                'description': 'Qahva va shirinliklar. Ishlash va dam olish uchun qulay joy.',
                'rating': 4.4,
                'category': categories[3],
                'latitude': 39.6550,
                'longitude': 66.9580,
                'image_url': 'https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800',
                'tables': ['1', '2', '3', '4']
            },
        ]

        def download_image(url, filename):
            try:
                img_path = media_dir / filename
                if not img_path.exists():
                    self.stdout.write(f"Downloading {filename}...")
                    opener = urllib.request.build_opener()
                    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                    urllib.request.install_opener(opener)
                    urllib.request.urlretrieve(url, img_path)
                return f'menu/{filename}'
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error downloading {filename}: {e}"))
                return None

        menu_items_templates = {
            'Milliy oshxona': {
                'food': [
                    {'name': 'Osh (Plov)', 'desc': 'Samarqandlik ustalar tomonidan tayyorlangan an\'anaviy osh', 'price': 45000, 'img': 'osh.jpg', 'url': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400'},
                    {'name': 'Manti', 'desc': 'Bug\'doy unidan yasalgan, go\'shtli manti', 'price': 35000, 'img': 'manti.jpg', 'url': 'https://images.unsplash.com/photo-1534939561126-855b8675edd7?w=400'},
                    {'name': 'Shashlik', 'desc': 'Qo\'y go\'shtidan tayyorlangan shashlik', 'price': 55000, 'img': 'shashlik.jpg', 'url': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400'},
                    {'name': 'Lag\'mon', 'desc': 'Qo\'lga cho\'zilgan lag\'mon, sabzavotli sous bilan', 'price': 38000, 'img': 'lagmon.jpg', 'url': 'https://images.unsplash.com/photo-1571501679680-de32f1b1aad3?w=400'},
                    {'name': 'Norin', 'desc': 'Qaynatilgan ot go\'shti bilan norin', 'price': 50000, 'img': 'norin.jpg', 'url': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=400'},
                    {'name': 'Somsa', 'desc': 'Yog\'li xamirdan yasalgan somsa', 'price': 15000, 'img': 'somsa.jpg', 'url': 'https://images.unsplash.com/photo-1606787366850-de6330128bfc?w=400'},
                    {'name': 'Dimlama', 'desc': 'Sabzavot va go\'sht bilan dimlama', 'price': 42000, 'img': 'dimlama.jpg', 'url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400'},
                    {'name': 'KFC Tovuq', 'desc': 'Qovurilgan tovuq bo\'laklari', 'price': 48000, 'img': 'kfc.jpg', 'url': 'https://images.unsplash.com/photo-1626645738196-c2a7c87a8f58?w=400'},
                ],
                'drink': [
                    {'name': 'Ayron', 'desc': 'Sovuq ayron', 'price': 8000, 'img': 'ayron.jpg', 'url': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400'},
                    {'name': 'Kompot', 'desc': 'Mevali kompot', 'price': 10000, 'img': 'kompot.jpg', 'url': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400'},
                    {'name': 'Choy', 'desc': 'Issiq qora choy', 'price': 5000, 'img': 'choy.jpg', 'url': 'https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=400'},
                    {'name': 'Shaftoli sharbati', 'desc': 'Tabiiy shaftoli sharbati', 'price': 12000, 'img': 'shaftoli.jpg', 'url': 'https://images.unsplash.com/photo-1546173159-315724a31696?w=400'},
                    {'name': 'Kvas', 'desc': 'Tersilgan kvas', 'price': 7000, 'img': 'kvas.jpg', 'url': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400'},
                ]
            },
            'Fast Food': {
                'food': [
                    {'name': 'Cheeseburger', 'desc': 'Pishloqli burger', 'price': 35000, 'img': 'cheeseburger.jpg', 'url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400'},
                    {'name': 'Chicken Burger', 'desc': 'Tovuqli burger', 'price': 32000, 'img': 'chickenburger.jpg', 'url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400'},
                    {'name': 'Pizza', 'desc': 'Italiancha pizza', 'price': 65000, 'img': 'pizza.jpg', 'url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400'},
                    {'name': 'Hot Dog', 'desc': 'Amerikancha hot dog', 'price': 22000, 'img': 'hotdog.jpg', 'url': 'https://images.unsplash.com/photo-1612392062631-94b7e871c4d3?w=400'},
                    {'name': 'Fri (Coca-Cola)', 'desc': 'Katta fri va kola', 'price': 28000, 'img': 'fri.jpg', 'url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400'},
                    {'name': 'Wings', 'desc': 'Achchiq tovuq qanotchalari', 'price': 45000, 'img': 'wings.jpg', 'url': 'https://images.unsplash.com/photo-1608039755401-742074f0548d?w=400'},
                    {'name': 'Nuggets', 'desc': 'Tovuq nuggets', 'price': 38000, 'img': 'nuggets.jpg', 'url': 'https://images.unsplash.com/photo-1562967914-608f82629710?w=400'},
                    {'name': 'Donar', 'desc': 'Doner kebab', 'price': 40000, 'img': 'donar.jpg', 'url': 'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400'},
                ],
                'drink': [
                    {'name': 'Coca-Cola', 'desc': '0.5L Coca-Cola', 'price': 12000, 'img': 'cola.jpg', 'url': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400'},
                    {'name': 'Fanta', 'desc': '0.5L Fanta', 'price': 12000, 'img': 'fanta.jpg', 'url': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400'},
                    {'name': 'Sprite', 'desc': '0.5L Sprite', 'price': 12000, 'img': 'sprite.jpg', 'url': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400'},
                    {'name': 'Milkshake', 'desc': 'Vanilli milkshake', 'price': 25000, 'img': 'milkshake.jpg', 'url': 'https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400'},
                    {'name': 'Muvoqqat', 'desc': 'Sovuq muvoqqat', 'price': 15000, 'img': 'smoothie.jpg', 'url': 'https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=400'},
                ]
            },
            'Evropa oshxona': {
                'food': [
                    {'name': 'Steyk', 'desc': 'Yaxshi pishirilgan steak', 'price': 95000, 'img': 'steak.jpg', 'url': 'https://images.unsplash.com/photo-1600891964092-4316c288032e?w=400'},
                    {'name': 'Pasta Carbonara', 'desc': 'Italiyancha pasta carbonara', 'price': 55000, 'img': 'carbonara.jpg', 'url': 'https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400'},
                    {'name': 'Risotto', 'desc': 'Zaqqumli risotto', 'price': 60000, 'img': 'risotto.jpg', 'url': 'https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=400'},
                    {'name': 'Bruschetta', 'desc': 'Italiyancha bruschetta', 'price': 28000, 'img': 'bruschetta.jpg', 'url': 'https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?w=400'},
                    {'name': 'Salat Sezar', 'desc': 'Tovuqli sezar salati', 'price': 38000, 'img': 'cesarsalad.jpg', 'url': 'https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400'},
                    {'name': 'Qisqabaq kremi', 'desc': 'Sovuq qisqabaq kremi', 'price': 25000, 'img': 'cream.jpg', 'url': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400'},
                    {'name': 'Tiramisu', 'desc': 'Italiyancha tiramisu', 'price': 35000, 'img': 'tiramisu.jpg', 'url': 'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400'},
                    {'name': 'Panna Cotta', 'desc': 'Italiyancha panna cotta', 'price': 30000, 'img': 'pannacotta.jpg', 'url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400'},
                ],
                'drink': [
                    {'name': 'Kafe Latte', 'desc': 'Issiq latte kafesi', 'price': 18000, 'img': 'latte.jpg', 'url': 'https://images.unsplash.com/photo-1570968915860-54d5c301fa9f?w=400'},
                    {'name': 'Kapuchino', 'desc': 'Klassik kapuchino', 'price': 18000, 'img': 'cappuccino.jpg', 'url': 'https://images.unsplash.com/photo-1570968915860-54d5c301fa9f?w=400'},
                    {'name': 'Yaxshi vino', 'desc': 'Qizil yaxshi vino', 'price': 85000, 'img': 'wine.jpg', 'url': 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=400'},
                    {'name': 'Kokteyl', 'desc': 'Mojito kokteyl', 'price': 45000, 'img': 'mojito.jpg', 'url': 'https://images.unsplash.com/photo-1551538827-9c037cb4f32a?w=400'},
                    {'name': 'Ayran', 'desc': 'Turshq ayron', 'price': 10000, 'img': 'ayran.jpg', 'url': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400'},
                ]
            },
            'Kafe': {
                'food': [
                    {'name': 'Cheesecake', 'desc': 'Amerikancha cheesecake', 'price': 32000, 'img': 'cheesecake.jpg', 'url': 'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400'},
                    {'name': 'Tort', 'desc': 'Shirin tort', 'price': 28000, 'img': 'cake.jpg', 'url': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400'},
                    {'name': 'Croissant', 'desc': 'Fransuz croissant', 'price': 18000, 'img': 'croissant.jpg', 'url': 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400'},
                    {'name': 'Sandwich', 'desc': 'Tovuqli sandwich', 'price': 25000, 'img': 'sandwich.jpg', 'url': 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400'},
                    {'name': 'Pancake', 'desc': 'Asal va saryog\'li pancake', 'price': 22000, 'img': 'pancake.jpg', 'url': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400'},
                    {'name': 'Waffle', 'desc': 'Belgiyancha waffle', 'price': 24000, 'img': 'waffle.jpg', 'url': 'https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=400'},
                    {'name': 'Cookie', 'desc': 'Shokoladli cookie', 'price': 12000, 'img': 'cookie.jpg', 'url': 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=400'},
                    {'name': 'Muffin', 'desc': 'Blueberry muffin', 'price': 15000, 'img': 'muffin.jpg', 'url': 'https://images.unsplash.com/photo-1607958996333-41aef7caefaa?w=400'},
                ],
                'drink': [
                    {'name': 'Americano', 'desc': 'Qora amerikano kafesi', 'price': 15000, 'img': 'americano.jpg', 'url': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400'},
                    {'name': 'Espresso', 'desc': 'Kuchli espresso', 'price': 12000, 'img': 'espresso.jpg', 'url': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400'},
                    {'name': 'Greenchay', 'desc': 'Yashil choy', 'price': 10000, 'img': 'greentea.jpg', 'url': 'https://images.unsplash.com/photo-1556881286-fc6915169721?w=400'},
                    {'name': 'Hot Chocolate', 'desc': 'Issiq shokolad', 'price': 22000, 'img': 'hotchoco.jpg', 'url': 'https://images.unsplash.com/photo-1517578239113-b03992dcdd25?w=400'},
                    {'name': 'Frappe', 'desc': 'Sovuq kofe frappe', 'price': 25000, 'img': 'frappe.jpg', 'url': 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400'},
                ]
            }
        }

        menu_cat_map = {
            'Suyuq taomlar': 'food',
            'Qovurma taomlar': 'food',
            'Non va pishiriqlar': 'food',
            'Salatlar': 'food',
            'Shirinliklar': 'food',
            'Hojatxona ichimliklar': 'drink',
            'Sovuq ichimliklar': 'drink',
            'Issiq ichimliklar': 'drink',
        }

        for res_data in restaurants_data:
            existing = Restaurant.objects.filter(name=res_data['name']).first()
            if existing:
                self.stdout.write(f"Restaurant exists: {res_data['name']}")
                restaurant = existing
            else:
                image_url = res_data.pop('image_url')
                tables_data = res_data.pop('tables')
                
                try:
                    img_name = f"{res_data['name'].replace(' ', '_')[:20]}.jpg"
                    img_path = base_dir / 'media' / 'restaurants' / img_name
                    
                    if not img_path.exists():
                        self.stdout.write(f"Downloading image for {res_data['name']}...")
                        opener = urllib.request.build_opener()
                        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
                        urllib.request.install_opener(opener)
                        urllib.request.urlretrieve(image_url, img_path)
                    
                    restaurant = Restaurant.objects.create(
                        name=res_data['name'],
                        address=res_data['address'],
                        phone=res_data['phone'],
                        description=res_data['description'],
                        rating=res_data['rating'],
                        category=res_data['category'],
                        latitude=res_data['latitude'],
                        longitude=res_data['longitude'],
                        image=f'restaurants/{img_name}'
                    )
                    
                    for table_num in tables_data:
                        Table.objects.get_or_create(
                            restaurant=restaurant,
                            table_number=table_num,
                            defaults={'capacity': 4, 'is_available': True}
                        )
                    
                    self.stdout.write(self.style.SUCCESS(f"Created: {restaurant.name}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error with {res_data['name']}: {e}"))
                    continue

            restaurant_category_name = res_data.get('category').name if hasattr(res_data.get('category'), 'name') else restaurant.category.name
            if restaurant_category_name in menu_items_templates:
                templates = menu_items_templates[restaurant_category_name]
                
                for item in templates['food']:
                    if not MenuItem.objects.filter(restaurant=restaurant, name=item['name']).exists():
                        img_path = download_image(item['url'], item['img'])
                        MenuItem.objects.create(
                            restaurant=restaurant,
                            name=item['name'],
                            description=item['desc'],
                            price=item['price'],
                            image=img_path,
                            category=menu_categories['Qovurma taomlar'],
                            item_type='food',
                            is_available=True
                        )
                        self.stdout.write(f"  + Menu item: {item['name']}")
                
                for item in templates['drink']:
                    if not MenuItem.objects.filter(restaurant=restaurant, name=item['name']).exists():
                        img_path = download_image(item['url'], item['img'])
                        MenuItem.objects.create(
                            restaurant=restaurant,
                            name=item['name'],
                            description=item['desc'],
                            price=item['price'],
                            image=img_path,
                            category=menu_categories['Issiq ichimliklar'],
                            item_type='drink',
                            is_available=True
                        )
                        self.stdout.write(f"  + Drink: {item['name']}")

        self.stdout.write(self.style.SUCCESS('\n=== Barcha namuna ma\'lumotlar qo\'shildi! ==='))
        self.stdout.write(f"Jami restoranlar: {Restaurant.objects.count()}")
        self.stdout.write(f"Jami stollar: {Table.objects.count()}")
        self.stdout.write(f"Jami menyu elementlari: {MenuItem.objects.count()}")
