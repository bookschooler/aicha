"""
29_eda_search_by_district.py
카페_검색지수 vs 매출 — 상위 100개 상권별 상관관계 분석
- 매출 상위 100개 상권 (상권별 평균 매출 기준)
- 각 상권별 n=9분기 데이터로 Pearson r, p-value 계산
- 결과: eda_search_corr_by_district.csv
"""

import os
import pandas as pd
import numpy as np
from scipy import stats

os.chdir('/teamspace/studios/this_studio/aicha')

df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')

# 명동 관광특구 제외 (EDA 메모: 이상치, 회귀 단계에서 공식 처리 예정)
MYEONGDONG_CODE = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
df_clean = df[~df['상권_코드'].isin(MYEONGDONG_CODE)].copy()

# 로그 매출
df_clean['log_매출'] = np.log1p(df_clean['당월_매출_금액'])

# 상권별 평균 매출로 상위 100개 선정
top100_codes = (
    df_clean.groupby('상권_코드')['당월_매출_금액']
    .mean()
    .sort_values(ascending=False)
    .head(100)
    .index
)

df_top = df_clean[df_clean['상권_코드'].isin(top100_codes)].copy()

print(f"분석 대상: 상위 100개 상권 × 최대 9분기")
print(f"전체 행 수: {len(df_top)}\n")

# 상권별 카페_검색지수 vs 매출 / log_매출 상관계수 계산
results = []
for code, grp in df_top.groupby('상권_코드'):
    name = grp['상권_코드_명'].iloc[0]
    type_ = grp['상권_구분_코드_명_x'].iloc[0]
    avg_sales = grp['당월_매출_금액'].mean() / 1e8  # 억원

    # 결측 제거
    valid = grp[['카페_검색지수', '당월_매출_금액', 'log_매출']].dropna()
    n = len(valid)

    if n < 3:
        continue

    # 원매출 vs 검색지수
    r_raw, p_raw = stats.pearsonr(valid['카페_검색지수'], valid['당월_매출_금액'])
    # 로그매출 vs 검색지수
    r_log, p_log = stats.pearsonr(valid['카페_검색지수'], valid['log_매출'])

    results.append({
        '상권_코드': code,
        '상권명': name,
        '상권유형': type_,
        '평균매출_억원': round(avg_sales, 2),
        'n분기': n,
        'r_원매출': round(r_raw, 4),
        'p_원매출': round(p_raw, 4),
        'r_로그매출': round(r_log, 4),
        'p_로그매출': round(p_log, 4),
        '유의_원매출': '***' if p_raw < 0.001 else ('**' if p_raw < 0.01 else ('*' if p_raw < 0.05 else '')),
        '유의_로그매출': '***' if p_log < 0.001 else ('**' if p_log < 0.01 else ('*' if p_log < 0.05 else '')),
    })

result_df = pd.DataFrame(results).sort_values('평균매출_억원', ascending=False)

# 저장
result_df.to_csv('eda_search_corr_by_district.csv', index=False, encoding='utf-8-sig')
print("저장 완료: eda_search_corr_by_district.csv\n")

# ── 요약 출력 ──
print("=" * 60)
print("[ 전체 요약 ]")
print(f"분석 상권 수: {len(result_df)}개")

pos_sig = result_df[(result_df['r_로그매출'] > 0) & (result_df['p_로그매출'] < 0.05)]
neg_sig = result_df[(result_df['r_로그매출'] < 0) & (result_df['p_로그매출'] < 0.05)]
insig   = result_df[result_df['p_로그매출'] >= 0.05]

print(f"  양(+)의 유의한 상관 (p<0.05): {len(pos_sig)}개")
print(f"  음(-)의 유의한 상관 (p<0.05): {len(neg_sig)}개")
print(f"  유의하지 않음:                {len(insig)}개")

print(f"\n로그매출 기준 r 평균: {result_df['r_로그매출'].mean():.4f}")
print(f"로그매출 기준 r 중앙값: {result_df['r_로그매출'].median():.4f}")

# ── 상관 높은 상위 10개 ──
print("\n" + "=" * 60)
print("[ 검색지수↑ → 매출↑  상위 10개 상권 (log매출 기준) ]")
top_pos = result_df.nlargest(10, 'r_로그매출')[
    ['상권명', '상권유형', '평균매출_억원', 'r_로그매출', 'p_로그매출', '유의_로그매출']
]
print(top_pos.to_string(index=False))

# ── 상관 낮은(음) 하위 10개 ──
print("\n" + "=" * 60)
print("[ 검색지수↑ → 매출↓  하위 10개 상권 (log매출 기준) ]")
top_neg = result_df.nsmallest(10, 'r_로그매출')[
    ['상권명', '상권유형', '평균매출_억원', 'r_로그매출', 'p_로그매출', '유의_로그매출']
]
print(top_neg.to_string(index=False))

# ── 유의한 상관 전체 목록 ──
print("\n" + "=" * 60)
print("[ 유의한 상관 (p<0.05) 상권 전체 ]")
sig_all = result_df[result_df['p_로그매출'] < 0.05].sort_values('r_로그매출', ascending=False)
print(sig_all[['상권명', '상권유형', '평균매출_억원', 'r_로그매출', 'p_로그매출', '유의_로그매출']].to_string(index=False))
