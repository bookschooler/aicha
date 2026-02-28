"""
28_eda_advanced.py
심화 EDA 3종:
  ① 다중공선성 히트맵 (R² 상위 30개 변수)
  ② 분기별 매출 추이 + 검색트렌드 연동
  ③ 상권 유형별 주요 변수 비교
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import koreanize_matplotlib
import seaborn as sns

os.chdir('/teamspace/studios/this_studio/aicha')

df_all = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
df     = df_all[df_all['기준_년분기_코드'] == 20253].copy()

# 매출 파생변수 제외 (27번과 동일 기준)
exclude = [
    '기준_년_코드', '기준_분기_코드', '기준_년분기_코드',
    '상권_코드', '상권_구분_코드', '상권_구분_코드_명_x', '상권_코드_명',
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ① 다중공선성 히트맵 — R² 상위 30개 변수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("① 다중공선성 히트맵 생성 중...")

corr_rank = pd.read_csv('eda_correlation_table_nooutlier.csv', encoding='utf-8-sig')
top30_cols = corr_rank.head(30)['변수명'].tolist()
top30_cols = [c for c in top30_cols if c in df.columns]

corr_matrix = df[top30_cols].corr()

fig, ax = plt.subplots(figsize=(18, 15))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # 상삼각 마스크
sns.heatmap(
    corr_matrix, mask=mask, annot=True, fmt='.2f',
    cmap='RdYlGn', center=0, vmin=-1, vmax=1,
    linewidths=0.5, annot_kws={'size': 7},
    ax=ax
)
ax.set_title('X변수 간 다중공선성 히트맵 (R² 상위 30개, 20253 기준)\n|r| > 0.7 이면 다중공선성 주의', fontsize=13)
ax.tick_params(axis='x', labelsize=8, rotation=45)
ax.tick_params(axis='y', labelsize=8, rotation=0)
plt.tight_layout()
plt.savefig('eda_multicollinearity_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ eda_multicollinearity_heatmap.png 저장")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ② 분기별 매출 추이 + 카페 검색지수 연동
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("② 분기별 매출 추이 생성 중...")

quarters = sorted(df_all['기준_년분기_코드'].unique())
quarter_labels = [str(q) for q in quarters]

# 전체 평균 매출 추이
매출_추이 = df_all.groupby('기준_년분기_코드')['당월_매출_금액'].mean() / 1e6

# 상권 유형별 평균 매출 추이
유형별_추이 = df_all.groupby(['기준_년분기_코드', '상권_구분_코드_명_x'])['당월_매출_금액'].mean() / 1e6
유형별_추이 = 유형별_추이.unstack('상권_구분_코드_명_x')

# 카페 검색지수 전체 평균
검색_추이 = df_all.groupby('기준_년분기_코드')['카페_검색지수'].mean()

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# 상단: 상권 유형별 매출 추이
ax1 = axes[0]
for col in 유형별_추이.columns:
    ax1.plot(quarter_labels, 유형별_추이[col].values, marker='o', label=col, linewidth=2)
ax1.set_title('상권 유형별 분기별 평균 매출 추이 (백만원)', fontsize=12)
ax1.set_ylabel('평균 매출 (백만원)')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=30)

# 하단: 전체 매출 vs 카페 검색지수
ax2 = axes[1]
color1, color2 = 'steelblue', 'darkorange'
ax2.plot(quarter_labels, 매출_추이.values, marker='o', color=color1, label='평균 매출(백만원)', linewidth=2)
ax2.set_ylabel('평균 매출 (백만원)', color=color1)
ax2.tick_params(axis='y', labelcolor=color1)

ax2_twin = ax2.twinx()
ax2_twin.plot(quarter_labels, 검색_추이.values, marker='s', color=color2,
              label='카페 검색지수', linewidth=2, linestyle='--')
ax2_twin.set_ylabel('카페 검색지수', color=color2)
ax2_twin.tick_params(axis='y', labelcolor=color2)

ax2.set_title('전체 평균 매출 vs 카페 검색지수 분기별 추이', fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.tick_params(axis='x', rotation=30)

lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)

plt.tight_layout()
plt.savefig('eda_quarterly_trend.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ eda_quarterly_trend.png 저장")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ③ 상권 유형별 주요 변수 비교 (박스플롯)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("③ 상권 유형별 비교 생성 중...")

compare_vars = [
    ('당월_매출_금액', '당월 매출 (백만원)', 1e6),
    ('총_직장_인구_수', '직장 인구 수', 1),
    ('총_유동인구_수', '유동 인구 수', 1),
    ('공급갭_지수', '공급갭 지수', 1),
    ('카페_검색지수', '카페 검색지수', 1),
    ('지하철_역_수', '지하철 역 수', 1),
]

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
axes = axes.flatten()
유형순서 = sorted(df['상권_구분_코드_명_x'].dropna().unique())

for i, (col, label, scale) in enumerate(compare_vars):
    ax = axes[i]
    data = [df[df['상권_구분_코드_명_x'] == t][col].dropna() / scale for t in 유형순서]
    bp = ax.boxplot(data, labels=유형순서, patch_artist=True, showfliers=False)

    colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52']
    for patch, color in zip(bp['boxes'], colors[:len(유형순서)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_title(label, fontsize=11)
    ax.set_ylabel(label, fontsize=9)
    ax.tick_params(axis='x', labelsize=8, rotation=15)
    ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('상권 유형별 주요 변수 분포 비교 (20253 기준, 이상치 제외)', fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig('eda_by_district_type.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ eda_by_district_type.png 저장")

print("\n✅ 전체 완료!")
print("  - eda_multicollinearity_heatmap.png")
print("  - eda_quarterly_trend.png")
print("  - eda_by_district_type.png")
