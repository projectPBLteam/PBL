from django.shortcuts import render, redirect
# 로그인한 사용자만 업로드할 수 있도록 @login_required 추가
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .forms import UploadFileForm
from django.db import connection    #DB 커서 접근용
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import EmailLoginForm, RegisterForm
import re   #파일 이름 정제용
from django.contrib import messages
from .models import Data, UsageHistory, CustomUser

# 모듈 임포트
from modules.data_utils import read_csvfile, maketbl, insert_data
from modules.privacy import laplace_local_differential_privacy
from modules.statistics_basic import calculate_mean, calculate_median, calculate_mode
from modules.user_input import FindQueryN

# CSRF 
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
import json
from django.contrib.auth.decorators import login_required
 
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
@csrf_exempt  # fetch로 호출할 때 CSRF 문제 제거
def upload_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({"success": False, "message": "파일이 없습니다."})

        try:
            original_filename = uploaded_file.name
            table_name = _sanitize_table_name(original_filename)

            csv_data = read_csvfile(uploaded_file.file)

            with connection.cursor() as cursor:
                maketbl(csv_data, cursor, table_name)
                insert_data(csv_data, cursor, table_name)

            data_obj = Data.objects.create(data_name=table_name, user=request.user)
            UsageHistory.objects.create(usage_type="register", user=request.user, data=data_obj)

            return JsonResponse({"success": True})
        
        except ValueError as e:
            return JsonResponse({"success": False, "message": str(e)})
        
        except Exception as e:
            print(f"오류: {e}")
            return JsonResponse({"success": False, "message": "알 수 없는 오류 발생"})

    return JsonResponse({"success": False, "message": "POST 요청만 허용됩니다."})

@login_required
def data_list_api(request):
    data_objs = Data.objects.filter(user=request.user).values(
        'id', 'data_name', 'user__email', 'date_created', 'usage_count'
    )
    data_list = [
        {
            "id": str(d.data_id),
            "name": d.data_name,
            "provider": d.user.email,
            "uploadDate": d.data_date.strftime("%Y.%m.%d"),
            "usageCount": d.data_usage,
        }
        for d in data_objs
    ]
    return JsonResponse({"success": True, "data": data_list})

def data_list_view(request):
    if request.user.is_authenticated:
        data_objects = Data.objects.filter(user=request.user)
        data_list = [
            {
                "id": str(d.data_id),
                "name": d.data_name,
                "provider": d.user.email,
                "uploadDate": d.data_date.strftime("%Y.%m.%d"),
                "usageCount": d.data_usage,
            }
            for d in data_objects
        ]
        return JsonResponse({"success": True, "data": data_list})
    return JsonResponse({"success": False, "message": "로그인 필요"})

def data_detail(request, id):
    try:
        obj = DataModel.objects.get(id=id)
    except DataModel.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터 없음!"})

    return JsonResponse({
        "success": True,
        "data": {
            "id": obj.id,
            "name": obj.name,
            "provider": obj.provider,
            "uploadDate": obj.upload_date.strftime("%Y-%m-%d"),
            "usageCount": obj.usage_count,
            "catalog": obj.catalog,
        }
    })

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
    if data_id:
        try:
            data_obj = Data.objects.get(pk=data_id)
            raw_data_with_header = _load_dynamic_table_as_list(data_obj.data_name)

            if not raw_data_with_header or len(raw_data_with_header) < 2:
                raise ValueError("데이터가 비어있습니다.")

            columns = raw_data_with_header[0]
            raw_data = raw_data_with_header[1:]
            noisy_values=[]

            if stat and selected_col:
                try:
                    col_idx = columns.index(selected_col)
                except ValueError:
                    result_text = f"컬럼 '{selected_col}'을 찾을 수 없습니다."
                    col_idx = None

                numeric_values = []
                if col_idx is not None:
                    for row in raw_data:
                        try:
                            numeric_values.append(float(row[col_idx]))
                        except (ValueError, TypeError):
                            continue

                if not numeric_values:
                    result_text = f"선택한 컬럼 '{selected_col}'에서 숫자 데이터를 찾을 수 없습니다."
                else:
                    n = len(numeric_values)
                    sensitivity = (max(numeric_values) - min(numeric_values)) / n
                    epsilon = 0.7

                    if "query_budget" not in request.session:
                        request.session["query_budget"] = {}

                    q = request.session["query_budget"]

                    if data_id not in q:
                        q[data_id] = {}

                    if stat not in q[data_id]:
                        q[data_id][stat] = {}

                    if selected_col not in q[data_id][stat]:
                        initial_query_n = FindQueryN(numeric_values, n, epsilon, sensitivity)
                        q[data_id][stat][selected_col] = initial_query_n

                    QueryN = q[data_id][stat][selected_col]

                    if QueryN < 1:
                        result_text = f"이용하실 수 있는 쿼리 수를 모두 소진하셨습니다."
                    else:
                        q[data_id][stat][selected_col] = QueryN - 1
                        request.session["query_budget"] = q

                        noisy_values = laplace_local_differential_privacy(
                            numeric_values,
                            epsilon,
                            sensitivity
                        )

                        cleaned_noisy = []
                        for v in noisy_values:
                            try:
                                cleaned_noisy.append(float(v))
                            except (ValueError, TypeError):
                                continue

                        if not cleaned_noisy:
                            result_text = f"노이즈 적용 후 '{selected_col}' 컬럼에서 숫자 데이터를 찾을 수 없습니다."
                        else:
                            if stat == 'mean':
                                value = calculate_mean(cleaned_noisy)
                                result_text = f"평균({selected_col}) = {float(value):.4f}"
                            elif stat == 'median':
                                value = calculate_median(cleaned_noisy)
                                result_text = f"중앙값({selected_col}) = {float(value):.4f}"
                            elif stat == 'mode':
                                modes = calculate_mode(cleaned_noisy)
                                result_text = f"최빈값({selected_col}) = {list(modes)}"

                            result_text += f" (남은 쿼리: {q[data_id][stat][selected_col]}회)"

        except Data.DoesNotExist:
            result_text = "선택한 데이터가 존재하지 않습니다."
        except Exception as e:
            result_text = f"처리 중 오류: {e}{numeric_values}"

    ctx = {
        'result': result_text,
        'columns': columns,
        'selected_col': selected_col,
    }

    return render(request, 'datause3.html', ctx)


