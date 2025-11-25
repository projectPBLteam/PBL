from django.urls import path, include
from .views import DataList
from django.http import JsonResponse

urlpatterns = [
    path('api/', include('api.urls')),
    path('data/', DataList.as_view()),
    path('api/data-list/', data_list_api, name='data_list_api'),
]

def hello(request):
    return JsonResponse({"msg": "안뇽 나는 장고야!"})

urlpatterns = [
    path('api/hello/', hello),
]