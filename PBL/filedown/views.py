from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("csv 파일을 입력받을 페이지입니다.")