@csrf_exempt  # CSRF는 React에서 처리하므로 여기서는 임시로 제외
def auth_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST 요청만 허용됩니다."})

    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "잘못된 요청입니다."})

    # Django 기본 authenticate 사용 (User 모델이 이메일 기반이면 커스터마이징 필요)
    user = authenticate(request, username=email, password=password)
    if user:
        login(request, user)  # 세션 로그인
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "message": "아이디 또는 비밀번호가 틀렸습니다."})

User = get_user_model()

@csrf_exempt
def signup_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        username = email  # username에 email을 그대로 쓰거나 필요하면 분리

        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "message": "이미 가입된 이메일입니다."})

        user = User.objects.create_user(email=email, password=password)
        login(request, user)  # 회원가입 직후 바로 로그인
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "POST 요청만 허용돼요."})

def user_logout(request):
    logout(request)
    return redirect('main')

# -----------------------------
# 🔥 React용 분석 API (JSON 전용)
# -----------------------------
from django.views.decorators.csrf import csrf_exempt

@login_required
def api_get_columns(request, data_id):
    """특정 데이터의 컬럼 목록 반환"""
    try:
        data_obj = Data.objects.get(pk=data_id)
        raw = _load_dynamic_table_as_list(data_obj.data_name)

        if not raw or len(raw) < 1:
            return JsonResponse({"success": False, "message": "데이터가 비어있습니다."})

        columns = raw[0]
        return JsonResponse({"success": True, "columns": columns})

    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터가 존재하지 않습니다."})


@csrf_exempt
@login_required
def api_analyze(request, data_id):
    """React에서 요청하는 분석 API (평균/중앙값/최빈값)"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST만 허용됩니다."})

    try:
        body = json.loads(request.body)
        stat = body.get("stat")        # mean, median, mode
        selected_col = body.get("col") # 컬럼명
    except:
        return JsonResponse({"success": False, "message": "JSON 형식 오류"})

    if not stat or not selected_col:
        return JsonResponse({"success": False, "message": "stat 또는 col 누락"})

    try:
        data_obj = Data.objects.get(pk=data_id)
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터 없음"})

    # DB에서 데이터 불러오기
    raw_data_with_header = _load_dynamic_table_as_list(data_obj.data_name)
    columns = raw_data_with_header[0]
    rows = raw_data_with_header[1:]

    # -----------------------------
    # 컬럼 인덱스 찾기
    # -----------------------------
    if selected_col not in columns:
        return JsonResponse({"success": False, "message": "해당 컬럼 없음"})

    col_idx = columns.index(selected_col)

    # -----------------------------
    # 숫자만 파싱
    # -----------------------------
    numeric_values = []
    for row in rows:
        try:
            numeric_values.append(float(row[col_idx]))
        except:
            pass

    if not numeric_values:
        return JsonResponse({"success": False, "message": "해당 컬럼에 숫자가 없음"})

    # -----------------------------
    # 쿼리 제한 처리
    # -----------------------------
    n = len(numeric_values)
    sensitivity = (max(numeric_values) - min(numeric_values)) / n
    epsilon = 0.7

    if "query_budget" not in request.session:
        request.session["query_budget"] = {}
    q = request.session["query_budget"]

    if data_id not in q:
        q[data_id] = {}
    if stat not in q[data_id]:
        q[data_id][stat] = {}
    if selected_col not in q[data_id][stat]:
        q[data_id][stat][selected_col] = FindQueryN(
            numeric_values, n, epsilon, sensitivity
        )

    QueryN = q[data_id][stat][selected_col]

    if QueryN < 1:
        return JsonResponse({"success": False, "message": "쿼리 소진됨"})

    q[data_id][stat][selected_col] -= 1
    request.session["query_budget"] = q

    # -----------------------------
    # LDP 적용
    # -----------------------------
    noisy_values = laplace_local_differential_privacy(
        numeric_values, epsilon, sensitivity
    )

    clean = []
    for v in noisy_values:
        try:
            clean.append(float(v))
        except:
            pass

    if not clean:
        return JsonResponse({"success": False, "message": "노이즈 후 값 없음"})

    # -----------------------------
    # 결과 계산
    # -----------------------------
    if stat == "mean":
        value = calculate_mean(clean)
    elif stat == "median":
        value = calculate_median(clean)
    elif stat == "mode":
        modes = calculate_mode(clean)
        value = list(modes)
    else:
        return JsonResponse({"success": False, "message": "stat 잘못됨"})

    return JsonResponse({
        "success": True,
        "result": value,
        "remaining": q[data_id][stat][selected_col]
    })

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Data
from django.db import connection

@login_required
def data_columns_api(request, data_id):
    try:
        data_obj = Data.objects.get(pk=data_id, user=request.user)
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터가 존재하지 않습니다."})

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            [data_obj.data_name],
        )
        columns = [row[0] for row in cursor.fetchall()]

    return JsonResponse({"success": True, "columns": columns})