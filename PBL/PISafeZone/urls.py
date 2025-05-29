from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name='main'),
    path("fileupload/", views.upload_view),
    path("dataupload/", views.dataUpload),
    path("datauploadN/", views.dataUploadNext),
]
