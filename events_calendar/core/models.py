from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#007bff")  # hex color

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Event(models.Model):
    REPEAT_CHOICES = [
        ('none', 'Does not repeat'),
        ('yearly', 'Every year (birthdays, anniversaries)'),
        ('monthly', 'Every month'),
        ('weekly', 'Every week'),
        ('daily', 'Daily'),
    ]
    title = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_birthday = models.BooleanField(default=False, help_text="Check for birthdays")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    repeat = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='none')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')

    def __str__(self):
        return self.title
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    whatsapp_number = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.user.username