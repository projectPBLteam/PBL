import matplotlib.pyplot as plt
import io
import base64
import platform

if platform.system() == 'Windows': # Windows
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin': # Mac OS
    plt.rcParams['font.family'] = 'AppleGothic'
else: # Linux
    plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False

# 회귀 분석 시각화 (sklearn model 기반)
def plot_regression_result(X, y, model, x_label, y_label):
    plt.scatter(X, y, color='blue', label='데이터 점')
    plt.plot(X, model.predict(X), color='red', label='회귀선')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f"{x_label} vs {y_label} 회귀분석")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)

    plt.close()

    image_png = buffer.getvalue()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    return graphic

# 상관 분석 시각화
def plot_correlation_scatter(x, y, x_label, y_label, method='Pearson'):
    plt.scatter(x, y)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f"{x_label} vs {y_label} ({method} 상관분석)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# 신뢰 구간 시각화
def plot_confidence_intervals(x_vals, y_vals, lower_bounds, upper_bounds):
    plt.figure(figsize=(10, 6))
    plt.plot(x_vals, y_vals, label='샘플 평균', marker='o', color='green')
    plt.plot(x_vals, lower_bounds, label='신뢰 구간 하한', marker='o', color='blue')
    plt.plot(x_vals, upper_bounds, label='신뢰 구간 상한', marker='o', color='red')
    plt.fill_between(x_vals, lower_bounds, upper_bounds, color='gray', alpha=0.2)
    plt.title("각 쿼리별 신뢰 구간 변화 추이")
    plt.xlabel("쿼리 번호")
    plt.ylabel("값")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


