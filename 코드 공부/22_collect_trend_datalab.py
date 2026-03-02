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

import os       # 작업 디렉토리 변경 및 환경변수 접근용 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리(cwd) 변경
#    · os.getenv('키'): 환경변수 값 반환 (없으면 None)
#    · os.path.join(), os.path.exists() 등 경로 관련 함수 포함
#    · 이 스크립트에서는 aicha 폴더를 cwd로 지정해 파일명만으로 CSV 접근 가능하게 함

import json     # JSON 형식 데이터 변환용 내장 모듈
#  └ [json 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · json.dumps(객체): 파이썬 딕셔너리/리스트 → JSON 문자열 변환
#    · json.loads(문자열): JSON 문자열 → 파이썬 객체 변환
#    · json.dump(객체, 파일): 파이썬 객체를 JSON 형식으로 파일에 저장
#    · json.load(파일): JSON 파일을 읽어 파이썬 객체로 변환
#    · ensure_ascii=False: 한글을 유니코드 이스케이프 없이 그대로 저장

import time     # 시간 지연 처리용 내장 모듈
#  └ [time 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · time.sleep(초): 지정한 초만큼 실행을 일시 정지
#    · API 호출 사이에 sleep을 두어 서버 과부하 및 rate limit 위반 방지

import requests # HTTP 요청 전송 라이브러리
#  └ [requests 라이브러리]
#    · pip install requests 로 설치
#    · requests.get(url, headers, params, timeout): GET 방식 HTTP 요청 전송
#    · requests.post(url, headers, data): POST 방식 HTTP 요청 전송
#      · GET: 데이터를 URL 쿼리스트링에 담음 (검색, 조회)
#      · POST: 데이터를 요청 본문(body)에 담음 (생성, 전송)
#    · 반환: Response 객체
#      · resp.status_code: HTTP 응답 코드 (200=성공, 401=인증실패 등)
#      · resp.json(): 응답 body JSON → 파이썬 딕셔너리로 변환
#      · resp.text: 응답 body를 문자열 그대로 반환
#    · timeout=5: 5초 내 응답 없으면 예외 발생 (무한 대기 방지)

import pandas as pd  # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · CSV 읽기: pd.read_csv(파일명) → DataFrame 반환
#    · CSV 쓰기: df.to_csv(파일명, index=False, encoding='utf-8-sig')
#    · Series.unique(): 고유값 배열 반환 (중복 제거된 NumPy 배열)
#    · df.sort_values(컬럼): 컬럼 기준 정렬
#    · df.groupby(컬럼)[대상].pct_change(): 그룹별 전행 대비 변화율
#    · df.set_index(컬럼): 컬럼을 DataFrame 인덱스로 설정
#    · df.to_dict('index'): {행인덱스: {컬럼명: 값}} 딕셔너리로 변환
#    · Series.isin(값목록): 값이 목록에 있으면 True인 Boolean Series

import numpy as np   # 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · np.nan: 결측값 표현 (Not a Number)
#    · np.isnan(값): 값이 NaN이면 True
#    · np.mean(배열): 배열의 평균값 계산

from dotenv import load_dotenv  # .env 파일에서 환경변수 로드하는 라이브러리
#  └ [python-dotenv 라이브러리]
#    · pip install python-dotenv 로 설치
#    · load_dotenv(): 현재 디렉토리의 .env 파일을 읽어 환경변수로 등록
#    · .env 파일 예시: NAVER_CLIENT_ID=abc123
#    · os.getenv()로 해당 값에 접근 가능
#    · API 키 등 민감 정보를 코드에 직접 쓰지 않기 위해 사용

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경
#  └ os.chdir(경로)
#    · 기본문법: os.chdir(path)
#    · 이후 pd.read_csv('파일명.csv') 처럼 파일명만 써도 이 폴더에서 찾음
#    · 변경하지 않으면 스크립트 실행 위치에서 파일을 찾아 오류 발생

