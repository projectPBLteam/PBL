from django.db import models

class DataItem(models.Model):
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=100)
    upload_date = models.DateField()
    usage_count = models.IntegerField(default=0)