import numpy as np
import csv
import pymysql
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import mode, kurtosis, skew
from sklearn.linear_model import LinearRegression

def laplace_mechanism(P, epsilon, sensitivity):
    S = sensitivity / epsilon
    noise = np.random.normal(0, S)
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
    df = pd.read_csv(filename, encoding='utf-8')
    return df.values.tolist()

    # input_data=[]
    # with open(filename, 'r', encoding='utf-8') as f:
    #     rdr = csv.reader(f)
    #     for line in rdr:
    #         input_data.append(line)
    # return input_data

# DB 테이블 만들기
def maketbl(input_string, conn, curs):
    global tableN
    # 데이터 크기, 이름 확인
    input_len=[]
    input_type=[]
    input_id=[]
    for l in input_string[0]:
        i_id = l
        i_len= len(l)
        input_id.append(i_id)
        input_len.append(i_len)

		#데이터 타입 확인
    for value in input_string[1]:
            try:
                int(value)
                input_type.append('INT')
            except:
                try:
                    float(value)
                    input_type.append('FLOAT')
                except:
                    input_type.append('VARCHAR')
    #쿼리문 저장                
    query = f"CREATE TABLE userTable{tableN} ("
    
    for i in range(len(input_id)):
        col_def = f"{input_id[i]} {input_type[i]}"
        if input_type[i] == 'VARCHAR':
            col_def += f"(255)"  # 문자열이면 길이 설정
        query += col_def
        if i != len(input_id)-1:
            query += ", "
    query += ")"

    conn.commit()
    tableN += 1
    curs.execute(query)
    return 0
    
# DB table 정보 보내기
def insert_data(input_string, conn, curs, tableN):
    table_name = f"userTable{tableN}"
    input_id = []
    input_data = []

    for col in input_string[0]:
        input_id.append(col)
    for row in input_string[1:]:
        input_data.append(row)

    # 쿼리문 저장
    query = "INSERT INTO " + table_name + " ("
    for i in range(len(input_id)):
        query += input_id[i]
        if i != len(input_id) - 1:
            query += ", "
    query += ") VALUES ("
    for i in range(len(input_id)):
        query += "%s"
        if i != len(input_id) - 1:
            query += ", "
    query += ")"

    # 데이터 삽입
    for row in input_data:
        clean_row = [None if val in ['Null', 'null', '', None] else val for val in row]
        clean_row = [None if isinstance(val, str) and val == 'None' else val for val in clean_row]
        curs.execute(query, row)
        
    conn.commit()
    print(f"{len(input_data)}개의 데이터가 {table_name}에 삽입되었습니다.")

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
#회기분석
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


#결측치 처리
def Handling_Missing_Values(data):
    df = pd.DataFrame(data[1:], columns=data[0])
    for column in df.columns:
        if df[column].dtype in [np.float64, np.int64]:
            median_val = np.median(df[column].dropna())
            df[column].fillna(median_val, inplace=True)
        else:
            df[column].fillna("NULL", inplace=True)  # 문자열 컬럼 결측치 처리
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


#DB연결
conn = pymysql.connect(
    host = 'localhost',
    user = 'code',
    password = 'Ab123456',
    db = 'privacy_db',
    charset = 'utf8'
)

#DB와 상호 연결
curs = conn.cursor()

epsilon = 1.0
sensitivity = 1.0
tableN=1 #테이블 번호

if __name__ == '__main__':
    filename = input("읽을 파일의 이름을 입력하세요(확장자명까지):")

    if filename[-4:] == ".csv":     #엑셀파일일 경우 읽도록 함
        input_string = read_csvfile(filename)
        maketbl(input_string, conn, curs)
        insert_data(input_string, conn, curs, tableN - 1)

    query_n = 0
    confidence_intervals_lower = []
    confidence_intervals_upper = []

    while(1):
        user_input = input("쿼리를 요청하시겠습니까? (엔터 = 계속 / q = 종료): ")
        if user_input.lower() == 'q':
            break

        # 쿼리 발생
        query_n += 1
        result = laplace_local_differential_privacy(input_string, epsilon, sensitivity)

        col_name = input("신뢰 구간을 계산할 컬럼명을 입력하세요: ")
        try:
            col_idx = input_string[0].index(col_name)
        except ValueError:
            print(f"[오류] '{col_name}' 컬럼을 찾을 수 없습니다.")
            continue

        # 숫자 값만 추출
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

        view_stats = input("원하는 열의 통계를 보고 싶다면 y를 입력하세요: ").lower()
        if view_stats == 'y':
            col_name = input("통계를 보고 싶은 컬럼명을 입력하세요: ")
            print_column_statistics(result, col_name)
        view_stats = input("원하는 컬럼들의 회기분석을 진행하하고 싶다면 y를 입력하세요: ").lower()
        if view_stats == 'y':
            col_name1 = input("분석을 하고 싶은 첫번째 컬럼명을 입력하세요: ")
            col_name2 = input("분석을 하고 싶은 두번째 컬럼명을 입력하세요: ")
            Regression_Analysis(result, col_name1, col_name2)

        view_corr = input("상관분석을 진행하시겠습니까? (y/n): ").lower()
        if view_corr == 'y':
            col_name1 = input("상관분석을 하고 싶은 첫 번째 컬럼명을 입력하세요: ")
            col_name2 = input("상관분석을 하고 싶은 두 번째 컬럼명을 입력하세요: ")
            Correlation_Analysis(result, col_name1, col_name2)
        #print("결과", result)
       
# 신뢰 구간 시각화
if confidence_intervals_lower and confidence_intervals_upper:
    plt.figure(figsize=(10, 6))
    plt.plot(confidence_intervals_lower, label='신뢰 구간 하한', marker='o', color='blue')
    plt.plot(confidence_intervals_upper, label='신뢰 구간 상한', marker='o', color='red')
    plt.fill_between(range(len(confidence_intervals_lower)), confidence_intervals_lower, confidence_intervals_upper, color='gray', alpha=0.2)
    plt.title("각 쿼리별 신뢰 구간 변화 추이")
    plt.xlabel("쿼리 번호")
    plt.ylabel("값")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
