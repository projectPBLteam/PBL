from rest_framework import serializers
from .models import DataItem

class DataItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataItem
        fields = '__all__'