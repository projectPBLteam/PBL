import numpy as np
import csv
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import mode, kurtosis, skew
from sklearn.linear_model import LinearRegression

def choose_age_range(age_list):
    # std = np.std(age_list)
    # q1 = np.percentile(age_list, 25)
    # q3 = np.percentile(age_list, 75)
    # iqr = q3 - q1
    # age_range = max(age_list) - min(age_list)

    # condition_count = sum([
    #     std < 7,
    #     iqr < 10,
    #     age_range < 25
    # ])

    # if condition_count >= 2:
    #     return 5
    # else:
    #     return 10
    return 5
    
def age_process():
    age_col_name = 'Customer_Age'

    # 헤더에서 나이 컬럼 인덱스 찾기
    try:
        age_col_idx = input_string[0].index(age_col_name)
    except ValueError:
        print(f"[오류] '{age_col_name}' 컬럼을 찾을 수 없습니다.")
        age_col_idx = None

    if age_col_idx is not None:
        # 나이 데이터를 int 리스트로 추출
        age_values = []
        for row in input_string[1:]:
            try:
                age_values.append(int(row[age_col_idx]))
            except:
                continue  # 변환 불가 값은 무시

    #5 or 10 기준 선택 함수 실행
    size = choose_age_range(age_values)

    # 나이를 size 단위로 끊어서 변경
    processed_ages = [(age // size) * size for age in age_values]

    # 변경한 나이를 원본 데이터에 반영하려면 다음과 같이 할 수도 있음
    for i, row in enumerate(input_string[1:]):
        try:
            original_age = int(row[age_col_idx])
            row[age_col_idx] = str((original_age // size) * size)
        except:
            continue

    # 결과 출력해보기
    print(f"선택한 size: {size}")
    print(f"원본 나이: {age_values[:10]}")
    print(f"처리된 나이: {processed_ages[:10]}")



def laplace_mechanism(P, epsilon, sensitivity):
    S = sensitivity / epsilon
    noise = np.random.laplace(0, S)
    return P + noise

def laplace_local_differential_privacy(input_string, epsilon, sensitivity):
    result = Handling_Missing_Values(input_string)
    result = Handle_Outliers(result)
    noisy_data = []
    for row in result:
        noisy_row = []
        for item in row:
            try:
                num = float(item)
                num = laplace_mechanism(num, epsilon, sensitivity)
                noisy_row.append(str(int(num)))
            except ValueError:
                noisy_row.append(item)
        noisy_data.append(noisy_row)
    return noisy_data

# csv파일 읽기
def read_csvfile(filename):
    try:
        df = pd.read_csv(filename, encoding='utf-8', header=0)
        print(f"[디버깅] 읽은 데이터프레임:\n{df.head()}")
        print(f"[디버깅] 컬럼명: {list(df.columns)}")
        return [df.columns.tolist()] + df.values.tolist()
    except FileNotFoundError:
        print(f"[오류] '{filename}' 파일을 찾을 수 없습니다.")
        raise
    except Exception as e:
        print(f"[오류] CSV 파일을 읽는 중 문제가 발생했습니다: {e}")
        raise

# DB 없이 테이블 생성
def create_table(input_string):
    table = pd.DataFrame(input_string[1:], columns=input_string[0])
    return table

# DB 없이 데이터 삽입
def insert_data(input_string, table):
    df = pd.DataFrame(input_string[1:], columns=input_string[0])
    table = pd.concat([table, df], ignore_index=True)
    return table

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

    print(f"\n '{column_name}' 컬럼의 통계 정보:")
    print(f" 표본평균 (sample mean): {np.mean(np.random.choice(numeric_values, len(numeric_values)//5)):.3f}")
    print(f" 모평균 (Mean): {np.mean(numeric_values):.3f}")
    print(f" 중앙값 (Median): {np.median(numeric_values):.3f}")
    print(f" 최빈값 (Mode): {mode(numeric_values, keepdims=False).mode}")
    print(f" 표본 분산 (Sample Variance, ddof=1): {np.var(numeric_values, ddof=1):.3f}")
    print(f" 모분산 (Population Variance, ddof=0): {np.var(numeric_values):.3f}")
    print(f" 표본 표준편차 (Sample Std Dev, ddof=1): {np.std(numeric_values, ddof=1):.3f}")
    print(f" 모표준편차 (Population Std Dev, ddof=0): {np.std(numeric_values):.3f}")
    print(f" 평균의 표준 오차 (SEM): {np.std(numeric_values)/np.sqrt(len(numeric_values)):.3f}")
    print(f" 최대값: {np.max(numeric_values):.3f}")
    print(f" 최소값: {np.min(numeric_values):.3f}")
    print(f" 첨도 (Kurtosis): {kurtosis(numeric_values):.3f}")
    print(f" 왜도 (Skewness): {skew(numeric_values):.3f}")
    print(f" 범위 (Range): {np.max(numeric_values) - np.min(numeric_values):.3f}")

lr = LinearRegression()

#회귀 분석
def Regression_Analysis(data, column_name1, column_name2):
    header = data[0]
    try:
        col_idx1 = header.index(column_name1)
        col_idx2 = header.index(column_name2)
    except ValueError as e:
        print(f"[오류] '{e.args[0].split(': ')[-1]}' 컬럼을 찾을 수 없습니다.")
        return

    numeric_values1 = []
    numeric_values2 = []

    for row in data[1:]:
        try:
            x = float(row[col_idx1])
            y = float(row[col_idx2])
            numeric_values1.append(x)
            numeric_values2.append(y)
        except:
            continue

    if not numeric_values1:
        print(f"[알림] '{column_name1}' 컬럼에 숫자 데이터가 없습니다.")
        return
    if not numeric_values2:
        print(f"[알림] '{column_name2}' 컬럼에 숫자 데이터가 없습니다.")
        return

    X = np.array(numeric_values1).reshape(-1, 1)
    y = np.array(numeric_values2)
    lr.fit(X, y)
    print(f"기울기 (coef): {lr.coef_[0]}")
    print(f"절편 (intercept): {lr.intercept_}")

    # 그래프 그리기
    plt.scatter(X, y, color='blue', label='데이터 점')
    plt.plot(X, lr.predict(X), color='red', label='회귀선')
    plt.xlabel(column_name1)
    plt.ylabel(column_name2)
    plt.title(f"{column_name1} vs {column_name2} 회귀분석")
    plt.legend()
    plt.grid(True)
    plt.show()

#상관분석
def Correlation_Analysis(data, column_name1, column_name2):
    header = data[0]
    try:
        col_idx1 = header.index(column_name1)
        col_idx2 = header.index(column_name2)
    except ValueError:
        print(f"[오류] '{column_name1}' 또는 '{column_name2}' 컬럼을 찾을 수 없습니다.")
        return

    numeric_values1 = []
    numeric_values2 = []

    for row in data[1:]:
        try:
            x = float(row[col_idx1])
            y = float(row[col_idx2])
            numeric_values1.append(x)
            numeric_values2.append(y)
        except:
            continue

    if not numeric_values1 or not numeric_values2:
        print(f"[알림] 숫자 데이터가 부족합니다.")
        return

    correlation = np.corrcoef(numeric_values1, numeric_values2)[0, 1]
    print(f"\n'{column_name1}'과(와) '{column_name2}'의 피어슨 상관계수: {correlation:.3f}")

# 결측치 처리
def Handling_Missing_Values(data):
    df = pd.DataFrame(data[1:], columns=data[0])
    for column in df.columns:
        if df[column].dtype in [np.float64, np.int64]:
            median_val = np.median(df[column].dropna())
            df[column] = df[column].fillna(median_val)
        else:
            df[column] = df[column].fillna("NULL")  # 문자열 컬럼 결측치 처리
    return [data[0]] + df.astype(str).values.tolist()


#이상치 처리
def Handle_Outliers(data):
    df = pd.DataFrame(data[1:], columns=data[0])
    
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].dtype in [np.float64, np.int64]:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                median_val = df[col].median()
                outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                df.loc[outliers, col] = median_val
        except:
            continue
    
    return [data[0]] + df.astype(str).values.tolist()

if __name__ == '__main__':
    filename = input("읽을 파일의 이름을 입력하세요(확장자명까지): ")

    if filename.endswith(".csv"):
        try:
            input_string = read_csvfile(filename)
            #print(f"[디버깅] input_string 첫 번째 행 (헤더): {input_string[0]}")
            col_namei = input("보고싶은 컬럼명을 입력하세요: ")
            table = create_table(input_string)
            table = insert_data(input_string, table)
        except Exception as e:
            print(f"[오류] 파일 처리 중 문제가 발생했습니다: {e}")
            exit(1)
    else:
        print("[오류] CSV 파일만 지원됩니다.")
        exit(1)

    query_n = 0
    confidence_intervals_lower = []
    confidence_intervals_upper = []
    noisy_results = []
    epsilon = 0.1
    sensitivity = 1.0

    while True:
        # user_input = input("쿼리를 요청하시겠습니까? (엔터 = 계속 / q = 종료): ")
        user_input = " "
        if user_input.lower() == 'q':
            break

        try:
            query_n += 1
            result = laplace_local_differential_privacy(input_string, epsilon, sensitivity)
            input_string = result
            age_process()

            if col_namei not in result[0]:
                print(f"[오류] '{col_namei}' 컬럼을 찾을 수 없습니다. 가능한 컬럼: {input_string[0]}")
                continue

            col_idx = input_string[0].index(col_namei)

            numeric_values = []
            for row in result[1:]:
                try:
                    x = float(row[col_idx])
                    numeric_values.append(x)
                except ValueError:
                    continue

            if len(numeric_values) < 5:
                print("데이터가 부족하여 샘플링할 수 없습니다.")
                continue

            sample_values = numeric_values[:10]
            SD = np.std(numeric_values, ddof=0)
            SE = SD / np.sqrt(len(sample_values))
            CI_lower = np.mean(sample_values) - 1.96 * SE
            CI_upper = np.mean(sample_values) + 1.96 * SE

            print(f"\n쿼리 #{query_n}: {sample_values}")
            print(f"표준편차 SD: {SD:.2f}, 표준 오차 SE: {SE:.2f}")
            print(f"95% 신뢰 구간: ({CI_lower:.2f} ~ {CI_upper:.2f})")

            confidence_intervals_lower.append(CI_lower)
            confidence_intervals_upper.append(CI_upper)

            # view_stats = input("원하는 열의 통계를 보고 싶다면 y를 입력하세요: ").lower()
            view_stats = 'y'
            if view_stats == 'y':
                # col_name = input("통계를 보고 싶은 컬럼명을 입력하세요: ")
                col_name = 'Customer_Age'
                if col_name not in input_string[0]:
                    print(f"[오류] '{col_name}' 컬럼을 찾을 수 없습니다. 가능한 컬럼: {input_string[0]}")
                else:
                    print_column_statistics(result, col_name)

            view_stats = input("원하는 컬럼들의 회귀분석을 진행하고 싶다면 y를 입력하세요: ").lower()
            if view_stats == 'y':
                col_name1 = col_name
                # col_name2 = input("분석을 하고 싶은 두 번째 컬럼명을 입력하세요: ")
                col_name2 = 'Credit_Limit'
                if col_name1 not in input_string[0] or col_name2 not in input_string[0]:
                    print(f"[오류] 입력한 컬럼 중 하나가 존재하지 않습니다. 가능한 컬럼: {input_string[0]}")
                else:
                    Regression_Analysis(result, col_name1, col_name2)

            view_corr = input("상관분석을 진행하시겠습니까? (y/n): ").lower()
            if view_corr == 'y':
                col_name1 = col_name
                # col_name2 = input("상관분석을 하고 싶은 두 번째 컬럼명을 입력하세요: ")
                col_name2 = 'Credit_Limit'
                if col_name1 not in input_string[0] or col_name2 not in input_string[0]:
                    print(f"[오류] 입력한 컬럼 중 하나가 존재하지 않습니다. 가능한 컬럼: {input_string[0]}")
                else:
                    Correlation_Analysis(result, col_name1, col_name2)

        except Exception as e:
            print(f"[오류] 쿼리 처리 중 문제가 발생했습니다: {e}")
            continue

    # 신뢰 구간 시각화
    # if confidence_intervals_lower and confidence_intervals_upper:
    #     plt.figure(figsize=(10, 6))
    #     plt.plot(range(query_n), noisy_results, marker='o', linestyle='-', label='Noisy Results')
    #     plt.plot(confidence_intervals_lower, label='신뢰 구간 하한', marker='o', color='blue')
    #     plt.plot(confidence_intervals_upper, label='신뢰 구간 상한', marker='o', color='red')
    #     plt.fill_between(range(len(confidence_intervals_lower)), confidence_intervals_lower, confidence_intervals_upper, color='gray', alpha=0.2)
    #     plt.title("Query results before confidence interval convergence")
    #     plt.xlabel("Query count")
    #     plt.ylabel("Noisy result")
    #     plt.legend()
    #     plt.grid(True)
    #     plt.tight_layout()
    #     plt.show()

    # # 그래프 그리기
    # plt.figure(figsize=(10, 6))
    # plt.plot(range(num_queries), noisy_results, marker='o', linestyle='-', label='Noisy Results')
    # plt.axhline(y=true_mean, color='red', linestyle='--', label='True Value')