load_dotenv()  # .env 파일을 읽어서 환경변수로 등록
#  └ load_dotenv()
#    · 기본문법: load_dotenv(dotenv_path=None)
#    · dotenv_path 미지정 시 현재 디렉토리와 상위 디렉토리에서 .env 파일 자동 탐색
#    · 호출 후 os.getenv()로 .env에 정의된 변수 접근 가능

NAVER_CLIENT_ID     = os.getenv('NAVER_CLIENT_ID')      # 네이버 클라이언트 ID
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')  # 네이버 클라이언트 시크릿
#  └ os.getenv(키, 기본값=None)
#    · 기본문법: os.getenv(key, default=None)
#    · 환경변수 값 반환, 없으면 None 반환 (KeyError 발생 없음)
#    · os.environ["키"]와 달리 없어도 오류 안 남 → 안전한 접근 방식

DATALAB_URL = 'https://openapi.naver.com/v1/datalab/search'  # 데이터랩 API URL

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

QUARTERS = sorted(set(QUARTER_MAP.values()))  # 20232~20253 전체 분기 (중복 제거 후 정렬)
#  └ set(QUARTER_MAP.values())
#    · 기본문법: set(iterable)
#    · 딕셔너리 values()에서 중복 제거 → {20232, 20233, 20234, ...} 집합 생성
#    · 집합(set): 순서 없음, 중복 없음, 빠른 in 연산
#
#  └ sorted(iterable)
#    · 기본문법: sorted(iterable, key=None, reverse=False)
#    · iterable을 정렬한 새 리스트 반환
#    · 원본 변경 없음 (list.sort()는 원본 변경)
#    · reverse=True면 내림차순

QUARTERS_OUTPUT = [q for q in QUARTERS if q >= 20233]  # 저장용 분기 (20232 제외)
#  └ 리스트 컴프리헨션 [표현식 for 변수 in iterable if 조건]
#    · 기본문법: [표현식 for 변수 in iterable if 조건]
#    · 조건(if q >= 20233)이 True인 원소만 포함한 새 리스트 생성
#    · if 없으면 모든 원소 포함, if 있으면 필터링


# ══════════════════════════════════════════════════════
# 데이터랩 API 호출 함수
# ══════════════════════════════════════════════════════
def call_datalab(keyword_groups, retries=3):
    """네이버 데이터랩 API 호출 (최대 5개 그룹, 실패 시 재시도)"""
    headers = {
        'X-Naver-Client-Id':     NAVER_CLIENT_ID,      # 네이버 클라이언트 ID 인증 헤더
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET,  # 네이버 클라이언트 시크릿 헤더
        'Content-Type':          'application/json',   # 요청 본문이 JSON임을 서버에 알림
    }
    body = {
        'startDate'    : START_DATE,       # 조회 시작일
        'endDate'      : END_DATE,         # 조회 종료일
        'timeUnit'     : 'month',          # 월별 데이터 요청
        'keywordGroups': keyword_groups,   # 비교할 키워드 그룹 목록 (최대 5개)
    }
    for attempt in range(retries):  # 최대 retries번 재시도 (기본값 3)
        resp = requests.post(DATALAB_URL, headers=headers, data=json.dumps(body))
        #  └ requests.post(url, headers, data)
        #    · 기본문법: requests.post(url, headers=None, data=None, json=None)
        #    · POST 방식 HTTP 요청 전송 (GET과 달리 본문에 데이터를 담아 전송)
        #    · GET: 데이터를 URL 쿼리스트링에 담음 (보통 조회/검색)
        #    · POST: 데이터를 요청 body에 담음 (보통 생성/전송, 복잡한 요청)
        #    · data=json.dumps(body): 파이썬 딕셔너리 → JSON 문자열로 변환해 전송
        #    · json= 파라미터로도 딕셔너리 직접 전달 가능 (자동 변환)
        #
        #  └ json.dumps(객체)
        #    · 기본문법: json.dumps(obj, ensure_ascii=True, indent=None)
        #    · 파이썬 객체(딕셔너리/리스트 등) → JSON 형식의 문자열로 변환
        #    · json.dump(파일저장)과 구분: dumps = dump to String (문자열 반환)

        if resp.status_code == 200:  # HTTP 200 = 성공 응답
            return resp.json()       # JSON 응답을 파이썬 딕셔너리로 변환해 반환
            #  └ resp.json()
            #    · 기본문법: Response.json()
            #    · 응답 body의 JSON 문자열 → 파이썬 딕셔너리/리스트로 파싱
            #    · resp.text는 문자열 그대로, resp.json()은 파이썬 객체로 변환

        print(f"  API {resp.status_code}: {resp.text[:200]} (재시도 {attempt+1}/{retries})")
        time.sleep(2 ** attempt)  # 지수 백오프: 1초, 2초, 4초 대기
        #  └ 2 ** attempt (거듭제곱 연산자)
        #    · 기본문법: 밑 ** 지수
        #    · attempt=0: 2^0=1초, attempt=1: 2^1=2초, attempt=2: 2^2=4초
        #    · 지수 백오프(Exponential Backoff): 실패할수록 대기 시간을 2배씩 늘려
        #      서버 과부하 방지 및 일시적 오류 자연 해소를 기다리는 전략

    raise Exception(f"DataLab API 호출 실패: {resp.status_code}")
    #  └ raise Exception(메시지)
    #    · 기본문법: raise 예외클래스(메시지)
    #    · 예외를 직접 발생시켜 프로그램 흐름을 중단하고 호출한 쪽에서 처리하도록 전달
    #    · try-except로 잡지 않으면 프로그램 종료 + 오류 메시지 출력


