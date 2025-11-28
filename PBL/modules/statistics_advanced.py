import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from .visualization import plot_regression_result, plot_correlation_scatter

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
        result_text = "[오류] 유효한 데이터가 부족합니다."
        return result_text

    x_np = np.array(x).reshape(-1, 1)
    y_np = np.array(y)

    model = LinearRegression()
    model.fit(x_np, y_np)

    slope = model.coef_[0]
    intercept = model.intercept_
    r_squared = model.score(x_np, y_np)

    result_text = f"""
    [회귀분석 결과]
    slope: {slope:.4f}
    intercept: {intercept:.4f}
    r_squared: {r_squared:.4f}
    """

    # plot_regression_result(x_np, y_np, model, col1, col2)

    return result_text

# 상관 분석 실행 및 시각화
def run_correlation_analysis(data, col1, col2, method):
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
        result_text = "[오류] 유효한 데이터가 부족합니다."
        return result_text

    x_np = np.array(x)
    y_np = np.array(y)
    result = None

    if method == 'pearson':
        result = pearson_correlation(x_np, y_np)
    elif method == 'spearman':
        result = spearman_correlation(x_np, y_np)
    else:
        result_text = "지원하지 않는 상관 분석 방법입니다."
        return result_text
    
    corr = result['correlation']
    p_value = result['p_value']
    
    result_text = f"""
[({method.capitalize()}) 상관 분석 결과]
상관 계수 (Correlation): {corr:.4f}
유의 확률 (P-value): {p_value:.4f}
"""
    return result_text

    # plot_correlation_scatter(x_np, y_np, col1, col2, method.capitalize())

