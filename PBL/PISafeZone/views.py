from django.shortcuts import render, redirect
# 로그인한 사용자만 업로드할 수 있도록 @login_required 추가
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import UploadFileForm
from django.db import connection    #DB 커서 접근용
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import EmailLoginForm, RegisterForm
import re   #파일 이름 정제용
from django.contrib import messages
from .models import Data, UsageHistory, CustomUser
import contextlib
import io
import traceback
import pandas as pd
import numpy as np

# 모듈 임포트
from modules.data_utils import read_csvfile, maketbl, insert_data
from modules.privacy import laplace_local_differential_privacy
from modules.statistics_basic import *
from modules.statistics_advanced import run_regression_analysis, run_correlation_analysis
from modules.user_input import FindQueryN

# CSRF 
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
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


SAFE_BUILTINS = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "round": round,
    "sorted": sorted,
    "map": map,
    "filter": filter,
    "all": all,
    "any": any,
    "float": float,
    "int": int,
    "str": str,
    "dict": dict,
    "list": list,
    "tuple": tuple,
    "set": set,
    "print": print,
}


def _build_dataframe(columns, rows):
    df = pd.DataFrame(rows, columns=columns)
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def _select_numeric_seed(columns, rows):
    for idx, _ in enumerate(columns):
        numeric_values = []
        for row in rows:
            try:
                numeric_values.append(float(row[idx]))
            except (ValueError, TypeError, IndexError):
                continue
        if numeric_values:
            return numeric_values
    return [0.0, 1.0]


def _consume_query_budget(request, data_id, stat_key, identifier, sample_values, epsilon=0.7):
    if not sample_values:
        sample_values = [0.0, 1.0]
    n = len(sample_values)
    value_range = max(sample_values) - min(sample_values)
    sensitivity = (value_range / n) if value_range else (1.0 / max(1, n))

    if "query_budget" not in request.session:
        request.session["query_budget"] = {}
    q = request.session["query_budget"]
    q.setdefault(data_id, {})
    q[data_id].setdefault(stat_key, {})

    if identifier not in q[data_id][stat_key]:
        q[data_id][stat_key][identifier] = FindQueryN(sample_values, n, epsilon, sensitivity)

    remaining = q[data_id][stat_key][identifier]
    if remaining < 1:
        return False, 0

    q[data_id][stat_key][identifier] = remaining - 1
    request.session["query_budget"] = q
    request.session.modified = True
    return True, q[data_id][stat_key][identifier]


def _append_console_log(session, data_id, entry):
    history = session.get("custom_console_history", {})
    history[data_id] = history.get(data_id, "") + entry
    session["custom_console_history"] = history
    session.modified = True
    return history[data_id]


def _execute_user_code(code, df, columns):
    output_buffer = io.StringIO()
    safe_globals = {
        "__builtins__": SAFE_BUILTINS,
        "np": np,
        "pd": pd,
        "df": df.copy(),
        "columns": columns,
    }
    try:
        compiled = compile(code, "<사용자 코드>", "exec")
        with contextlib.redirect_stdout(output_buffer):
            exec(compiled, safe_globals, {})
        output = output_buffer.getvalue().strip()
        return output if output else "코드가 성공적으로 실행되었습니다."
    except Exception:
        output = output_buffer.getvalue()
        output += "\n" + traceback.format_exc(limit=5)
        return output.strip()


def _handle_custom_code(request, data_id, code, columns, raw_rows, current_log):
    trimmed_code = (code or "").strip()
    if not trimmed_code:
        return "실행할 코드를 입력해주세요.", current_log

    df = _build_dataframe(columns, raw_rows)
    numeric_seed = _select_numeric_seed(columns, raw_rows)
    allowed, remaining = _consume_query_budget(
        request,
        data_id,
        "custom_code",
        "__custom_console__",
        numeric_seed,
    )

    if not allowed:
        entry = f">>> {trimmed_code}\n[예산 부족] 이용 가능한 쿼리가 없습니다.\n"
        updated_log = _append_console_log(request.session, data_id, entry)
        return "이용하실 수 있는 쿼리 수를 모두 소진하셨습니다. (남은 쿼리: 0회)", updated_log

    execution_output = _execute_user_code(trimmed_code, df, columns)
    entry = f">>> {trimmed_code}\n{execution_output}\n(남은 쿼리: {remaining}회)\n"
    updated_log = _append_console_log(request.session, data_id, entry)
    return "사용자 코드가 실행되었습니다. 아래 콘솔에서 결과를 확인하세요.", updated_log



