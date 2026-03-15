#!/usr/bin/env python3
"""
22_collect_trend_datalab.py

네이버 데이터랩 검색 트렌드 수집
- '성수 카페'를 고정 앵커로 사용
- 218개 역명에 대해 '{역명} 카페' 키워드로 분기별 상대 검색량 수집
- 배치당 4개 역명 + 앵커 = 5개 키워드 그룹 (API 제한)
- 정규화: (역명_비율 / 앵커_비율) × 앵커_단독_비율
- 출력: search_trend_raw.csv (역명×분기)
"""

import os
import json
import time
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv

os.chdir('/teamspace/studios/this_studio/aicha')
load_dotenv()

NAVER_CLIENT_ID     = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
DATALAB_URL         = 'https://openapi.naver.com/v1/datalab/search'

START_DATE = '2023-04-01'   # 20233 성장률 계산을 위해 20232(Q2)도 수집
END_DATE   = '2025-09-30'

QUARTER_MAP = {
    '2023-04': 20232, '2023-05': 20232, '2023-06': 20232,  # 성장률 계산용 (출력 제외)
    '2023-07': 20233, '2023-08': 20233, '2023-09': 20233,
    '2023-10': 20234, '2023-11': 20234, '2023-12': 20234,
    '2024-01': 20241, '2024-02': 20241, '2024-03': 20241,
    '2024-04': 20242, '2024-05': 20242, '2024-06': 20242,
    '2024-07': 20243, '2024-08': 20243, '2024-09': 20243,
    '2024-10': 20244, '2024-11': 20244, '2024-12': 20244,
    '2025-01': 20251, '2025-02': 20251, '2025-03': 20251,
    '2025-04': 20252, '2025-05': 20252, '2025-06': 20252,
    '2025-07': 20253, '2025-08': 20253, '2025-09': 20253,
}
QUARTERS        = sorted(set(QUARTER_MAP.values()))          # 20232~20253 (계산용)
QUARTERS_OUTPUT = [q for q in QUARTERS if q >= 20233]        # 20233~20253 (저장용)


def call_datalab(keyword_groups, retries=3):
    """네이버 데이터랩 API 호출 (최대 5개 그룹)"""
    headers = {
        'X-Naver-Client-Id':     NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET,
        'Content-Type':          'application/json',
    }
    body = {
        'startDate':     START_DATE,
        'endDate':       END_DATE,
        'timeUnit':      'month',
        'keywordGroups': keyword_groups,
    }
    for attempt in range(retries):
        resp = requests.post(DATALAB_URL, headers=headers, data=json.dumps(body))
        if resp.status_code == 200:
            return resp.json()
        print(f"  API {resp.status_code}: {resp.text[:200]} (재시도 {attempt+1}/{retries})")
        time.sleep(2 ** attempt)
    raise Exception(f"DataLab API 호출 실패: {resp.status_code}")


def parse_result(result):
    """{groupName: {period(YYYY-MM): ratio}} 파싱"""
    out = {}
    for item in result['results']:
        out[item['title']] = {d['period'][:7]: d['ratio'] for d in item['data']}
    return out


# ── 1. 앵커 단독 호출 ────────────────────────────────────────────
print("▶ 앵커(성수 카페) 단독 baseline 수집 중...")
anchor_result = call_datalab([{'groupName': '성수 카페', 'keywords': ['성수 카페']}])
anchor_solo   = parse_result(anchor_result)['성수 카페']  # {YYYY-MM: ratio}
print(f"  앵커 월별 데이터: {len(anchor_solo)}개월")
time.sleep(0.5)

# ── 2. 역명 목록 로드 ────────────────────────────────────────────
to_map   = pd.read_csv('to_map_with_station.csv')
stations = sorted(to_map['최근접_역명'].unique())
print(f"▶ 고유 역명: {len(stations)}개")

# ── 3. 배치(4개씩) API 호출 ──────────────────────────────────────
BATCH_SIZE = 4
batches    = [stations[i:i+BATCH_SIZE] for i in range(0, len(stations), BATCH_SIZE)]
print(f"▶ {len(batches)}개 배치 처리 시작\n")

all_station_monthly = {}  # {역명: {YYYY-MM: normalized_ratio}}

