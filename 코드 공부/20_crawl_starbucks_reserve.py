"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
20_crawl_starbucks_reserve.py — 스타벅스 리저브 수집 & 상권 매핑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  카카오 로컬 API로 서울 내 스타벅스 리저브 매장 수집
  → 찻집과 같은 방식으로 WGS84→TM 변환 후 KDTree로 상권 매핑
  → 상권별 스타벅스_리저브_수 집계 (고급 카페 수요 공급지표)

입력: to_map.csv
출력: starbucks_reserve_mapped.csv (매장별 상세)
      starbucks_reserve_count.csv  (상권별 집계)
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리 변경
#    · os.getenv('키'): 환경변수 값 반환 (없으면 None, KeyError 없음)
#    · 이 스크립트에서는 aicha 폴더를 cwd로 지정해 파일명만으로 CSV 접근 가능하게 함

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(파일명): CSV 파일을 읽어 DataFrame으로 반환
#    · pd.DataFrame(딕셔너리리스트): 딕셔너리 리스트를 DataFrame으로 변환
#    · df.rename(columns={기존:새이름}): 컬럼명 변경
#    · df.drop_duplicates(subset=컬럼목록): 지정 컬럼 조합 기준 중복 제거
#    · df.groupby('컬럼').size(): 그룹별 행 수 집계
#    · df.merge(다른df, on=키, how='left'): 키 기준 LEFT JOIN
#    · Series.fillna(값): NaN을 지정값으로 채우기
#    · Series.astype(타입): 데이터 타입 변환 (예: float → int)
#    · df.sort_values('컬럼', ascending=False): 내림차순 정렬
#    · df.to_csv(경로, index=False, encoding='utf-8-sig'): CSV 파일로 저장

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · numpy 배열: 파이썬 리스트보다 수치 연산이 훨씬 빠름
#    · np.column_stack([배열1, 배열2]): 1D 배열들을 열 방향으로 쌓아 2D 배열 생성
#    · array[인덱스배열]: 팬시 인덱싱 — 여러 위치 값을 한 번에 추출

import requests                     # HTTP API 요청 전송 라이브러리
#  └ [requests 라이브러리]
#    · pip install requests 로 설치
#    · requests.get(url, headers, params, timeout): GET 방식 HTTP 요청 전송
#      · GET: 데이터를 URL 쿼리스트링에 담음 (조회/검색)
#    · 반환: Response 객체
#      · resp.json(): 응답 body의 JSON → 파이썬 딕셔너리로 변환
#      · resp.status_code: HTTP 응답 코드 (200=성공)
#    · params 딕셔너리: 자동으로 URL 쿼리스트링으로 변환되어 전송됨

import time                         # 시간 지연 처리용 내장 모듈
#  └ [time 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · time.sleep(초): 지정한 초만큼 실행을 일시 정지
#    · 카카오 API 연속 호출 시 sleep으로 rate limit 방지

from pyproj import Transformer      # 좌표계(CRS) 변환 라이브러리
#  └ [pyproj 라이브러리]
#    · pip install pyproj 로 설치
#    · 다양한 좌표계 간 변환 지원
#    · EPSG:4326: WGS84 (GPS/위경도 표준, 카카오 API 반환 형식)
#    · EPSG:5181: 한국 TM좌표 (미터 단위, 상권 데이터 좌표계)
#    · Transformer.from_crs(원본CRS, 대상CRS, always_xy=True): 변환기 생성
#      - always_xy=True: 항상 (경도, 위도) 순서로 처리 (좌표 순서 혼동 방지)
#    · transformer.transform(경도배열, 위도배열): 배열 전체를 한 번에 변환

from scipy.spatial import cKDTree   # 고속 최근접 이웃 탐색 알고리즘 라이브러리
#  └ [scipy.spatial.cKDTree]
#    · pip install scipy 로 설치
#    · KD-Tree: 다차원 공간에서 최근접 이웃을 빠르게 탐색하는 자료구조
#    · cKDTree(좌표배열): C 언어 구현 고속 버전
#    · tree.query(점배열, k=1): 각 점에서 가장 가까운 k개 이웃 탐색
#      · 반환: (거리배열, 인덱스배열) 튜플

from dotenv import load_dotenv      # .env 파일에서 환경변수 로드하는 라이브러리
#  └ [python-dotenv 라이브러리]
#    · pip install python-dotenv 로 설치
#    · load_dotenv(): .env 파일을 읽어 환경변수로 등록
#    · 이후 os.getenv('키')로 API 키 등 민감 정보에 접근
#    · .env 파일을 .gitignore에 추가해 GitHub에 올라가지 않도록 관리

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경
#  └ os.chdir(경로)
#    · 기본문법: os.chdir(path)
#    · 이후 pd.read_csv('파일명.csv') 처럼 파일명만 써도 이 폴더에서 찾음

