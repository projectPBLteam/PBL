from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from django.db import connection    #DB 커서 접근용
import re   #파일 이름 정제용
from django.contrib import messages
from .models import file_DB, User

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
    return render(request, 'main.html')

def dataUpload(request):
    return render(request, 'dataupload.html')

def dataUploadNext(request):
    form = UploadFileForm()
    return render(request, 'dataupload2.html', {'form':form})

def upload_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']

            original_filename = uploaded_file.name
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
                
                # try: 
                #     #file_DB에 관련 데이터 INSERT
                #     file_record = file_DB(
                #         data_name = table_name,
                #         # 아직 회원가입과 미연동으로 임의 설정
                #         user = temp_user
                #         # user = request.user
                #     )
                #     file_record.save()  # 데이터 베이스에 INSERT
                # except Exception as e:
                #     raise Exception(f"메타데이터 저장 실패: {e}")

                #모든 DB 작업 성공시 자동으로 커밋
                messages.success(request, "파일이 업로드 되었습니다.")
                return render(request, 'dataupload2.html')
            
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
            return render(request, 'dataupload2.html', {'form': form})
    else:
        form = UploadFileForm()
    return render(request, 'dataupload2.html', {'form':form})


def datause(request):
    return render(request, 'datause.html')

def datause2(request):
    return render(request, 'datause2.html')

def datause3(request):
    return render(request, 'datause3.html')