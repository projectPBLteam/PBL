# 파일 업로드 폼 (이후 여기에 유효성 검사등을 추가 할 예정)
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='이메일', 
        widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': '이메일'})
    )
    
    password = forms.CharField(
        label='비밀번호', 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'})
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='이메일', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '이메일'}))
    
    # 1. 폼 필드 이름을 모델 필드와 일치시킴 (예: 'first_name')
    first_name = forms.CharField(label='이름', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '이름'}))
    
    password1 = forms.CharField(label='비밀번호', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'}))
    password2 = forms.CharField(label='비밀번호 확인', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호 확인'}))

    class Meta:
        model = CustomUser
        # 2. Meta.fields에는 모델에 저장할 필드만 나열
        fields = ['email', 'first_name'] # 'username' 대신 'first_name'

    # save 메서드를 재정의
    def save(self, commit=True):
        # 부모 클래스(UserCreationForm)의 save()대신, CustomUser 모델의 create_user 메서드를 직접 호출
        
        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            
            # 폼에서 받은 'first_name' 값을 모델의 'first_name' 필드로 전달
            first_name=self.cleaned_data['first_name'], 
            # 모델에 다른 필수 필드가 있다면 여기서 추가
        )
        return user


class UploadFileForm(forms.Form):
    file = forms.FileField()