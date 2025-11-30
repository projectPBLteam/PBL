from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .forms import UploadFileForm
from django.db import connection   
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import EmailLoginForm, RegisterForm
import re  
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


from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
import json
from django.contrib.auth.decorators import login_required

def _sanitize_table_name(filename):
    name_without_extension = filename.rsplit('.', 1)[0]
    sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', name_without_extension)
    return sanitized_name.lower()

def main(request):
    return render(request, 'main.html')

def info_hub(request):
    return render(request, 'info_hub.html')

@login_required
def dataUpload(request):
    return redirect('dataUploadNext')

@login_required
def dataUploadNext(request):
    form = UploadFileForm()
    return render(request, 'dataupload2.html',  {'form':form})

@login_required
@csrf_exempt
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
    data_objs = Data.objects.filter(user=request.user).select_related('user')
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
def data_detail(request, id):
    try:
        obj = Data.objects.get(data_id=id, user=request.user)
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터 없음!"})

    return JsonResponse({
        "success": True,
        "data": {
            "id": str(obj.data_id),
            "name": obj.data_name,
            "provider": obj.user.email,
            "uploadDate": obj.data_date.strftime("%Y.%m.%d"),
            "usageCount": obj.data_usage,
            "catalog": obj.catalog if hasattr(obj, 'catalog') else "미지정",
        }
    })

@login_required
def datause(request):
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
        try:
            compiled = compile(code, "<사용자 코드>", "eval")
            is_expression = True
        except SyntaxError:
            compiled = compile(code, "<사용자 코드>", "exec")
            is_expression = False

        with contextlib.redirect_stdout(output_buffer):
            
            if is_expression:
                result = eval(compiled, safe_globals, {})
                if result is not None:
                    print(result) 
            else:
                exec(compiled, safe_globals, {})

        output = output_buffer.getvalue().strip()
        
        return output if output else "코드가 성공적으로 실행되었습니다. (출력 없음)"
            
    except Exception:
        output = output_buffer.getvalue()
        output += "\n" + traceback.format_exc(limit=5)
        return output.strip()


def _handle_custom_code(request, data_id, code, columns, raw_rows, current_log):
    trimmed_code = (code or "").strip()
    if not trimmed_code:
        return "실행할 코드를 입력해주세요.", current_log

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
    
    epsilon = 0.7 
    all_indices = {col: i for i, col in enumerate(columns)}
    noisy_col_data = {}
    
    for name in columns:
        if name == 'id':
            continue 

        is_integer_column = True
        raw_values = []
        
        for row in raw_rows: 
            try:
                val = row[all_indices[name]]
                float_val = float(val)
                
                if float_val != int(float_val):
                    is_integer_column = False
                    
                raw_values.append(float_val)
            except (ValueError, TypeError, IndexError):
                is_integer_column = False
                continue

        if len(raw_values) > 1: 
            n = len(raw_values)
            value_range = max(raw_values) - min(raw_values)
            col_sensitivity = (value_range / n) if value_range else (1.0 / max(1, n))
            noisy_values = laplace_local_differential_privacy(raw_values, epsilon, col_sensitivity)
            cleaned = []
            for v in noisy_values:
                try:
                    float_v = float(v)
                    
                    if is_integer_column:
                        cleaned.append(int(round(float_v))) 
                    else:
                        cleaned.append(float_v)
                        
                except (TypeError, ValueError):
                    continue
            noisy_col_data[name] = cleaned
            
        elif len(raw_values) == 1:
            if is_integer_column:
                noisy_col_data[name] = [int(raw_values[0])]
            else:
                noisy_col_data[name] = raw_values

    noisy_rows = []
    for row_idx in range(len(raw_rows)):
        new_row = list(raw_rows[row_idx])
        valid_row = True
        
        for name in columns:
            col_idx = all_indices[name]
            
            if name in noisy_col_data:
                source_list = noisy_col_data[name]
                if row_idx < len(source_list):
                    new_row[col_idx] = source_list[row_idx]
                else:
                    valid_row = False 
                    break
            
        if valid_row:
            noisy_rows.append(new_row)

    dp_df = _build_dataframe(columns, noisy_rows)
    execution_output = _execute_user_code(trimmed_code, dp_df, columns)
    
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


