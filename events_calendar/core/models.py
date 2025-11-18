from django.db import models

class Event(models.Model):
    REPEAT_CHOICES = [
        ('none', 'Does not repeat'),
        ('yearly', 'Every year (birthdays, anniversaries)'),
        ('monthly', 'Every month'),
        ('weekly', 'Every week'),
    ]
    title = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_birthday = models.BooleanField(default=False, help_text="Check for birthdays")
    repeat = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='none')

    def __str__(self):
        return self.title