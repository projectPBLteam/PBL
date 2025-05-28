import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from visualization import plot_regression_result, plot_correlation_scatter

# 피어슨 상관 계수
def pearson_correlation(x, y):
    corr, p = stats.pearsonr(x, y)
    return {'correlation': corr, 'p_value': p}

# 스피어만 상관 계수
def spearman_correlation(x, y):
    corr, p = stats.spearmanr(x, y)
    return {'correlation': corr, 'p_value': p}

# 회귀 분석 실행 및 시각화
def run_regression_analysis(data, col1, col2):
    header = data[0]
    idx1 = header.index(col1)
    idx2 = header.index(col2)

    x, y = [], []
    for row in data[1:]:
        try:
            x.append(float(row[idx1]))
            y.append(float(row[idx2]))
        except:
            continue

    if len(x) < 2:
        print("[오류] 유효한 데이터가 부족합니다.")
        return

    x_np = np.array(x).reshape(-1, 1)
    y_np = np.array(y)

    model = LinearRegression()
    model.fit(x_np, y_np)

    slope = model.coef_[0]
    intercept = model.intercept_
    r_squared = model.score(x_np, y_np)

    print("\n[회귀분석 결과]")
    print(f"slope: {slope:.4f}")
    print(f"intercept: {intercept:.4f}")
    print(f"r_squared: {r_squared:.4f}")

    plot_regression_result(x_np, y_np, model, col1, col2)

# 상관 분석 실행 및 시각화
def run_correlation_analysis(data, col1, col2, method='pearson'):
    header = data[0]
    idx1 = header.index(col1)
    idx2 = header.index(col2)

    x, y = [], []
    for row in data[1:]:
        try:
            x.append(float(row[idx1]))
            y.append(float(row[idx2]))
        except:
            continue

    x_np = np.array(x)
    y_np = np.array(y)

    if method == 'pearson':
        result = pearson_correlation(x_np, y_np)
    elif method == 'spearman':
        result = spearman_correlation(x_np, y_np)
    else:
        print("지원하지 않는 상관 분석 방법입니다.")
        return

    print(f"\n[{method.capitalize()} 상관 분석 결과]")
    for k, v in result.items():
        print(f"{k}: {v:.4f}")

    plot_correlation_scatter(x_np, y_np, col1, col2, method.capitalize())

