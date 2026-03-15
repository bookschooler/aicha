"""
19_map_tea_shops.py
찻집 WGS84 좌표 → 최근접 상권 센트로이드 매핑 → 상권별 찻집_수 집계
"""
import os
import pandas as pd
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

os.chdir('/teamspace/studios/this_studio/aicha')

# ──────────────────────────────────────────
# 1. 데이터 로드
# ──────────────────────────────────────────
df_tea = pd.read_csv('tea_shops_list.csv')
df_map = pd.read_csv('to_map.csv')

print(f"찻집 수: {len(df_tea)}")
print(f"상권 수: {len(df_map)}")

# ──────────────────────────────────────────
# 2. 찻집 WGS84 → TM(EPSG:5181) 변환
# ──────────────────────────────────────────
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
tea_x, tea_y = transformer.transform(df_tea['lon'].values, df_tea['lat'].values)
df_tea = df_tea.copy()
df_tea['tm_x'] = tea_x
df_tea['tm_y'] = tea_y

# ──────────────────────────────────────────
# 3. KDTree로 최근접 상권 매핑
# ──────────────────────────────────────────
map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values
tree = cKDTree(map_coords)

distances, indices = tree.query(np.column_stack([tea_x, tea_y]), k=1)

df_tea['상권_코드']    = df_map['상권_코드'].values[indices]
df_tea['상권_코드_명']  = df_map['상권_코드_명'].values[indices]
df_tea['nearest_dist_m'] = distances

print(f"\n최근접 상권 매핑 완료")
print(f"평균 거리: {distances.mean():.0f}m | 최대: {distances.max():.0f}m")
print(f"500m 이내: {(distances <= 500).mean()*100:.1f}% | 1km 이내: {(distances <= 1000).mean()*100:.1f}%")

# ──────────────────────────────────────────
# 4. 상권별 찻집_수 집계 (전체 1,650개 기준, 없으면 0)
# ──────────────────────────────────────────
tea_count = df_tea.groupby('상권_코드').size().reset_index(name='찻집_수')

df_result = df_map[['상권_코드', '상권_코드_명']].merge(tea_count, on='상권_코드', how='left')
df_result['찻집_수'] = df_result['찻집_수'].fillna(0).astype(int)

print(f"\n상권별 집계 결과:")
print(f"  찻집 있는 상권: {(df_result['찻집_수'] > 0).sum()}개")
print(f"  찻집 0인 상권:  {(df_result['찻집_수'] == 0).sum()}개")
print(f"  최대 찻집_수:   {df_result['찻집_수'].max()}")

print(f"\n찻집 많은 상권 TOP 10:")
print(df_result.sort_values('찻집_수', ascending=False).head(10).to_string(index=False))

# ──────────────────────────────────────────
# 5. 저장
# ──────────────────────────────────────────
df_tea.to_csv('tea_shops_mapped.csv', index=False, encoding='utf-8-sig')
print(f"\n[저장] tea_shops_mapped.csv  ({len(df_tea)}행) — 찻집별 매핑 상세")

df_result.to_csv('tea_shop_count.csv', index=False, encoding='utf-8-sig')
print(f"[저장] tea_shop_count.csv    ({len(df_result)}행) — 상권별 찻집_수")
