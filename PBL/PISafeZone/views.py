from django.shortcuts import render, redirect
# [수정] 로그인한 사용자만 업로드할 수 있도록 @login_required 추가
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import UploadFileForm
from django.db import connection    #DB 커서 접근용
from django.contrib.auth import authenticate, login, logout
from .forms import EmailLoginForm, RegisterForm
import re   #파일 이름 정제용
from django.contrib import messages
from .models import Data, UsageHistory, CustomUser

# data_utils 모듈 임포트
from .data_utils import read_csvfile, maketbl, insert_data

# 파일 이름을 DB 테이블 이름으로 사용할 수 있도록 정제하는 헬퍼 함수
def _sanitize_table_name(filename):
    """파일 이름에서 확장자를 제거하고, DB 테이블명으로 사용 불가능한 문자를 언더스코어_로 대체"""
    #확장자 제거
    name_without_extension = filename.rsplit('.', 1)[0]
    #특수 문자(공백 포함)를 언더스코어_로 대체
    sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', name_without_extension)
    #테이블명은 소문자로 변환
    #mysql 예약어 충돌 방지를 위해 'dyn_' 접두사를 추가
    return "dyn_" + sanitized_name.lower()

def main(request):
    #  return HttpResponse("csv 파일을 입력받을 페이지입니다.")
    return render(request, 'main.html')

def dataUpload(request):
    return render(request, 'dataupload.html')
    # datainput = request.GET['datainput']
    # datainput = request.POST['datainput']
    # return HttpResponse("Other Page test = " + datainput)

def dataUploadNext(request):
    form = UploadFileForm()
    return render(request, 'dataupload2.html',  {'form':form})

@login_required
def upload_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            original_filename = uploaded_file.name
            
            # 💡 [중요] 이 코드가 반드시 있어야 합니다.
            table_name = _sanitize_table_name(original_filename)

            # DB 커서 설정
            conn = connection

            try:
                # 파일 읽기
                csv_data = read_csvfile(uploaded_file.file)

                #테이블 생성
                with conn.cursor() as cursor:
                    maketbl(csv_data, cursor, table_name)

                    # 데이터 삽입
                    insert_data(csv_data, cursor, table_name)
                
                # 💡 [수정] 올바른 모델 필드 이름 ('user', 'data')을 사용합니다.
                
                # 업로드 메타데이터 저장 (ERD: Data)
                data_obj = Data.objects.create(
                    data_name=table_name,
                    user=request.user   #'user_id' -> 'user'
                )
                
                # 이용 내역 기록 (register)
                UsageHistory.objects.create(
                    usage_type="register",
                    user=request.user,  #'user_id' -> 'user'
                    data=data_obj       #'data_id' -> 'data'
                )

                #모든 DB 작업 성공시 자동으로 커밋
                messages.success(request, "파일이 업로드 되었습니다.")
                return redirect('dataUploadNext')
            
            except ValueError as e:
                # maketbl 이나 read_csvfile에서 발생한 명확한 오류를 그대로 사용자에게 보여줌
                messages.error(request, e)
                form = UploadFileForm() 
                return render(request, 'dataupload2.html', {'form': form})
            
            except Exception as e:
                # DB 오류, SQL 구문 오류, 데이터 불일치 오류 등
                print("==================================================")
                print(f"오류: {e}")
                print("==================================================")
                messages.error(request, f"동적 DB 처리 중 알 수 없는 오류가 발생했습니다. 상세: {e}")
                form = UploadFileForm() 
                return render(request, 'dataupload2.html', {'form': form})
    
        else:
            messages.error(request, f"폼이 유효하지 않습니다.")
            form = UploadFileForm(request.POST, request.FILES) # 폼을 다시 전달
            return render(request, 'dataupload2.html', {'form': form})
    
    else: # GET 요청
        form = UploadFileForm()
    return render(request, 'dataupload2.html', {'form':form})


def datause(request):
    return render(request, 'datause.html')

def datause2(request):
    files = Data.objects.all().select_related('user').order_by('-data_date')
    return render(request, 'datause2.html', { 'files': files })

def datause3(request):
    return render(request, 'datause3.html')

def auth_view(request):
    login_form = EmailLoginForm(request, data=request.POST or None)
    register_form = RegisterForm(request.POST or None)
    active_tab = 'login'  # 기본 탭은 로그인

    if request.method == 'POST':
        if 'login_submit' in request.POST:
            active_tab = 'login'
            if login_form.is_valid():
                email = login_form.cleaned_data.get('username')
                password = login_form.cleaned_data.get('password')
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    return redirect('main')
        elif 'register_submit' in request.POST:
            active_tab = 'register'
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect('main')

    return render(request, 'auth.html', {
        'login_form': login_form,
        'register_form': register_form,
        'active_tab': active_tab
    })

def user_logout(request):
    logout(request)
    return redirect('main')