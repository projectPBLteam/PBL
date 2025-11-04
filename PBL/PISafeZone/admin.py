from django.contrib import admin
from .models import CustomUser, Data, UsageHistory

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Data)
admin.site.register(UsageHistory)