def parse_result(result):
    """API 응답에서 {그룹명: {월: 비율}} 형태로 파싱"""
    out = {}
    for item in result['results']:  # 각 키워드 그룹의 결과를 순회
        out[item['title']] = {d['period'][:7]: d['ratio'] for d in item['data']}
        #  └ 딕셔너리 컴프리헨션 {키: 값 for 원소 in iterable}
        #    · 기본문법: {키_표현식: 값_표현식 for 변수 in iterable}
        #    · 리스트 컴프리헨션과 유사하지만 {} 로 감싸고 키:값 쌍 생성
        #    · d['period'][:7]: 'YYYY-MM-DD' 형식 문자열에서 앞 7글자만 ('YYYY-MM')
        #    · d['ratio']: 해당 월의 검색 비율 (0~100 범위의 상대값)
        #    · 결과 예시: {'2023-07': 45.2, '2023-08': 52.1, '2023-09': 48.7, ...}
    return out  # {그룹명: {YYYY-MM: ratio}} 형태의 중첩 딕셔너리 반환


# ══════════════════════════════════════════════════════
# 1. 앵커(성수 카페) 단독 호출
# ══════════════════════════════════════════════════════
print("▶ 앵커(성수 카페) 단독 baseline 수집 중...")
anchor_result = call_datalab([{'groupName': '성수 카페', 'keywords': ['성수 카페']}])
#  └ keyword_groups 파라미터 구조: 리스트[딕셔너리] 형태
#    · groupName: 그룹 이름 (API 응답에서 title로 반환됨, 나중에 parse_result에서 키로 사용)
#    · keywords: 해당 그룹에 포함할 키워드 목록 (여러 개 가능, OR 조건으로 합산)
#    · 여기서는 앵커 혼자만 호출해 '단독' 기준값(baseline) 수집

