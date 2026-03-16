# 44_add_demand_details.py
# 수요 요인 지수 hover용 상세 정보 추가
#
# 출력:
#   station_with_lines.csv   - station_coords.csv + 호선 정보 추가
#   api/unified_ranking.csv  - 아래 컬럼 추가:
#       지하철_역_목록        : "5호선 굽은다리역, 5호선 명일역" 형식
#       집객시설_수_raw       : 실제값 (개)
#       총_직장_인구_수_raw   : 실제값 (명)
#       월_평균_소득_금액_raw : 실제값 (원)
#       총_가구_수_raw        : 실제값 (가구)
#       카페_검색지수_raw     : 실제값 (0~1)

import os, time, re
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'api', '.env'))
KAKAO_KEY = os.environ.get('KAKAO_API_KEY', '')
BASE = os.path.dirname(__file__)
ROOT = os.path.dirname(BASE)  # work/ 의 부모 = aicha/

# ── 파일 경로 ──────────────────────────────────────────────────
STATION_COORDS  = os.path.join(BASE, 'station_coords.csv')
STATION_LINES   = os.path.join(BASE, 'station_with_lines.csv')
MAP_STATION     = os.path.join(BASE, 'to_map_with_station.csv')
ANALYSIS_READY  = os.path.join(BASE, '33_analysis_ready.csv')
UNIFIED_RANKING = os.path.join(ROOT, 'api', 'unified_ranking.csv')
LOG_FILE        = os.path.join(BASE, '44_demand_details_log.txt')

logs = []
def log(msg): print(msg); logs.append(msg)

# ══════════════════════════════════════════════════════════════
# 1단계: 역명별 호선 조회 (카카오 API)
# ══════════════════════════════════════════════════════════════
def get_line_from_kakao(station_name: str) -> str:
    """카카오 장소검색으로 역의 호선 추출. 예: '5호선', '2호선, 6호선'"""
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    headers = {'Authorization': f'KakaoAK {KAKAO_KEY}'}
    params = {'query': station_name, 'category_group_code': 'SW8', 'size': 5}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        docs = r.json().get('documents', [])
        lines = set()
        for doc in docs:
            # place_name에 역명 포함 여부로 필터 (동명이역 방지)
            pure_name = re.sub(r'\s*[0-9]+호선', '', doc.get('place_name', '')).strip()
            if pure_name.replace(' ', '') != station_name.replace(' ', ''):
                continue
            cat = doc.get('category_name', '')
            # "교통,수송 > 지하철,전철 > 수도권 2호선" → "2호선"
            m = re.findall(r'(\d+호선)', cat)
            if m:
                lines.update(m)
            # 경의중앙선, 신분당선 등 특수 호선
            for special in ['경의중앙선', '신분당선', '경춘선', '수인분당선', '공항철도', 'GTX', '경강선', '서해선', 'KTX']:
                if special in cat:
                    lines.add(special)
        return ', '.join(sorted(lines)) if lines else ''
    except Exception as e:
        return ''

log('=== 44_add_demand_details.py 시작 ===')
log(f'Kakao API 키: {"있음" if KAKAO_KEY else "없음 ← .env 확인 필요"}')

# ── 호선 정보 캐시 파일이 있으면 재사용 ─────────────────────
df_stations = pd.read_csv(STATION_COORDS)
log(f'역 수: {len(df_stations)}개')

if os.path.exists(STATION_LINES):
    df_with_lines = pd.read_csv(STATION_LINES)
    log(f'[캐시] station_with_lines.csv 사용 ({len(df_with_lines)}개)')
else:
    log('카카오 API로 호선 정보 수집 중...')
    lines_list = []
    for i, row in df_stations.iterrows():
        name = row['역명']
        line = get_line_from_kakao(name)
        lines_list.append(line)
        if (i + 1) % 20 == 0:
            log(f'  {i+1}/{len(df_stations)} 완료...')
        time.sleep(0.05)
    df_with_lines = df_stations.copy()
    df_with_lines['호선'] = lines_list
    df_with_lines.to_csv(STATION_LINES, index=False, encoding='utf-8-sig')
    log(f'[저장] {STATION_LINES}')

# 호선 미확인 역 확인
missing_line = df_with_lines[df_with_lines['호선'].fillna('') == '']['역명'].tolist()
if missing_line:
    log(f'호선 미확인 역 {len(missing_line)}개: {missing_line[:10]}')

