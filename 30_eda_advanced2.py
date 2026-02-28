"""
30_eda_advanced2.py
추가 심화 EDA 3종

① VIF(분산팽창지수) — 다중공선성 수치화
② 블루오션 후보 상권 스크리닝 — 수요↑ 공급↓ 조건 필터
③ 자치구별 매출 분포 히트맵 (바 차트)

산출물:
  eda_vif_table.csv
  eda_blueocean_candidates.csv
  eda_vif.png
  eda_blueocean.png
  eda_gu_sales.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor

os.chdir('/teamspace/studios/this_studio/aicha')

# ── 한글 폰트 설정 ──
font_path = '/system/conda/miniconda3/envs/cloudspace/lib/python3.12/site-packages/koreanize_matplotlib/fonts/NanumGothic.ttf'
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# ── 데이터 로드 ──
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
to_map = pd.read_csv('to_map.csv', encoding='utf-8-sig')

# 명동 관광특구 제외 (이상치 메모)
MYEONGDONG = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
df = df[~df['상권_코드'].isin(MYEONGDONG)].copy()
df['log_매출'] = np.log1p(df['당월_매출_금액'])

# 최신 분기 단일 스냅샷 (VIF, 블루오션 분석용)
df25 = df[df['기준_년분기_코드'] == 20253].copy()

print(f"분석 데이터: {len(df25)}개 상권 (20253 기준, 명동 제외)\n")

# ══════════════════════════════════════════
# ① VIF 분석
# ══════════════════════════════════════════
print("=" * 60)
print("① VIF 분석")
print("=" * 60)

# 상관관계 상위 변수 + 주요 지표 선택 (R² 기준 상위 + 트렌드 포함)
VIF_VARS = [
    '카페음료_점포수',
    '공급갭_지수',
    '집객시설_수',
    '총_직장_인구_수',
    '여성_직장_인구_수',
    '여성연령대_50_직장_인구_수',
    '총_유동인구_수',
    '여성_유동인구_수',
    '총_상주인구_수',
    '찻집_수',
    '스타벅스_리저브_수',
    '지하철_노선_수',
    '유동밀도_지수',
    '상주밀도_지수',
    '여가소비_지수',
    '카페_검색지수',
]

# 결측 없는 행만 사용
vif_df = df25[VIF_VARS].dropna()
print(f"VIF 계산 대상: {len(VIF_VARS)}개 변수, n={len(vif_df)}\n")

vif_results = []
for i, col in enumerate(VIF_VARS):
    vif_val = variance_inflation_factor(vif_df.values, i)
    vif_results.append({'변수명': col, 'VIF': round(vif_val, 2)})

vif_table = pd.DataFrame(vif_results).sort_values('VIF', ascending=False)
vif_table['위험등급'] = vif_table['VIF'].apply(
    lambda v: '🔴 제거 권고 (>10)' if v > 10 else ('🟡 주의 (5~10)' if v > 5 else '🟢 양호 (<5)')
)
vif_table.to_csv('eda_vif_table.csv', index=False, encoding='utf-8-sig')
print(vif_table.to_string(index=False))

# VIF 시각화
fig, ax = plt.subplots(figsize=(10, 7))
colors = ['#e74c3c' if v > 10 else ('#f39c12' if v > 5 else '#2ecc71')
          for v in vif_table['VIF']]
bars = ax.barh(vif_table['변수명'], vif_table['VIF'], color=colors)
ax.axvline(5, color='orange', linestyle='--', alpha=0.7, label='주의 (VIF=5)')
ax.axvline(10, color='red', linestyle='--', alpha=0.7, label='제거 권고 (VIF=10)')
for bar, v in zip(bars, vif_table['VIF']):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{v:.1f}', va='center', fontsize=9)
ax.set_xlabel('VIF (분산팽창지수)')
ax.set_title('다중공선성 VIF 분석\n(빨강=제거권고>10, 주황=주의5~10, 초록=양호<5)', fontsize=13)
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('eda_vif.png', dpi=150)
plt.close()
print("\n→ eda_vif.png 저장 완료")

# ══════════════════════════════════════════
# ② 블루오션 후보 상권 스크리닝
# ══════════════════════════════════════════
print("\n" + "=" * 60)
print("② 블루오션 후보 상권 스크리닝")
print("=" * 60)

# 필요 컬럼 확인 후 결측 제거
SCREEN_COLS = ['상권_코드', '상권_코드_명', '상권_구분_코드_명_x',
               '당월_매출_금액', 'log_매출',
               '공급갭_지수', '찻집_수', '카페음료_점포수',
               '총_직장_인구_수', '여성_직장_인구_수',
               '총_유동인구_수', '여성_유동인구_수',
               '집객시설_수', '지하철_노선_수']
bo = df25[SCREEN_COLS].dropna(subset=['공급갭_지수','총_직장_인구_수','당월_매출_금액']).copy()

# 각 지표 백분위 순위 계산
bo['pct_공급갭']    = bo['공급갭_지수'].rank(pct=True)          # 높을수록 공급 부족(블루오션)
bo['pct_직장인구']  = bo['총_직장_인구_수'].rank(pct=True)      # 높을수록 수요↑
bo['pct_유동인구']  = bo['총_유동인구_수'].rank(pct=True)       # 높을수록 수요↑
bo['pct_매출']      = bo['당월_매출_금액'].rank(pct=True)       # 너무 높으면 이미 레드오션일 수 있음
bo['pct_찻집수_inv']= (1 - bo['찻집_수'].rank(pct=True))       # 찻집 적을수록(역수) 블루오션

# 블루오션 점수 = 수요(직장+유동) × 공급갭 × 찻집 적음
# 매출은 중간 정도 (상위 20% 초과는 이미 레드오션, 하위 20%는 수요 자체가 없음)
bo['블루오션_점수'] = (
    bo['pct_공급갭'] * 0.30 +
    bo['pct_직장인구'] * 0.25 +
    bo['pct_유동인구'] * 0.15 +
    bo['pct_찻집수_inv'] * 0.20 +
    bo['집객시설_수'].rank(pct=True) * 0.10
)

# 매출 필터: 하위 20% 제외 (수요 자체 없는 곳) + 상위 10% 제외 (이미 포화)
매출_하한 = bo['당월_매출_금액'].quantile(0.20)
매출_상한 = bo['당월_매출_금액'].quantile(0.90)
bo_filtered = bo[(bo['당월_매출_금액'] >= 매출_하한) &
                 (bo['당월_매출_금액'] <= 매출_상한)].copy()

top50 = bo_filtered.nlargest(50, '블루오션_점수').reset_index(drop=True)
top50.index += 1

# 출력용 정리
출력컬럼 = ['상권_코드_명', '상권_구분_코드_명_x', '블루오션_점수',
           '공급갭_지수', '찻집_수', '총_직장_인구_수', '총_유동인구_수',
           '당월_매출_금액', 'pct_매출']
top50['당월_매출_억원'] = (top50['당월_매출_금액'] / 1e8).round(2)
top50['블루오션_점수'] = top50['블루오션_점수'].round(4)
top50['pct_매출'] = (top50['pct_매출'] * 100).round(1)

print(f"\n필터 기준: 매출 하위20%({매출_하한/1e8:.1f}억) 초과 & 상위10%({매출_상한/1e8:.1f}억) 이하")
print(f"후보군: {len(bo_filtered)}개 → 상위 50개 선정\n")
print(top50[['상권_코드_명', '상권_구분_코드_명_x', '블루오션_점수',
            '공급갭_지수', '찻집_수', '총_직장_인구_수', '당월_매출_억원', 'pct_매출']].to_string())

# 저장
top50.to_csv('eda_blueocean_candidates.csv', index=True, index_label='순위', encoding='utf-8-sig')
print("\n→ eda_blueocean_candidates.csv 저장 완료")

# 블루오션 시각화 — 산점도: 공급갭 vs 직장인구, 색=블루오션점수
fig, ax = plt.subplots(figsize=(12, 8))
sc = ax.scatter(
    bo_filtered['공급갭_지수'],
    bo_filtered['총_직장_인구_수'] / 1000,
    c=bo_filtered['블루오션_점수'],
    cmap='RdYlGn', alpha=0.6, s=40
)
# 상위 20개 레이블
for _, row in top50.head(20).iterrows():
    ax.annotate(
        row['상권_코드_명'],
        (row['공급갭_지수'], row['총_직장_인구_수'] / 1000),
        fontsize=7, alpha=0.85,
        xytext=(4, 2), textcoords='offset points'
    )
plt.colorbar(sc, ax=ax, label='블루오션 점수')
ax.set_xlabel('공급갭_지수 (카페음료_점포수 / 찻집_수+1)')
ax.set_ylabel('총 직장인구 (천명)')
ax.set_title('블루오션 후보 상권 스크리닝\n(공급갭↑ × 직장인구↑ = 초록이 블루오션)', fontsize=13)
plt.tight_layout()
plt.savefig('eda_blueocean.png', dpi=150)
plt.close()
print("→ eda_blueocean.png 저장 완료")

# ══════════════════════════════════════════
# ③ 자치구별 매출 분포
# ══════════════════════════════════════════
print("\n" + "=" * 60)
print("③ 자치구별 매출 분포")
print("=" * 60)

# 자치구 정보 조인
gu_map = to_map[['상권_코드', '자치구_코드_명']].drop_duplicates('상권_코드')
df25_gu = df25.merge(gu_map, on='상권_코드', how='left')

# 자치구별 집계
gu_stats = df25_gu.groupby('자치구_코드_명').agg(
    상권수=('상권_코드', 'count'),
    평균매출_억원=('당월_매출_금액', lambda x: x.mean() / 1e8),
    중앙매출_억원=('당월_매출_금액', lambda x: x.median() / 1e8),
    총매출_억원=('당월_매출_금액', lambda x: x.sum() / 1e8),
).reset_index().sort_values('평균매출_억원', ascending=False)

print(gu_stats.to_string(index=False))

# 자치구별 시각화 — 평균매출 바 차트 + 중앙값 점
fig, axes = plt.subplots(2, 1, figsize=(14, 12))

# (a) 평균 매출
ax1 = axes[0]
bars = ax1.bar(gu_stats['자치구_코드_명'], gu_stats['평균매출_억원'],
               color='steelblue', alpha=0.8, label='평균 매출')
ax1.scatter(gu_stats['자치구_코드_명'], gu_stats['중앙매출_억원'],
            color='tomato', zorder=5, s=50, label='중앙값 매출')
ax1.set_ylabel('매출 (억원)')
ax1.set_title('자치구별 상권 평균 매출 (20253, 명동 제외)', fontsize=13)
ax1.tick_params(axis='x', rotation=45)
ax1.legend()

# (b) 상권 수
ax2 = axes[1]
ax2.bar(gu_stats.sort_values('상권수', ascending=False)['자치구_코드_명'],
        gu_stats.sort_values('상권수', ascending=False)['상권수'],
        color='mediumpurple', alpha=0.8)
ax2.set_ylabel('상권 수')
ax2.set_title('자치구별 상권 수', fontsize=13)
ax2.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('eda_gu_sales.png', dpi=150)
plt.close()
print("\n→ eda_gu_sales.png 저장 완료")

print("\n" + "=" * 60)
print("전체 완료!")
print("  eda_vif_table.csv")
print("  eda_blueocean_candidates.csv")
print("  eda_vif.png")
print("  eda_blueocean.png")
print("  eda_gu_sales.png")