anchor_solo = parse_result(anchor_result)['성수 카페']  # 앵커의 월별 검색 비율 딕셔너리
#  └ parse_result(anchor_result): {그룹명: {월: 비율}} 반환
#  └ ['성수 카페']: 그룹명 '성수 카페'에 해당하는 {월: 비율} 딕셔너리 선택
print(f"  앵커 월별 데이터: {len(anchor_solo)}개월")
time.sleep(0.5)  # API 호출 간격 대기 (연속 호출로 인한 rate limit 방지)
#  └ time.sleep(초)
#    · 기본문법: time.sleep(secs)
#    · 지정한 초만큼 실행을 일시 정지
#    · API rate limit: 단위 시간당 허용 호출 수 초과 시 차단됨 → sleep으로 방지


# ══════════════════════════════════════════════════════
# 2. 역명 목록 로드
# ══════════════════════════════════════════════════════
to_map   = pd.read_csv('to_map_with_station.csv')  # 상권↔역 매핑 파일 로드
#  └ pd.read_csv(파일경로)
#    · 기본문법: pd.read_csv(filepath, encoding=None, sep=',', header=0)
#    · CSV 파일을 읽어 DataFrame으로 반환
#    · encoding 미지정 시 기본값 'utf-8' 사용

stations = sorted(to_map['최근접_역명'].unique())  # 유니크 역명 정렬 목록
#  └ Series.unique()
#    · 기본문법: Series.unique()
#    · 시리즈의 고유값만 담은 NumPy 배열 반환 (중복 제거)
#    · set()으로 중복 제거와 유사하지만 pandas Series에서 더 효율적
#    · 반환: numpy.ndarray (순서는 처음 등장 순서)
#
#  └ sorted(iterable)
#    · 기본문법: sorted(iterable, key=None, reverse=False)
#    · NumPy 배열을 정렬된 파이썬 리스트로 반환
#    · 이후 배치 슬라이싱([i:i+4])을 위해 리스트 형태로 변환

print(f"▶ 고유 역명: {len(stations)}개")


# ══════════════════════════════════════════════════════
# 3. 배치(4개씩) API 호출
# ══════════════════════════════════════════════════════
BATCH_SIZE = 4  # 앵커 포함 5그룹 = API 최대 허용 수 (4개 역명 + 앵커 1개)
batches    = [stations[i:i+BATCH_SIZE] for i in range(0, len(stations), BATCH_SIZE)]
#  └ 리스트 컴프리헨션으로 배치 분할
#    · stations[i:i+4]: i번째부터 i+4번째 미만까지의 부분 리스트 (슬라이싱)
#    · range(0, len(stations), 4): 0, 4, 8, 12, ... 처럼 4씩 건너뛰는 정수 시퀀스
#    · 결과: [[역1,역2,역3,역4], [역5,역6,역7,역8], ...] 형태의 중첩 리스트

print(f"▶ {len(batches)}개 배치 처리 시작\n")

all_station_monthly = {}  # {역명: {YYYY-MM: 정규화된 검색량}} 저장용 딕셔너리

