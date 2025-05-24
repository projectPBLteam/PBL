from django.db import models

# 데이터 모델(테이블)
class table_total_data(models.Model):
    tableName = models.CharField(max_length=255, primary_key=True)
    uploadTime = models.CharField(max_length=100)
    Noise = models.BooleanField(null=True)

# class tableName(models.Model):
#     tableName = models.CharField(max_length=255)
#     uploadTime = models.CharField(max_length=100)
#     Noise = models.BooleanField()