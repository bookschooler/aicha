# 41_tableau_prep.py
# Tableau 대시보드용 데이터 준비 (7개 슬라이드)
#
# 생성 파일:
#   41_tableau_sangwon.csv       - 상권별 블루오션 점수 + 중심 lon/lat + 자치구 (슬라이드 1,2,3,6)
#   41_tableau_teashops.csv      - 찻집 실제 위치 lon/lat (슬라이드 1)
#   41_tableau_trend.csv         - 상위 상권 9분기 매출 추세 (슬라이드 5)
#   41_tableau_demand_heatmap.csv - 수요변수 히트맵 long형 (슬라이드 4)
#   41_tableau_sensitivity.csv   - 민감도 분석 long형 (슬라이드 7)
#   41_tableau_log.txt           - 실행 로그
#
# 입력:
#   35_blueocean_ranking.csv, 36_unified_top30.csv
#   to_map_with_station.csv, tea_shops_mapped.csv
#   34_oof_residuals.csv, 33_analysis_ready.csv
#   37_demand_profile.csv
#   39_sensitivity_q1.csv, 39_sensitivity_q2.csv

import pandas as pd
import numpy as np
import os

BASE = os.path.dirname(os.path.abspath(__file__))
logs = []

def log(msg):
    print(msg)
    logs.append(msg)

log("=" * 60)
log("41_tableau_prep.py 시작")
log("=" * 60)

# ================================================================
# 공통 데이터 로드
# ================================================================
ranking  = pd.read_csv(os.path.join(BASE, '35_blueocean_ranking.csv'), encoding='utf-8-sig')
top30    = pd.read_csv(os.path.join(BASE, '36_unified_top30.csv'),     encoding='utf-8-sig')
coords   = pd.read_csv(os.path.join(BASE, 'to_map_with_station.csv'),  encoding='utf-8-sig')
teashops = pd.read_csv(os.path.join(BASE, 'tea_shops_mapped.csv'),     encoding='utf-8-sig')
residuals= pd.read_csv(os.path.join(BASE, '34_oof_residuals.csv'),     encoding='utf-8-sig')
ready    = pd.read_csv(os.path.join(BASE, '33_analysis_ready.csv'),    encoding='utf-8-sig')
profile  = pd.read_csv(os.path.join(BASE, '37_demand_profile.csv'),    encoding='utf-8-sig')
sen_q1   = pd.read_csv(os.path.join(BASE, '39_sensitivity_q1.csv'),    encoding='utf-8-sig')
sen_q2   = pd.read_csv(os.path.join(BASE, '39_sensitivity_q2.csv'),    encoding='utf-8-sig')

log(f"로드 완료: ranking={ranking.shape}, coords={coords.shape}, teashops={teashops.shape}")

# ================================================================
# 1. 41_tableau_sangwon.csv
#    상권별 블루오션 점수 + 중심 lon/lat + 자치구
#    슬라이드 1(지도 배경색), 2(2D 산점도), 3(랭킹), 6(자치구 히트맵)
# ================================================================
log("\n[1] 상권 마스터 데이터 생성...")

# coords에서 lon/lat + 자치구 추출 (최신 분기 기준 중복 제거)
coords_dedup = coords.groupby('상권_코드').first().reset_index()[
    ['상권_코드', '상권_코드_명', '행정동_코드_명', '자치구_코드_명', 'lon', 'lat']
]

# ranking에 좌표 join
sangwon = ranking.merge(coords_dedup[['상권_코드','자치구_코드_명','lon','lat']],
                        on='상권_코드', how='left')

# top30 순위 정보 병합 (통합순위, 피타고라스거리)
top30_slim = top30[['상권_코드_명','통합_순위','pythagorean_dist']].rename(
    columns={'통합_순위':'통합순위_top30', 'pythagorean_dist':'피타고라스거리'}
)
sangwon = sangwon.merge(top30_slim, on='상권_코드_명', how='left')

