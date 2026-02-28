"""
27b_eda_correlation_nooutlier.py
전체 X변수 vs 당월_매출_금액 상관관계 EDA (이상치 제거 버전)
이상치 기준: 매출 상위 5% 제외 (95퍼센타일 초과)
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
from scipy import stats

os.chdir('/teamspace/studios/this_studio/aicha')

# ── 데이터 로드 (최신 분기) ────────────────────────────────────────────────
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
df = df[df['기준_년분기_코드'] == 20253].copy()

# ── 이상치 제거: 매출 상위 5% 제외 ──────────────────────────────────────────
p95 = df['당월_매출_금액'].quantile(0.95)
df = df[df['당월_매출_금액'] <= p95].copy()
print(f"분석 데이터: {df.shape[0]}개 상권 (상위 5% 제외, 기준: {p95/1e6:.1f}백만원)")

y = df['당월_매출_금액']

# ── 제외할 컬럼 ────────────────────────────────────────────────────────────
exclude = [
    '기준_년_코드', '기준_분기_코드', '기준_년분기_코드',
    '상권_코드', '상권_구분_코드', '상권_구분_코드_명', '상권_코드_명',
    '당월_매출_금액',
]
x_cols = [
    c for c in df.columns
    if c not in exclude
    and df[c].dtype in ['float64', 'int64']
    and '매출' not in c
    and '평균' not in c
    and 'QUARTER' not in c
]
print(f"분석 변수: {len(x_cols)}개\n")

# ── 각 변수별 통계 계산 ────────────────────────────────────────────────────
results = []
for col in x_cols:
    x = df[col]
    mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    n = mask.sum()
    if n < 10:
        continue

    x_valid = x[mask]
    y_valid = y[mask]

    q1, q2, q3 = x_valid.quantile([0.25, 0.5, 0.75])
    r, p = stats.pearsonr(x_valid, y_valid)
    r2 = r ** 2

    results.append({
        '변수명': col,
        'N': n,
        '평균': round(x_valid.mean(), 2),
        '중앙값': round(q2, 2),
        'Q1': round(q1, 2),
        'Q3': round(q3, 2),
        '상관계수(r)': round(r, 4),
        'R²': round(r2, 4),
        'p-value': round(p, 6),
        '유의': '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
    })

result_df = pd.DataFrame(results).sort_values('R²', ascending=False)

# ── 출력 ─────────────────────────────────────────────────────────────────
print("=" * 80)
print("▶ 전체 변수 R² 순위 (상위 30개) — 이상치 제거 버전")
print("=" * 80)
print(result_df[['변수명', 'R²', '상관계수(r)', 'p-value', '유의', 'N']].head(30).to_string(index=False))

print("\n" + "=" * 80)
print("▶ R² 하위 10개 (관련 없는 변수)")
print("=" * 80)
print(result_df[['변수명', 'R²', '상관계수(r)', 'p-value', '유의']].tail(10).to_string(index=False))

result_df.to_csv('eda_correlation_table_nooutlier.csv', index=False, encoding='utf-8-sig')
print(f"\n✅ 전체 순위표 저장: eda_correlation_table_nooutlier.csv")

# ── 상위 20개 산점도 ─────────────────────────────────────────────────────
top20 = result_df.head(20)
fig, axes = plt.subplots(4, 5, figsize=(24, 18))
axes = axes.flatten()

for i, (_, row) in enumerate(top20.iterrows()):
    col = row['변수명']
    x = df[col]
    mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    x_v, y_v = x[mask], y[mask]

    ax = axes[i]
    ax.scatter(x_v, y_v, alpha=0.3, s=15, color='darkorange')

    slope, intercept, *_ = stats.linregress(x_v, y_v)
    x_line = np.linspace(x_v.min(), x_v.max(), 100)
    ax.plot(x_line, slope * x_line + intercept, color='red', linewidth=1.5)

    ax.set_title(f"{col}\nR²={row['R²']:.3f}  r={row['상관계수(r)']:.3f}  {row['유의']}", fontsize=8)
    ax.set_xlabel(col, fontsize=7)
    ax.set_ylabel('당월_매출_금액', fontsize=7)
    ax.tick_params(labelsize=6)

plt.suptitle('X변수 vs 당월_매출_금액 산점도 - R² 상위 20개 (이상치 제거, 20253 기준)', fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig('eda_scatter_top20_nooutlier.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 산점도 저장: eda_scatter_top20_nooutlier.png")
