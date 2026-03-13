"""
43_prepare_api_data.py
목적: 6개 수요 변수의 백분위 점수를 계산하여 api/unified_ranking.csv에 추가
입력: 33_analysis_ready.csv, api/unified_ranking.csv
출력: api/unified_ranking.csv (갱신)
"""
import pandas as pd

# 데이터 로드
df_raw = pd.read_csv('33_analysis_ready.csv')
df_rank = pd.read_csv('api/unified_ranking.csv')

# 최신 분기(20253) 데이터만 추출
latest = df_raw[df_raw['기준_년분기_코드'] == 20253][
    ['상권_코드_명', '집객시설_수', '총_직장_인구_수', '월_평균_소득_금액',
     '총_가구_수', '카페_검색지수', '지하철_노선_수']
].copy()

# 6개 수요 변수 → 0~100 백분위 변환
demand_vars = ['집객시설_수', '총_직장_인구_수', '월_평균_소득_금액',
               '총_가구_수', '카페_검색지수', '지하철_노선_수']

for col in demand_vars:
    pct_col = col + '_pct'
    latest[pct_col] = latest[col].rank(pct=True) * 100

# unified_ranking에 join (기존 pct 컬럼 있으면 덮어쓰기)
pct_cols = [c + '_pct' for c in demand_vars]
drop_cols = [c for c in pct_cols if c in df_rank.columns]
df_rank = df_rank.drop(columns=drop_cols, errors='ignore')

df_merged = df_rank.merge(
    latest[['상권_코드_명'] + pct_cols],
    on='상권_코드_명',
    how='left'
)

# NaN → 50(중앙값)으로 채움 (데이터 없는 상권)
df_merged[pct_cols] = df_merged[pct_cols].fillna(50.0)

df_merged.to_csv('api/unified_ranking.csv', index=False)
print(f"완료: {len(df_merged)}개 상권, 추가 컬럼: {pct_cols}")
print(df_merged[['상권_코드_명'] + pct_cols].head(3).to_string())
