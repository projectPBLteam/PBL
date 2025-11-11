import os
from scipy import stats
from .privacy import laplace_local_differential_privacy
from .statistics_basic import print_column_statistics
from .statistics_advanced import run_regression_analysis, run_correlation_analysis
from .visualization import plot_confidence_intervals
from .data_utils import read_csvfile, maketbl, insert_data
import pymysql
import numpy as np

# 상대 신뢰구간 길이 계산 함수
def relative_ci_width(data, confidence=0.95):
    if len(data) < 2:
        return np.inf
    mean = np.mean(data)
    sem = stats.sem(data)
    margin = sem * stats.t.ppf((1 + confidence) / 2., len(data) - 1)
    width = 2 * margin
    return width / abs(mean) if mean != 0 else np.inf

# 수렴 판단 함수 (적응형 threshold)
def find_convergence(values, window_size=5, threshold=0.05, streak_required=5):
    streak = 0
    for i in range(len(values) - window_size + 1):
        window = values[i:i + window_size]
        rel_width = relative_ci_width(window)
        if rel_width < threshold:
            streak += 1
            if streak >= streak_required:
                return i + window_size
        else:
            streak = 0
    return None

def FindQueryN(raw, n, epsilon, sensitivity):
    # 신뢰구간 제한 쿼리 수 계산
    window_size = int(max(20, min(100, n * 0.003)))
    threshold = max(0.01, min(0.1, sensitivity / np.mean(raw)))
    streak_required = 5
    convergence_list = []

    for _ in range(20):
        # 1차원 리스트 반환
        noisy_values = laplace_local_differential_privacy(raw, epsilon, sensitivity)
        conv = find_convergence(noisy_values, window_size, threshold, streak_required)
        convergence_list.append(conv)

    # 수렴 결과 유효값만 사용
    valid_convs = [x for x in convergence_list if x is not None]
    if not valid_convs:
        return 1  # 수렴하지 않으면 최소 1회
    # 평균 수렴 시점 반환
    N = int(np.mean(valid_convs))
    return N

        

def start_user_session():
    # DB 연결
    conn = pymysql.connect(
        host='%',
        user='ddu',
        password='mickey423212',
        db='MyLocalDB',
        charset='utf8'
    )
    curs = conn.cursor()
    epsilon = 0.5
    sensitivity = 1.0

    filename = input("읽을 파일의 이름을 입력하세요(확장자명까지): ")
    if not filename.endswith(".csv"):
        print("[오류] CSV 파일만 지원됩니다.")
        return

    input_string = read_csvfile(filename)
    tablename = "userTable_" + os.path.splitext(os.path.basename(filename))[0]

    maketbl(input_string, conn, curs, tablename)
    insert_data(input_string, conn, curs, tablename)

    query_n = 0
    confidence_intervals_lower = []
    confidence_intervals_upper = []

    while True:
        user_input = input("쿼리를 요청하시겠습니까? (엔터 = 계속 / q = 종료): ")
        if user_input.lower() == 'q':
            break

        query_n += 1
        result = laplace_local_differential_privacy(input_string, epsilon, sensitivity)

        col_name = input("신뢰 구간을 계산할 컬럼명을 입력하세요: ")
        try:
            col_idx = input_string[0].index(col_name)
        except ValueError:
            print(f"[오류] '{col_name}' 컬럼을 찾을 수 없습니다.")
            continue

        numeric_values = []
        for row in input_string[1:]:
            try:
                x = float(row[col_idx])
                numeric_values.append(x)
            except:
                continue

        if len(numeric_values) < 5:
            print("데이터가 부족하여 샘플링할 수 없습니다.")
            continue

        sample_values = np.random.choice(numeric_values, size=5, replace=False)
        SD = np.std(numeric_values, ddof=0)
        SE = SD / np.sqrt(len(sample_values))
        CI_lower = np.mean(sample_values) - 1.96 * SE
        CI_upper = np.mean(sample_values) + 1.96 * SE

        print(f"\n쿼리 #{query_n}: {sample_values}")
        print(f"표준편차 SD: {SD:.2f}, 표준 오차 SE: {SE:.2f}")
        print(f"95% 신뢰 구간: ({CI_lower:.2f} ~ {CI_upper:.2f})")

        confidence_intervals_lower.append(CI_lower)
        confidence_intervals_upper.append(CI_upper)

        if input("원하는 열의 통계를 보고 싶다면 y를 입력하세요: ").lower() == 'y':
            col_name = input("통계를 보고 싶은 컬럼명을 입력하세요: ")
            print_column_statistics(result, col_name)
            
        if input("회귀분석을 진행하시겠습니까? (y/n): ").lower() == 'y':
            col1 = input("첫 번째 컬럼명을 입력하세요: ")
            col2 = input("두 번째 컬럼명을 입력하세요: ")
            run_regression_analysis(result, col1, col2)

        if input("상관분석을 진행하시겠습니까? (y/n): ").lower() == 'y':
            col1 = input("첫 번째 컬럼명을 입력하세요: ")
            col2 = input("두 번째 컬럼명을 입력하세요: ")
            method = input("방법을 선택하세요 (pearson/spearman): ").lower()
            run_correlation_analysis(result, col1, col2, method=method)

        if confidence_intervals_lower and confidence_intervals_upper:
            plot_confidence_intervals(
                list(range(1, query_n + 1)),
                [np.mean(np.random.choice(numeric_values, size=5, replace=False)) for _ in range(query_n)],
                confidence_intervals_lower,
                confidence_intervals_upper
            )
