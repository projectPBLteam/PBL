# PISafeZone/models.py

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
import uuid 
from django.conf import settings # settings.AUTH_USER_MODEL을 사용하기 위함


# [수정 1] CustomUserManager는 BaseUserManager를 상속 (BaseUserManager가 create_user를 가짐)
class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수 항목입니다.")
        
        email = self.normalize_email(email)
        
        # forms.py에서 first_name을 사용하므로, 여기서도 받아줍니다.
        first_name = extra_fields.pop('first_name', '') 
        
        user = self.model(email=email, first_name=first_name, **extra_fields)
        user.set_password(password)  # 비밀번호 해싱
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
            
        # create_user를 재사용하여 슈퍼유저 생성
        return self.create_user(email, password, **extra_fields)

# [수정 2] 'AbstractUser' 대신 'AbstractBaseUser, PermissionsMixin' 사용
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # [수정 3] 'user_id = UUIDField' 삭제! 
    # Django가 자동으로 'id' (AutoField, PK) 필드를 생성해줍니다.
    # 이것이 Django 인증 시스템이 기대하는 방식입니다.
    
    email = models.EmailField(unique=True) # 이메일을 고유 식별자로
    first_name = models.CharField(max_length=150, blank=True) # forms.py와 일치
    
    # AbstractBaseUser 사용 시 필수 필드들
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name'] # 슈퍼유저 생성 시 first_name도 받음

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# ----------------------------------------------
# ERD 기반 모델 (file_DB 대신 표준 이름 사용)
# ----------------------------------------------

class Data(models.Model):
    # ERD의 data_id (UUID)
    data_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data_name = models.CharField(max_length=100)
    data_usage = models.IntegerField(default=0)
    data_date = models.DateField(auto_now_add=True)
    
    # [수정 4] 필드 이름을 'user'로 변경 (DB에는 'user_id' 컬럼 생성)
    #    settings.AUTH_USER_MODEL을 사용하여 CustomUser에 연결
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    catalog = models.CharField(max_length=200)  # ← 혹시 이거 있음?
    def __str__(self):
        return self.data_name

class UsageHistory(models.Model):
    class UsageType(models.TextChoices):
        REGISTER = 'register', 'Register'
        ANALYZE = 'analyze', 'Analyze'

    usage_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usage_type = models.CharField(max_length=10, choices=UsageType.choices)
    
    # [수정 4] 여기도 'user'로 변경
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # 'data' 필드도 'Data' 모델을 올바르게 참조
    data = models.ForeignKey(Data, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.usage_type}: {self.user.email}"