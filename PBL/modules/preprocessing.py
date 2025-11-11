# import pandas as pd
# import numpy as np

# #결측치 처리
# def handle_missing_values(data):
#     df = pd.DataFrame(data[1:], columns=data[0])
#     for column in df.columns:
#         if df[column].dtype in [np.float64, np.int64]:
#             median_val = np.median(df[column].dropna())
#             df[column].fillna(median_val, inplace=True)
#         else:
#             df[column].fillna("NULL", inplace=True)  # 문자열 컬럼 결측치 처리
#     return [data[0]] + df.values.tolist()

# #이상치 처리
# def handle_outliers(data):
#     df = pd.DataFrame(data[1:], columns=data[0])
    
#     for col in df.columns:
#         try:
#             df[col] = pd.to_numeric(df[col], errors='coerce')
#             if df[col].dtype in [np.float64, np.int64]:
#                 Q1 = df[col].quantile(0.25)
#                 Q3 = df[col].quantile(0.75)
#                 IQR = Q3 - Q1
#                 lower_bound = Q1 - 1.5 * IQR
#                 upper_bound = Q3 + 1.5 * IQR
#                 median_val = df[col].median()
#                 outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
#                 df.loc[outliers, col] = median_val
#         except:
#             continue
    
#     return [data[0]] + df.values.tolist()

import pandas as pd
import numpy as np

# 결측치 처리
def handle_missing_values(data):
    df = pd.DataFrame(data[1:], columns=data[0])
    for column in df.columns:
        # 숫자 컬럼만 처리
        df[column] = pd.to_numeric(df[column], errors='coerce')  # 변환 불가값 → NaN
        median_val = df[column].median()
        df[column].fillna(median_val, inplace=True)
    return [data[0]] + df.values.tolist()  # 숫자는 float 유지

# 이상치 처리
def handle_outliers(data):
    df = pd.DataFrame(data[1:], columns=data[0])
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        median_val = df[col].median()
        outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        df.loc[outliers, col] = median_val
        df[col].fillna(median_val, inplace=True)  # NaN 보정
    return [data[0]] + df.values.tolist()  # float 유지
