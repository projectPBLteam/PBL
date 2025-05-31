from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name='main'),
    path("fileupload/", views.upload_view),
    path("dataupload/", views.dataUpload),
    path("dataupload/page2", views.dataUploadNext),
    path("datause", views.datause),
    path("datause/page2", views.datause2),
    path("datause/page3", views.datause3),
]
