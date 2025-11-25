from django.urls import path
from .views import auth_view, signup_view
from . import views

urlpatterns = [
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
    path('api/data-list/', views.data_list_view, name='data_list'),
]