for idx, batch in enumerate(batches):  # 배치 인덱스와 배치 내용을 함께 순회
    keyword_groups = [{'groupName': '성수 카페', 'keywords': ['성수 카페']}]  # 앵커 항상 첫 그룹에 포함
    for stn in batch:
        keyword_groups.append({'groupName': stn, 'keywords': [f'{stn} 카페']})
        #  └ list.append(원소)
        #    · 기본문법: list.append(object)
        #    · 리스트 끝에 원소 1개 추가 (원본 수정, 반환값 없음)
        #    · list.extend(리스트)와 차이: append는 요소 1개, extend는 리스트를 이어붙임
        #    · 예: [].append([1,2]) → [[1,2]] / [].extend([1,2]) → [1,2]

    try:
        result       = call_datalab(keyword_groups)  # API 호출 (앵커 + 4개 역명)
        parsed       = parse_result(result)          # 응답 파싱 → {그룹명: {월: 비율}}
        anchor_batch = parsed.get('성수 카페', {})   # 이 배치 내에서의 앵커 비율
        #  └ dict.get(키, 기본값)
        #    · 기본문법: dict.get(key, default=None)
        #    · 키가 없으면 기본값 반환 (KeyError 발생 없음)
        #    · dict[키]는 없으면 KeyError 발생, .get()은 안전한 접근 방식

        for stn in batch:
            stn_data   = parsed.get(stn, {})  # 해당 역의 월별 비율 딕셔너리
            normalized = {}
            for period, a_solo in anchor_solo.items():  # 앵커 단독 기준 월별로 정규화
                a_batch = anchor_batch.get(period)  # 같은 배치 내 앵커의 해당 월 비율
                s_batch = stn_data.get(period)      # 같은 배치 내 역의 해당 월 비율
                if a_batch and a_batch > 0 and s_batch is not None and a_solo is not None:
                    normalized[period] = (s_batch / a_batch) * a_solo
                    # 정규화 공식: (역_비율 / 앵커_비율) × 앵커_단독_비율
                    # 이유: 배치마다 앵커의 기준값이 달라지는 문제를
                    #       단독 호출 앵커값(앵커_단독_비율)으로 보정하여 전체 일관성 유지
                else:
                    normalized[period] = np.nan  # 계산 불가 시 NaN으로 채움
                    #  └ np.nan
                    #    · NumPy의 NaN(Not a Number) 값
                    #    · 결측값 표현에 사용 (None과 달리 수치 계산에서 무시 가능)
                    #    · np.isnan(값): 값이 NaN이면 True

            all_station_monthly[stn] = normalized  # 해당 역의 정규화 결과 저장

        print(f"  배치 {idx+1:3d}/{len(batches)} 완료: {batch}")

    except Exception as e:  # API 호출 실패 시
        print(f"  배치 {idx+1} 오류: {e} → NaN 채움")
        for stn in batch:
            all_station_monthly[stn] = {p: np.nan for p in anchor_solo}
            #  └ 딕셔너리 컴프리헨션 {키: 값 for 원소 in iterable}
            #    · 오류 난 배치의 역들은 모든 월을 NaN으로 채워 후속 처리에서 보간

    time.sleep(0.5)  # 배치 간 대기 (0.5초)


# ══════════════════════════════════════════════════════
# 4. 월별 → 분기별 평균 산출
# ══════════════════════════════════════════════════════
print("\n▶ 분기별 평균 산출 중...")
records = []
for stn, monthly in all_station_monthly.items():  # {역명: {월: 비율}} 역명별 순회
    #  └ dict.items()
    #    · 기본문법: dict.items()
    #    · 딕셔너리의 (키, 값) 쌍을 담은 view 객체 반환
    #    · for k, v in dict.items(): k=키, v=값으로 동시 접근

    by_q = {q: [] for q in QUARTERS}  # 분기별 빈 리스트 초기화
    #  └ 딕셔너리 컴프리헨션
    #    · {20232: [], 20233: [], 20234: ...} 형태로 각 분기에 빈 리스트 생성
    #    · 이후 각 월 데이터를 해당 분기 리스트에 append해서 분기 내 평균 계산에 활용

    for period, ratio in monthly.items():  # 월별 비율 순회
        q = QUARTER_MAP.get(period)        # 해당 월이 속하는 분기 코드
        if q and not np.isnan(ratio):
            #  └ np.isnan(값)
            #    · 기본문법: numpy.isnan(x)
            #    · 값이 NaN이면 True, 유효한 숫자면 False
            #    · not np.isnan(ratio): NaN이 아닌 유효한 값일 때만 추가
            by_q[q].append(ratio)  # 해당 분기의 비율 리스트에 추가

    row = {'역명': stn}
    for q in QUARTERS:
        row[q] = np.mean(by_q[q]) if by_q[q] else np.nan  # 분기 내 월별 평균
        #  └ np.mean(배열)
        #    · 기본문법: numpy.mean(a, axis=None)
        #    · 배열의 평균값 계산 (모든 원소의 합 / 원소 수)
        #    · by_q[q]가 빈 리스트([])이면 계산 불가 → np.nan 저장
    records.append(row)  # 역명별 분기 평균 행을 records에 추가

