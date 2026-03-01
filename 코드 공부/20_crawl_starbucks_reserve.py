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

import os                           # 파일 경로, 작업 디렉토리 (17번에서 상세 설명)
import pandas as pd                 # 데이터프레임 라이브러리 (17번에서 상세 설명)
import numpy as np                  # 수치 배열 계산 (17번에서 상세 설명)
import requests                     # HTTP API 요청 (17번에서 상세 설명)
import time                         # API 호출 간격 조절 (17번에서 상세 설명)
from pyproj import Transformer      # 좌표계 변환 (17번에서 상세 설명)
from scipy.spatial import cKDTree   # 최근접 탐색 KD트리 (17번에서 상세 설명)
from dotenv import load_dotenv      # .env 환경변수 로드 (17번에서 상세 설명)

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리 변경 (19번에서 상세 설명)
load_dotenv()  # .env 파일 읽기

KAKAO_KEY = os.getenv('KAKAO_API_KEY')                     # 카카오 API 키
HEADERS   = {'Authorization': f'KakaoAK {KAKAO_KEY}'}     # 인증 헤더


# ══════════════════════════════════════════════════════
# 1. 카카오 API로 스타벅스 리저브 매장 수집
# ══════════════════════════════════════════════════════
def search_kakao(query, x, y, radius=20000):
    """카카오 키워드 검색 — 서울 중심 반경 내 최대 45건 수집"""
    url     = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    results = []
    for page in range(1, 4):  # 1~3페이지 순차 호출
        params = {
            'query' : query,    # 검색어 (예: "스타벅스 리저브")
            'x'     : x,        # 검색 중심 경도 (WGS84)
            'y'     : y,        # 검색 중심 위도 (WGS84)
            'radius': radius,   # 중심으로부터 검색 반경 (단위: m)
            'page'  : page,     # 페이지 번호
            'size'  : 15,       # 페이지당 결과 수 (최대 15)
        }
        resp  = requests.get(url, headers=HEADERS, params=params, timeout=5)
        #  └ requests.get(): GET 방식 API 요청 (17번에서 상세 설명)
        #    · x, y, radius: 특정 위치 중심 반경 검색 파라미터 (카카오 로컬 API 기능)

        data  = resp.json()         # JSON 응답 → 파이썬 딕셔너리
        items = data.get('documents', [])  # 검색 결과 목록
        results.extend(items)       # 결과를 전체 리스트에 추가

        if data['meta']['is_end']:  # 마지막 페이지면 중단
            break
        time.sleep(0.1)  # 페이지 간 대기

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
df = pd.DataFrame(raw)  # 딕셔너리 리스트 → DataFrame (17번에서 상세 설명)

if df.empty:      # 수집 결과 없으면
    print("결과 없음!")
    exit()        # 스크립트 종료 (sys.exit()와 동일 효과)
    #  └ exit(): 프로그램 종료 (대화형 환경/스크립트 모두 사용 가능)

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
#  └ df.rename(columns={기존명: 새이름, ...})
#    · 컬럼명 변경 (원본 변경 시 inplace=True 옵션 필요, 기본은 새 DataFrame 반환)
#    · columns 파라미터에 딕셔너리로 {기존: 새이름} 전달

df['lon'] = df['lon'].astype(float)  # 경도 문자열 → 실수 변환
df['lat'] = df['lat'].astype(float)  # 위도 문자열 → 실수 변환
#  └ Series.astype(타입)
#    · 시리즈의 데이터 타입 변환
#    · 카카오 API는 x, y 값을 문자열로 반환 → float으로 변환 필요

df = df[df['도로명주소'].str.startswith('서울', na=False)].copy()
#  └ Series.str.startswith('서울', na=False)
#    · 문자열 시리즈에서 '서울'로 시작하는 행만 True
#    · .str: pandas의 문자열 메소드 접근자 (문자열 컬럼에 str 메소드 적용)
#    · na=False: NaN이면 False 처리 (True면 NaN도 포함)
#    · .copy(): 필터링 후 복사본 생성 (경고 방지)
print(f"서울 내: {len(df)}개")