@csrf_exempt 
def auth_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST 요청만 허용됩니다."})

    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "잘못된 요청입니다."})

    user = authenticate(request, username=email, password=password)
    if user:
        login(request, user) 
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
        username = email 

        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "message": "이미 가입된 이메일입니다."})

        user = User.objects.create_user(email=email, password=password)
        login(request, user)
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "POST 요청만 허용돼요."})

def user_logout(request):
    logout(request)
    return redirect('main')

from django.views.decorators.csrf import csrf_exempt

@login_required
def api_get_columns(request, data_id):
    """특정 데이터의 컬럼 목록 반환"""
    try:
        data_obj = Data.objects.get(pk=data_id, user=request.user)
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터가 존재하지 않습니다."})

    raw = _load_dynamic_table_as_list(data_obj.data_name)
    if not raw or len(raw) < 1:
        return JsonResponse({"success": False, "message": "데이터가 비어있습니다."})

    columns = raw[0]
    return JsonResponse({"success": True, "columns": columns})


@csrf_exempt
@login_required
def api_increment_usage(request, data_id):
    """데이터 분석 화면 진입 시 이용 횟수 증가"""
    try:
        from django.db.models import F
        data_obj = Data.objects.get(pk=data_id, user=request.user)
        Data.objects.filter(pk=data_id, user=request.user).update(data_usage=F('data_usage') + 1)
        data_obj.refresh_from_db()
        
        UsageHistory.objects.create(
            usage_type="analyze",
            user=request.user,
            data=data_obj
        )
        
        return JsonResponse({
            "success": True,
            "usageCount": data_obj.data_usage
        })
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터가 존재하지 않습니다."})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"오류 발생: {str(e)}"})