# ══════════════════════════════════════════════════════════════
# 2단계: 각 상권 기준 반경 내 역 Top-K 목록 생성
# ══════════════════════════════════════════════════════════════
df_map = pd.read_csv(MAP_STATION)
df_ranking = pd.read_csv(UNIFIED_RANKING)

LAT_REF = 37.5
LON_SCALE = np.cos(np.radians(LAT_REF))

station_coords = df_with_lines[['역_lon', '역_lat']].values.copy()
station_coords[:, 0] *= LON_SCALE
map_coords = df_map[['lon', 'lat']].values.copy()
map_coords[:, 0] *= LON_SCALE

RADIUS_DEG = 1500 / 111320  # 1.5km → 도 단위
K = 8  # 최대 탐색 역 수

tree = cKDTree(station_coords)
dists, idxs = tree.query(map_coords, k=K)
dists_m = dists * 111320

subway_list = []
for i in range(len(df_map)):
    seen_lines = set()
    entries = []
    # 노선 수 기준으로 고유 노선 선택 (최대 5개 노선)
    for j in range(K):
        if dists_m[i, j] > 1500:  # 1.5km 초과는 제외
            break
        idx = idxs[i, j]
        name = df_with_lines.iloc[idx]['역명']
        line = str(df_with_lines.iloc[idx].get('호선', '') or '')
        entry = f'{line} {name}'.strip() if line else name
        # 동일 역명 중복 제거
        if entry not in entries:
            entries.append(entry)
        # 고유 노선 추적 (노선 수 제한: 지하철_노선_수 컬럼 기준)
        target_n = int(df_map.iloc[i].get('지하철_노선_수', 0))
        for ln in re.findall(r'(\d+호선|경의중앙선|신분당선|경춘선|수인분당선|공항철도|경강선|서해선)', line):
            seen_lines.add(ln)
        if target_n > 0 and len(seen_lines) >= target_n:
            break
    subway_list.append(', '.join(entries[:5]) if entries else '')

df_map['지하철_역_목록'] = subway_list
log(f'[샘플] 굽은다리역 3번: {df_map[df_map["상권_코드_명"] == "굽은다리역 3번"]["지하철_역_목록"].values}')
log(f'[샘플] 강남역: {df_map[df_map["상권_코드_명"] == "강남역"]["지하철_역_목록"].values}')
log(f'[샘플] 홍대입구역(홍대): {df_map[df_map["상권_코드_명"].str.contains("홍대입구", na=False)]["지하철_역_목록"].values[:2]}')

# ══════════════════════════════════════════════════════════════
# 3단계: 수요변수 실제값 추가 (최신 분기 2025Q3)
# ══════════════════════════════════════════════════════════════
df_analysis = pd.read_csv(ANALYSIS_READY)
LATEST_Q = df_analysis['기준_년분기_코드'].max()
log(f'최신 분기: {LATEST_Q}')

df_latest = df_analysis[df_analysis['기준_년분기_코드'] == LATEST_Q].copy()
demand_raw_cols = {
    '집객시설_수':       '집객시설_수_raw',
    '총_직장_인구_수':   '총_직장_인구_수_raw',
    '월_평균_소득_금액': '월_평균_소득_금액_raw',
    '총_가구_수':       '총_가구_수_raw',
    '카페_검색지수':     '카페_검색지수_raw',
}
df_raw = df_latest[['상권_코드_명'] + list(demand_raw_cols.keys())].copy()
df_raw = df_raw.rename(columns=demand_raw_cols)

# ══════════════════════════════════════════════════════════════
# 4단계: unified_ranking.csv에 병합
# ══════════════════════════════════════════════════════════════
# 지하철_역_목록
subway_mapping = df_map.set_index('상권_코드_명')['지하철_역_목록'].to_dict()
df_ranking['지하철_역_목록'] = df_ranking['상권_코드_명'].map(subway_mapping).fillna('')

# 수요변수 실제값
df_ranking = df_ranking.merge(df_raw, on='상권_코드_명', how='left')

df_ranking.to_csv(UNIFIED_RANKING, index=False, encoding='utf-8-sig')
log(f'[저장] {UNIFIED_RANKING} ({len(df_ranking)}행, {len(df_ranking.columns)}컬럼)')
log(f'추가된 컬럼: 지하철_역_목록, {", ".join(demand_raw_cols.values())}')

with open(LOG_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(logs))
log(f'[로그] {LOG_FILE}')
log('=== 완료 ===')