df = df.drop_duplicates(subset=['가게명', '지번주소']).reset_index(drop=True)
#  └ df.drop_duplicates(subset=['컬럼1', '컬럼2'])
#    · 여러 컬럼 조합 기준으로 중복 제거 (가게명+주소가 같으면 중복)
#  └ .reset_index(drop=True)
#    · 행 인덱스를 0부터 재설정
#    · drop=True: 기존 인덱스를 컬럼으로 추가하지 않고 버림
print(f"중복 제거 후: {len(df)}개")
print(df[['가게명', '도로명주소']].to_string())


# ══════════════════════════════════════════════════════
# 3. WGS84 → TM → 최근접 상권 매핑
# ══════════════════════════════════════════════════════
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
#  └ WGS84 → TM 변환기 생성 (19번과 동일, 자세한 설명은 17번 참조)

sb_x, sb_y = transformer.transform(df['lon'].values, df['lat'].values)
#  └ 스타벅스 리저브 WGS84 위경도 → TM 좌표로 변환 (19번과 동일 방식)

df['tm_x'] = sb_x  # 변환된 TM X좌표 저장
df['tm_y'] = sb_y  # 변환된 TM Y좌표 저장

df_map     = pd.read_csv('to_map.csv')                          # 상권 좌표 로드
map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values     # 상권 TM좌표 배열
tree       = cKDTree(map_coords)                                # 상권 좌표로 KD트리 구축

distances, indices = tree.query(np.column_stack([sb_x, sb_y]), k=1)
#  └ tree.query(): 각 스타벅스 매장에서 가장 가까운 상권 탐색 (19번에서 상세 설명)

df['상권_코드']      = df_map['상권_코드'].values[indices]    # 인덱스로 상권코드 매핑
df['상권_코드_명']   = df_map['상권_코드_명'].values[indices] # 인덱스로 상권명 매핑
df['nearest_dist_m'] = distances                               # 가장 가까운 상권까지 거리

print(f"\n매핑 완료 — 평균 거리: {distances.mean():.0f}m | 최대: {distances.max():.0f}m")


# ══════════════════════════════════════════════════════
# 4. 상권별 스타벅스_리저브_수 집계
# ══════════════════════════════════════════════════════
sb_count = df.groupby('상권_코드').size().reset_index(name='스타벅스_리저브_수')
#  └ df.groupby('상권_코드').size(): 상권별 스타벅스 매장 수 집계 (19번에서 상세 설명)

df_result = df_map[['상권_코드', '상권_코드_명']].merge(sb_count, on='상권_코드', how='left')
#  └ .merge(, how='left'): 왼쪽(df_map) 기준 조인 → 매장 없는 상권도 유지 (19번에서 상세 설명)

df_result['스타벅스_리저브_수'] = df_result['스타벅스_리저브_수'].fillna(0).astype(int)
#  └ .fillna(0): NaN → 0 (매장 없는 상권) / .astype(int): 정수형 변환

print(f"\n스타벅스 리저브 있는 상권: {(df_result['스타벅스_리저브_수'] > 0).sum()}개")
print(f"\nTOP 10:")
print(df_result.sort_values('스타벅스_리저브_수', ascending=False).head(10).to_string(index=False))


# ══════════════════════════════════════════════════════
# 5. 저장
# ══════════════════════════════════════════════════════
df.to_csv('starbucks_reserve_mapped.csv', index=False, encoding='utf-8-sig')
print(f"\n[저장] starbucks_reserve_mapped.csv ({len(df)}행)")

df_result.to_csv('starbucks_reserve_count.csv', index=False, encoding='utf-8-sig')
print(f"[저장] starbucks_reserve_count.csv ({len(df_result)}행)")
