from django.urls import path
from . import views, views_html

html_patterns = [
    # HTML Pages
    path('', views_html.admin_login_page, name='admin-login-page'),
    path('admin-login/', views_html.admin_login_page, name='admin-login'),
    path('admin-panel/', views_html.superadmin_dashboard_view, name='superadmin-dashboard-page'),
    path('admin-panel/restaurants/', views_html.superadmin_restaurants_view, name='superadmin-restaurants-page'),
    path('admin-panel/restaurants/update/<int:pk>/', views_html.update_restaurant, name='update-restaurant'),
    path('admin-panel/admins/', views_html.superadmin_admins_view, name='superadmin-admins-page'),
    path('admin-panel/admins/create/', views_html.create_restaurant_admin, name='create-restaurant-admin'),
    path('admin-panel/admins/update/<int:pk>/', views_html.update_restaurant_admin, name='update-restaurant-admin'),
    path('admin-panel/admins/delete/<int:pk>/', views_html.delete_restaurant_admin, name='delete-restaurant-admin'),
    path('admin-panel/expenses/', views_html.superadmin_expenses_view, name='superadmin-expenses-page'),
    path('admin-panel/kpi/', views_html.superadmin_kpi_view, name='superadmin-kpi-page'),
    path('admin-panel/settings/', views_html.superadmin_settings_view, name='superadmin-settings-page'),
    path('admin-panel/feedbacks/', views_html.superadmin_feedbacks_view, name='superadmin-feedbacks-page'),
    
    # Restaurant Admin Pages
    path('restaurant-admin/<int:restaurant_id>/', views_html.restaurant_admin_dashboard, name='restaurant-admin-dashboard'),
    path('restaurant-admin/<int:restaurant_id>/bookings/', views_html.restaurant_bookings_view, name='restaurant-bookings'),
    path('restaurant-admin/<int:restaurant_id>/tables/', views_html.restaurant_tables_view, name='restaurant-tables'),
    path('restaurant-admin/<int:restaurant_id>/menu/', views_html.restaurant_menu_view, name='restaurant-menu'),
    path('restaurant-admin/<int:restaurant_id>/staff/', views_html.restaurant_staff_view, name='restaurant-staff'),
    path('restaurant-admin/<int:restaurant_id>/expenses/', views_html.restaurant_expenses_view, name='restaurant-expenses'),
    path('restaurant-admin/<int:restaurant_id>/revenue/', views_html.restaurant_revenue_view, name='restaurant-revenue'),
    path('restaurant-admin/<int:restaurant_id>/kpi/', views_html.restaurant_kpi_view, name='restaurant-kpi'),
]

api_patterns = [
    path('auth/superadmin/login/', views.superadmin_login, name='api-superadmin-login'),
    path('auth/restaurant-admin/login/', views.restaurant_admin_login, name='api-restaurant-admin-login'),
    path('auth/staff/login/', views.staff_login, name='api-staff-login'),
    path('settings/', views.app_settings, name='api-settings'),
    path('superadmin/dashboard/', views.superadmin_dashboard, name='api-superadmin-dashboard'),
    path('superadmin/restaurant-admins/', views.superadmin_list, name='api-superadmin-admins'),
    path('superadmin/restaurant-admins/<int:pk>/', views.superadmin_detail, name='api-superadmin-admin-detail'),
    path('superadmin/restaurants/', views.superadmin_restaurants, name='api-superadmin-restaurants'),
    path('superadmin/restaurants/<int:pk>/', views.superadmin_restaurant_detail, name='api-superadmin-restaurant-detail'),
    
    path('restaurants/<int:restaurant_id>/dashboard/', views.restaurant_dashboard, name='api-restaurant-dashboard'),
    path('restaurants/<int:restaurant_id>/expenses/', views.expense_list, name='api-expense-list'),
    path('restaurants/<int:restaurant_id>/revenues/', views.revenue_list, name='api-revenue-list'),
    path('restaurants/<int:restaurant_id>/staff/', views.staff_list, name='api-staff-list'),
    path('restaurants/<int:restaurant_id>/table-qr/', views.table_qr_list, name='api-table-qr-list'),
    path('restaurants/<int:restaurant_id>/kpi/', views.kpi_report, name='api-kpi-report'),
    
    path('expense-categories/', views.expense_categories, name='api-expense-categories'),
    path('staff/<int:pk>/', views.staff_detail, name='api-staff-detail'),
    path('table-qr/<int:pk>/', views.table_qr_detail, name='api-table-qr-detail'),
    path('table/<str:token>/', views.table_by_token, name='api-table-by-token'),
    path('notifications/<int:admin_id>/', views.notifications, name='api-notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='api-mark-notification-read'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='api-booking-detail'),
]
