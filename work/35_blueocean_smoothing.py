# 35_blueocean_smoothing.py
# 공간적 평활화(Spatial Smoothing)를 통한 공급지수 안정화
# 
# 목적: 찻집 데이터의 희소성으로 인한 지표 변동성(점포 1개 차이에 급변)을 해결
# 방법: 내 상권 지표(70%) + 반경 500m 내 인접 상권 평균 지표(30%) 가중 평균
# 
# 입력: 35_blueocean_ranking.csv, api/to_map.csv
# 출력: 35_blueocean_ranking_smoothed.csv (최종 안정화 버전)

import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import os

BASE = os.path.dirname(os.path.abspath(__file__))
IN_RANK = os.path.join(BASE, '35_blueocean_ranking.csv')
IN_MAP  = os.path.join(BASE, 'api', 'to_map.csv')
OUT_RANK = os.path.join(BASE, '35_blueocean_ranking_smoothed.csv')
API_OUT  = os.path.join(BASE, 'api', 'unified_ranking.csv')

print("=== 공간적 평활화(Spatial Smoothing) 프로세스 시작 ===")

# 1. 데이터 로드
df_rank = pd.read_csv(IN_RANK, encoding='utf-8-sig')
df_map  = pd.read_csv(IN_MAP, encoding='utf-8-sig')

# 좌표 정보 매핑 (상권_코드 기준)
coords = df_map[['상권_코드', '엑스좌표_값', '와이좌표_값']].drop_duplicates('상권_코드')
df = df_rank.merge(coords, on='상권_코드', how='left')

# 좌표가 없는 데이터 제외 (분석의 신뢰성 확보)
df = df.dropna(subset=['엑스좌표_값', '와이좌표_값'])
print(f"좌표 매핑 완료: {len(df)}개 상권")

# 2. KDTree 구성 및 인접 상권 검색 (반경 500m)
tree = cKDTree(df[['엑스좌표_값', '와이좌표_값']].values)
radius = 500  # 500미터
all_neighbors = tree.query_ball_point(df[['엑스좌표_값', '와이좌표_값']].values, radius)

# 3. 공급지수 평활화 계산
# q2_supply_score = 기존 복합 공급지수
smoothed_supply = []

for i, neighbors in enumerate(all_neighbors):
    my_val = df.iloc[i]['q2_supply_score']
    
    if len(neighbors) > 1: # 나 자신 제외 인접 상권이 있는 경우
        neighbor_indices = [idx for idx in neighbors if idx != i]
        neighbor_avg = df.iloc[neighbor_indices]['q2_supply_score'].mean()
        # 가중 평균 (나: 0.7, 주변: 0.3)
        smoothed_val = (my_val * 0.7) + (neighbor_avg * 0.3)
    else:
        smoothed_val = my_val # 인접 상권이 없으면 그대로 유지
        
    smoothed_supply.append(smoothed_val)

df['q2_supply_score'] = smoothed_supply
df['q1_supply_score'] = smoothed_supply

# 4. 스코어 및 사분면 재분류
# Q2 스코어 = 0.5 * 잔차점수 + 0.5 * 평활화공급점수
df['q2_score'] = 0.5 * df['q2_residual_score'] + 0.5 * df['q2_supply_score']
df['q1_score'] = 0.5 * df['q1_residual_score'] + 0.5 * df['q1_supply_score']

# 랭킹 재산정
df['블루오션_랭킹'] = df['q2_score'].rank(ascending=False, method='min').astype(int)
df = df.sort_values('블루오션_랭킹')

# 불필요한 좌표 컬럼 제거 후 저장
# 모든 원본 컬럼 유지 (백엔드에서 다양한 Demand Factors를 보여줘야 하므로)
final_df = df.drop(columns=['엑스좌표_값', '와이좌표_값'])

final_df.to_csv(OUT_RANK, index=False, encoding='utf-8-sig')
final_df.to_csv(API_OUT, index=False, encoding='utf-8-sig') # 백엔드 연동용 서빙 데이터 교체

print(f"결과 저장 완료: {OUT_RANK}")
print(f"백엔드 데이터 업데이트 완료: {API_OUT}")
print("=== 평활화 완료! 이제 점포 1개 차이에 지표가 흔들리지 않습니다. ===")
