from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import DataItem
from .serializers import DataItemSerializer

class DataList(APIView):
    def get(self, request):
        items = DataItem.objects.all()
        serializer = DataItemSerializer(items, many=True)
        return Response(serializer.data)
