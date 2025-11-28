from django.urls import path, include
from .views import DataList
from django.http import JsonResponse
from .views import data_detail
from . import api_views


urlpatterns = [
    path('api/', include('api.urls')),
    path('data/', DataList.as_view()),
    path('api/data-list/', data_list_api, name='data_list_api'),
    path("data-detail/<int:id>/", data_detail),
    path("api/data/<int:data_id>/columns/", views.api_get_columns, name="data_columns"),
    path('data/<uuid:data_id>/columns/', api_views.get_columns, name='get_columns'),
    path('data/<uuid:data_id>/analyze/', api_views.analyze_data, name='analyze_data'),
]

def hello(request):
    return JsonResponse({"msg": "안뇽 나는 장고야!"})

urlpatterns = [
    path('api/hello/', hello),
]