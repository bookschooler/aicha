#!/usr/bin/env python3
"""
25_eda.py

EDA (탐색적 데이터 분석)
Step 1. Y변수 (당월_매출_금액) 분포 확인
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib  # NanumGothic 자동 적용

os.chdir('/teamspace/studios/this_studio/aicha')

df = pd.read_csv('y_demand_supply_trend_merge.csv',
                 usecols=['기준_년분기_코드', '상권_코드', '당월_매출_금액'])

y     = df['당월_매출_금액']
log_y = np.log1p(y)

# ── 통계값 미리 계산 ─────────────────────────────────────────────
Q1, Q3   = y.quantile(0.25), y.quantile(0.75)
IQR      = Q3 - Q1
y_med    = y.median()
y_mean   = y.mean()
y_skew   = y.skew()
y_kurt   = y.kurtosis()
ly_skew  = log_y.skew()
ly_kurt  = log_y.kurtosis()
ly_med   = log_y.median()
ly_mean  = log_y.mean()
n_outlier = (y > Q3 + 3 * IQR).sum()

# ── 기초 통계 출력 ───────────────────────────────────────────────
print("=== Y변수 (당월_매출_금액) 기초 통계 ===")
print(f"행 수       : {len(y):,}")
print(f"결측치      : {y.isna().sum()}")
print(f"최솟값      : {y.min():>20,.0f} 원")
print(f"1%ile       : {y.quantile(0.01):>20,.0f} 원")
print(f"5%ile       : {y.quantile(0.05):>20,.0f} 원")
print(f"25%ile (Q1) : {Q1:>20,.0f} 원")
print(f"중앙값      : {y_med:>20,.0f} 원")
print(f"평균        : {y_mean:>20,.0f} 원")
print(f"75%ile (Q3) : {Q3:>20,.0f} 원")
print(f"95%ile      : {y.quantile(0.95):>20,.0f} 원")
print(f"99%ile      : {y.quantile(0.99):>20,.0f} 원")
print(f"최댓값      : {y.max():>20,.0f} 원")
print(f"표준편차    : {y.std():>20,.0f} 원")
print(f"왜도(skew)  : {y_skew:.4f}")
print(f"첨도(kurt)  : {y_kurt:.4f}")

print(f"\n=== 로그변환 후 ===")
print(f"왜도(skew)  : {ly_skew:.4f}")
print(f"첨도(kurt)  : {ly_kurt:.4f}")

print(f"\n=== 특이값 ===")
print(f"0원 이하    : {(y <= 0).sum()}개")
print(f"IQR 기반 이상치 (Q3+3*IQR 초과): {n_outlier:,}개 ({n_outlier/len(y)*100:.1f}%)")
print(f"  이상치 기준값: {Q3 + 3*IQR:,.0f} 원")

# ── 시각화 ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Y변수 분포: 당월 매출 금액', fontsize=14, fontweight='bold')

# 1. 원본 히스토그램
ax1 = axes[0]
ax1.hist(y / 1e6, bins=80, color='steelblue', edgecolor='white', linewidth=0.3)
ax1.set_title(f'원본 (단위: 백만 원)\n왜도={y_skew:.2f}  첨도={y_kurt:.1f}', fontsize=11)
ax1.set_xlabel('매출 (백만 원)')
ax1.set_ylabel('점포 수')
ax1.axvline(y_med  / 1e6, color='red',    linestyle='--', label=f'중앙값 {y_med/1e6:.0f}')
ax1.axvline(y_mean / 1e6, color='orange', linestyle='--', label=f'평균 {y_mean/1e6:.0f}')
ax1.legend(fontsize=9)

# 2. 로그변환 히스토그램
ax2 = axes[1]
ax2.hist(log_y, bins=60, color='seagreen', edgecolor='white', linewidth=0.3)
ax2.set_title(f'로그 변환 (log1p)\n왜도={ly_skew:.2f}  첨도={ly_kurt:.2f}', fontsize=11)
ax2.set_xlabel('log(매출 + 1)')
ax2.set_ylabel('점포 수')
ax2.axvline(ly_med,  color='red',    linestyle='--', label=f'중앙값 {ly_med:.2f}')
ax2.axvline(ly_mean, color='orange', linestyle='--', label=f'평균 {ly_mean:.2f}')
ax2.legend(fontsize=9)

# 3. 분기별 박스플롯
df['log_y'] = log_y
quarters    = sorted(df['기준_년분기_코드'].unique())
data_by_q   = [df[df['기준_년분기_코드'] == q]['log_y'].values for q in quarters]

ax3 = axes[2]
bp = ax3.boxplot(data_by_q, tick_labels=[str(q) for q in quarters], patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightcoral')
    patch.set_alpha(0.7)
ax3.set_title('분기별 log(매출) 분포', fontsize=11)
ax3.set_xlabel('분기')
ax3.set_ylabel('log(매출 + 1)')
ax3.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('eda_y_distribution.png', dpi=150, bbox_inches='tight')
print("\n시각화 저장 완료: eda_y_distribution.png")
plt.show()
