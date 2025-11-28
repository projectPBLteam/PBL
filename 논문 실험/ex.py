import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

# ================================
# 설정(한 번 실행 시 고정, threshold와 streak_required만 바꿔 실험)
# ================================
CSV_FILE = "CardBase.csv"
TARGET_COL = "Credit_Limit"

# ε 후보들
EPSILONS = [0.5, 0.75, 1.0, 1.25]

# 반복 샘플 수(동일 쿼리 반복; 실험용)
total_queries = 200

# 수렴 판단 파라미터(실험에서 변경)
window_size = 30
threshold = 0.01         # 실험에서 변경
streak_required = 3     # 실험에서 변경

# 실험 반복 횟수
num_runs = 5

# ================================
# 함수 정의
# ================================
def generate_dp_query_values(true_value, sensitivity, epsilon, n_queries, seed=None):
    rng = np.random.default_rng(seed)  # seed=None이면 시스템 난수 사용
    scale = sensitivity / epsilon
    return [true_value + rng.laplace(0, scale) for _ in range(n_queries)]

def relative_ci_width(data, confidence=0.95):
    if len(data) < 2:
        return np.inf
    mean = np.mean(data)
    sem = stats.sem(data)
    margin = sem * stats.t.ppf((1 + confidence) / 2., len(data) - 1)
    width = 2 * margin
    return width / abs(mean) if mean != 0 else np.inf

def find_convergence(values, window_size, threshold, streak_required=5):
    streak = 0
    for i in range(len(values) - window_size):
        window = values[i:i + window_size]
        rel_width = relative_ci_width(window)
        if rel_width < threshold:
            streak += 1
            if streak >= streak_required:
                return i + window_size
        else:
            streak = 0
    return None

# 누적 평균 및 95% CI 계산
def cumulative_mean_and_ci(series):
    means, ci_lowers, ci_uppers = [], [], []
    for i in range(1, len(series) + 1):
        window = series[:i]
        mean = np.mean(window)
        sem = stats.sem(window)
        margin = sem * stats.t.ppf(0.975, df=i - 1) if i > 1 else 0
        means.append(mean)
        ci_lowers.append(mean - margin)
        ci_uppers.append(mean + margin)
    return np.array(means), np.array(ci_lowers), np.array(ci_uppers)

# ================================
# 데이터 로딩
# ================================
df = pd.read_csv(CSV_FILE)
y = df[TARGET_COL].dropna().values
true_mean = np.mean(y)
n = len(y)

# 민감도(현재 방식 유지)
sensitivity = (y.max() - y.min()) / n

print("[INFO] --- Settings ---")
print(f"[INFO] File: {CSV_FILE}, Column: {TARGET_COL}, n={n}")
print(f"[INFO] sensitivity(base): {sensitivity:.6f}")
print(f"[INFO] window_size: {window_size}, threshold: {threshold}, streak_required: {streak_required}")
print(f"[INFO] total_queries: {total_queries}, num_runs: {num_runs}")
print(f"[INFO] epsilons: {EPSILONS}")

# ================================
# ε별 실험 수행
# ================================
# ε별 결과 저장 딕셔너리
results = {}  # key = epsilon, value = dict with fields:
# {
#   'convergence_list': [...],
#   'dp_vals_all': [[...], ...],  # run별 dp 시퀀스
#   'last_run': {'dp_values', 'converged_at', 'means', 'ci_lowers', 'ci_uppers', 'scale'}
# }

for eps in EPSILONS:
    scale = sensitivity / eps

    convergence_list = []
    dp_vals_all = []

    for run in range(num_runs):
        seed = None  # 시스템 랜덤 시드 사용 → 매번 다르게
        dp_vals = generate_dp_query_values(true_mean, sensitivity, eps, total_queries, seed=seed)
        conv = find_convergence(dp_vals, window_size, threshold, streak_required)
        convergence_list.append(conv)
        dp_vals_all.append(dp_vals)

    # 마지막 실험 기준 누적 통계
    dp_values = dp_vals_all[-1]
    converged_at = convergence_list[-1]
    means, ci_lowers, ci_uppers = cumulative_mean_and_ci(dp_values)

    results[eps] = {
        'convergence_list': convergence_list,
        'dp_vals_all': dp_vals_all,
        'last_run': {
            'dp_values': dp_values,
            'converged_at': converged_at,
            'means': means,
            'ci_lowers': ci_lowers,
            'ci_uppers': ci_uppers,
            'scale': scale
        }
    }

   # 요약 출력
    valid_convs = [x for x in convergence_list if x is not None]
    print(f"\n[RESULT ε={eps}] ---")
    print(f"Convergence list (all {num_runs} runs):")
    print(convergence_list)

    if valid_convs:
        print(f"Average convergence point (over {len(valid_convs)} runs): {np.mean(valid_convs):.2f}")
    else:
        print("No convergence detected in any run.")

    print(f"scale: {scale:.6f}")

