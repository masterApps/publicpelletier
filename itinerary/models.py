from django.db import models
from datetime import datetime

# Create your models here.
class Meetings(models.Model):
    date_start = models.DateField(default=datetime.now)
    date_end = models.DateField(default=datetime.now)
    location = models.CharField(max_length=200)
    host = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.location} - {self.host} ({self.date_start})"

    class Meta:
        verbose_name_plural = "Meetings"