load_dotenv()  # .env 파일 읽기
#  └ load_dotenv()
#    · 기본문법: load_dotenv(dotenv_path=None)
#    · 현재 디렉토리와 상위 디렉토리에서 .env 파일 자동 탐색 후 환경변수 등록

KAKAO_KEY = os.getenv('KAKAO_API_KEY')                    # 카카오 API 키
HEADERS   = {'Authorization': f'KakaoAK {KAKAO_KEY}'}    # 인증 헤더
#  └ os.getenv('키')
#    · 기본문법: os.getenv(key, default=None)
#    · 환경변수 값 반환, 없으면 None (KeyError 없음)
#    · f'KakaoAK {KAKAO_KEY}': 카카오 API 인증 헤더 형식


# ══════════════════════════════════════════════════════
# 1. 카카오 API로 스타벅스 리저브 매장 수집
# ══════════════════════════════════════════════════════
def search_kakao(query, x, y, radius=20000):
    """카카오 키워드 검색 — 서울 중심 반경 내 최대 45건 수집"""
    url     = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    results = []
    for page in range(1, 4):  # 1~3페이지 순차 호출 (페이지당 최대 15건)
        #  └ range(start, stop)
        #    · 기본문법: range(start, stop, step=1)
        #    · range(1, 4) → 1, 2, 3 (stop 미포함)

        params = {
            'query' : query,    # 검색어 (예: "스타벅스 리저브")
            'x'     : x,        # 검색 중심 경도 (WGS84)
            'y'     : y,        # 검색 중심 위도 (WGS84)
            'radius': radius,   # 중심으로부터 검색 반경 (단위: m)
            'page'  : page,     # 페이지 번호
            'size'  : 15,       # 페이지당 결과 수 (최대 15)
        }
        resp  = requests.get(url, headers=HEADERS, params=params, timeout=5)
        #  └ requests.get(url, headers, params, timeout)
        #    · 기본문법: requests.get(url, headers=None, params=None, timeout=None)
        #    · GET 방식 HTTP 요청 전송
        #    · params: 딕셔너리 → URL 쿼리스트링으로 자동 변환
        #    · x, y, radius: 카카오 로컬 API의 특정 위치 중심 반경 검색 파라미터
        #    · timeout=5: 5초 내 응답 없으면 예외 발생

        data  = resp.json()              # JSON 응답 → 파이썬 딕셔너리
        #  └ Response.json()
        #    · 기본문법: Response.json()
        #    · 응답 body JSON 문자열 → 파이썬 딕셔너리/리스트로 파싱

        items = data.get('documents', [])  # 검색 결과 목록 (없으면 빈 리스트)
        #  └ dict.get(키, 기본값)
        #    · 기본문법: dict.get(key, default=None)
        #    · 키 없으면 기본값 반환 (KeyError 없음)

        results.extend(items)            # 결과를 전체 리스트에 추가
        #  └ list.extend(iterable)
        #    · 기본문법: list.extend(iterable)
        #    · 리스트에 iterable의 모든 원소를 추가 (이어붙임)
        #    · append는 요소 1개, extend는 리스트를 이어붙임

        if data['meta']['is_end']:  # 마지막 페이지면 중단
            break
        time.sleep(0.1)  # 페이지 간 대기 (rate limit 방지)

    return results  # 수집된 전체 결과 반환


# 서울 중심 좌표 (WGS84) — 검색 중심점으로 사용
SEOUL_X, SEOUL_Y = 126.9779, 37.5663

print("스타벅스 리저브 수집 중...")
raw = search_kakao('스타벅스 리저브', x=SEOUL_X, y=SEOUL_Y, radius=20000)
#  └ radius=20000: 서울 중심에서 20km 반경 내 검색 (서울 전역 커버)
print(f"수집: {len(raw)}건")


# ══════════════════════════════════════════════════════
# 2. 서울 필터링 & 컬럼 정제
# ══════════════════════════════════════════════════════
df = pd.DataFrame(raw)  # 딕셔너리 리스트 → DataFrame 생성
#  └ pd.DataFrame(데이터)
#    · 기본문법: pd.DataFrame(data, index=None, columns=None)
#    · 딕셔너리 리스트를 받아 DataFrame으로 변환
#    · 각 딕셔너리의 키가 컬럼명, 값이 셀 값이 됨

if df.empty:      # 수집 결과 없으면
    print("결과 없음!")
    exit()        # 스크립트 종료
    #  └ exit()
    #    · 기본문법: exit(status=None)
    #    · 프로그램 종료 (대화형 환경/스크립트 모두 사용 가능)
    #    · sys.exit()와 동일한 효과

