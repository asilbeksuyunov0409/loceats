from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('me/', views.me, name='me'),
    path('user/', views.update_user, name='update_user'),
    path('feedback/send/', views.feedback_send, name='feedback_send'),
    path('feedbacks/', views.get_feedbacks, name='get_feedbacks'),
    path('feedback/reply/', views.reply_to_feedback, name='reply_to_feedback'),
]
