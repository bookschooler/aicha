"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
19_map_tea_shops.py — 찻집을 상권에 매핑 + 상권별 찻집_수 집계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  찻집의 WGS84 좌표 → TM좌표로 변환 후
  KDTree로 각 찻집과 가장 가까운 상권 센트로이드에 매핑
  → 상권별 찻집_수 집계 (1,650개 상권, 없으면 0)

입력: tea_shops_list.csv, to_map.csv
출력: tea_shops_mapped.csv (찻집별 매핑 상세)
      tea_shop_count.csv   (상권별 찻집_수)
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리(cwd) 변경
#    · 이후 pd.read_csv('파일명.csv') 처럼 파일명만 써도 이 폴더에서 찾음
#    · 변경하지 않으면 스크립트 실행 위치에서 파일을 찾아 오류 발생

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(파일명): CSV 파일을 읽어 DataFrame으로 반환
#    · DataFrame.copy(): 원본 DataFrame의 독립적인 복사본 생성
#    · df.merge(다른df, on=키, how='left'): 키 기준 두 DataFrame 결합 (SQL LEFT JOIN)
#    · df.groupby('컬럼').size(): 그룹별 행 수 집계
#    · Series.fillna(값): NaN(결측값)을 지정값으로 채우기
#    · Series.astype(타입): 데이터 타입 변환 (예: float → int)
#    · df.sort_values('컬럼', ascending=False): 내림차순 정렬
#    · df.to_csv(경로, index=False, encoding='utf-8-sig'): CSV 파일로 저장

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · numpy 배열: 파이썬 리스트보다 수치 연산이 훨씬 빠름
#    · np.column_stack([배열1, 배열2]): 1D 배열 여러 개를 열 방향으로 쌓아 2D 배열 생성
#    · array[인덱스배열]: 팬시 인덱싱 — 인덱스 배열에 해당하는 원소들을 한 번에 추출
#    · (조건배열).mean(): True=1, False=0으로 처리해 비율(0~1) 계산

from pyproj import Transformer      # 좌표계(CRS) 변환 라이브러리
#  └ [pyproj 라이브러리]
#    · pip install pyproj 로 설치
#    · 다양한 좌표계 간 변환 지원 (WGS84 위경도 ↔ TM 평면좌표 등)
#    · EPSG:4326: WGS84 (GPS/위경도 표준, Google Maps 등에서 사용)
#    · EPSG:5181: 한국 TM좌표 (미터 단위, 상권 데이터의 좌표계)
#    · Transformer.from_crs(원본CRS, 대상CRS, always_xy=True): 변환기 생성
#      - always_xy=True: 항상 (경도, 위도) 순서로 처리 (좌표 순서 혼동 방지)
#    · transformer.transform(경도배열, 위도배열): 배열 전체를 한 번에 변환
#    · 상권 데이터가 TM 좌표이므로 찻집 좌표도 TM으로 맞춰야 KDTree 거리 계산 가능

from scipy.spatial import cKDTree   # 고속 최근접 이웃 탐색 알고리즘 라이브러리
#  └ [scipy.spatial.cKDTree]
#    · pip install scipy 로 설치
#    · KD-Tree(K-Dimensional Tree): 다차원 공간에서 최근접 이웃을 빠르게 탐색하는 자료구조
#    · cKDTree(좌표배열): C 언어로 구현된 고속 버전 (파이썬 KDTree보다 빠름)
#    · tree.query(점 또는 점배열, k=1): 각 점에서 가장 가까운 k개 이웃 탐색
#      · 반환: (거리배열, 인덱스배열) 튜플
#      · 인덱스: 트리 구축에 사용한 원본 배열의 행 번호
#    · 브루트포스(모든 쌍 비교) O(n²) 대신 O(log n) 으로 빠른 검색 가능

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경
#  └ os.chdir(경로)
#    · 기본문법: os.chdir(path)
#    · 현재 작업 디렉토리(CWD, Current Working Directory) 변경
#    · 이후 상대 경로('파일.csv')가 이 폴더 기준으로 해석됨
#    · 서버 환경에서 파일을 찾지 못하는 문제를 방지하기 위해 사용


# ══════════════════════════════════════════════════════
# 1. 데이터 로드
# ══════════════════════════════════════════════════════
df_tea = pd.read_csv('tea_shops_list.csv')  # 필터링 완료된 찻집 목록 로드
#  └ pd.read_csv(파일경로)
#    · 기본문법: pd.read_csv(filepath, encoding=None, sep=',', header=0)
#    · CSV 파일을 읽어 DataFrame으로 반환
#    · encoding 미지정 시 기본값 'utf-8' 사용
#    · os.chdir로 디렉토리 변경했으므로 파일명만으로 접근 가능

df_map = pd.read_csv('to_map.csv')          # 1,650개 상권 좌표 정보 로드

print(f"찻집 수: {len(df_tea)}")  # DataFrame의 총 행 수 (len(df))
print(f"상권 수: {len(df_map)}")