df = df.rename(columns={         # 영문 컬럼명 → 한글로 변경
    'place_name'       : '가게명',
    'address_name'     : '지번주소',
    'road_address_name': '도로명주소',
    'phone'            : '전화번호',
    'place_url'        : 'URL',
    'category_name'    : '카테고리',
    'x'                : 'lon',   # 경도
    'y'                : 'lat',   # 위도
})
#  └ df.rename(columns={기존명: 새이름})
#    · 기본문법: DataFrame.rename(columns=None, inplace=False)
#    · 컬럼명 변경 (딕셔너리로 {기존이름: 새이름} 지정)
#    · inplace=True: 원본 변경 / 기본값 False: 새 DataFrame 반환

df['lon'] = df['lon'].astype(float)  # 경도 문자열 → 실수 변환
df['lat'] = df['lat'].astype(float)  # 위도 문자열 → 실수 변환
#  └ Series.astype(타입)
#    · 기본문법: Series.astype(dtype)
#    · 시리즈의 데이터 타입 변환
#    · 카카오 API는 x, y 값을 문자열로 반환 → float으로 변환 필요
#    · astype(float): 문자열 "126.9779" → 실수 126.9779

df = df[df['도로명주소'].str.startswith('서울', na=False)].copy()
#  └ Series.str.startswith('서울', na=False)
#    · 기본문법: Series.str.startswith(pat, na=None)
#    · 문자열 시리즈에서 '서울'로 시작하는 행만 True
#    · .str: pandas의 문자열 메소드 접근자 (Series에 문자열 메소드를 일괄 적용)
#    · na=False: NaN이면 False 처리 (True면 NaN도 포함되어 오류 위험)
#
#  └ .copy()
#    · 기본문법: DataFrame.copy(deep=True)
#    · 필터링 후 복사본 생성 (SettingWithCopyWarning 경고 방지)

print(f"서울 내: {len(df)}개")

df = df.drop_duplicates(subset=['가게명', '지번주소']).reset_index(drop=True)
#  └ df.drop_duplicates(subset=['컬럼1', '컬럼2'])
#    · 기본문법: DataFrame.drop_duplicates(subset=None, keep='first')
#    · 여러 컬럼 조합 기준으로 중복 제거 (가게명+주소가 같으면 중복)
#    · keep='first'(기본): 중복 중 첫 번째 행만 유지
#
#  └ .reset_index(drop=True)
#    · 기본문법: DataFrame.reset_index(drop=False)
#    · 행 인덱스를 0부터 재설정
#    · drop=True: 기존 인덱스를 컬럼으로 추가하지 않고 버림

print(f"중복 제거 후: {len(df)}개")
print(df[['가게명', '도로명주소']].to_string())
#  └ .to_string()
#    · 기본문법: DataFrame.to_string(index=True)
#    · DataFrame 전체를 잘리지 않고 문자열로 출력 (print 시 유용)


# ══════════════════════════════════════════════════════
# 3. WGS84 → TM → 최근접 상권 매핑
# ══════════════════════════════════════════════════════
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
#  └ Transformer.from_crs(원본CRS, 대상CRS, always_xy=True)
#    · 기본문법: Transformer.from_crs(crs_from, crs_to, always_xy=False)
#    · WGS84(위경도) → 한국 TM좌표(미터 단위) 변환기 생성
#    · "EPSG:4326": WGS84 (카카오 API 반환 형식)
#    · "EPSG:5181": 한국 TM 좌표계 (상권 데이터 좌표계와 동일해야 거리 계산 가능)
#    · always_xy=True: 항상 (경도, 위도) 순서 입력

sb_x, sb_y = transformer.transform(df['lon'].values, df['lat'].values)
#  └ transformer.transform(경도배열, 위도배열)
#    · 기본문법: Transformer.transform(xx, yy)
#    · 스타벅스 리저브 WGS84 위경도 → TM 좌표로 일괄 변환
#    · .values: pandas Series → NumPy 배열로 변환 (변환기 입력에 필요)
#    · 반환: (TM_x배열, TM_y배열) 튜플

df['tm_x'] = sb_x  # 변환된 TM X좌표 저장
df['tm_y'] = sb_y  # 변환된 TM Y좌표 저장

df_map     = pd.read_csv('to_map.csv')                       # 상권 좌표 로드
map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values  # 상권 TM좌표 배열 추출
#  └ df[['컬럼1', '컬럼2']].values
#    · 이중 대괄호로 두 컬럼 선택 → .values로 NumPy 2D 배열 변환
#    · 결과: [[x1,y1], [x2,y2], ...] 형태의 (1650 × 2) 배열

tree       = cKDTree(map_coords)  # 상권 좌표로 KD트리 구축
#  └ cKDTree(좌표배열)
#    · 기본문법: cKDTree(data, leafsize=10)
#    · 1,650개 상권의 TM 좌표로 탐색 트리 생성

