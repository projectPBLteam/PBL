import numpy as np
from scipy import stats

# 기초 통계 함수

# 1. 평균
def calculate_mean(data):
    return np.mean(data)

# 2. 중앙값
def calculate_median(data):
    return np.median(data)

# 3. 최빈값 (여러 개일 경우 모두 반환)
def calculate_mode(data):
    values, counts = np.unique(data, return_counts=True)
    max_count = np.max(counts)
    return values[counts == max_count]

# 4. 범위
def calculate_range(data):
    return np.max(data) - np.min(data)

# 5. 분산 (표본 분산, 자유도 1)
def calculate_variance(data):
    return np.var(data, ddof=1)

# 6. 표준 편차 (표본 표준편차)
def calculate_std_dev(data):
    return np.std(data, ddof=1)

# 7. 평균의 표준 오차 
def calculate_sem(data):
    return stats.sem(data)

# 8. 분포 - 첨도 (Kurtosis)
def calculate_kurtosis(data):
    return stats.kurtosis(data)

# 9. 분포 - 왜도 (Skewness)
def calculate_skewness(data):
    return stats.skew(data)

# 10. 모분산 (모집단 분산)
def calculate_population_variance(data):
    return np.var(data, ddof=0)

# 11. 모표준편차 (모집단 표준편차)
def calculate_population_std_dev(data):
    return np.std(data, ddof=0)



# 통계값 출력

def print_column_statistics(data, column_name):
    header = data[0]
    try:
        col_idx = header.index(column_name)
    except ValueError:
        print(f"[오류] '{column_name}' 컬럼을 찾을 수 없습니다.")
        return

    numeric_values = []
    for row in data[1:]:
        try:
            num = float(row[col_idx])
            numeric_values.append(num)
        except:
            continue

    if not numeric_values:
        print(f"[알림] '{column_name}' 컬럼에 숫자 데이터가 없습니다.")
        return

    print(f"\n'{column_name}' 컬럼의 통계 정보:")
    print(f" 표본평균 (sample mean): {calculate_mean(np.random.choice(numeric_values, len(numeric_values)//5)):.3f}")
    print(f" 모평균 (population mean): {calculate_mean(numeric_values):.3f}")
    print(f" 중앙값: {calculate_median(numeric_values):.3f}")
    print(f" 최빈값: {calculate_mode(numeric_values)}")
    print(f" 표본 분산: {calculate_variance(numeric_values):.3f}")
    print(f" 모분산: {calculate_population_variance(numeric_values):.3f}")
    print(f" 표본 표준편차: {calculate_std_dev(numeric_values):.3f}")
    print(f" 모표준편차: {calculate_population_std_dev(numeric_values):.3f}")
    print(f" 평균의 표준 오차: {calculate_sem(numeric_values):.3f}")
    print(f" 최대값: {np.max(numeric_values):.3f}")
    print(f" 최소값: {np.min(numeric_values):.3f}")
    print(f" 범위: {calculate_range(numeric_values):.3f}")
    print(f" 첨도: {calculate_kurtosis(numeric_values):.3f}")
    print(f" 왜도: {calculate_skewness(numeric_values):.3f}")