# ================================
# 시각화 1: 한 그래프에 4개 ε의 누적 평균 + 95% CI + 수렴 지점 마커
# ================================
plt.figure(figsize=(13, 7))

colors = {
    EPSILONS[0]: "#63b3ec",  # blue
    EPSILONS[1]: "#eab222",  # orange
    EPSILONS[2]: "#5bd05d",  # green
    EPSILONS[3]: "#cc60db"   # red
}

x_axis = np.arange(1, total_queries + 1)

for eps in EPSILONS:
    lr = results[eps]['last_run']
    means = lr['means']
    ci_lowers = lr['ci_lowers']
    ci_uppers = lr['ci_uppers']
    converged_at = lr['converged_at']
    col = colors[eps]

    # 얇은 CI 밴드
    plt.fill_between(x_axis, ci_lowers, ci_uppers, color=col, alpha=0.12, label=f"ε={eps} 95% CI")
    # 누적 평균 라인
    plt.plot(x_axis, means, color=col, label=f"ε={eps} mean")

    # 🔴 수렴 지점 마커 찍기
    if converged_at:
        plt.scatter(converged_at, means[converged_at-1], 
                    color=col, edgecolor='black', s=80, zorder=5,
                    label=f"ε={eps} converged@{converged_at}")

# true mean 기준선(연구용)
plt.axhline(y=true_mean, color='black', linestyle='--', label=f'True Mean ({true_mean:.3f})')

plt.xscale('log')
plt.xlabel('Number of Queries (log scale)')
plt.ylabel('Estimate Value')
plt.title('DP Mean Estimate with 95% CI by ε (Convergence Marker)')
plt.legend(ncol=2)
plt.grid(True, which="both", ls="--", lw=0.5)


plt.tight_layout()
plt.show()


# ================================
# 시각화 2 (변형): ε별 개별 그래프를 2x2 서브플롯으로 한 화면에 출력
# ================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=False)
axes = axes.flatten()

titles = {
    EPSILONS[0]: f"ε={EPSILONS[0]}",
    EPSILONS[1]: f"ε={EPSILONS[1]}",
    EPSILONS[2]: f"ε={EPSILONS[2]}",
    EPSILONS[3]: f"ε={EPSILONS[3]}"
}

for idx, eps in enumerate(EPSILONS):
    ax = axes[idx]
    lr = results[eps]['last_run']
    dp_values = lr['dp_values']
    converged_at = lr['converged_at']
    col = colors[eps]

    ax.plot(dp_values, label=f"DP Query Value (ε={eps})", color=col, alpha=0.85, linewidth=1.2)
    if converged_at:
        ax.axvline(x=converged_at, color='red', linestyle='--', linewidth=0.8, 
                   label=f"Converged at {converged_at}")
    ax.axhline(y=true_mean, color='green', linestyle='--', linewidth=0.8, label='True Mean')

    ax.set_title(titles[eps])
    ax.set_xlabel("Query Count")
    ax.set_ylabel("DP Query Value")
    #ax.set_ylim(210000, 280000) 
    ax.set_ylim(225000, 265000)
    ax.grid(True)
    ax.legend(loc="upper right")

# 빈 서브플롯이 없도록 하고 레이아웃 정리
plt.suptitle("DP Query Sequence with Convergence Point (All ε)", fontsize=14)
plt.tight_layout(rect=[0, 0.02, 1, 0.96])
plt.show()

import matplotlib.pyplot as plt
# plt.subplots(1, 1, ...)을 사용하여 하나의 축(ax)만 생성합니다.
fig, ax = plt.subplots(1, 1, figsize=(12, 7))

# True Mean을 모든 데이터 위에 한 번만 표시합니다.
ax.axhline(y=true_mean, color='green', linestyle='--', linewidth=1.5, label='True Mean', zorder=0)

# 모든 엡실론(ε)의 결과를 하나의 축에 순서대로 그립니다.
for idx, eps in enumerate(EPSILONS):
    lr = results[eps]['last_run']
    dp_values = lr['dp_values']
    converged_at = lr['converged_at']
    col = colors[eps]

    # 1. DP Query Value 추이 플로팅
    ax.plot(dp_values, label=f"ε={eps}", color=col, alpha=0.85, linewidth=1.2)
    
    # 2. 수렴 지점(Converged at) 플로팅
    # 수렴 지점을 해당 선의 색상과 점선(:)으로 표시합니다. (범례 복잡도 문제로 별도 라벨은 생략)
    if converged_at:
        ax.axvline(x=converged_at, color=col, linestyle=':', linewidth=0.8)
        # 선택 사항: 수렴 지점에 텍스트 주석 추가 (복잡해질 수 있어 주석 처리)
        # ax.text(converged_at, dp_values[converged_at], f'C', color=col, fontsize=9)