for idx, batch in enumerate(batches):
    keyword_groups = [{'groupName': '성수 카페', 'keywords': ['성수 카페']}]
    for stn in batch:
        keyword_groups.append({'groupName': stn, 'keywords': [f'{stn} 카페']})

    try:
        result = call_datalab(keyword_groups)
        parsed = parse_result(result)
        anchor_batch = parsed.get('성수 카페', {})

        for stn in batch:
            stn_data   = parsed.get(stn, {})
            normalized = {}
            for period, a_solo in anchor_solo.items():
                a_batch = anchor_batch.get(period)
                s_batch = stn_data.get(period)
                if a_batch and a_batch > 0 and s_batch is not None and a_solo is not None:
                    normalized[period] = (s_batch / a_batch) * a_solo
                else:
                    normalized[period] = np.nan
            all_station_monthly[stn] = normalized

        print(f"  배치 {idx+1:3d}/{len(batches)} 완료: {batch}")

    except Exception as e:
        print(f"  배치 {idx+1} 오류: {e} → NaN 채움")
        for stn in batch:
            all_station_monthly[stn] = {p: np.nan for p in anchor_solo}

    time.sleep(0.5)

# ── 4. 월별 → 분기별 평균 ────────────────────────────────────────
print("\n▶ 분기별 평균 산출 중...")
records = []
for stn, monthly in all_station_monthly.items():
    by_q = {q: [] for q in QUARTERS}
    for period, ratio in monthly.items():
        q = QUARTER_MAP.get(period)
        if q and not np.isnan(ratio):
            by_q[q].append(ratio)
    row = {'역명': stn}
    for q in QUARTERS:
        row[q] = np.mean(by_q[q]) if by_q[q] else np.nan
    records.append(row)

station_qdf = pd.DataFrame(records)

# ── NaN 후처리 ───────────────────────────────────────────────────
# ① 경의중앙 신촌역 → 신촌역 데이터로 대체 (아무도 '경의중앙 신촌역 카페'로 검색 안 함)
shinchon_row = station_qdf[station_qdf['역명'] == '신촌역']
if not shinchon_row.empty:
    for q in QUARTERS:
        station_qdf.loc[station_qdf['역명'] == '경의중앙 신촌역', q] = shinchon_row.iloc[0][q]
    print("  [보정] 경의중앙 신촌역 → 신촌역 데이터로 대체 완료")

# ② 나머지 역 부분 NaN → 분기 순서대로 선형 보간 (양 끝 NaN은 이웃값으로 채움)
q_cols = QUARTERS
station_qdf[q_cols] = (
    station_qdf.set_index('역명')[q_cols]
               .T.interpolate(method='linear', limit_direction='both').T
               .values
)
nan_left = station_qdf[q_cols].isna().sum().sum()
print(f"  [보정] 선형 보간 후 잔여 NaN: {nan_left}개")

# 저장 시 20232 컬럼 제외 (계산용)
save_cols = ['역명'] + QUARTERS_OUTPUT
station_qdf[save_cols].to_csv('search_trend_raw.csv', index=False, encoding='utf-8-sig')
print(f"  역명×분기 저장: search_trend_raw.csv {station_qdf[save_cols].shape}")

# ── 5. 상권×분기 패널 생성 ───────────────────────────────────────
print("\n▶ 상권×분기 패널 생성 중...")
mapping = to_map[['상권_코드', '최근접_역명']].copy()
stn_dict = station_qdf.set_index('역명').to_dict('index')  # {역명: {분기: ratio}}

rows = []
for _, r in mapping.iterrows():
    코드 = r['상권_코드']
    역명 = r['최근접_역명']
    vals = stn_dict.get(역명, {})
    for q in QUARTERS:            # 20232 포함하여 QoQ 계산용
        rows.append({
            '기준_년분기_코드': q,
            '상권_코드':       코드,
            '카페_검색지수':   vals.get(q, np.nan),
        })

panel = pd.DataFrame(rows).sort_values(['상권_코드', '기준_년분기_코드']).reset_index(drop=True)

# QoQ 성장률 (20232가 있으므로 20233 성장률도 유효하게 계산됨)
panel['검색량_성장률'] = (
    panel.sort_values(['상권_코드', '기준_년분기_코드'])
         .groupby('상권_코드')['카페_검색지수']
         .pct_change(fill_method=None) * 100
)

# 20232는 계산용이었으므로 최종 저장 시 제외
panel = panel[panel['기준_년분기_코드'].isin(QUARTERS_OUTPUT)].reset_index(drop=True)

panel.to_csv('search_trend_index.csv', index=False, encoding='utf-8-sig')
print(f"  상권×분기 저장: search_trend_index.csv {panel.shape}")
print(panel.head(10).to_string(index=False))
