from django.shortcuts import render, redirect
# 로그인한 사용자만 업로드할 수 있도록 @login_required 추가
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import UploadFileForm
from django.db import connection    #DB 커서 접근용
from django.contrib.auth import authenticate, login, logout
from .forms import EmailLoginForm, RegisterForm
import re   #파일 이름 정제용
from django.contrib import messages
from .models import Data, UsageHistory, CustomUser

# 모듈 임포트
from modules.data_utils import read_csvfile, maketbl, insert_data
from modules.privacy import laplace_local_differential_privacy
from modules.statistics_basic import calculate_mean, calculate_median, calculate_mode
from modules.user_input import FindQueryN


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

def info_hub(request):
    return render(request, 'info_hub.html')

@login_required
def dataUpload(request):
    # 업로드 첫 페이지는 사용하지 않고 바로 page2로 이동
    return redirect('dataUploadNext')
    # datainput = request.GET['datainput']
    # datainput = request.POST['datainput']
    # return HttpResponse("Other Page test = " + datainput)

@login_required
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

@login_required
def datause(request):
    # 중간 페이지 없이 바로 목록 페이지로 이동
    return redirect('datause2')

@login_required
def datause2(request):
    files = Data.objects.all().select_related('user').order_by('-data_date')
    return render(request, 'datause2.html', { 'files': files })

def _load_dynamic_table_as_list(table_name):
    """동적으로 생성된 테이블을 [columns] + rows 형태의 리스트로 반환"""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            [table_name],
        )
        columns = [r[0] for r in cursor.fetchall()]
        if not columns:
            return [[], []]
        cursor.execute(f"SELECT `{ '`, `'.join(columns) }` FROM `{table_name}`")
        rows = cursor.fetchall()
    return [columns] + [list(r) for r in rows]



@login_required
def datause3(request):
    data_id = request.GET.get('data')
    stat = request.GET.get('stat')
    selected_col = request.GET.get('col')

    result_text = None
    columns = []
    session_key = None

    if data_id:
        session_key = f'query_budget_{data_id}'

        try:
            data_obj = Data.objects.get(pk=data_id)
            raw_data_with_header = _load_dynamic_table_as_list(data_obj.data_name)

            if not raw_data_with_header or len(raw_data_with_header) < 2:
                 raise ValueError("데이터가 비어있습니다.")

            columns = raw_data_with_header[0] # 원본 컬럼명
            raw_data = raw_data_with_header[1:] # 순수 데이터

            # 기본 선택값 보정
            if stat and selected_col:
                col_idx = columns.index(selected_col)
                
                # 1. 원본 데이터에서 숫자 리스트 추출
                numeric_values = []
                for row in raw_data:
                    try:
                        numeric_values.append(float(row[col_idx]))
                    except Exception:
                        continue

                if numeric_values:
                    # 원본 숫자 리스트 기준으로 LDP 파라미터 계산
                    n = len(numeric_values)
                    sensitivity = (max(numeric_values) - min(numeric_values)) / n 
                    epsilon = 0.7

                    # 세션에서 쿼리 예산 확인
                    if session_key not in request.session:
                        initial_query_n = FindQueryN(raw_data_with_header, n, epsilon, sensitivity)
                        request.session[session_key] = initial_query_n

                    QueryN = request.session.get(session_key, 0)

                    if QueryN >= 1:
                        request.session[session_key] = QueryN - 1
                        
                        # LDP 함수에 '숫자 리스트' 전달
                        noisy_numeric_values = laplace_local_differential_privacy(
                            numeric_values,
                            epsilon, 
                            sensitivity
                        )

                        cleaned_noisy_values = []
                        for v in noisy_numeric_values:
                            try:
                                cleaned_noisy_values.append(float(v))
                            except (ValueError, TypeError):
                                continue
                        noisy_numeric_values = cleaned_noisy_values
                        
                        # LDP 함수가 리스트가 아닌 단일 값을 반환하는 경우, 강제로 리스트로 만듭니다. (방어 코드)
                        if not isinstance(noisy_numeric_values, (list, tuple)):
                            if isinstance(noisy_numeric_values, (int, float)):
                                # 예: 0.0 -> [0.0]
                                noisy_numeric_values = [noisy_numeric_values] 
                            else:
                                # 알 수 없는 값이면 빈 리스트로 처리
                                noisy_numeric_values = [] 

                        # '노이즈 적용된 값'으로 최종 통계 계산
                        if noisy_numeric_values:
                            if stat == 'mean':
                                value = calculate_mean(noisy_numeric_values)
                                result_text = f"평균({selected_col}) = {value:.4f}"
                            elif stat == 'median':
                                value = calculate_median(noisy_numeric_values)
                                result_text = f"중앙값({selected_col}) = {value:.4f}"
                            elif stat == 'mode':
                                modes = calculate_mode(noisy_numeric_values)
                                result_text = f"최빈값({selected_col}) = {list(modes)}"
                            
                            result_text += f" (남은 쿼리: {QueryN - 1}회)"
                        else:
                             result_text = f"노이즈 적용 후 '{selected_col}' 컬럼에서 숫자 데이터를 찾을 수 없습니다."
                    
                    else: # if QueryN < 1
                        result_text = f"이용하실 수 있는 쿼리 수를 모두 소진하셨습니다."
                
                else: # if numeric_values:
                    result_text = f"선택한 컬럼 '{selected_col}'에서 숫자 데이터를 찾을 수 없습니다."
            
            # (stat이 None인 경우, 이 블록 전체를 건너뛰고 렌더링)

        except Data.DoesNotExist:
            result_text = "선택한 데이터가 존재하지 않습니다."
        except Exception as e:
            # 쿼리 횟수 만료 등 세션 오류 발생 시를 대비하여 세션 키 삭제
            if session_key in request.session:
                 del request.session[session_key]
            result_text = f"처리 중 오류: {e}"

        ctx = {
            'result': result_text,
            'columns': columns,
            'selected_col': selected_col,
        }
            
    return render(request, 'datause3.html', ctx)



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