# 사분면 한글 레이블 추가
quadrant_map = {
    'Q1': 'Q1 안전진입 (수요있음+찻집없음)',
    'Q2': 'Q2 선점 (잠재수요+찻집없음)',
    'Q3': 'Q3 포화 (수요있음+찻집있음)',
    'Q4': 'Q4 비추 (수요없음+찻집없음)'
}
sangwon['사분면_레이블'] = sangwon['사분면'].map(quadrant_map).fillna(sangwon['사분면'])

# Q1/Q2만 is_blueocean 플래그
sangwon['블루오션여부'] = sangwon['사분면'].isin(['Q1','Q2']).map({True:'블루오션', False:'일반'})

# 컬럼 정리 및 저장
cols_out = [
    '상권_코드', '상권_코드_명', '상권유형', '자치구_코드_명',
    'lon', 'lat',
    '사분면', '사분면_레이블', '블루오션여부', '구조적블루오션',
    'residual_latest', 'residual_avg', 'supply_shortage',
    'q1_score', 'q2_score', '찻집수_latest', '매출_latest',
    '카페음료_점포수', 'cafe_revenue_per_store',
    '통합순위_top30', '피타고라스거리'
]
cols_out = [c for c in cols_out if c in sangwon.columns]
sangwon[cols_out].to_csv(os.path.join(BASE, '41_tableau_sangwon.csv'),
                          index=False, encoding='utf-8-sig')
log(f"  저장: 41_tableau_sangwon.csv ({sangwon.shape[0]}행 × {len(cols_out)}열)")
log(f"  사분면 분포: {sangwon['사분면'].value_counts().to_dict()}")
log(f"  좌표 결측: {sangwon['lon'].isna().sum()}개")

# ================================================================
# 2. 41_tableau_teashops.csv
#    찻집 실제 위치 (슬라이드 1 — 지도 위 점 레이어)
# ================================================================
log("\n[2] 찻집 위치 데이터 정리...")

teashops_out = teashops[[
    '가게명', '카테고리', '도로명주소', 'lon', 'lat',
    '상권_코드', '상권_코드_명'
]].copy()
teashops_out = teashops_out.dropna(subset=['lon','lat'])
teashops_out.to_csv(os.path.join(BASE, '41_tableau_teashops.csv'),
                    index=False, encoding='utf-8-sig')
log(f"  저장: 41_tableau_teashops.csv ({len(teashops_out)}행)")
log(f"  좌표 있는 찻집: {len(teashops_out)} / {len(teashops)}개")

# ================================================================
# 3. 41_tableau_trend.csv
#    상위 상권 9분기 매출 추세 (슬라이드 5)
#    Q1 Top5 + Q2 Top5 + 전체 중간값 추세
# ================================================================
log("\n[3] 분기별 추세 데이터 생성...")

# Q1 Top5, Q2 Top5 상권 선택 (사분면 값이 'Q1_검증시장공백' 형태이므로 startswith 사용)
q1_top5 = sangwon[sangwon['사분면'].str.startswith('Q1')].nlargest(5, 'residual_latest')['상권_코드'].tolist()
q2_top5 = sangwon[sangwon['사분면'].str.startswith('Q2')].nlargest(5, 'supply_shortage')['상권_코드'].tolist()
target_codes = q1_top5 + q2_top5

# 분기별 잔차 + 매출 데이터 (target 상권 + 전체 중간값)
trend_target = residuals[residuals['상권_코드'].isin(target_codes)].copy()

# 상권명/사분면 join
trend_target = trend_target.merge(
    sangwon[['상권_코드','상권_코드_명','사분면','사분면_레이블','상권유형']],
    on='상권_코드', how='left'
)

