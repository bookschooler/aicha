"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
18b_filter_by_blog.py — 네이버 블로그 API로 찻집 필터링
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  18번에서 수집된 찻집 후보들 중 '찻잎차' 전문점인지 확인
  → 찻잎차 언급 0 + 한방차 언급 있으면 한방차 가게로 제거 후보로 플래그

흐름:
  - 가게명 + 찻잎차 키워드 → 네이버 블로그 검색 → 언급 수 카운트
  - 가게명 + 한방차 키워드 → 네이버 블로그 검색 → 언급 수 카운트
  - 분류: KEEP(찻잎차 언급 있음) / REMOVE(한방차만) / UNKNOWN(둘 다 없음)

입력: tea_shops_dedup.csv
출력: tea_shops_scored.csv
"""

import pandas as pd   # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(파일명): CSV 파일을 읽어 DataFrame으로 반환
#    · Series.tolist(): pandas Series → 파이썬 리스트 변환
#    · Series.map(함수): 각 원소에 함수를 적용해 새 Series 반환
#    · Series.value_counts(): 각 값의 등장 횟수를 내림차순으로 반환
#    · df.apply(함수, axis=1): 각 행에 함수를 적용해 새 Series 반환
#    · df.to_csv(경로, index=False, encoding='utf-8-sig'): CSV 파일로 저장
#    · df[조건]: Boolean Indexing — 조건이 True인 행만 필터링
#    · df[['컬럼1', '컬럼2']]: 이중 대괄호로 여러 컬럼 동시 선택

import requests       # HTTP API 요청 전송 라이브러리
#  └ [requests 라이브러리]
#    · pip install requests 로 설치
#    · requests.get(url, headers, params, timeout): GET 방식 HTTP 요청 전송
#      · GET: 데이터를 URL 쿼리스트링에 담음 (조회/검색에 사용)
#    · 반환: Response 객체
#      · resp.status_code: HTTP 응답 코드 (200=성공, 401=인증실패, 429=rate limit 등)
#      · resp.json(): 응답 body의 JSON → 파이썬 딕셔너리로 변환
#    · timeout=5: 5초 내 응답 없으면 예외 발생 (무한 대기 방지)

import os             # 파일 경로 및 환경변수 접근용 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.getenv(키, 기본값=None): 환경변수 값 반환 (없으면 None, KeyError 없음)
#    · os.environ["키"]: 환경변수 접근 (없으면 KeyError 발생)
#    · os.path.exists(경로): 파일/폴더 존재 여부 확인 → True/False

import time           # 시간 지연 처리용 내장 모듈
#  └ [time 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · time.sleep(초): 지정한 초만큼 실행을 일시 정지
#    · API 호출 사이에 sleep을 두어 서버 과부하 및 rate limit 위반 방지
#    · 네이버 블로그 API: 초당 10회 제한 → 0.12초 간격으로 호출

import json           # JSON 형식 데이터 변환용 내장 모듈
#  └ [json 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · json.load(파일객체): JSON 파일 → 파이썬 딕셔너리로 읽기
#    · json.dump(객체, 파일, ensure_ascii=False, indent=2): 파이썬 객체 → JSON 파일로 저장
#    · ensure_ascii=False: 한글을 유니코드 이스케이프 없이 그대로 저장
#    · indent=2: JSON을 2칸 들여쓰기로 보기 좋게 저장

from dotenv import load_dotenv  # .env 파일에서 환경변수 로드하는 라이브러리
#  └ [python-dotenv 라이브러리]
#    · pip install python-dotenv 로 설치
#    · load_dotenv(): 현재 디렉토리의 .env 파일을 읽어 환경변수로 등록
#    · .env 파일 예시: NAVER_CLIENT_ID=abc123
#    · 호출 후 os.getenv()로 해당 값에 접근 가능
#    · API 키 등 민감 정보를 코드에 직접 쓰지 않기 위해 사용 (보안)

load_dotenv()  # .env 파일 읽기

# 네이버 API 인증 정보
CLIENT_ID     = os.getenv('NAVER_CLIENT_ID')      # 네이버 클라이언트 ID
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')  # 네이버 클라이언트 시크릿
#  └ os.getenv(키, 기본값=None)
#    · 기본문법: os.getenv(key, default=None)
#    · 환경변수 값 반환, 없으면 None 반환 (KeyError 발생 없음)
#    · os.environ["키"]와 달리 없어도 오류 안 남 → 안전한 접근 방식
#    · 반환된 None 그대로 사용하면 API 요청 시 인증 오류 발생

HEADERS = {
    'X-Naver-Client-Id':     CLIENT_ID,     # 네이버 API 인증 헤더
    'X-Naver-Client-Secret': CLIENT_SECRET, # 네이버 API 시크릿 헤더
}

# 찻잎차 관련 키워드 (이 키워드 언급 많을수록 찻잎차 전문점 → KEEP)
LEAF_KEYWORDS = ['녹차', '홍차', '우롱차', '보이차', '백차', '황차', '다원', '티하우스']

# 한방차 관련 키워드 (찻잎차 언급 없고 이것만 있으면 한방차 가게 → REMOVE 후보)
HERB_KEYWORDS = ['쌍화차', '생강차', '한방차', '대추차', '모과차', '한방']

PROGRESS_FILE = 'blog_filter_progress.json'  # 진행 상황 저장 파일명


# ══════════════════════════════════════════════════════
# 네이버 블로그 검색 함수
# ══════════════════════════════════════════════════════
def search_blog_count(query: str) -> int:
    """가게명 + 키워드로 네이버 블로그 검색 → 검색 결과 총 건수 반환"""
    url    = 'https://openapi.naver.com/v1/search/blog'  # 네이버 블로그 검색 API URL
    params = {'query': query, 'display': 1}              # 결과 1건만 받음 (total 수만 필요)
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=5)
        #  └ requests.get(url, headers, params, timeout)
        #    · 기본문법: requests.get(url, headers=None, params=None, timeout=None)
        #    · GET 방식 HTTP 요청 전송
        #    · headers: 딕셔너리로 요청 헤더 추가 (네이버 API 인증 헤더 포함)
        #    · params: 딕셔너리 → 자동으로 URL 쿼리스트링으로 변환
        #    · 네이버 블로그 검색: 실제 블로그 글 내용보다 total(총 검색 건수)만 사용

        if resp.status_code == 200:  # HTTP 200 = 성공
            return resp.json().get('total', 0)  # 총 검색 결과 수 반환 (없으면 0)
            #  └ resp.status_code
            #    · 기본문법: Response.status_code (속성)
            #    · HTTP 응답 코드 (200=성공, 400=요청오류, 401=인증실패, 429=rate limit 등)
            #
            #  └ resp.json().get('total', 0)
            #    · resp.json(): 응답 body JSON → 파이썬 딕셔너리로 변환
            #    · .get('total', 0): 'total' 키 없으면 0 반환 (안전한 접근)

    except Exception:
        pass  # 오류 발생 시 무시하고 -1 반환
    return -1  # 오류 시 -1 반환 (0건과 구분하기 위해)


def score_shop(name: str) -> dict:
    """한 가게에 대해 찻잎차/한방차 키워드별 블로그 언급 수 집계"""
    leaf_total = 0  # 찻잎차 키워드 총 언급 수
    herb_total = 0  # 한방차 키워드 총 언급 수

    for kw in LEAF_KEYWORDS:
        cnt = search_blog_count(f'{name} {kw}')  # 예: "차마시는 뜰 녹차" 검색
        if cnt > 0:
            leaf_total += cnt
        time.sleep(0.12)  # 네이버 API rate limit 준수 (초당 10회)
        #  └ time.sleep(초)
        #    · 기본문법: time.sleep(secs)
        #    · 0.12초 = 약 8회/초 → 네이버 API 허용 한도(10회/초) 안에 유지

    for kw in HERB_KEYWORDS:
        cnt = search_blog_count(f'{name} {kw}')  # 예: "차마시는 뜰 쌍화차" 검색
        if cnt > 0:
            herb_total += cnt
        time.sleep(0.12)

    return {'leaf_count': leaf_total, 'herb_count': herb_total}  # 결과 딕셔너리 반환


# ══════════════════════════════════════════════════════
# 진행 상황 로드 (중단 후 재시작 지원)
# ══════════════════════════════════════════════════════
if os.path.exists(PROGRESS_FILE):  # 이전 진행 파일 있으면
    #  └ os.path.exists(경로)
    #    · 기본문법: os.path.exists(path)
    #    · 파일 또는 폴더가 존재하면 True, 없으면 False

    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        #  └ with open(파일, mode, encoding) as f:
        #    · 기본문법: open(file, mode='r', encoding=None)
        #    · 파일을 열고 블록 종료 시 자동으로 닫음 (f.close() 불필요)
        #    · 'r' = 읽기 모드, 'w' = 쓰기(덮어쓰기), 'a' = 추가 쓰기

        progress = json.load(f)  # JSON 파일 → 파이썬 딕셔너리로 읽기
        #  └ json.load(파일객체)
        #    · 기본문법: json.load(fp)
        #    · 파일에서 JSON을 읽어 파이썬 객체(dict/list)로 변환
        #    · json.loads(문자열)과 구분: load는 파일, loads는 문자열

    print(f"이전 진행 로드: {len(progress)}개 완료")
else:
    progress = {}  # 처음 실행이면 빈 딕셔너리

df    = pd.read_csv('tea_shops_dedup.csv')  # 중복 제거된 찻집 목록 로드
names = df['가게명'].tolist()               # 가게명만 리스트로 추출
#  └ Series.tolist()
#    · 기본문법: Series.tolist()
#    · pandas Series를 파이썬 리스트로 변환

remaining = [n for n in names if n not in progress]  # 아직 처리 안 된 가게만
#  └ 리스트 컴프리헨션 (조건부 필터링)
#    · 기본문법: [표현식 for 변수 in iterable if 조건]
#    · if n not in progress: progress 딕셔너리 키에 없는 가게명만 포함
#    · dict의 in 연산: 키(key)를 검색 → O(1) 빠른 조회

print(f"남은 가게: {len(remaining)}개 / 전체 {len(names)}개")
print(f"예상 소요: 약 {len(remaining) * 15 / 60:.0f}분\n")
#  └ f-string 안의 :.0f
#    · 기본문법: f"{값:.소수점자리f}"
#    · :.0f: 소수점 0자리까지만 표시 (정수처럼 출력)
#    · :.2f: 소수점 2자리까지 표시


# ══════════════════════════════════════════════════════
# 스코어링 실행
# ══════════════════════════════════════════════════════
for i, name in enumerate(remaining, 1):
    #  └ enumerate(iterable, start=0)
    #    · 기본문법: enumerate(iterable, start=0)
    #    · 각 원소에 순번을 붙여 (번호, 원소) 튜플로 반환
    #    · start=1: 번호를 1부터 시작

    result   = score_shop(name)     # 가게 하나씩 찻잎차/한방차 언급 수 집계
    progress[name] = result         # 결과를 딕셔너리에 저장 (가게명 → 결과)

    # 분류 결과 플래그 결정
    flag = ''
    if result['leaf_count'] == 0 and result['herb_count'] > 0:
        flag = '⚠️ 제거후보'      # 한방차만 있음 → 제거 후보
    elif result['leaf_count'] == 0 and result['herb_count'] == 0:
        flag = '❓ 정보없음'      # 블로그 언급 없음 → 수동 확인 필요

    print(f"[{i:3d}/{len(remaining)}] {name:25s} | "
          f"찻잎:{result['leaf_count']:6d} | 한방:{result['herb_count']:5d} {flag}")
    #  └ f-string 포맷 지정자
    #    · {:3d}: 정수를 최소 3자리로 (앞에 공백 패딩, 숫자 정렬용)
    #    · {:25s}: 문자열을 최소 25자리로 (뒤에 공백 패딩, 컬럼 정렬용)
    #    · {:6d}: 정수를 최소 6자리로

    if i % 10 == 0:  # 10개마다 진행 상황 저장
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
            #  └ json.dump(객체, 파일, ensure_ascii=False, indent=2)
            #    · 기본문법: json.dump(obj, fp, ensure_ascii=True, indent=None)
            #    · 파이썬 객체(딕셔너리 등)를 JSON 형식으로 파일에 저장
            #    · ensure_ascii=False: 한글을 \uXXXX 이스케이프 없이 그대로 저장
            #    · indent=2: JSON을 2칸 들여쓰기로 보기 좋게 정렬

# 최종 저장 (전체 완료 후)
with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
    json.dump(progress, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════
# 결과 정리 & 저장
# ══════════════════════════════════════════════════════
df['leaf_count'] = df['가게명'].map(lambda n: progress.get(n, {}).get('leaf_count', -1))
df['herb_count'] = df['가게명'].map(lambda n: progress.get(n, {}).get('herb_count', -1))
#  └ Series.map(함수 또는 딕셔너리)
#    · 기본문법: Series.map(arg, na_action=None)
#    · 시리즈의 각 원소에 함수를 적용해 새 Series 반환
#    · lambda n: progress.get(n, {}).get('leaf_count', -1)
#      → 가게명(n)으로 progress 딕셔너리를 조회
#      → 없으면 {} → 그 안에서 'leaf_count' 조회, 없으면 -1 반환
#    · 연쇄된 .get() 호출: 중첩 딕셔너리를 안전하게 접근 (KeyError 없음)


def classify(row):
    """찻잎/한방 언급 수 기반으로 가게 분류"""
    if row['leaf_count'] > 0:
        return 'KEEP'    # 찻잎차 언급 있음 → 유지
    elif row['herb_count'] > 0:
        return 'REMOVE'  # 찻잎차 없고 한방차만 → 제거
    else:
        return 'UNKNOWN' # 둘 다 없음 → 수동 확인


df['filter_result'] = df.apply(classify, axis=1)
#  └ df.apply(함수, axis=1)
#    · 기본문법: DataFrame.apply(func, axis=0)
#    · axis=1: 각 행에 함수 적용 (axis=0이면 각 열에 적용)
#    · 함수는 각 행(Series)을 받아 반환값으로 새 컬럼 값 생성
#    · 결과: 'KEEP', 'REMOVE', 'UNKNOWN' 중 하나가 각 행에 할당

print('\n=== 분류 결과 ===')
print(df['filter_result'].value_counts().to_string())
#  └ Series.value_counts()
#    · 기본문법: Series.value_counts(normalize=False, sort=True)
#    · 각 값의 등장 횟수를 내림차순으로 반환
#    · to_string(): 전체를 잘리지 않고 문자열로 출력

print('\n[제거 후보]')
print(df[df['filter_result'] == 'REMOVE'][['가게명', 'leaf_count', 'herb_count']].to_string(index=False))
#  └ df[조건]
#    · 기본문법: df[Boolean Series]
#    · 조건이 True인 행만 필터링 (Boolean Indexing)
#    · df['filter_result'] == 'REMOVE': 각 행이 'REMOVE'인지 확인 → Boolean Series
#
#  └ df[['컬럼1', '컬럼2', '컬럼3']]
#    · 기본문법: df[리스트_of_컬럼명]
#    · 이중 대괄호로 여러 컬럼 동시 선택 (결과는 DataFrame)
#    · 단일 컬럼 선택: df['컬럼'] → Series / 다중 선택: df[['컬럼']] → DataFrame
#
#  └ .to_string(index=False)
#    · 기본문법: DataFrame.to_string(index=True)
#    · DataFrame 전체를 잘리지 않고 문자열로 출력
#    · index=False: 행 번호(0,1,2...) 없이 데이터만 출력

print('\n[정보 없음 (수동 확인 필요)]')
print(df[df['filter_result'] == 'UNKNOWN'][['가게명', 'leaf_count', 'herb_count']].to_string(index=False))

df.to_csv('tea_shops_scored.csv', index=False, encoding='utf-8-sig')  # 분류 결과 저장
#  └ df.to_csv(경로, index=False, encoding='utf-8-sig')
#    · 기본문법: DataFrame.to_csv(path, sep=',', index=True, encoding=None)
#    · index=False: 행 번호를 CSV에 포함하지 않음
#    · encoding='utf-8-sig': BOM 포함 UTF-8 → 엑셀에서 한글 안 깨짐
print('\n[저장] tea_shops_scored.csv')
