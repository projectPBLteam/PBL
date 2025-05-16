from django.db import models

# 데이터 모델(장고 내부에 테이블을 만듬)
class Fileinput(models.Model):
    filedata = models.CharField()
    tableN = models.CharField()