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

import pandas as pd   # 데이터프레임 라이브러리
import requests       # HTTP API 요청 라이브러리 (17번에서 상세 설명)
import os             # 파일 경로, 환경변수 관련 (17번에서 상세 설명)
import time           # API 호출 간격 조절용 (17번에서 상세 설명)
import json           # JSON 파일 읽기/쓰기 (18번에서 상세 설명)
from dotenv import load_dotenv  # .env 파일 환경변수 로드 (17번에서 상세 설명)

load_dotenv()  # .env 파일 읽기

# 네이버 API 인증 정보
CLIENT_ID     = os.getenv('NAVER_CLIENT_ID')      # 네이버 클라이언트 ID
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')  # 네이버 클라이언트 시크릿
#  └ os.getenv(키, 기본값=None)
#    · 환경변수 값 반환, 없으면 None (KeyError 없음)
#    · os.environ["키"]와 달리 없어도 오류 안 남

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
        #  └ requests.get() : GET 방식 HTTP 요청 (17번에서 상세 설명)
        #    · 여기서는 카카오 대신 네이버 API에 요청
        #    · 결과에서 실제 블로그 글 내용보다 total(총 검색 건수)만 사용

        if resp.status_code == 200:  # HTTP 200 = 성공
            return resp.json().get('total', 0)  # 총 검색 결과 수 반환 (없으면 0)
            #  └ resp.status_code: HTTP 응답 코드 (200=성공, 400=요청오류, 401=인증실패 등)
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
        time.sleep(0.12)  # 네이버 API rate limit 준수

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
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        #  └ with open(파일, mode, encoding) as f:
        #    · 파일을 열고 블록 종료 시 자동으로 닫음 (f.close() 불필요)
        #    · 'r' = 읽기 모드, 'w' = 쓰기(덮어쓰기), 'a' = 추가 쓰기
        progress = json.load(f)  # JSON 파일 → 파이썬 딕셔너리로 읽기
        #  └ json.load(파일객체): 파일에서 JSON 읽기 (18번에서 상세 설명)
    print(f"이전 진행 로드: {len(progress)}개 완료")
else:
    progress = {}  # 처음 실행이면 빈 딕셔너리

df    = pd.read_csv('tea_shops_dedup.csv')  # 중복 제거된 찻집 목록 로드
names = df['가게명'].tolist()               # 가게명만 리스트로 추출

remaining = [n for n in names if n not in progress]  # 아직 처리 안 된 가게만
print(f"남은 가게: {len(remaining)}개 / 전체 {len(names)}개")
print(f"예상 소요: 약 {len(remaining) * 15 / 60:.0f}분\n")
#  └ f-string 안의 :.0f : 소수점 0자리까지만 표시 (정수처럼 출력)


# ══════════════════════════════════════════════════════
# 스코어링 실행
# ══════════════════════════════════════════════════════
for i, name in enumerate(remaining, 1):
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
    #  └ f-string 포맷 지정자:
    #    · {:3d}: 정수를 최소 3자리로 (앞에 공백 패딩)
    #    · {:25s}: 문자열을 최소 25자리로 (뒤에 공백 패딩)
    #    · {:6d}: 정수를 최소 6자리로

    if i % 10 == 0:  # 10개마다 진행 상황 저장
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
            #  └ json.dump(객체, 파일, ensure_ascii=False, indent=2)
            #    · ensure_ascii=False: 한글 그대로 저장 (이스케이프 안 함)
            #    · indent=2: JSON을 2칸 들여쓰기로 보기 좋게 저장

# 최종 저장 (전체 완료 후)
with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
    json.dump(progress, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════
# 결과 정리 & 저장
# ══════════════════════════════════════════════════════
df['leaf_count'] = df['가게명'].map(lambda n: progress.get(n, {}).get('leaf_count', -1))
df['herb_count'] = df['가게명'].map(lambda n: progress.get(n, {}).get('herb_count', -1))
#  └ Series.map(함수 또는 딕셔너리)
#    · 시리즈의 각 원소에 함수를 적용해 새 Series 반환
#    · lambda n: progress.get(n, {}).get('leaf_count', -1)
#      → 가게명(n)으로 progress 딕셔너리 조회
#      → 없으면 {} → 그 안에서 'leaf_count' 조회, 없으면 -1 반환


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
#    · 각 행에 함수를 적용 (axis=1 = 행 단위)
#    · 함수는 각 행(Series)을 받아 반환값으로 새 컬럼 값 생성

print('\n=== 분류 결과 ===')
print(df['filter_result'].value_counts().to_string())
#  └ Series.value_counts(): 각 값의 등장 횟수를 내림차순으로 반환

print('\n[제거 후보]')
print(df[df['filter_result'] == 'REMOVE'][['가게명', 'leaf_count', 'herb_count']].to_string(index=False))
#  └ df[조건]: 조건이 True인 행만 필터링 (Boolean Indexing)
#  └ df[['컬럼1', '컬럼2']]: 여러 컬럼 선택 (이중 대괄호 사용)
#  └ .to_string(index=False): 인덱스(행 번호) 없이 문자열로 출력

print('\n[정보 없음 (수동 확인 필요)]')
print(df[df['filter_result'] == 'UNKNOWN'][['가게명', 'leaf_count', 'herb_count']].to_string(index=False))

df.to_csv('tea_shops_scored.csv', index=False, encoding='utf-8-sig')  # 분류 결과 저장
print('\n[저장] tea_shops_scored.csv')
