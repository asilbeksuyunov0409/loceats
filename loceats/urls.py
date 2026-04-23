from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from admins import views_html
from admins.urls import api_patterns

urlpatterns = [
    # Admin Panel HTML Pages - must be before Django admin
    path('admin-login/', views_html.admin_login_page, name='admin-login'),
    path('restaurant-admin-login/', views_html.restaurant_admin_login_page, name='restaurant-admin-login'),
    path('admin-panel/', views_html.superadmin_dashboard_view, name='superadmin-dashboard-page'),
    path('admin-panel/restaurants/', views_html.superadmin_restaurants_view, name='superadmin-restaurants-page'),
    path('admin-panel/restaurants/update/<int:pk>/', views_html.update_restaurant, name='update-restaurant'),
    path('admin-panel/restaurants/delete/<int:pk>/', views_html.delete_restaurant, name='delete-restaurant'),
    path('admin-panel/admins/', views_html.superadmin_admins_view, name='superadmin-admins-page'),
    path('admin-panel/admins/create/', views_html.create_restaurant_admin, name='create-restaurant-admin'),
    path('admin-panel/admins/update/<int:pk>/', views_html.update_restaurant_admin, name='update-restaurant-admin'),
    path('admin-panel/admins/delete/<int:pk>/', views_html.delete_restaurant_admin, name='delete-restaurant-admin'),
    path('admin-panel/expenses/', views_html.superadmin_expenses_view, name='superadmin-expenses-page'),
    path('admin-panel/kpi/', views_html.superadmin_kpi_view, name='superadmin-kpi-page'),
    path('admin-panel/settings/', views_html.superadmin_settings_view, name='superadmin-settings-page'),
    path('admin-panel/chat/', views_html.superadmin_chat_view, name='superadmin-chat-page'),
    path('admin-panel/users/', views_html.superadmin_users_view, name='superadmin-users-page'),
    path('admin-panel/orders/', views_html.superadmin_orders_view, name='superadmin-orders-page'),
    
    # Restaurant Admin Pages
    path('restaurant-admin/', views_html.restaurant_admin_login_page, name='restaurant-admin-login'),
    path('restaurant-admin/<int:restaurant_id>/', views_html.restaurant_admin_dashboard, name='restaurant-admin-dashboard'),
    path('restaurant-admin/<int:restaurant_id>/bookings/', views_html.restaurant_bookings_view, name='restaurant-bookings'),
    path('restaurant-admin/<int:restaurant_id>/orders/', views_html.restaurant_orders_view, name='restaurant-orders'),
    path('restaurant-admin/<int:restaurant_id>/tables/', views_html.restaurant_tables_view, name='restaurant-tables'),
    path('restaurant-admin/<int:restaurant_id>/menu/', views_html.restaurant_menu_view, name='restaurant-menu'),
    path('restaurant-admin/<int:restaurant_id>/reviews/', views_html.restaurant_reviews_view, name='restaurant-reviews'),
    path('restaurant-admin/<int:restaurant_id>/staff/', views_html.restaurant_staff_view, name='restaurant-staff'),
    path('restaurant-admin/<int:restaurant_id>/chat/', views_html.restaurant_chat_view, name='restaurant-chat'),
    path('restaurant-admin/<int:restaurant_id>/expenses/', views_html.restaurant_expenses_view, name='restaurant-expenses'),
    path('restaurant-admin/<int:restaurant_id>/revenue/', views_html.restaurant_revenue_view, name='restaurant-revenue'),
    path('restaurant-admin/<int:restaurant_id>/kpi/', views_html.restaurant_kpi_view, name='restaurant-kpi'),
    path('restaurant-admin/<int:restaurant_id>/attendance/', views_html.restaurant_attendance_view, name='restaurant-attendance'),
    path('restaurant-admin/<int:restaurant_id>/warehouse/', views_html.restaurant_warehouse_view, name='restaurant-warehouse'),
    
    # Django Admin and API
    # Staff Login
    path('staff-login/', views_html.staff_login_page, name='staff-login'),
    path('staff/<int:restaurant_id>/orders/', views_html.staff_orders_view, name='staff-orders'),
    path('staff/<int:restaurant_id>/orders/<int:order_id>/', views_html.staff_update_order, name='staff-update-order'),
    path('staff/<int:restaurant_id>/update-order/<int:order_id>/', views_html.simple_update_order, name='simple-update-order'),
    path('staff/<int:restaurant_id>/warehouse/', views_html.staff_warehouse_view, name='staff-warehouse'),
    path('staff/<int:restaurant_id>/bookings/', views_html.staff_bookings_view, name='staff-bookings'),
    
    path('admin/', admin.site.urls),
    path('api/', include('restaurants.urls')),
    path('api/auth/', include('users.urls')),
    path('api/admin/', include((api_patterns, 'admins'))),
]

# Media fayllarni serve qilish - DEBUG dan qat'iy nazar
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