# 그래프 제목 및 축 설정
ax.set_title("DP Query Sequence Comparison by Epsilon (All on One Plot)")
ax.set_xlabel("Query Count")
ax.set_ylabel("DP Query Value")

# ⭐ 이전 요청에 따라 변동성을 강조하기 위해 Y축 범위를 좁게 설정 ⭐
ax.set_ylim(225000, 265000) 

ax.grid(True)
# 범례를 표시하여 각 선이 어떤 엡실론(ε) 값인지 구별합니다.
ax.legend(title='Epsilon (ε)', loc="upper right")

plt.suptitle("Combined DP Query Sequence with Convergence Point (All ε)", fontsize=14)
plt.tight_layout(rect=[0, 0.02, 1, 0.96])
plt.show()

# ================================
# 시각화 3 (누적 평균 기반 95% CI로 Stable/Unstable 표시)
# ================================
fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=True, sharey=False)
axes = axes.flatten()

conf_level = 0.95
z = stats.norm.ppf(1 - (1 - conf_level) / 2)  # ≈ 1.96

for idx, eps in enumerate(EPSILONS):
    ax = axes[idx]
    lr = results[eps]['last_run']
    dp_values = np.array(lr['dp_values'])
    converged_at = lr['converged_at']
    col = colors[eps]

    # 누적 평균과 누적 표준편차 기반 CI 계산
    rolling_means = []
    ci_lower = []
    ci_upper = []
    for t in range(1, len(dp_values) + 1):
        mean_t = np.mean(dp_values[:t])
        std_t = np.std(dp_values[:t], ddof=1) if t > 1 else 0.0
        margin = z * std_t / np.sqrt(t)
        rolling_means.append(mean_t)
        ci_lower.append(mean_t - margin)
        ci_upper.append(mean_t + margin)

    rolling_means = np.array(rolling_means)
    ci_lower = np.array(ci_lower)
    ci_upper = np.array(ci_upper)

    # Stable / Unstable 판별 (누적평균의 CI가 true_mean을 포함?)
    stable_mask = (ci_lower <= true_mean) & (ci_upper >= true_mean)
    stable_ratio = np.mean(stable_mask) * 100
    unstable_ratio = 100 - stable_ratio

    # 공통 x, y = 누적평균
    x_idx = np.arange(len(dp_values))
    y_all = rolling_means

    # 에러바 크기 (비대칭)
    yerr_lower_all = np.abs(y_all - ci_lower)
    yerr_upper_all = np.abs(ci_upper - y_all)

    # Stable
    ax.errorbar(x_idx[stable_mask], y_all[stable_mask],
                yerr=[yerr_lower_all[stable_mask], yerr_upper_all[stable_mask]],
                fmt='o', markersize=3, ecolor=col, elinewidth=0.8, alpha=0.7,
                mfc=col, mec=col, color=col, label='Stable')

    # Unstable
    ax.errorbar(x_idx[~stable_mask], y_all[~stable_mask],
                yerr=[yerr_lower_all[~stable_mask], yerr_upper_all[~stable_mask]],
                fmt='o', markersize=3, ecolor='red', elinewidth=0.8, alpha=0.7,
                mfc='none', mec='red', color='red', label='Unstable')

    # 참값, 수렴 지점
    ax.axhline(y=true_mean, color='green', linestyle='--', linewidth=0.8, label='True Mean')
    if converged_at is not None:
        ax.axvline(x=converged_at, color='black', linestyle='--', linewidth=0.8,
                   label=f"Converged at {converged_at}")

        ### ✅ 항상 출력되도록 보장
        before_mask = np.arange(len(dp_values)) < converged_at
        after_mask = ~before_mask

        unstable_before = np.sum(~stable_mask & before_mask)
        unstable_after = np.sum(~stable_mask & after_mask)

        total_before = np.sum(before_mask)
        total_after = np.sum(after_mask)

        unstable_ratio_before = (unstable_before / total_before * 100) if total_before > 0 else 0.0
        unstable_ratio_after = (unstable_after / total_after * 100) if total_after > 0 else 0.0

        print(f"[ε={eps}]")
        print(f"  수렴 전 Unstable 비율: {unstable_ratio_before:.2f}% "
              f"({unstable_before}/{total_before})")
        print(f"  수렴 후 Unstable 비율: {unstable_ratio_after:.2f}% "
              f"({unstable_after}/{total_after})")
        print(f"  수렴 이후 Unstable 개수: {unstable_after}\n")

    ax.set_title(f"ε={eps} | Stable={stable_ratio:.1f}%, Unstable={unstable_ratio:.1f}%")
    ax.set_xlabel("Query Count")
    ax.set_ylabel("Rolling Mean of DP Values")
    ax.grid(True)
    ax.legend(loc="upper right")

plt.suptitle("DP Query Stability by 95% CI (Rolling Mean, All ε)", fontsize=14)
plt.tight_layout(rect=[0, 0.02, 1, 0.96])
plt.show()
