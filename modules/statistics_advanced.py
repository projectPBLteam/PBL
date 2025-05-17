import numpy as np
from scipy import stats
from visualization import plot_regression_result, plot_correlation_scatter

# 단순 선형 회귀 분석
def simple_linear_regression(x, y):
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'std_error': std_err
    }

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

    x_np = np.array(x)
    y_np = np.array(y)
    result = simple_linear_regression(x_np, y_np)

    print("\n[회귀분석 결과]")
    for k, v in result.items():
        print(f"{k}: {v:.4f}")

    plot_regression(x_np, y_np, result['slope'], result['intercept'], col1, col2)

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
