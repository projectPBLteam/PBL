from django.shortcuts import render
from django.http import HttpResponse

def main(request):
    #  return HttpResponse("csv 파일을 입력받을 페이지입니다.")
    return render(request, 'main.html')

def otherpage(request):
    # datainput = request.GET['datainput']
    datainput = request.POST['datainput']
    return HttpResponse("Other Page test = " + datainput)