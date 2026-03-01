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

import os                           # 파일 경로, 작업 디렉토리 관련 (17번에서 상세 설명)
import pandas as pd                 # 데이터프레임 라이브러리 (17번에서 상세 설명)
import numpy as np                  # 수치 배열 계산 (17번에서 상세 설명)
from pyproj import Transformer      # 좌표계 변환 (17번에서 상세 설명)
from scipy.spatial import cKDTree   # 최근접 탐색 KD트리 (17번에서 상세 설명)

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경
#  └ os.chdir(경로)
#    · 현재 작업 디렉토리(CWD) 변경
#    · 이후 상대 경로('파일.csv')가 이 폴더 기준으로 해석됨
#    · 서버 환경에서 파일을 찾지 못하는 문제를 방지하기 위해 사용


# ══════════════════════════════════════════════════════
# 1. 데이터 로드
# ══════════════════════════════════════════════════════
df_tea = pd.read_csv('tea_shops_list.csv')  # 필터링 완료된 찻집 목록 로드
#  └ pd.read_csv(파일명)
#    · CSV 파일을 DataFrame으로 읽기 (17번에서 상세 설명)
#    · os.chdir로 디렉토리 변경했으므로 파일명만으로 접근 가능

df_map = pd.read_csv('to_map.csv')          # 1,650개 상권 좌표 정보 로드

print(f"찻집 수: {len(df_tea)}")  # DataFrame의 총 행 수 출력
print(f"상권 수: {len(df_map)}")


# ══════════════════════════════════════════════════════
# 2. 찻집 WGS84 좌표 → TM(EPSG:5181) 좌표 변환
# ══════════════════════════════════════════════════════
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
#  └ Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
#    · WGS84(위경도) → 한국 TM좌표(미터 단위)로 변환하는 변환기 생성
#    · 17번과 반대 방향 (17번: TM→WGS84, 여기서: WGS84→TM)
#    · 상권 좌표가 TM이므로 찻집 좌표도 TM으로 맞춰야 KDTree 거리 계산 가능

tea_x, tea_y = transformer.transform(df_tea['lon'].values, df_tea['lat'].values)
#  └ transformer.transform(경도배열, 위도배열)
#    · WGS84 위경도 → TM 좌표(미터 단위) 배열로 변환
#    · .values: pandas Series를 NumPy 배열로 변환 (변환기 입력에 필요)
#    · 반환: (TM_x배열, TM_y배열)

df_tea = df_tea.copy()  # 원본 변경 방지를 위해 복사본 생성 (17번에서 상세 설명)
df_tea['tm_x'] = tea_x  # 변환된 TM X좌표 컬럼 추가
df_tea['tm_y'] = tea_y  # 변환된 TM Y좌표 컬럼 추가


# ══════════════════════════════════════════════════════
# 3. KDTree로 최근접 상권 매핑
# ══════════════════════════════════════════════════════
map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values  # 상권 TM좌표 배열 추출
#  └ df[['컬럼1', '컬럼2']].values
#    · 두 컬럼을 선택 후 NumPy 2D 배열로 변환
#    · .values: (행수 × 2) 형태의 numpy ndarray 반환

tree = cKDTree(map_coords)  # 상권 좌표들로 KD트리 구축
#  └ cKDTree(좌표배열): 공간 인덱싱 트리 생성 (17번에서 상세 설명)
#    · 여기서는 상권 좌표로 트리 구축
#    · 각 찻집에서 가장 가까운 상권을 빠르게 찾기 위함

distances, indices = tree.query(np.column_stack([tea_x, tea_y]), k=1)
#  └ np.column_stack([배열1, 배열2])
#    · 1D 배열 여러 개를 열 방향으로 쌓아 2D 배열 생성
#    · 예: [1,2,3]과 [4,5,6] → [[1,4],[2,5],[3,6]] (3행×2열)
#    · tree.query()의 입력은 2D 배열이어야 하므로 변환 필요
#  └ tree.query(검색점배열, k=1)
#    · 각 찻집 좌표에서 가장 가까운 상권 1개 탐색 (17번에서 상세 설명)
#    · 반환: (거리배열, 인덱스배열)
#    · 인덱스는 df_map의 행 번호 → 해당 상권 정보 접근에 사용

