# 42_tableau_geojson.py
# Shapefile + 블루오션 데이터를 미리 합쳐서 GeoJSON으로 저장
# → Tableau에서 조인 없이 바로 연결 가능
#
# 핵심:
#   1. Shapefile CRS(EPSG:5181) → WGS84(EPSG:4326) 변환 (Tableau는 WGS84 필요)
#   2. TRDAR_CD(str) = 상권_코드(str 변환) 로 merge
#   3. 불필요한 컬럼 제거 후 GeoJSON 저장
#
# 출력:
#   41_tableau_blueocean_map.geojson  — Tableau 슬라이드 1 전용
#   42_geojson_log.txt

import geopandas as gpd
import pandas as pd
import os, json

BASE = os.path.dirname(os.path.abspath(__file__))
logs = []
def log(msg): print(msg); logs.append(msg)

log("=" * 60)
log("42_tableau_geojson.py 시작")
log("=" * 60)

# ── 1. Shapefile 읽기 ───────────────────────────────────────────
shp_path = os.path.join(BASE, '상권_영역', '서울시 상권분석서비스(영역-상권).shp')
gdf = gpd.read_file(shp_path, encoding='cp949')
log(f"\n[1] Shapefile 로드: {len(gdf)}행, CRS={gdf.crs}")

# ── 2. WGS84로 좌표계 변환 (Tableau는 EPSG:4326 필요) ──────────
gdf = gdf.to_crs(epsg=4326)
log(f"[2] 좌표계 변환 완료: EPSG:5181 → EPSG:4326")

# ── 3. 필요한 컬럼만 추출 ───────────────────────────────────────
gdf = gdf[['TRDAR_CD', 'TRDAR_SE_C', 'geometry']].copy()
gdf = gdf.rename(columns={'TRDAR_CD': '상권_코드', 'TRDAR_SE_C': '상권구분코드'})
gdf['상권_코드'] = gdf['상권_코드'].astype(str).str.strip()
log(f"[3] 컬럼 정리: {gdf.columns.tolist()}")

# ── 4. 블루오션 데이터 로드 ─────────────────────────────────────
sangwon = pd.read_csv(os.path.join(BASE, '41_tableau_sangwon.csv'), encoding='utf-8-sig')
sangwon['상권_코드'] = sangwon['상권_코드'].astype(str).str.strip()

# Tableau에 넣을 컬럼만 선택 (geometry 파일 용량 최소화)
keep_cols = [
    '상권_코드', '상권_코드_명', '상권유형', '자치구_코드_명',
    '사분면', '사분면_레이블', '블루오션여부', '구조적블루오션',
    'residual_latest', 'supply_shortage',
    '찻집수_latest', '매출_latest', '카페음료_점포수',
    '통합순위_top30', '피타고라스거리', 'lon', 'lat'
]
keep_cols = [c for c in keep_cols if c in sangwon.columns]
sangwon_slim = sangwon[keep_cols]
log(f"[4] 블루오션 데이터: {len(sangwon_slim)}행, 컬럼={len(keep_cols)}개")

# ── 5. Merge ────────────────────────────────────────────────────
merged = gdf.merge(sangwon_slim, on='상권_코드', how='left')
matched = merged['상권_코드_명'].notna().sum()
log(f"[5] Merge 완료: 전체 {len(merged)}행, 데이터 매칭 {matched}행 ({len(merged)-matched}개 미매칭)")

# ── 6. GeoJSON 저장 ─────────────────────────────────────────────
out_path = os.path.join(BASE, '41_tableau_blueocean_map.geojson')
merged.to_file(out_path, driver='GeoJSON', encoding='utf-8')
size_mb = os.path.getsize(out_path) / 1024 / 1024
log(f"[6] GeoJSON 저장 완료: 41_tableau_blueocean_map.geojson ({size_mb:.1f} MB)")

# ── 7. 확인 ─────────────────────────────────────────────────────
log("\n사분면 분포:")
dist = merged['사분면'].value_counts(dropna=False)
for k, v in dist.items():
    log(f"  {k}: {v}개")

log("\n" + "=" * 60)
log("Tableau 연결 방법:")
log("  1. Connect > Spatial File → 41_tableau_blueocean_map.geojson 선택")
log("  2. Geometry 더블클릭 → 지도 자동 생성")
log("  3. Color → 사분면_레이블")
log("  4. 찻집 레이어: 두 번째 데이터소스 → 41_tableau_teashops.csv")
log("     계산 필드: MAKEPOINT([lat],[lon]) → Dual Axis")
log("=" * 60)

with open(os.path.join(BASE, '42_geojson_log.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(logs))
print("\n로그 저장: 42_geojson_log.txt")
