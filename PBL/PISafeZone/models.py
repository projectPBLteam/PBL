from django.db import models

# User에 관한 모델(테이블)
class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

# 데이터 모델(테이블)
class file_DB(models.Model):
    data_id = models.AutoField(primary_key=True)
    data_name = models.CharField(max_length=100)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    data_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.data_id