station_qdf = pd.DataFrame(records)  # 딕셔너리 리스트 → 역명 × 분기 형태의 DataFrame 생성
#  └ pd.DataFrame(데이터)
#    · 기본문법: pd.DataFrame(data, index=None, columns=None)
#    · 딕셔너리 리스트(records)를 받아 DataFrame으로 변환
#    · 각 딕셔너리의 키가 컬럼명, 값이 셀 값이 됨


# ══════════════════════════════════════════════════════
# NaN 후처리
# ══════════════════════════════════════════════════════

# 보정 1: 경의중앙 신촌역 → 신촌역 데이터로 대체 (검색어로 의미 없는 역명)
shinchon_row = station_qdf[station_qdf['역명'] == '신촌역']  # 2호선 신촌역 데이터 행 추출
if not shinchon_row.empty:  # 신촌역 데이터가 있으면
    #  └ DataFrame.empty
    #    · 기본문법: DataFrame.empty (속성, 괄호 없음)
    #    · DataFrame에 행이 하나도 없으면 True
    #    · not df.empty: 데이터가 있을 때 실행

    for q in QUARTERS:
        station_qdf.loc[station_qdf['역명'] == '경의중앙 신촌역', q] = shinchon_row.iloc[0][q]
        #  └ df.loc[조건, 컬럼]
        #    · 기본문법: DataFrame.loc[행_조건, 컬럼명]
        #    · 조건에 맞는 행의 특정 컬럼 값을 가져오거나 설정(할당)
        #    · .loc: 라벨(이름) 기반 인덱싱 (.iloc은 위치 기반)
        #    · = 할당 시: 조건에 해당하는 행들의 컬럼 값을 일괄 변경
        #
        #  └ DataFrame.iloc[행_번호]
        #    · 기본문법: DataFrame.iloc[0] → 첫 번째 행 (Series 반환)
        #    · 위치(정수) 기반 인덱싱 (.loc은 라벨 기반)
        #    · .iloc[0][q]: 첫 번째 행의 q 컬럼 값
    print("  [보정] 경의중앙 신촌역 → 신촌역 데이터로 대체 완료")

# 보정 2: 나머지 역 부분 NaN → 선형 보간 (앞뒤 값으로 추정)
q_cols = QUARTERS
station_qdf[q_cols] = (
    station_qdf.set_index('역명')[q_cols]  # 역명을 인덱스로 설정 (분기 컬럼만 남김)
    #  └ DataFrame.set_index(컬럼)
    #    · 기본문법: DataFrame.set_index(keys, drop=True)
    #    · 지정 컬럼을 DataFrame의 행 인덱스(레이블)로 설정
    #    · 원본은 변경하지 않고 새 DataFrame 반환

               .T                  # 전치: 행↔열 교환 (분기가 행이 되고 역명이 열이 됨)
    #  └ DataFrame.T
    #    · 기본문법: DataFrame.T (속성, 괄호 없음)
    #    · DataFrame의 행과 열을 서로 교환 (전치 행렬, Transpose)
    #    · 전치 전: 행=역명, 열=분기 / 전치 후: 행=분기, 열=역명
    #    · interpolate는 열 방향(axis=0)으로 동작하므로
    #      역명별로 시계열 보간하려면 분기를 행으로 전치해야 함

               .interpolate(method='linear', limit_direction='both')  # 선형 보간
    #  └ DataFrame.interpolate(method, limit_direction)
    #    · 기본문법: DataFrame.interpolate(method='linear', limit_direction='forward')
    #    · NaN 값을 앞뒤 유효한 값 사이를 직선으로 이어 추정
    #    · method='linear': 선형 보간 (이전값과 다음값을 직선으로 연결)
    #    · limit_direction='both': 양방향 보간
    #      - 'forward': 앞에서 뒤로만 (NaN 앞에 값 있어야 함)
    #      - 'backward': 뒤에서 앞으로만
    #      - 'both': 양방향 모두 → 시작/끝 NaN도 처리
    #    · 현재 상태: 분기가 행 → 각 역명(열)에 대해 시간 순서(행)로 보간

               .T                  # 다시 전치 (원래 방향으로 복구: 행=역명, 열=분기)
               .values             # NumPy 배열로 변환 (DataFrame에 다시 대입하기 위해)
    #  └ DataFrame.values
    #    · 기본문법: DataFrame.values (속성)
    #    · DataFrame의 데이터를 NumPy ndarray로 반환
    #    · 인덱스/컬럼명 없이 순수 데이터만 반환
)
nan_left = station_qdf[q_cols].isna().sum().sum()  # 보간 후 잔여 NaN 수 확인
#  └ DataFrame.isna()
#    · 기본문법: DataFrame.isna() 또는 DataFrame.isnull() (동일)
#    · 각 원소가 NaN이면 True, 값이 있으면 False인 Boolean DataFrame 반환
#
#  └ .sum()
#    · 첫 번째 .sum(): 각 컬럼별 True(=NaN) 개수 합산 → Series 반환
#    · 두 번째 .sum(): Series의 모든 값을 합산 → 전체 NaN 개수
print(f"  [보정] 선형 보간 후 잔여 NaN: {nan_left}개")

