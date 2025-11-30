from django.urls import path
from .views import auth_view, signup_view
from . import views

urlpatterns = [
    # 기본 페이지/인증
    path("", views.main, name='main'),
    path("fileupload/", views.upload_view),
    path("dataupload/", views.dataUpload),
    path("dataupload/page2", views.dataUploadNext, name='dataUploadNext'),
    path("info/", views.info_hub, name='info_hub'),
    path("datause", views.datause),
    path("datause/page2", views.datause2),
    path("datause/page3", views.datause3),
    path('login/', views.auth_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', views.user_logout, name='logout'),

    # 템플릿에서 쓰는 데이터 목록/업로드
    path('data-list/', views.data_list_api, name='data_list_api'),
    path('data-upload/', views.upload_view, name='data_upload'),

    # React용 JSON API
    path('api/data-list/', views.data_list_view, name='data_list'),
    path('api/data-detail/<uuid:id>/', views.data_detail, name='data_detail'),
    path("api/data/<uuid:data_id>/columns/", views.api_get_columns, name="data_columns"),
    path("api/data/<uuid:data_id>/increment-usage/", views.api_increment_usage, name="data_increment_usage"),
    path("api/data/<uuid:data_id>/analyze/", views.api_analyze, name="data_analyze_api"),
    path("api/data/<uuid:data_id>/custom-console/", views.api_custom_console, name="data_custom_console"),
]
