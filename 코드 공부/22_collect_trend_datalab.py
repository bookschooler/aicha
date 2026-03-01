"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
22_collect_trend_datalab.py — 네이버 데이터랩 검색 트렌드 수집
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  '성수 카페'를 고정 앵커(기준점)로 삼아
  218개 역명에 대해 '{역명} 카페' 키워드의 분기별 검색량 수집
  → 앵커 대비 상대값으로 정규화 → 상권별 카페_검색지수 생성

핵심 개념:
  - 데이터랩 API: 키워드 그룹별 상대 검색량(0~100)을 월별로 반환
  - 최대 5개 그룹 동시 비교 → 4개 역명 + 앵커 = 5그룹/호출
  - 정규화: (역명_비율 / 앵커_비율) × 앵커_단독_비율

입력: to_map_with_station.csv
출력: search_trend_raw.csv (역명별 분기별 정규화 검색지수)
      search_trend_index.csv (상권×분기 패널, QoQ 성장률 포함)
"""

import os       # 작업 디렉토리 변경 (17번에서 상세 설명)
import json     # JSON 변환 (18번에서 상세 설명)
import time     # 호출 간격 조절 (17번에서 상세 설명)
import requests # HTTP API 요청 (17번에서 상세 설명)
import pandas as pd  # 데이터프레임 (17번에서 상세 설명)
import numpy as np   # 수치 배열 계산 (17번에서 상세 설명)
from dotenv import load_dotenv  # .env 환경변수 로드 (17번에서 상세 설명)

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리 변경
load_dotenv()  # .env 파일 읽기

NAVER_CLIENT_ID     = os.getenv('NAVER_CLIENT_ID')      # 네이버 클라이언트 ID
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')  # 네이버 클라이언트 시크릿
DATALAB_URL         = 'https://openapi.naver.com/v1/datalab/search'  # 데이터랩 API URL

START_DATE = '2023-04-01'  # 20232 분기 포함 (QoQ 성장률 계산용 앵커 분기)
END_DATE   = '2025-09-30'  # 20253 분기까지 수집

# 월 → 분기 코드 매핑 딕셔너리 (예: '2023-07' → 20233)
QUARTER_MAP = {
    '2023-04': 20232, '2023-05': 20232, '2023-06': 20232,  # QoQ 계산용 (저장 제외)
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
QUARTERS        = sorted(set(QUARTER_MAP.values()))           # 20232~20253 전체 분기
#  └ set(QUARTER_MAP.values()): 딕셔너리 값들에서 중복 제거
#  └ sorted(): 오름차순 정렬

QUARTERS_OUTPUT = [q for q in QUARTERS if q >= 20233]        # 저장용 분기 (20232 제외)
#  └ [x for x in iterable if 조건]: 리스트 컴프리헨션 (조건 만족하는 원소만 포함)


# ══════════════════════════════════════════════════════
# 데이터랩 API 호출 함수
# ══════════════════════════════════════════════════════
def call_datalab(keyword_groups, retries=3):
    """네이버 데이터랩 API 호출 (최대 5개 그룹, 실패 시 재시도)"""
    headers = {
        'X-Naver-Client-Id':     NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET,
        'Content-Type':          'application/json',  # 요청 본문이 JSON임을 알림
    }
    body = {
        'startDate'    : START_DATE,       # 조회 시작일
        'endDate'      : END_DATE,         # 조회 종료일
        'timeUnit'     : 'month',          # 월별 데이터 요청
        'keywordGroups': keyword_groups,   # 비교할 키워드 그룹 목록
    }
    for attempt in range(retries):  # 최대 3번 재시도
        resp = requests.post(DATALAB_URL, headers=headers, data=json.dumps(body))
        #  └ requests.post(url, headers, data)
        #    · POST 방식 HTTP 요청 전송 (GET과 달리 본문에 데이터를 담아 전송)
        #    · GET: 데이터를 URL에 담음 / POST: 데이터를 본문에 담음
        #    · data=json.dumps(body): 파이썬 딕셔너리 → JSON 문자열로 변환해 전송
        #  └ json.dumps(객체): 파이썬 객체 → JSON 문자열 변환 (json.dump와 다름)
        #    · json.dump: 파일에 저장 / json.dumps: 문자열로 반환

        if resp.status_code == 200:  # 성공
            return resp.json()       # JSON 응답 반환
        print(f"  API {resp.status_code}: {resp.text[:200]} (재시도 {attempt+1}/{retries})")
        time.sleep(2 ** attempt)     # 지수 백오프: 1초, 2초, 4초 대기
        #  └ 2 ** attempt: 2의 attempt 제곱
        #    · attempt=0: 2^0=1초, attempt=1: 2^1=2초, attempt=2: 2^2=4초
        #    · 지수 백오프: 실패할수록 대기 시간을 늘려 서버 부하 줄임

    raise Exception(f"DataLab API 호출 실패: {resp.status_code}")
    #  └ raise Exception(메시지): 예외를 직접 발생시켜 호출한 쪽에서 처리하도록 전달


def parse_result(result):
    """API 응답에서 {그룹명: {월: 비율}} 형태로 파싱"""
    out = {}
    for item in result['results']:
        out[item['title']] = {d['period'][:7]: d['ratio'] for d in item['data']}
        #  └ 딕셔너리 컴프리헨션: {키: 값 for 원소 in iterable}
        #    · d['period'][:7]: 'YYYY-MM-DD' 형식에서 앞 7글자만 (= 'YYYY-MM')
        #    · d['ratio']: 해당 월의 검색 비율 (0~100)
        #    · 결과: {'2023-07': 45.2, '2023-08': 52.1, ...}
    return out  # {그룹명: {YYYY-MM: ratio}} 딕셔너리 반환


# ══════════════════════════════════════════════════════
# 1. 앵커(성수 카페) 단독 호출
# ══════════════════════════════════════════════════════
print("▶ 앵커(성수 카페) 단독 baseline 수집 중...")
anchor_result = call_datalab([{'groupName': '성수 카페', 'keywords': ['성수 카페']}])
#  └ keyword_groups: 리스트[딕셔너리] 형태
#    · groupName: 그룹 이름 (API 응답에서 title로 반환됨)
#    · keywords: 해당 그룹에 포함할 키워드 목록 (여러 개 가능)

anchor_solo = parse_result(anchor_result)['성수 카페']  # 앵커의 월별 검색 비율
print(f"  앵커 월별 데이터: {len(anchor_solo)}개월")
time.sleep(0.5)  # API 호출 간격 대기


# ══════════════════════════════════════════════════════
# 2. 역명 목록 로드
# ══════════════════════════════════════════════════════
to_map   = pd.read_csv('to_map_with_station.csv')           # 상권↔역 매핑 파일 로드
stations = sorted(to_map['최근접_역명'].unique())           # 유니크 역명 정렬 목록
#  └ Series.unique(): 고유값 배열 반환 (중복 제거된 NumPy 배열)
#    · set()으로 중복 제거와 유사하지만 pandas Series에서 더 효율적
print(f"▶ 고유 역명: {len(stations)}개")


# ══════════════════════════════════════════════════════
# 3. 배치(4개씩) API 호출
# ══════════════════════════════════════════════════════
BATCH_SIZE = 4  # 앵커 포함 5그룹 = API 최대 허용 수
batches    = [stations[i:i+BATCH_SIZE] for i in range(0, len(stations), BATCH_SIZE)]
#  └ 리스트 슬라이싱으로 배치 생성
#    · stations[i:i+4]: i번째부터 i+4번째 미만까지의 부분 리스트
#    · range(0, len(stations), 4): 0, 4, 8, 12, ... (4씩 건너뜀)
#    · 결과: [[역1,역2,역3,역4], [역5,역6,역7,역8], ...]

print(f"▶ {len(batches)}개 배치 처리 시작\n")

all_station_monthly = {}  # {역명: {YYYY-MM: 정규화된 검색량}} 저장용 딕셔너리

for idx, batch in enumerate(batches):
    keyword_groups = [{'groupName': '성수 카페', 'keywords': ['성수 카페']}]  # 앵커 항상 포함
    for stn in batch:
        keyword_groups.append({'groupName': stn, 'keywords': [f'{stn} 카페']})
        #  └ list.append(원소): 리스트 끝에 원소 1개 추가
        #    · append는 요소 1개, extend는 리스트를 이어붙임

    try:
        result      = call_datalab(keyword_groups)  # API 호출 (앵커 + 4개 역명)
        parsed      = parse_result(result)          # 응답 파싱
        anchor_batch = parsed.get('성수 카페', {})  # 이 배치에서의 앵커 비율

        for stn in batch:
            stn_data   = parsed.get(stn, {})  # 해당 역의 월별 비율
            normalized = {}
            for period, a_solo in anchor_solo.items():  # 월별로 정규화
                a_batch = anchor_batch.get(period)  # 같은 배치 내 앵커 비율
                s_batch = stn_data.get(period)      # 같은 배치 내 역 비율
                if a_batch and a_batch > 0 and s_batch is not None and a_solo is not None:
                    normalized[period] = (s_batch / a_batch) * a_solo
                    # 정규화 공식: (역_비율 / 앵커_비율) × 앵커_단독_비율
                    # 배치마다 앵커 기준점이 달라지는 문제를 앵커_단독_비율로 보정
                else:
                    normalized[period] = np.nan  # 계산 불가 → NaN
                    #  └ np.nan: NumPy의 NaN 값 (Not a Number, 결측값 표현)

            all_station_monthly[stn] = normalized

        print(f"  배치 {idx+1:3d}/{len(batches)} 완료: {batch}")

    except Exception as e:
        print(f"  배치 {idx+1} 오류: {e} → NaN 채움")
        for stn in batch:
            all_station_monthly[stn] = {p: np.nan for p in anchor_solo}
            #  └ 딕셔너리 컴프리헨션: {키: 값 for 원소 in iterable}
            #    · 오류 난 배치의 역들은 모든 월을 NaN으로 채움

    time.sleep(0.5)  # 배치 간 대기


# ══════════════════════════════════════════════════════
# 4. 월별 → 분기별 평균 산출
# ══════════════════════════════════════════════════════
print("\n▶ 분기별 평균 산출 중...")
records = []
for stn, monthly in all_station_monthly.items():  # 역명별로 순회
    by_q = {q: [] for q in QUARTERS}  # 분기별 빈 리스트 초기화
    #  └ 딕셔너리 컴프리헨션: {키: 값 for 원소 in iterable}
    #    · {20232: [], 20233: [], ...} 형태로 각 분기에 빈 리스트 생성

    for period, ratio in monthly.items():  # 월별 비율 순회
        q = QUARTER_MAP.get(period)  # 해당 월이 속하는 분기 코드
        if q and not np.isnan(ratio):
            #  └ np.isnan(값): 값이 NaN이면 True
            by_q[q].append(ratio)    # 해당 분기의 비율 리스트에 추가

    row = {'역명': stn}
    for q in QUARTERS:
        row[q] = np.mean(by_q[q]) if by_q[q] else np.nan  # 분기 내 월별 평균
        #  └ np.mean(배열): 평균값 계산
        #  └ 리스트가 비어있으면(by_q[q]==[]) NaN 저장
    records.append(row)

station_qdf = pd.DataFrame(records)  # 역명 × 분기 형태의 DataFrame 생성


# ══════════════════════════════════════════════════════
# NaN 후처리
# ══════════════════════════════════════════════════════

# 보정 1: 경의중앙 신촌역 → 신촌역 데이터로 대체 (검색어로 의미 없는 역명)
shinchon_row = station_qdf[station_qdf['역명'] == '신촌역']  # 2호선 신촌역 데이터
if not shinchon_row.empty:  # 신촌역 데이터가 있으면
    for q in QUARTERS:
        station_qdf.loc[station_qdf['역명'] == '경의중앙 신촌역', q] = shinchon_row.iloc[0][q]
        #  └ df.loc[조건, 컬럼]: 조건에 맞는 행의 특정 컬럼 값 가져오거나 설정
        #    · .loc: 라벨(이름) 기반 인덱싱
        #    · .iloc[0]: 첫 번째 행 (위치 기반 인덱싱)
    print("  [보정] 경의중앙 신촌역 → 신촌역 데이터로 대체 완료")

# 보정 2: 나머지 역 부분 NaN → 선형 보간 (앞뒤 값으로 추정)
q_cols = QUARTERS
station_qdf[q_cols] = (
    station_qdf.set_index('역명')[q_cols]  # 역명을 인덱스로 설정
               .T                           # 전치: 행↔열 교환 (분기가 행, 역명이 열)
               .interpolate(method='linear', limit_direction='both')  # 선형 보간
               #  └ DataFrame.interpolate(method='linear', limit_direction='both')
               #    · NaN 값을 앞뒤 유효한 값 사이를 직선으로 이어 추정
               #    · method='linear': 선형 보간 (가장 단순한 방법)
               #    · limit_direction='both': 앞/뒤 방향 모두 보간 (끝 NaN도 처리)
               .T                            # 다시 전치 (원래 방향으로 복구)
               .values                       # NumPy 배열로 변환
)
nan_left = station_qdf[q_cols].isna().sum().sum()  # 보간 후 잔여 NaN 수 확인
#  └ .isna().sum(): 컬럼별 NaN 수 / .sum(): 전체 합산 (이중 sum = 전체 NaN 개수)
print(f"  [보정] 선형 보간 후 잔여 NaN: {nan_left}개")

# 저장 시 20232 컬럼은 제외 (QoQ 계산용이었으므로)
save_cols = ['역명'] + QUARTERS_OUTPUT
station_qdf[save_cols].to_csv('search_trend_raw.csv', index=False, encoding='utf-8-sig')
print(f"  역명×분기 저장: search_trend_raw.csv {station_qdf[save_cols].shape}")


# ══════════════════════════════════════════════════════
# 5. 상권×분기 패널 생성
# ══════════════════════════════════════════════════════
print("\n▶ 상권×분기 패널 생성 중...")
mapping  = to_map[['상권_코드', '최근접_역명']].copy()  # 상권↔역 매핑 테이블
stn_dict = station_qdf.set_index('역명').to_dict('index')  # {역명: {분기: ratio}} 딕셔너리
#  └ df.set_index('컬럼'): 지정 컬럼을 DataFrame의 인덱스로 설정
#  └ .to_dict('index'): 각 행을 {인덱스: {컬럼명: 값}} 형태의 딕셔너리로 변환
#    · 'index' 모드: {행인덱스: {열1: 값1, 열2: 값2}} 형태
#    · 이후 stn_dict['홍대입구역'][20233] 으로 빠르게 접근 가능

rows = []
for _, r in mapping.iterrows():  # 상권↔역 매핑 행 단위 순회
    코드 = r['상권_코드']
    역명 = r['최근접_역명']
    vals = stn_dict.get(역명, {})  # 해당 역의 분기별 검색지수 딕셔너리
    for q in QUARTERS:             # 20232 포함해서 행 생성 (QoQ 계산용)
        rows.append({
            '기준_년분기_코드': q,
            '상권_코드'       : 코드,
            '카페_검색지수'   : vals.get(q, np.nan),  # 해당 분기의 검색지수 (없으면 NaN)
        })

panel = pd.DataFrame(rows).sort_values(['상권_코드', '기준_년분기_코드']).reset_index(drop=True)

# QoQ(전분기 대비) 성장률 계산
panel['검색량_성장률'] = (
    panel.sort_values(['상권_코드', '기준_년분기_코드'])   # 상권별, 분기 순서로 정렬
         .groupby('상권_코드')['카페_검색지수']            # 상권별 그룹화
         .pct_change(fill_method=None) * 100              # 전분기 대비 % 변화율
    #  └ Series.pct_change(fill_method=None)
    #    · 이전 값 대비 현재 값의 변화율 계산: (현재-이전)/이전
    #    · fill_method=None: NaN을 채우지 않음 (20232→20233 첫 성장률 정상 계산)
    #    · × 100: 비율(소수)을 % 단위로 변환
    #    · 첫 행은 이전 값이 없으므로 NaN
)

# 20232는 성장률 계산용이었으므로 저장 시 제외
panel = panel[panel['기준_년분기_코드'].isin(QUARTERS_OUTPUT)].reset_index(drop=True)
#  └ Series.isin(값목록): 해당 값이 목록에 있으면 True (여러 값 필터링에 유용)
#    · df['컬럼'].isin([값1, 값2]) = df['컬럼'] == 값1 | df['컬럼'] == 값2 와 동일

panel.to_csv('search_trend_index.csv', index=False, encoding='utf-8-sig')
print(f"  상권×분기 저장: search_trend_index.csv {panel.shape}")
print(panel.head(10).to_string(index=False))