# 저장 시 20232 컬럼은 제외 (QoQ 계산용으로만 사용했으므로)
save_cols = ['역명'] + QUARTERS_OUTPUT  # 역명 컬럼 + 저장 대상 분기 컬럼 목록
station_qdf[save_cols].to_csv('search_trend_raw.csv', index=False, encoding='utf-8-sig')
#  └ DataFrame.to_csv(경로, index, encoding)
#    · 기본문법: DataFrame.to_csv(path_or_buf, sep=',', index=True, encoding=None)
#    · index=False: 행 번호(0,1,2...)를 CSV에 포함하지 않음
#    · encoding='utf-8-sig': BOM 포함 UTF-8 → 엑셀에서 한글 안 깨짐
print(f"  역명×분기 저장: search_trend_raw.csv {station_qdf[save_cols].shape}")


# ══════════════════════════════════════════════════════
# 5. 상권×분기 패널 생성
# ══════════════════════════════════════════════════════
print("\n▶ 상권×분기 패널 생성 중...")
mapping  = to_map[['상권_코드', '최근접_역명']].copy()  # 상권↔역 매핑 테이블만 추출
#  └ DataFrame.copy()
#    · 기본문법: DataFrame.copy(deep=True)
#    · DataFrame의 복사본 생성 (원본과 독립적인 새 객체)
#    · deep=True(기본): 데이터까지 완전 복사 (원본 변경해도 복사본에 영향 없음)
#    · deep=False: 구조만 복사 (얕은 복사)

stn_dict = station_qdf.set_index('역명').to_dict('index')  # {역명: {분기: ratio}} 딕셔너리
#  └ DataFrame.set_index('컬럼')
#    · 기본문법: DataFrame.set_index(keys)
#    · 지정 컬럼을 DataFrame 인덱스로 설정 (컬럼은 인덱스로 이동)
#
#  └ DataFrame.to_dict('index')
#    · 기본문법: DataFrame.to_dict(orient='dict')
#    · orient='index': {행인덱스: {컬럼명: 값}} 형태의 중첩 딕셔너리로 변환
#    · 예: {'홍대입구역': {20233: 45.2, 20234: 38.1, ...}, ...}
#    · 이후 stn_dict['홍대입구역'][20233] 처럼 O(1) 속도로 빠르게 접근 가능