# ══════════════════════════════════════════════════════
# 2. 찻집 WGS84 좌표 → TM(EPSG:5181) 좌표 변환
# ══════════════════════════════════════════════════════
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
#  └ Transformer.from_crs(원본CRS, 대상CRS, always_xy=True)
#    · 기본문법: Transformer.from_crs(crs_from, crs_to, always_xy=False)
#    · WGS84(위경도) → 한국 TM좌표(미터 단위)로 변환하는 변환기 생성
#    · "EPSG:4326": WGS84 (위경도 좌표계, GPS/Google Maps 표준)
#    · "EPSG:5181": 한국 TM 좌표계 (미터 단위 평면 좌표)
#    · always_xy=True: 항상 (경도, 위도) 순서 입력 (기본값은 (위도, 경도))
#    · 왜 TM으로 변환? → 상권 좌표(to_map.csv)가 TM이므로 같은 단위로 맞춰야
#      거리(m) 계산 및 KDTree 탐색이 정확함

tea_x, tea_y = transformer.transform(df_tea['lon'].values, df_tea['lat'].values)
#  └ transformer.transform(경도배열, 위도배열)
#    · 기본문법: Transformer.transform(xx, yy)
#    · 경도(lon) 배열과 위도(lat) 배열을 한 번에 TM 좌표로 변환
#    · 반환: (TM_x배열, TM_y배열) 튜플
#    · .values: pandas Series → NumPy 배열로 변환 (변환기 입력에 필요)

df_tea = df_tea.copy()  # 원본 변경 방지를 위해 복사본 생성
#  └ DataFrame.copy()
#    · 기본문법: DataFrame.copy(deep=True)
#    · DataFrame의 복사본 생성 (원본과 독립적인 새 객체)
#    · deep=True(기본): 데이터까지 완전 복사 (원본 변경해도 복사본에 영향 없음)
#    · 슬라이싱/필터링 후 직접 컬럼 추가 시 발생하는
#      SettingWithCopyWarning 경고를 방지하기 위해 명시적으로 .copy() 호출

df_tea['tm_x'] = tea_x  # 변환된 TM X좌표 컬럼 추가
df_tea['tm_y'] = tea_y  # 변환된 TM Y좌표 컬럼 추가


# ══════════════════════════════════════════════════════
# 3. KDTree로 최근접 상권 매핑
# ══════════════════════════════════════════════════════
map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values  # 상권 TM좌표 배열 추출
#  └ df[['컬럼1', '컬럼2']].values
#    · df[['컬럼1', '컬럼2']]: 이중 대괄호로 두 컬럼 선택 → (행수 × 2) DataFrame
#    · .values: DataFrame → NumPy 2D 배열로 변환
#    · 결과: [[x1,y1], [x2,y2], ...] 형태의 (1650 × 2) 배열

tree = cKDTree(map_coords)  # 상권 좌표들로 KD트리 구축
#  └ cKDTree(좌표배열)
#    · 기본문법: cKDTree(data, leafsize=10)
#    · 1,650개 상권의 TM 좌표로 탐색 트리 생성
#    · 이후 query()로 임의의 점(찻집)에서 가장 가까운 상권을 O(log n)으로 탐색
#    · leafsize: 트리 최소 그룹 크기 (기본값 10, 보통 조정 불필요)

distances, indices = tree.query(np.column_stack([tea_x, tea_y]), k=1)
#  └ np.column_stack([배열1, 배열2])
#    · 기본문법: numpy.column_stack(tup)
#    · 1D 배열 여러 개를 열 방향으로 쌓아 2D 배열 생성
#    · 예: [1,2,3]과 [4,5,6] → [[1,4],[2,5],[3,6]] (3행×2열)
#    · tree.query()의 입력은 2D 배열이어야 하므로 변환 필요
#
#  └ tree.query(검색점배열, k=1)
#    · 기본문법: cKDTree.query(x, k=1, workers=1)
#    · 각 찻집 좌표에서 가장 가까운 상권 1개 탐색
#    · x: (찻집수 × 2) 형태의 2D 배열 (각 행이 하나의 찻집 좌표)
#    · k=1: 가장 가까운 1개 이웃만 찾기
#    · 반환: (거리배열, 인덱스배열) — 인덱스는 map_coords(=df_map)의 행 번호

df_tea['상권_코드']      = df_map['상권_코드'].values[indices]    # 인덱스로 상권 코드 매핑
df_tea['상권_코드_명']   = df_map['상권_코드_명'].values[indices]  # 인덱스로 상권명 매핑
df_tea['nearest_dist_m'] = distances                               # 가장 가까운 상권까지 거리(m)
#  └ numpy배열[인덱스배열] — 팬시 인덱싱(Fancy Indexing)
#    · 기본문법: array[정수배열]
#    · 인덱스 배열에 해당하는 위치의 원소들을 한 번에 추출
#    · 예: df_map['상권_코드'].values = [100, 101, 102, ...]
#          indices                    = [3, 0, 2, ...]   (각 찻집에 해당하는 상권 행 번호)
#          .values[indices]           = [102, 100, 101, ...] (인덱스에 해당하는 상권코드들)

