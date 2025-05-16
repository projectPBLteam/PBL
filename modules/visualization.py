import matplotlib.pyplot as plt

# 회귀 분석
def plot_regression_result(X, y, model, x_label, y_label):
    plt.scatter(X, y, color='blue', label='데이터 점')
    plt.plot(X, model.predict(X), color='red', label='회귀선')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f"{x_label} vs {y_label} 회귀분석")
    plt.legend()
    plt.grid(True)
    plt.show()

# 상관 분석 
def plot_correlation_scatter(x, y, x_label, y_label, method='Pearson'):
    plt.scatter(x, y)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f"{x_label} vs {y_label} ({method} 상관분석)")
    plt.grid(True)
    plt.show()

# 신뢰구간 시각화 
def plot_confidence_intervals(lower_bounds, upper_bounds):
    plt.figure(figsize=(10, 6))
    plt.plot(lower_bounds, label='신뢰 구간 하한', marker='o', color='blue')
    plt.plot(upper_bounds, label='신뢰 구간 상한', marker='o', color='red')
    plt.fill_between(range(len(lower_bounds)), lower_bounds, upper_bounds, color='gray', alpha=0.2)
    plt.title("각 쿼리별 신뢰 구간 변화 추이")
    plt.xlabel("쿼리 번호")
    plt.ylabel("값")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


