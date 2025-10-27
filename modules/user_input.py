import os
from privacy import laplace_local_differential_privacy
from statistics_basic import print_column_statistics
from statistics_advanced import run_regression_analysis, run_correlation_analysis
from visualization import plot_confidence_intervals
from io_utils import read_csvfile, maketbl, insert_data
import pymysql
import numpy as np

def detect_convergence(relative_widths, threshold, min_consecutive):
    count = 0
    for i, rw in enumerate(relative_widths):
        if not np.isnan(rw) and rw < threshold:
            count += 1
            if count >= min_consecutive:
                return i + 1
        else:
            count = 0
    return None


def start_user_session():
    # DB 연결
    conn = pymysql.connect(
        host='localhost',
        user='code',
        password='Ab!123456',
        db='privacy_db',
        charset='utf8'
    )
    curs = conn.cursor()


    # 파라미터 설정
    epsilon = 1.5
    sensitivity = 1.0
    threshold = 0.05        # 상대폭 5% 기준
    min_consec = 5         # 연속 30회 이하 유지 시 수렴
    max_queries = 100      # 안전장치(최대)

    # 수렴 분석용 리스트 초기화
    estimates = []
    rel_widths = []
    ci_lowers = []
    ci_uppers = []

    converged = False

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

    # 5) 쿼리 루프
    for query_n in range(1, max_queries + 1):
        # 5.1) 로컬 DP 적용
        noisy_data = laplace_local_differential_privacy(input_string, epsilon, sensitivity)

        # 5.2) 대상 컬럼 추출 (예: Customer_Age)
        col_idx = noisy_data[0].index('Customer_Age')
        vals = [float(r[col_idx]) for r in noisy_data[1:] if r[col_idx] not in (None,"")]
        if len(vals) < 5:
            print(f"[쿼리 #{query_n}] 데이터 부족, 스킵")
            continue

        # 5.3) 샘플링 및 추정값 계산
        sample = np.random.choice(vals, size=5, replace=False)
        est = sample.mean()
        estimates.append(est)

        # 5.4) CI 계산 (표준오차 기반)
        SD = np.std(vals, ddof=0)
        SE = SD / np.sqrt(len(sample))
        ci_lower = est - 1.96 * SE
        ci_upper = est + 1.96 * SE
        ci_lowers.append(ci_lower)
        ci_uppers.append(ci_upper)

        # 5.5) 상대 폭 계산
        rel_w = (ci_upper - ci_lower) / est if est != 0 else np.nan
        rel_widths.append(rel_w)

        print(f"[쿼리 #{query_n}] CI 폭: {ci_upper-ci_lower:.4f}, 상대폭: {rel_w:.4f}")

        # 5.6) 수렴 판단
        point = detect_convergence(rel_widths, threshold, min_consec)
        if point:
            print(f"→ 쿼리 #{point} 에서 수렴 판정 (상대폭 {threshold*100:.1f}% 이하 {min_consec}회 연속)")
            converged = True
            break

    if not converged:
        print(f"최대 {max_queries}회 쿼리했지만 수렴하지 않음.")

    # 6) 최종 CI 시각화
    plot_confidence_intervals(
        list(range(1, len(estimates)+1)),
        estimates,
        ci_lowers,
        ci_uppers
    )

    # while True:
    #     user_input = input("쿼리를 요청하시겠습니까? (엔터 = 계속 / q = 종료): ")
    #     if user_input.lower() == 'q':
    #        break

    #     query_n += 1
    #     result = laplace_local_differential_privacy(input_string, epsilon, sensitivity)

    #     # col_name = input("신뢰 구간을 계산할 컬럼명을 입력하세요: ")
    #     col_name = 'Customer_Age'

    #     try:
    #         col_idx = input_string[0].index(col_name)
    #     except ValueError:
    #         print(f"[오류] '{col_name}' 컬럼을 찾을 수 없습니다.")
    #         continue

    #     numeric_values = []
    #     for row in input_string[1:]:
    #         try:
    #             x = float(row[col_idx])
    #             numeric_values.append(x)
    #         except:
    #             continue

    #     if len(numeric_values) < 5:
    #         print("데이터가 부족하여 샘플링할 수 없습니다.")
    #         continue

    #     sample_values = np.random.choice(numeric_values, size=5, replace=False)
    #     SD = np.std(numeric_values, ddof=0)
    #     SE = SD / np.sqrt(len(sample_values))
    #     CI_lower = np.mean(sample_values) - 1.96 * SE
    #     CI_upper = np.mean(sample_values) + 1.96 * SE

    #     print(f"\n쿼리 #{query_n}: {sample_values}")
    #     print(f"표준편차 SD: {SD:.2f}, 표준 오차 SE: {SE:.2f}")
    #     print(f"95% 신뢰 구간: ({CI_lower:.2f} ~ {CI_upper:.2f})")

    #     confidence_intervals_lower.append(CI_lower)
    #     confidence_intervals_upper.append(CI_upper)

        # if input("원하는 열의 통계를 보고 싶다면 y를 입력하세요: ").lower() == 'y':
        #     col_name = input("통계를 보고 싶은 컬럼명을 입력하세요: ")
        #     print_column_statistics(result, col_name)
            
        # if input("회귀분석을 진행하시겠습니까? (y/n): ").lower() == 'y':
        #     col1 = input("첫 번째 컬럼명을 입력하세요: ")
        #     col2 = input("두 번째 컬럼명을 입력하세요: ")
        #     run_regression_analysis(result, col1, col2)

        # if input("상관분석을 진행하시겠습니까? (y/n): ").lower() == 'y':
        #     col1 = input("첫 번째 컬럼명을 입력하세요: ")
        #     col2 = input("두 번째 컬럼명을 입력하세요: ")
        #     method = input("방법을 선택하세요 (pearson/spearman): ").lower()
        #     run_correlation_analysis(result, col1, col2, method=method)

        # if confidence_intervals_lower and confidence_intervals_upper:
        #     plot_confidence_intervals(
        #         list(range(1, query_n + 1)),
        #         [np.mean(np.random.choice(numeric_values, size=5, replace=False)) for _ in range(query_n)],
        #         confidence_intervals_lower,
        #         confidence_intervals_upper
        #     )
