"""
20_crawl_starbucks_reserve.py
카카오 로컬 API로 서울 스타벅스 리저브 매장 수집 → 상권별 집계
"""
import os
import pandas as pd
import numpy as np
import requests
import time
from pyproj import Transformer
from scipy.spatial import cKDTree
from dotenv import load_dotenv

os.chdir('/teamspace/studios/this_studio/aicha')
load_dotenv()

KAKAO_KEY = os.getenv('KAKAO_API_KEY')
HEADERS = {'Authorization': f'KakaoAK {KAKAO_KEY}'}

# ──────────────────────────────────────────
# 1. 카카오 API로 스타벅스 리저브 수집
# ──────────────────────────────────────────
def search_kakao(query, x, y, radius=20000):
    """카카오 키워드 검색 — 한 페이지"""
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    results = []
    for page in range(1, 4):  # 최대 3페이지 (45건)
        params = {
            'query': query,
            'x': x, 'y': y,
            'radius': radius,
            'page': page,
            'size': 15,
        }
        resp = requests.get(url, headers=HEADERS, params=params, timeout=5)
        data = resp.json()
        items = data.get('documents', [])
        results.extend(items)
        if data['meta']['is_end']:
            break
        time.sleep(0.1)
    return results

# 서울 중심 좌표 (WGS84)
SEOUL_X, SEOUL_Y = 126.9779, 37.5663

print("스타벅스 리저브 수집 중...")
raw = search_kakao('스타벅스 리저브', x=SEOUL_X, y=SEOUL_Y, radius=20000)
print(f"수집: {len(raw)}건")

# ──────────────────────────────────────────
# 2. 서울 필터링 & 정제
# ──────────────────────────────────────────
df = pd.DataFrame(raw)
if df.empty:
    print("결과 없음!")
    exit()

df = df.rename(columns={
    'place_name': '가게명',
    'address_name': '지번주소',
    'road_address_name': '도로명주소',
    'phone': '전화번호',
    'place_url': 'URL',
    'category_name': '카테고리',
    'x': 'lon',
    'y': 'lat',
})

df['lon'] = df['lon'].astype(float)
df['lat'] = df['lat'].astype(float)

# 서울만 필터링
df = df[df['도로명주소'].str.startswith('서울', na=False)].copy()
print(f"서울 내: {len(df)}개")

# 중복 제거 (가게명+주소 기준)
df = df.drop_duplicates(subset=['가게명', '지번주소']).reset_index(drop=True)
print(f"중복 제거 후: {len(df)}개")
print(df[['가게명', '도로명주소']].to_string())

# ──────────────────────────────────────────
# 3. WGS84 → TM → 최근접 상권 매핑
# ──────────────────────────────────────────
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
sb_x, sb_y = transformer.transform(df['lon'].values, df['lat'].values)
df['tm_x'] = sb_x
df['tm_y'] = sb_y

df_map = pd.read_csv('to_map.csv')
map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values
tree = cKDTree(map_coords)

distances, indices = tree.query(np.column_stack([sb_x, sb_y]), k=1)
df['상권_코드']      = df_map['상권_코드'].values[indices]
df['상권_코드_명']   = df_map['상권_코드_명'].values[indices]
df['nearest_dist_m'] = distances

print(f"\n매핑 완료 — 평균 거리: {distances.mean():.0f}m | 최대: {distances.max():.0f}m")

# ──────────────────────────────────────────
# 4. 상권별 스타벅스_리저브_수 집계
# ──────────────────────────────────────────
sb_count = df.groupby('상권_코드').size().reset_index(name='스타벅스_리저브_수')

df_result = df_map[['상권_코드', '상권_코드_명']].merge(sb_count, on='상권_코드', how='left')
df_result['스타벅스_리저브_수'] = df_result['스타벅스_리저브_수'].fillna(0).astype(int)

print(f"\n스타벅스 리저브 있는 상권: {(df_result['스타벅스_리저브_수'] > 0).sum()}개")
print(f"\nTOP 10:")
print(df_result.sort_values('스타벅스_리저브_수', ascending=False).head(10).to_string(index=False))

# ──────────────────────────────────────────
# 5. 저장
# ──────────────────────────────────────────
df.to_csv('starbucks_reserve_mapped.csv', index=False, encoding='utf-8-sig')
print(f"\n[저장] starbucks_reserve_mapped.csv ({len(df)}행)")

df_result.to_csv('starbucks_reserve_count.csv', index=False, encoding='utf-8-sig')
print(f"[저장] starbucks_reserve_count.csv ({len(df_result)}행)")