df_tea['상권_코드']    = df_map['상권_코드'].values[indices]   # 인덱스로 상권 코드 매핑
df_tea['상권_코드_명']  = df_map['상권_코드_명'].values[indices] # 인덱스로 상권명 매핑
df_tea['nearest_dist_m'] = distances  # 가장 가까운 상권까지의 거리(m) 저장
#  └ numpy배열[인덱스배열]: 인덱스 배열에 해당하는 원소를 한 번에 추출 (팬시 인덱싱)
#    · df_map['상권_코드'].values = [100, 101, 102, ...]
#    · indices = [3, 0, 2, ...] (각 찻집에 해당하는 상권 행 번호)
#    · .values[indices] = [102, 100, 101, ...] (인덱스에 해당하는 상권코드들)

print(f"\n최근접 상권 매핑 완료")
print(f"평균 거리: {distances.mean():.0f}m | 최대: {distances.max():.0f}m")
print(f"500m 이내: {(distances <= 500).mean()*100:.1f}% | 1km 이내: {(distances <= 1000).mean()*100:.1f}%")
#  └ (조건배열).mean(): True=1, False=0으로 처리 → 비율(0~1) 계산, ×100 = 퍼센트


# ══════════════════════════════════════════════════════
# 4. 상권별 찻집_수 집계 (전체 1,650개 기준, 없으면 0)
# ══════════════════════════════════════════════════════
tea_count = df_tea.groupby('상권_코드').size().reset_index(name='찻집_수')
#  └ df.groupby('컬럼')
#    · 지정 컬럼의 값이 같은 행끼리 그룹으로 묶음
#    · 예: 상권_코드가 같은 찻집들을 하나의 그룹으로
#  └ .size()
#    · 각 그룹의 행 수 반환 (찻집이 몇 개인지)
#    · .count()와 달리 NaN도 포함해서 셈
#  └ .reset_index(name='찻집_수')
#    · 그룹 키(상권_코드)를 다시 일반 컬럼으로 내려옴
#    · name='찻집_수': 집계된 수 컬럼의 이름 지정

df_result = df_map[['상권_코드', '상권_코드_명']].merge(tea_count, on='상권_코드', how='left')
#  └ df.merge(다른df, on=키컬럼, how='left')
#    · 두 DataFrame을 키 컬럼 기준으로 결합 (SQL의 JOIN)
#    · on='상권_코드': 두 DataFrame 모두에 있는 기준 컬럼
#    · how='left': 왼쪽(df_map) 기준 → 찻집 없는 상권도 유지 (찻집_수=NaN)
#    · how='inner': 양쪽 모두에 있는 행만 유지
#    · how='outer': 양쪽 모두 유지

df_result['찻집_수'] = df_result['찻집_수'].fillna(0).astype(int)
#  └ Series.fillna(값)
#    · NaN(결측값)을 지정한 값으로 채움
#    · 찻집 없는 상권의 NaN → 0으로 대체
#  └ .astype(int)
#    · 데이터 타입 변환 (float → int)
#    · fillna(0) 후에도 dtype이 float이므로 int로 명시 변환

print(f"\n상권별 집계 결과:")
print(f"  찻집 있는 상권: {(df_result['찻집_수'] > 0).sum()}개")
print(f"  찻집 0인 상권:  {(df_result['찻집_수'] == 0).sum()}개")
print(f"  최대 찻집_수:   {df_result['찻집_수'].max()}")

print(f"\n찻집 많은 상권 TOP 10:")
print(df_result.sort_values('찻집_수', ascending=False).head(10).to_string(index=False))
#  └ df.sort_values('컬럼', ascending=False)
#    · 지정 컬럼 기준으로 정렬
#    · ascending=False: 내림차순 (큰 값이 위)
#    · ascending=True: 오름차순 (기본값)


# ══════════════════════════════════════════════════════
# 5. 저장
# ══════════════════════════════════════════════════════
df_tea.to_csv('tea_shops_mapped.csv', index=False, encoding='utf-8-sig')
#  └ df.to_csv(경로, index=False, encoding='utf-8-sig')
#    · DataFrame을 CSV 저장 (17번에서 상세 설명)
print(f"\n[저장] tea_shops_mapped.csv  ({len(df_tea)}행) — 찻집별 매핑 상세")

df_result.to_csv('tea_shop_count.csv', index=False, encoding='utf-8-sig')
print(f"[저장] tea_shop_count.csv    ({len(df_result)}행) — 상권별 찻집_수")