@csrf_exempt
@login_required
def api_analyze(request, data_id):
    """React에서 요청하는 분석 API (평균/회귀 등 포함)"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST만 허용됩니다."})

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON 형식 오류"})

    stat = body.get("stat")
    col_single = body.get("col")
    col_y = body.get("col_y")
    col_x = body.get("col_x")

    if not stat:
        return JsonResponse({"success": False, "message": "stat 누락"})

    dual_required = stat in {"regression", "correlation_p", "correlation_s"}
    if dual_required:
        if not col_y or not col_x:
            return JsonResponse({"success": False, "message": "Y/X 컬럼을 모두 선택해주세요."})
        target_columns = [col_y, col_x]
        selected_key = f"{col_y} vs {col_x}"
        main_col = col_y
    else:
        if not col_single:
            return JsonResponse({"success": False, "message": "컬럼을 선택해주세요."})
        target_columns = [col_single]
        selected_key = col_single
        main_col = col_single

    try:
        data_obj = Data.objects.get(pk=data_id, user=request.user)
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터 없음"})

    raw_with_header = _load_dynamic_table_as_list(data_obj.data_name)
    if not raw_with_header or len(raw_with_header) < 2:
        return JsonResponse({"success": False, "message": "데이터가 비어있습니다."})

    columns = raw_with_header[0]
    raw_rows = raw_with_header[1:]

    col_data = {}
    col_indices = {}
    for name in target_columns:
        if name not in columns:
            return JsonResponse({"success": False, "message": f"컬럼 '{name}'을 찾을 수 없습니다."})
        idx = columns.index(name)
        col_indices[name] = idx
        numeric_values = []
        for row in raw_rows:
            try:
                numeric_values.append(float(row[idx]))
            except (ValueError, TypeError):
                continue
        if not numeric_values:
            return JsonResponse({"success": False, "message": f"컬럼 '{name}'에 숫자 데이터가 없습니다."})
        col_data[name] = numeric_values

    main_values = col_data[main_col]
    n = len(main_values)
    epsilon = 0.7
    value_range = max(main_values) - min(main_values)
    sensitivity = (value_range / n) if value_range else (1.0 / max(1, n))

    data_key = str(data_id)
    session_budget = request.session.setdefault("query_budget", {})
    stat_bucket = session_budget.setdefault(data_key, {}).setdefault(stat, {})
    if selected_key not in stat_bucket:
        stat_bucket[selected_key] = FindQueryN(main_values, n, epsilon, sensitivity)

    remaining = stat_bucket[selected_key]
    if remaining < 1:
        return JsonResponse({"success": False, "message": "이용 가능한 쿼리가 모두 소진되었습니다."})

    stat_bucket[selected_key] = remaining - 1
    request.session["query_budget"] = session_budget
    request.session.modified = True

    noisy_col_data = {}
    for name, numeric_values in col_data.items():
        col_range = max(numeric_values) - min(numeric_values)
        col_sensitivity = (col_range / len(numeric_values)) if col_range else (1.0 / max(1, len(numeric_values)))
        noisy_values = laplace_local_differential_privacy(numeric_values, epsilon, col_sensitivity)
        cleaned = []
        for v in noisy_values:
            try:
                cleaned.append(float(v))
            except (TypeError, ValueError):
                continue
        if not cleaned:
            return JsonResponse({"success": False, "message": f"'{name}' 컬럼에서 노이즈 적용 후 값이 없습니다."})
        noisy_col_data[name] = cleaned

    result_text = ""
    if stat == "mean":
        value = calculate_mean(noisy_col_data[main_col])
        result_text = f"평균({selected_key}) = {float(value):.4f}"
    elif stat == "median":
        value = calculate_median(noisy_col_data[main_col])
        result_text = f"중앙값({selected_key}) = {float(value):.4f}"
    elif stat == "mode":
        modes = calculate_mode(noisy_col_data[main_col])
        result_text = f"최빈값({selected_key}) = {list(modes)}"
    elif stat == "variance":
        value = calculate_variance(noisy_col_data[main_col])
        result_text = f"표본분산({selected_key}) = {float(value):.4f}"
    elif stat == "std_dev":
        value = calculate_std_dev(noisy_col_data[main_col])
        result_text = f"표준편차({selected_key}) = {float(value):.4f}"
    elif stat == "sem":
        value = calculate_sem(noisy_col_data[main_col])
        result_text = f"표준오차({selected_key}) = {float(value):.4f}"
    elif stat == "regression" or stat.startswith("correlation_"):
        noisy_data_with_header = [columns[:]]
        for row_idx in range(len(raw_rows)):
            new_row = list(raw_rows[row_idx])
            valid_row = True
            for name in target_columns:
                source_list = noisy_col_data[name]
                col_idx = col_indices[name]
                if row_idx < len(source_list):
                    new_row[col_idx] = source_list[row_idx]
                else:
                    valid_row = False
                    break
            if valid_row:
                noisy_data_with_header.append(new_row)

        if stat == "regression":
            result_text = run_regression_analysis(noisy_data_with_header, col_x, col_y)
        else:
            method = "pearson" if stat == "correlation_p" else "spearman"
            result_text = run_correlation_analysis(noisy_data_with_header, col_x, col_y, method)
    else:
        return JsonResponse({"success": False, "message": "지원하지 않는 stat 입니다."})

    return JsonResponse({
        "success": True,
        "result": result_text,
        "remaining": stat_bucket[selected_key]
    })


@csrf_exempt
@login_required
def api_custom_console(request, data_id):
    """React에서 사용자 정의 코드를 실행하거나 로그를 반환"""
    try:
        data_obj = Data.objects.get(pk=data_id, user=request.user)
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터 없음"})

    raw_with_header = _load_dynamic_table_as_list(data_obj.data_name)
    if not raw_with_header or len(raw_with_header) < 2:
        return JsonResponse({"success": False, "message": "데이터가 비어있습니다."})

    columns = raw_with_header[0]
    raw_rows = raw_with_header[1:]

    session_history = request.session.get("custom_console_history", {})
    data_key = str(data_id)
    current_log = session_history.get(data_key, "")

    if request.method == "GET":
        return JsonResponse({"success": True, "log": current_log})

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "지원하지 않는 메서드입니다."})

    try:
        body = json.loads(request.body)
        code = body.get("code", "")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON 형식 오류"})

    message, updated_log = _handle_custom_code(
        request,
        data_key,
        code,
        columns,
        raw_rows,
        current_log,
    )
    return JsonResponse({"success": True, "message": message, "log": updated_log})

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