@login_required
def datause3(request):
    data_id = request.GET.get('data') or request.POST.get('data')
    stat = request.GET.get('stat') or request.POST.get('stat')
    
    selected_col_single = request.GET.get('col_single') 
    selected_col_y = request.GET.get('col_y')
    selected_col_x = request.GET.get('col_x')

    is_custom_mode = request.method == "POST" and request.POST.get('mode') == 'custom_code'
    if is_custom_mode:
        stat = 'custom_code'
    last_custom_code = request.POST.get('custom_code', '') if is_custom_mode else ''

    if stat in ('regression', 'correlation_p', 'correlation_s'):
        selected_col = f"{selected_col_y} vs {selected_col_x}"
    else:
        selected_col = selected_col_single
    
    result_text = None
    columns = []
    custom_console_history = request.session.get("custom_console_history", {})
    custom_console_log = custom_console_history.get(data_id, "")

    def _render_response():
        return render(
            request,
            'datause3.html',
            {
                'result': result_text,
                'columns': columns,
                'selected_col_single': selected_col_single,
                'selected_col_y': selected_col_y,
                'selected_col_x': selected_col_x,
                'stat': stat,
                'data_id': data_id,
                'custom_console_log': custom_console_log,
                'is_custom_mode': is_custom_mode,
                'last_custom_code': last_custom_code,
            },
        )
    
    if data_id:
        try:
            data_obj = Data.objects.get(pk=data_id)
            raw_data_with_header = _load_dynamic_table_as_list(data_obj.data_name)
        
            if not raw_data_with_header or len(raw_data_with_header) < 2:
                raise ValueError("데이터가 비어있습니다.")

            columns = raw_data_with_header[0]
            raw_data = raw_data_with_header[1:]

            if is_custom_mode:
                result_text, custom_console_log = _handle_custom_code(
                    request,
                    data_id,
                    request.POST.get('custom_code'),
                    columns,
                    raw_data,
                    custom_console_log,
                )
            else:
                col_to_process = []
                
                if stat in ('regression', 'correlation_p', 'correlation_s'):
                    if not selected_col_y or not selected_col_x:
                        result_text = "분석을 위해 종속 변수(Y)와 독립 변수(X)를 모두 선택해야 합니다."
                        return _render_response()
                    col_to_process.append(selected_col_y)
                    col_to_process.append(selected_col_x)
                    
                elif selected_col_single:
                    col_to_process.append(selected_col_single)
                else:
                    col_to_process = []

                if col_to_process:
                    col_data = {}
                    col_indices = {}
                    
                    for col_name in col_to_process:
                        try:
                            col_idx = columns.index(col_name)
                            col_indices[col_name] = col_idx
                            
                            numeric_values = []
                            for row in raw_data:
                                try:
                                    numeric_values.append(float(row[col_idx]))
                                except (ValueError, TypeError):
                                    continue
                            col_data[col_name] = numeric_values
                            
                        except ValueError:
                            result_text = f"컬럼 '{col_name}'을(를) 찾을 수 없습니다."
                            return _render_response()
                
                    main_col_name = selected_col_y if stat == 'regression' else selected_col_single
                    main_values = col_data.get(main_col_name, [])
                    
                    if not main_values:
                        result_text = f"선택한 컬럼에서 숫자 데이터를 찾을 수 없습니다."
                        return _render_response()
                    
                    n = len(main_values)
                    sensitivity = (max(main_values) - min(main_values)) / n
                    epsilon = 0.7

                    if "query_budget" not in request.session:
                        request.session["query_budget"] = {}

                    q = request.session["query_budget"]

                    if data_id not in q:
                        q[data_id] = {}

                    if stat not in q[data_id]:
                        q[data_id][stat] = {}

                    if selected_col not in q[data_id][stat]:
                        initial_query_n = FindQueryN(main_values, n, epsilon, sensitivity)
                        q[data_id][stat][selected_col] = initial_query_n

                    QueryN = q[data_id][stat][selected_col]

                    if QueryN < 1:
                        result_text = f"이용하실 수 있는 쿼리 수를 모두 소진하셨습니다. (남은 쿼리: 0회)"
                    else:
                        q[data_id][stat][selected_col] = QueryN - 1
                        request.session["query_budget"] = q
                        
                        noisy_col_data = {}
                        for col_name, numeric_values in col_data.items():
                            sensitivity_col = (max(numeric_values) - min(numeric_values)) / len(numeric_values)
                            noisy_values = laplace_local_differential_privacy(
                                numeric_values,
                                epsilon,
                                sensitivity_col
                            )
                            noisy_col_data[col_name] = [float(v) for v in noisy_values if isinstance(v, (int, float))]
                        
                        data_length = len(raw_data)
                        noisy_data_with_header = [columns[:]] 
                        
                        for i in range(data_length):
                            new_row = raw_data[i][:]
                            valid_row = True
                            for col_name in col_to_process:
                                original_idx = col_indices[col_name]
                                noisy_list = noisy_col_data[col_name]
                                
                                if i < len(noisy_list):
                                    new_row[original_idx] = noisy_list[i]
                                else:
                                    valid_row = False
                            
                            if valid_row:
                                noisy_data_with_header.append(new_row)

                        if stat == 'mean':
                            value = calculate_mean(noisy_col_data[main_col_name])
                            result_text = f"평균({selected_col}) = {float(value):.4f}"
                        elif stat == 'median':
                            value = calculate_median(noisy_col_data[main_col_name])
                            result_text = f"중앙값({selected_col}) = {float(value):.4f}"
                        elif stat == 'mode':
                            modes = calculate_mode(noisy_col_data[main_col_name])
                            result_text = f"최빈값({selected_col}) = {list(modes)}"
                        elif stat == 'variance':
                            value = calculate_variance(noisy_col_data[main_col_name])
                            result_text = f"표본분산({selected_col}) = {float(value):.4f}"
                        elif stat == 'std_dev':
                            value = calculate_std_dev(noisy_col_data[main_col_name])
                            result_text = f"표준편차({selected_col}) = {float(value):.4f}"
                        elif stat == 'sem':
                            value = calculate_sem(noisy_col_data[main_col_name])
                            result_text = f"표준오차({selected_col}) = {float(value):.4f}"
                        
                        elif stat == 'regression':
                            result_text = run_regression_analysis(
                                noisy_data_with_header, 
                                selected_col_x, 
                                selected_col_y
                            )

                        elif stat == 'correlation_p': 
                            result_text = run_correlation_analysis(
                                noisy_data_with_header, 
                                selected_col_x, 
                                selected_col_y,
                                'pearson'
                            )

                        elif stat == 'correlation_s': 
                            result_text = run_correlation_analysis(
                                noisy_data_with_header, 
                                selected_col_x, 
                                selected_col_y,
                                'spearman'
                            )
                        
                        result_text += f"\n (남은 쿼리: {q[data_id][stat][selected_col]}회)"

        except Data.DoesNotExist:
            result_text = "선택한 데이터가 존재하지 않습니다."
        except Exception as e:
            result_text = f"처리 중 오류: {e}"
    else:
        if is_custom_mode:
            result_text = "데이터를 먼저 선택한 뒤 사용자 코드를 실행할 수 있습니다."

    return _render_response()


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