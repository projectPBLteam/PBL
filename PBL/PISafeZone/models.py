from django.db import models

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