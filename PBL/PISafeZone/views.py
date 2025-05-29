from django.shortcuts import render
from django.http import HttpResponse
from .models import Fileinput
from .forms import UploadFileForm
import csv
from io import TextIOWrapper

def main(request):
    #  return HttpResponse("csv 파일을 입력받을 페이지입니다.")
    return render(request, 'main.html')

def dataUpload(request):
    return render(request, 'dataupload.html')
    # datainput = request.GET['datainput']
    # datainput = request.POST['datainput']
    # return HttpResponse("Other Page test = " + datainput)

def dataUploadNext(request):
    return render(request, 'dataupload2.html')

def upload_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            try:
                text_file = TextIOWrapper(uploaded_file.file, encoding='euc-kr')
                reader = csv.DictReader(text_file, delimiter=',')  # 구분자 꼭 확인!
                
                for row in reader:
                    print(row)  # 잘 읽히는지 확인
                    Fileinput.objects.create(
                        기준년월 = row['기준년월'],
                        신우편번호 = row['신우편번호'],
                        연령대코드 = int(row['연령대코드']),
                        성별코드 = row['성별코드'],
                        개인소득구간코드 = int(row['개인소득구간코드']),
                        가구소득금액 = int(row['가구소득금액']) if row['가구소득금액'] else None,
                        개인소득금액 = int(row['개인소득금액'])
                    )
                return render(request, 'upload_success.html')

            except Exception as e:
                print(f"CSV 처리 중 에러: {e}")
                return HttpResponse("CSV 파일 처리 중 오류가 발생했습니다.")
        else:
            return HttpResponse("폼이 유효하지 않습니다.")
    else:
        form = UploadFileForm()
    return render(request, 'upload_form.html', {'form': form})