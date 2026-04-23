from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    user_phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    image = models.ImageField(upload_to='feedback/', blank=True, null=True)
    admin_reply = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Fikr-mulohaza'
        verbose_name_plural = 'Fikr-mulohazalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_name or 'Mehmon'} - {self.message[:50]}"