print(f"\n최근접 상권 매핑 완료")
print(f"평균 거리: {distances.mean():.0f}m | 최대: {distances.max():.0f}m")
print(f"500m 이내: {(distances <= 500).mean()*100:.1f}% | 1km 이내: {(distances <= 1000).mean()*100:.1f}%")
#  └ (distances <= 500).mean()
#    · distances <= 500: 각 거리가 500 이하인지 확인 → Boolean 배열 (True/False)
#    · .mean(): True=1, False=0으로 처리 → True의 비율(0~1) 계산
#    · × 100: 퍼센트로 변환


# ══════════════════════════════════════════════════════
# 4. 상권별 찻집_수 집계 (전체 1,650개 기준, 없으면 0)
# ══════════════════════════════════════════════════════
tea_count = df_tea.groupby('상권_코드').size().reset_index(name='찻집_수')
#  └ df.groupby('컬럼')
#    · 기본문법: DataFrame.groupby(by)
#    · 지정 컬럼의 값이 같은 행끼리 그룹으로 묶음
#    · 예: 상권_코드가 같은 찻집들을 하나의 그룹으로
#
#  └ .size()
#    · 기본문법: GroupBy.size()
#    · 각 그룹의 행 수 반환 (찻집이 몇 개인지)
#    · .count()와 달리 NaN도 포함해서 셈
#
#  └ .reset_index(name='찻집_수')
#    · 기본문법: Series.reset_index(name=None)
#    · 그룹 키(상권_코드)를 다시 일반 컬럼으로 내려옴
#    · name='찻집_수': size()로 집계된 수 컬럼의 이름 지정

df_result = df_map[['상권_코드', '상권_코드_명']].merge(tea_count, on='상권_코드', how='left')
#  └ df.merge(다른df, on=키컬럼, how='left')
#    · 기본문법: DataFrame.merge(right, on=None, how='inner')
#    · 두 DataFrame을 키 컬럼 기준으로 결합 (SQL의 JOIN과 동일 개념)
#    · on='상권_코드': 두 DataFrame 모두에 있는 기준 컬럼
#    · how='left': 왼쪽(df_map) 기준 → 찻집 없는 상권도 유지 (찻집_수=NaN으로)
#    · how='inner': 양쪽 모두에 있는 행만 유지 (찻집 없는 상권 제외됨)
#    · how='outer': 양쪽 모두 유지

df_result['찻집_수'] = df_result['찻집_수'].fillna(0).astype(int)
#  └ Series.fillna(값)
#    · 기본문법: Series.fillna(value, method=None)
#    · NaN(결측값)을 지정한 값으로 채움
#    · 찻집 없는 상권의 찻집_수 NaN → 0으로 대체
#
#  └ .astype(타입)
#    · 기본문법: Series.astype(dtype)
#    · 데이터 타입 변환
#    · fillna(0) 후에도 dtype이 float64이므로 int로 명시 변환
#    · 이유: LEFT JOIN 후 NaN이 있으면 정수형 유지가 안 됨 (float로 바뀜)

print(f"\n상권별 집계 결과:")
print(f"  찻집 있는 상권: {(df_result['찻집_수'] > 0).sum()}개")
print(f"  찻집 0인 상권:  {(df_result['찻집_수'] == 0).sum()}개")
print(f"  최대 찻집_수:   {df_result['찻집_수'].max()}")

print(f"\n찻집 많은 상권 TOP 10:")
print(df_result.sort_values('찻집_수', ascending=False).head(10).to_string(index=False))
#  └ df.sort_values('컬럼', ascending=False)
#    · 기본문법: DataFrame.sort_values(by, ascending=True, na_position='last')
#    · 지정 컬럼 기준으로 정렬
#    · ascending=False: 내림차순 (큰 값이 위로)
#    · ascending=True(기본값): 오름차순
#
#  └ .head(n)
#    · 기본문법: DataFrame.head(n=5)
#    · 상위 n개 행만 반환 (기본값 5)
#
#  └ .to_string(index=False)
#    · 기본문법: DataFrame.to_string(index=True)
#    · DataFrame 전체를 잘리지 않고 문자열로 출력
#    · index=False: 행 번호(0,1,2...) 없이 데이터만 출력


# ══════════════════════════════════════════════════════
# 5. 저장
# ══════════════════════════════════════════════════════
df_tea.to_csv('tea_shops_mapped.csv', index=False, encoding='utf-8-sig')
#  └ df.to_csv(경로, index=False, encoding='utf-8-sig')
#    · 기본문법: DataFrame.to_csv(path, sep=',', index=True, encoding=None)
#    · index=False: 행 번호를 CSV에 포함하지 않음
#    · encoding='utf-8-sig': BOM 포함 UTF-8 → 엑셀에서 한글 안 깨짐
print(f"\n[저장] tea_shops_mapped.csv  ({len(df_tea)}행) — 찻집별 매핑 상세")

df_result.to_csv('tea_shop_count.csv', index=False, encoding='utf-8-sig')
print(f"[저장] tea_shop_count.csv    ({len(df_result)}행) — 상권별 찻집_수")
