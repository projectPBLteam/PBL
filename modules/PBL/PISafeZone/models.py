from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# 데이터 모델(테이블)
class Fileinput(models.Model):
    기준년월 = models.CharField(max_length=6, default=0)
    신우편번호 = models.CharField(max_length=5, default=0)
    연령대코드 = models.IntegerField(default=0)
    성별코드 = models.CharField(max_length=1, default=0)
    개인소득구간코드 = models.IntegerField(default=0)
    가구소득금액 = models.IntegerField(null=True, blank=True)
    개인소득금액 = models.IntegerField(default=0)
    # tableName = models.CharField(max_length=255, primary_key=True)
    # uploadTime = models.CharField(max_length=100)
    # Noise = models.BooleanField(null=True)

# class tableName(models.Model):
#     tableName = models.CharField(max_length=255)
#     uploadTime = models.CharField(max_length=100)
#     Noise = models.BooleanField()

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
    username = None  # 기본 username 필드 제거
    email = models.EmailField(unique=True)  # 이메일을 고유 식별자로

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # username, first_name 등 필요 없음

    objects = CustomUserManager()

    def __str__(self):
        return self.email