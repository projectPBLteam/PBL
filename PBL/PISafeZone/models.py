from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수 항목입니다.")
        if not password:
            raise ValueError("비밀번호는 필수 항목입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # 비밀번호 해싱
        user.save(using=self._db)
        return user
    
    # 관리자 계정 만들 때를 대비
    #def create_superuser(self, email, password=None, **extra_fields):
    #    extra_fields.setdefault("is_staff", True)
    #    extra_fields.setdefault("is_superuser", True)
    #    extra_fields.setdefault("is_active", True)
    #    return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    username = None  # 기본 username 필드 제거
    email = models.EmailField(unique=True)  # 이메일을 고유 식별자로
    USERNAME_FIELD = "email"

    objects = CustomUserManager()
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
# 데이터 모델(테이블)
class file_DB(models.Model):
    data_id = models.AutoField(primary_key=True)
    data_name = models.CharField(max_length=100)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    data_date = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.data_id