# 전체 중간값 추세 (비교 기준선)
trend_median = residuals.groupby('기준_년분기_코드').agg(
    당월_매출_금액=('당월_매출_금액','median'),
    oof_residual=('oof_residual','median')
).reset_index()
trend_median['상권_코드_명'] = '전체 중간값'
trend_median['사분면'] = '기준선'
trend_median['사분면_레이블'] = '전체 중간값 (기준선)'
trend_median['상권유형'] = '-'

# 검색지수 추가 (ready에서)
if '카페_검색지수' in ready.columns:
    search_trend = ready.groupby('기준_년분기_코드')['카페_검색지수'].mean().reset_index()
    trend_target = trend_target.merge(search_trend, on='기준_년분기_코드', how='left')
    trend_median = trend_median.merge(search_trend, on='기준_년분기_코드', how='left')

# 분기 레이블 (20233 → '2023Q3')
def fmt_quarter(q):
    s = str(q)
    return f"{s[:4]}Q{s[4]}"

trend_target['분기'] = trend_target['기준_년분기_코드'].apply(fmt_quarter)
trend_median['분기'] = trend_median['기준_년분기_코드'].apply(fmt_quarter)

out_cols_t = ['분기','기준_년분기_코드','상권_코드_명','사분면','사분면_레이블','상권유형',
              '당월_매출_금액','oof_residual']
if '카페_검색지수' in trend_target.columns:
    out_cols_t.append('카페_검색지수')

trend_combined = pd.concat([
    trend_target[[c for c in out_cols_t if c in trend_target.columns]],
    trend_median[[c for c in out_cols_t if c in trend_median.columns]]
], ignore_index=True)

trend_combined.to_csv(os.path.join(BASE, '41_tableau_trend.csv'),
                      index=False, encoding='utf-8-sig')
log(f"  저장: 41_tableau_trend.csv ({len(trend_combined)}행)")
log(f"  포함 상권: Q1 Top5 + Q2 Top5 + 전체중간값 / 분기={sorted(trend_combined['기준_년분기_코드'].unique())}")

# ================================================================
# 4. 41_tableau_demand_heatmap.csv
#    수요변수 6개 × 상위 10개 상권 (슬라이드 4)
#    wide → long 변환
# ================================================================
log("\n[4] 수요변수 히트맵 데이터 생성...")

DEMAND_VARS = ['집객시설_수','총_직장_인구_수','월_평균_소득_금액',
               '총_가구_수','카페_검색지수','지하철_노선_수']
PCT_VARS    = [v+'_pct' for v in DEMAND_VARS]

# profile에 사분면 정보 merge
profile2 = profile.merge(
    sangwon[['상권_코드_명','사분면','사분면_레이블']],
    on='상권_코드_명', how='left'
)

# wide → long (pct 기준: 전체 상권 내 분위수)
pct_cols = [c for c in PCT_VARS if c in profile2.columns]
if pct_cols:
    heatmap = profile2.melt(
        id_vars=['상권_코드_명','사분면','사분면_레이블','그룹','순위'],
        value_vars=pct_cols,
        var_name='변수_pct', value_name='분위수'
    )
    heatmap['변수명'] = heatmap['변수_pct'].str.replace('_pct','')
    SHAP_ORDER = {v: i for i, v in enumerate(DEMAND_VARS)}
    heatmap['SHAP순위'] = heatmap['변수명'].map(SHAP_ORDER).fillna(99).astype(int)
else:
    # pct 없으면 원값 사용 후 min-max 정규화
    raw_cols = [c for c in DEMAND_VARS if c in profile2.columns]
    heatmap = profile2.melt(
        id_vars=['상권_코드_명','사분면','사분면_레이블','그룹','순위'],
        value_vars=raw_cols,
        var_name='변수명', value_name='원값'
    )
    heatmap['분위수'] = heatmap.groupby('변수명')['원값'].transform(
        lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
    )
    heatmap['SHAP순위'] = heatmap['변수명'].map({v:i for i,v in enumerate(DEMAND_VARS)}).fillna(99).astype(int)

