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
import logging

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
    # statistics_basic과 statistics_advanced 모듈의 모든 함수 사용 차단
    blocked_functions = [
        # statistics_basic 모듈 함수들
        'calculate_mean', 'calculate_median', 'calculate_mode', 
        'calculate_range', 'calculate_variance', 'calculate_std_dev', 
        'calculate_sem', 'calculate_kurtosis', 'calculate_skewness',
        'calculate_population_variance', 'calculate_population_std_dev',
        'print_column_statistics',
        # statistics_advanced 모듈 함수들
        'run_regression_analysis', 'run_correlation_analysis',
        'pearson_correlation', 'spearman_correlation',
        # 기타 (레거시)
        'Regression_Analysis', 'Correlation_Analysis'
    ]
    
    code_lower = code.lower()
    for func in blocked_functions:
        if func.lower() in code_lower:
            raise ValueError(f"'{func}'와 같은 분석 모듈 함수는 직접 코드 입력에서 사용할 수 없습니다. 왼쪽 선택창에서 분석 옵션을 선택해주세요.")
    
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
    
logger = logging.getLogger(__name__)

def _handle_custom_code(request, data_id, code, columns, raw_rows, current_log):
    trimmed_code = (code or "").strip()
    if not trimmed_code:
        return "실행할 코드를 입력해주세요.", current_log

    # 사용한 코드 기록 확인 (같은 코드 재사용 방지)
    if "used_custom_codes" not in request.session:
        request.session["used_custom_codes"] = {}
    used_codes = request.session["used_custom_codes"]
    data_key = str(data_id)
    
    if data_key not in used_codes:
        used_codes[data_key] = {}
    
    # 코드의 해시값을 키로 사용 (공백/줄바꿈 정규화)
    import hashlib
    normalized_code = ' '.join(trimmed_code.split())
    code_hash = hashlib.md5(normalized_code.encode()).hexdigest()
    
    # 이미 사용한 코드인지 확인
    if code_hash in used_codes[data_key]:
        entry = f">>> {trimmed_code}\n[재사용 불가] 이미 사용한 통계처리입니다. 같은 분석은 한 번만 사용할 수 있습니다.\n"
        updated_log = _append_console_log(request.session, data_id, entry)
        return "이미 사용한 통계처리입니다. 같은 분석은 한 번만 사용할 수 있습니다. ", updated_log

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
    
    try:
        execution_output = _execute_user_code(trimmed_code, dp_df, columns)
        
        # 코드 실행 성공 시 사용한 코드 기록
        used_codes[data_key][code_hash] = True
        request.session["used_custom_codes"] = used_codes
        request.session.modified = True
        
        entry = f">>> {trimmed_code}\n{execution_output}\n"

        logger.info("---------------------------------------------------------------")
        logger.info("") 
        logger.info(f"(남은 쿼리: {remaining}회)")
        logger.info("") 
        logger.info("---------------------------------------------------------------")
        
        updated_log = _append_console_log(request.session, data_id, entry)
        return "사용자 코드가 실행되었습니다. 아래 콘솔에서 결과를 확인하세요.", updated_log
    except ValueError as e:
        # 분석 모듈 함수 사용 시도 시 에러 메시지 반환
        error_msg = str(e)
        entry = f">>> {trimmed_code}\n[오류] {error_msg}\n"
        updated_log = _append_console_log(request.session, data_id, entry)
        return error_msg, updated_log
    except Exception as e:
        # 기타 실행 오류
        error_msg = f"코드 실행 중 오류가 발생했습니다: {str(e)}"
        entry = f">>> {trimmed_code}\n[오류] {error_msg}\n"
        updated_log = _append_console_log(request.session, data_id, entry)
        return error_msg, updated_log



