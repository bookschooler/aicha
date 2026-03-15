import pandas as pd
import numpy as np
import re as _re
import traceback

log = []

try:
    df_map = pd.read_csv('to_map.csv')
    df_ranking = pd.read_csv('unified_ranking.csv')

    df_ranking['찻집수_latest'] = df_ranking['찻집수_latest'].fillna(0)
    df_ranking['매출_latest'] = df_ranking['매출_latest'].fillna(0)
    df_ranking['사분면'] = df_ranking['사분면'].fillna('일반 상권')
    df_ranking['블루오션_랭킹'] = pd.to_numeric(df_ranking['블루오션_랭킹'], errors='coerce').fillna(9999)

    df_ranking['unified_score'] = df_ranking[['q1_score', 'q2_score']].max(axis=1)
    df_ranking['unified_rank'] = df_ranking['unified_score'].rank(ascending=False, method='min').astype(int)

    _raw_to_pct = {
        '집객시설_수_raw': '집객시설_수_pct',
        '총_직장_인구_수_raw': '총_직장_인구_수_pct',
        '월_평균_소득_금액_raw': '월_평균_소득_금액_pct',
        '총_가구_수_raw': '총_가구_수_pct',
        '카페_검색지수_raw': '카페_검색지수_pct',
    }
    for raw_col, pct_col in _raw_to_pct.items():
        if raw_col in df_ranking.columns:
            df_ranking[pct_col] = df_ranking[raw_col].rank(pct=True, na_option='keep') * 100
        else:
            df_ranking[pct_col] = 50.0

    def _count_lines(subway_str):
        if not subway_str or (isinstance(subway_str, float) and subway_str != subway_str):
            return 0
        lines = set(_re.findall(
            r'(\d+호선|경의중앙선|신분당선|경춘선|수인분당선|공항철도|경강선|서해선)',
            str(subway_str)
        ))
        return len(lines)

    df_ranking['지하철_노선_수_raw'] = df_ranking['지하철_역_목록'].apply(_count_lines) \
        if '지하철_역_목록' in df_ranking.columns else 0
    df_ranking['지하철_노선_수_pct'] = df_ranking['지하철_노선_수_raw'].rank(
        pct=True, na_option='keep') * 100

    log.append('SUCCESS: 데이터 로드 완료')
    log.append(f'df_ranking: {len(df_ranking)}행, {len(df_ranking.columns)}컬럼')
    log.append(f'df_map: {len(df_map)}행')
    log.append(f'to_map.csv 컬럼: {list(df_map.columns)}')

    ranked_names = set(df_ranking['상권_코드_명'])
    df_map_ranked = df_map[df_map['상권_코드_명'].isin(ranked_names)].reset_index(drop=True)
    log.append(f'df_map_ranked: {len(df_map_ranked)}행')

    if df_map_ranked.empty:
        log.append('ERROR: df_map_ranked가 비어있음! (상권명 매칭 실패)')
        log.append(f'ranking 상권명 샘플: {list(df_ranking["상권_코드_명"].head(3))}')
        log.append(f'to_map 상권명 샘플: {list(df_map["상권_코드_명"].head(3))}')
    else:
        log.append(f'OK: KDTree 구성 가능. 좌표 컬럼: {[c for c in df_map.columns if "좌표" in c or "lon" in c.lower() or "lat" in c.lower()]}')

except Exception as e:
    log.append(f'EXCEPTION: {e}')
    log.append(traceback.format_exc())

with open('startup_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))
print('Done')