rows = []
for _, r in mapping.iterrows():  # 상권↔역 매핑 DataFrame을 행 단위로 순회
    #  └ DataFrame.iterrows()
    #    · 기본문법: DataFrame.iterrows()
    #    · 각 행을 (인덱스, Series) 튜플로 반환하는 이터레이터
    #    · _ : 인덱스(사용 안 함) / r: 해당 행의 Series
    #    · 주의: 대용량 데이터에서는 느림 → 소규모 매핑에 적합

    코드 = r['상권_코드']    # 해당 상권의 코드
    역명 = r['최근접_역명']  # 해당 상권과 가장 가까운 역명
    vals = stn_dict.get(역명, {})  # 해당 역의 분기별 검색지수 딕셔너리 (없으면 빈 딕셔너리)
    for q in QUARTERS:  # 20232 포함 전체 분기 (QoQ 계산용으로 필요)
        rows.append({
            '기준_년분기_코드': q,
            '상권_코드'       : 코드,
            '카페_검색지수'   : vals.get(q, np.nan),  # 해당 분기의 검색지수 (없으면 NaN)
        })

panel = pd.DataFrame(rows).sort_values(['상권_코드', '기준_년분기_코드']).reset_index(drop=True)
#  └ DataFrame.sort_values(컬럼목록)
#    · 기본문법: DataFrame.sort_values(by, ascending=True, na_position='last')
#    · 여러 컬럼 목록으로 정렬: 첫 번째 컬럼 기준 정렬 후, 같은 값은 두 번째 컬럼 기준
#    · ascending=True(기본): 오름차순 / ascending=False: 내림차순
#
#  └ .reset_index(drop=True)
#    · 기본문법: DataFrame.reset_index(drop=False)
#    · 정렬 후 흐트러진 행 인덱스를 0부터 순서대로 재설정
#    · drop=True: 기존 인덱스를 컬럼으로 추가하지 않고 버림


# QoQ(전분기 대비) 성장률 계산
panel['검색량_성장률'] = (
    panel.sort_values(['상권_코드', '기준_년분기_코드'])  # 상권별, 시간순 정렬
         .groupby('상권_코드')['카페_검색지수']           # 상권별 그룹화 후 검색지수 선택
         .pct_change(fill_method=None) * 100              # 전분기 대비 % 변화율
    #  └ Series.pct_change(fill_method)
    #    · 기본문법: Series.pct_change(periods=1, fill_method='pad', limit=None)
    #    · 이전 값 대비 현재 값의 변화율 계산: (현재 - 이전) / 이전
    #    · fill_method=None: NaN을 채우지 않고 그대로 계산
    #      (기본값 'pad'는 NaN을 이전 값으로 채운 후 계산 → 왜곡 방지를 위해 None 사용)
    #    · × 100: 소수(비율)를 % 단위로 변환 (0.15 → 15%)
    #    · 첫 행(이전 분기 없음): NaN
)

# 20232는 성장률 계산용이었으므로 저장 시 제외
panel = panel[panel['기준_년분기_코드'].isin(QUARTERS_OUTPUT)].reset_index(drop=True)
#  └ Series.isin(값목록)
#    · 기본문법: Series.isin(values)
#    · 시리즈의 각 원소가 values 목록에 있으면 True인 Boolean Series 반환
#    · df['컬럼'].isin([값1, 값2]) = (df['컬럼']==값1) | (df['컬럼']==값2) 와 동일
#    · 여러 값 필터링 시 == 조건 여러 개 OR 연결보다 간결함

panel.to_csv('search_trend_index.csv', index=False, encoding='utf-8-sig')  # 최종 저장
print(f"  상권×분기 저장: search_trend_index.csv {panel.shape}")
print(panel.head(10).to_string(index=False))
#  └ DataFrame.head(n)
#    · 기본문법: DataFrame.head(n=5)
#    · 상위 n행만 반환 (기본값 5)
#    · 데이터 미리보기에 사용
#
#  └ DataFrame.to_string(index=False)
#    · 기본문법: DataFrame.to_string(buf=None, index=True)
#    · DataFrame을 터미널 출력용 문자열로 변환
#    · index=False: 행 번호(0,1,2...) 없이 데이터만 출력