@login_required
def datause3(request):
    return


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
    keys_to_delete = [
        'used_analyses',
        'used_custom_codes',
        'custom_console_history',
        'last_executed_code',
        'last_execution_result',
        'custom_code_cache',
    ]

    for key in keys_to_delete:
        if key in request.session:
            del request.session[key]
            
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
    # React에서 요청하는 분석 API (평균/회귀 등 포함)
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

    # 사용한 분석 기록 확인
    used_analyses = request.session.setdefault("used_analyses", {})
    if data_key not in used_analyses:
        used_analyses[data_key] = {}
    if stat not in used_analyses[data_key]:
        used_analyses[data_key][stat] = {}
    
    # 이미 사용한 분석인지 확인
    if selected_key in used_analyses[data_key][stat]:
        return JsonResponse({
            "success": False, 
            "message": "이미 사용한 통계처리입니다. 같은 분석은 한 번만 사용할 수 있습니다. 결과를 반출하거나 페이지를 나간 후 다시 들어오시면 다시 분석할 수 있습니다."
        })

    remaining = stat_bucket[selected_key]
    if remaining < 1:
        return JsonResponse({"success": False, "message": "이용 가능한 쿼리가 모두 소진되었습니다."})

    stat_bucket[selected_key] = remaining - 1
    request.session["query_budget"] = session_budget
    
    # 분석 사용 기록
    used_analyses[data_key][stat][selected_key] = True
    request.session["used_analyses"] = used_analyses
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
    
    logger.info("---------------------------------------------------------------")
    logger.info("") 
    logger.info(f"(남은 쿼리: {remaining}회)")
    logger.info("") 
    logger.info("---------------------------------------------------------------")

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
    
    # 재사용 불가 또는 오류 메시지인 경우 success: False로 반환
    is_error = (
        "이미 사용한 통계처리" in message or
        "오류" in message or
        "사용할 수 없습니다" in message or
        "모듈 함수" in message
    )
    
    return JsonResponse({
        "success": not is_error, 
        "message": message, 
        "log": updated_log
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


@csrf_exempt
@login_required
def api_reset_used_analyses(request, data_id):
    """결과 반출 시 사용한 분석 기록 초기화 및 쿼리 차감"""
    try:
        data_obj = Data.objects.get(pk=data_id, user=request.user)
    except Data.DoesNotExist:
        return JsonResponse({"success": False, "message": "데이터가 존재하지 않습니다."})
    
    data_key = str(data_id)
    used_analyses = request.session.get("used_analyses", {})
    
    # 사용한 분석이 있다면 쿼리 차감
    if data_key in used_analyses and used_analyses[data_key]:
        if "query_budget" in request.session:
            q = request.session["query_budget"]
            if data_key in q:
                for stat_key in list(q[data_key].keys()):
                    if stat_key in used_analyses.get(data_key, {}):
                        for col_key in list(q[data_key][stat_key].keys()):
                            if col_key in used_analyses.get(data_key, {}).get(stat_key, {}):
                                # 쿼리 차감
                                if q[data_key][stat_key][col_key] > 0:
                                    q[data_key][stat_key][col_key] -= 1
                request.session["query_budget"] = q
                request.session.modified = True
        
        # 사용한 분석 기록 초기화 (다시 분석할 수 있도록)
        del used_analyses[data_key]
        request.session["used_analyses"] = used_analyses
        request.session.modified = True
    
    # 직접 코드 입력 기록도 초기화
    used_codes = request.session.get("used_custom_codes", {})
    if data_key in used_codes and used_codes[data_key]:
        # 사용한 코드가 있다면 쿼리 차감
        if "query_budget" in request.session:
            q = request.session["query_budget"]
            if data_key in q and "custom_code" in q[data_key]:
                if "__custom_console__" in q[data_key]["custom_code"]:
                    if q[data_key]["custom_code"]["__custom_console__"] > 0:
                        q[data_key]["custom_code"]["__custom_console__"] -= 1
            request.session["query_budget"] = q
            request.session.modified = True
        
        # 사용한 코드 기록 초기화
        del used_codes[data_key]
        request.session["used_custom_codes"] = used_codes
        request.session.modified = True
    
    return JsonResponse({"success": True, "message": "사용한 분석 기록이 초기화되었습니다."})