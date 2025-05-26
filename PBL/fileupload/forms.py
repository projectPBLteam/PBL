# 파일 업로드 폼 (이후 여기에 유효성 검사등을 추가 할 예정)
from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()