heatmap.to_csv(os.path.join(BASE, '41_tableau_demand_heatmap.csv'),
               index=False, encoding='utf-8-sig')
log(f"  저장: 41_tableau_demand_heatmap.csv ({len(heatmap)}행)")

# ================================================================
# 5. 41_tableau_sensitivity.csv
#    민감도 분석 long형 (슬라이드 7)
# ================================================================
log("\n[5] 민감도 분석 데이터 생성...")

# Q1
q1_long_list = []
rank_cols_q1 = [c for c in sen_q1.columns if c not in ['가중치','겹치는상권수(Q1)']]
for _, row in sen_q1.iterrows():
    for rank_col in rank_cols_q1:
        q1_long_list.append({
            '가중치': row['가중치'],
            '순위': rank_col,
            '상권명': row[rank_col],
            '사분면': 'Q1'
        })
q1_long = pd.DataFrame(q1_long_list)
q1_long['겹치는상권수'] = q1_long['가중치'].map(
    dict(zip(sen_q1['가중치'], sen_q1.get('겹치는상권수(Q1)', [None]*len(sen_q1))))
)

# Q2
q2_long_list = []
rank_cols_q2 = [c for c in sen_q2.columns if c not in ['가중치','겹치는상권수(Q2)']]
for _, row in sen_q2.iterrows():
    for rank_col in rank_cols_q2:
        q2_long_list.append({
            '가중치': row['가중치'],
            '순위': rank_col,
            '상권명': row[rank_col],
            '사분면': 'Q2'
        })
q2_long = pd.DataFrame(q2_long_list)
q2_long['겹치는상권수'] = q2_long['가중치'].map(
    dict(zip(sen_q2['가중치'], sen_q2.get('겹치는상권수(Q2)', [None]*len(sen_q2))))
)

sensitivity = pd.concat([q1_long, q2_long], ignore_index=True)
# 가중치 분리 (w1 추출)
sensitivity['w1'] = sensitivity['가중치'].str.extract(r'w=(\d\.\d)').astype(float)

sensitivity.to_csv(os.path.join(BASE, '41_tableau_sensitivity.csv'),
                   index=False, encoding='utf-8-sig')
log(f"  저장: 41_tableau_sensitivity.csv ({len(sensitivity)}행)")

# ================================================================
# 6. 41_tableau_gu_summary.csv
#    자치구 × 사분면 집계 (슬라이드 6)
# ================================================================
log("\n[6] 자치구별 요약 데이터 생성...")

gu_summary = sangwon.groupby(['자치구_코드_명','사분면']).agg(
    상권수=('상권_코드','count'),
    평균_잔차=('residual_latest','mean'),
    평균_공급부족=('supply_shortage','mean'),
    평균_찻집수=('찻집수_latest','mean')
).reset_index()

gu_summary.to_csv(os.path.join(BASE, '41_tableau_gu_summary.csv'),
                  index=False, encoding='utf-8-sig')
log(f"  저장: 41_tableau_gu_summary.csv ({len(gu_summary)}행)")

# ================================================================
# 최종 요약
# ================================================================
log("\n" + "=" * 60)
log("생성 완료 파일 목록:")
output_files = [
    '41_tableau_sangwon.csv',
    '41_tableau_teashops.csv',
    '41_tableau_trend.csv',
    '41_tableau_demand_heatmap.csv',
    '41_tableau_sensitivity.csv',
    '41_tableau_gu_summary.csv',
]
for f in output_files:
    path = os.path.join(BASE, f)
    if os.path.exists(path):
        df_tmp = pd.read_csv(path, encoding='utf-8-sig')
        log(f"  {f}: {df_tmp.shape[0]}행 x {df_tmp.shape[1]}열")
log("=" * 60)

# 로그 저장
with open(os.path.join(BASE, '41_tableau_log.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(logs))
print("\n로그 저장: 41_tableau_log.txt")