distances, indices = tree.query(np.column_stack([sb_x, sb_y]), k=1)
#  └ np.column_stack([배열1, 배열2])
#    · 기본문법: numpy.column_stack(tup)
#    · 1D 배열 두 개를 열 방향으로 쌓아 2D 배열 생성
#    · 예: [1,2]와 [3,4] → [[1,3],[2,4]] (2행×2열)
#    · tree.query()의 입력은 2D 배열이어야 하므로 변환 필요
#
#  └ tree.query(검색점배열, k=1)
#    · 기본문법: cKDTree.query(x, k=1)
#    · 각 스타벅스 매장 좌표에서 가장 가까운 상권 1개 탐색
#    · 반환: (거리배열, 인덱스배열) — 인덱스는 map_coords(=df_map) 행 번호

df['상권_코드']      = df_map['상권_코드'].values[indices]    # 인덱스로 상권코드 매핑
df['상권_코드_명']   = df_map['상권_코드_명'].values[indices]  # 인덱스로 상권명 매핑
df['nearest_dist_m'] = distances                               # 가장 가까운 상권까지 거리
#  └ numpy배열[인덱스배열] — 팬시 인덱싱(Fancy Indexing)
#    · 기본문법: array[정수배열]
#    · 인덱스 배열에 해당하는 위치의 원소들을 한 번에 추출
#    · indices = [3, 0, 2, ...]: 각 스타벅스 매장에 해당하는 상권 행 번호
#    · .values[indices]: 해당 행 번호의 상권코드/상권명을 한 번에 선택

print(f"\n매핑 완료 — 평균 거리: {distances.mean():.0f}m | 최대: {distances.max():.0f}m")


# ══════════════════════════════════════════════════════
# 4. 상권별 스타벅스_리저브_수 집계
# ══════════════════════════════════════════════════════
sb_count = df.groupby('상권_코드').size().reset_index(name='스타벅스_리저브_수')
#  └ df.groupby('상권_코드').size()
#    · 기본문법: DataFrame.groupby(by).size()
#    · 상권_코드가 같은 매장끼리 그룹화 후 그룹별 행 수(매장 수) 반환
#
#  └ .reset_index(name='스타벅스_리저브_수')
#    · 그룹 키(상권_코드)를 다시 일반 컬럼으로 내려옴
#    · name='스타벅스_리저브_수': 집계된 수 컬럼의 이름 지정

df_result = df_map[['상권_코드', '상권_코드_명']].merge(sb_count, on='상권_코드', how='left')
#  └ df.merge(다른df, on=키, how='left')
#    · 기본문법: DataFrame.merge(right, on=None, how='inner')
#    · 왼쪽(df_map) 기준 LEFT JOIN → 매장 없는 상권도 유지 (스타벅스_리저브_수=NaN)
#    · how='left': 왼쪽에만 있는 상권도 결과에 포함 (NaN으로 채워짐)

df_result['스타벅스_리저브_수'] = df_result['스타벅스_리저브_수'].fillna(0).astype(int)
#  └ Series.fillna(0)
#    · 기본문법: Series.fillna(value)
#    · NaN → 0으로 채움 (매장 없는 상권)
#
#  └ .astype(int)
#    · 기본문법: Series.astype(dtype)
#    · fillna 후 float64 → int로 변환 (NaN 없어진 후 정수형 가능)

print(f"\n스타벅스 리저브 있는 상권: {(df_result['스타벅스_리저브_수'] > 0).sum()}개")
print(f"\nTOP 10:")
print(df_result.sort_values('스타벅스_리저브_수', ascending=False).head(10).to_string(index=False))
#  └ df.sort_values('컬럼', ascending=False)
#    · 기본문법: DataFrame.sort_values(by, ascending=True)
#    · ascending=False: 내림차순 (큰 값 위)
#
#  └ .head(10)
#    · 기본문법: DataFrame.head(n=5)
#    · 상위 10개 행만 반환
#
#  └ .to_string(index=False)
#    · 행 번호 없이 전체 출력


# ══════════════════════════════════════════════════════
# 5. 저장
# ══════════════════════════════════════════════════════
df.to_csv('starbucks_reserve_mapped.csv', index=False, encoding='utf-8-sig')
#  └ df.to_csv(경로, index=False, encoding='utf-8-sig')
#    · 기본문법: DataFrame.to_csv(path, sep=',', index=True, encoding=None)
#    · index=False: 행 번호를 CSV에 포함하지 않음
#    · encoding='utf-8-sig': BOM 포함 UTF-8 → 엑셀에서 한글 안 깨짐
print(f"\n[저장] starbucks_reserve_mapped.csv ({len(df)}행)")

df_result.to_csv('starbucks_reserve_count.csv', index=False, encoding='utf-8-sig')
print(f"[저장] starbucks_reserve_count.csv ({len(df_result)}행)")
