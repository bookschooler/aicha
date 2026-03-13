import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pyproj import Transformer
from scipy.spatial import cKDTree
import requests
import os
from dotenv import load_dotenv
load_dotenv()  # 로컬: api/.env 읽기 / Render: 환경변수로 대체됨

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 로드
DATA_DIR = os.path.dirname(__file__)
try:
    df_map = pd.read_csv(os.path.join(DATA_DIR, "to_map.csv"))
    # 35_blueocean_ranking.csv 에서 복사된 파일 (1,038개 상권 전체 데이터)
    df_ranking = pd.read_csv(os.path.join(DATA_DIR, "unified_ranking.csv"))
    
    # NaN 처리
    df_ranking['찻집수_latest'] = df_ranking['찻집수_latest'].fillna(0)
    df_ranking['매출_latest'] = df_ranking['매출_latest'].fillna(0)
    df_ranking['사분면'] = df_ranking['사분면'].fillna('일반 상권')
    df_ranking['블루오션_랭킹'] = pd.to_numeric(df_ranking['블루오션_랭킹'], errors='coerce').fillna(9999)

    # 사분면별 내부 순위 계산 (사분면 분류와 일관된 순위 제공)
    q1_mask = df_ranking['사분면'] == 'Q1_검증시장공백'
    q2_mask = df_ranking['사분면'] == 'Q2_잠재수요미실현'
    df_ranking.loc[q1_mask, 'q1_rank'] = \
        df_ranking.loc[q1_mask, 'q1_score'].rank(ascending=False, method='min').astype(int)
    df_ranking.loc[q2_mask, 'q2_rank'] = \
        df_ranking.loc[q2_mask, 'q2_score'].rank(ascending=False, method='min').astype(int)

except Exception as e:
    print(f"Error loading data: {e}")
    df_map = pd.DataFrame(columns=['상권_코드', '상권_코드_명', '엑스좌표_값', '와이좌표_값'])
    df_ranking = pd.DataFrame()

# 사분면별 총 수 (사전 계산)
Q1_TOTAL = int((df_ranking['사분면'] == 'Q1_검증시장공백').sum()) if not df_ranking.empty else 0
Q2_TOTAL = int((df_ranking['사분면'] == 'Q2_잠재수요미실현').sum()) if not df_ranking.empty else 0

# KDTree 구성 — ranked 상권(unified_ranking.csv)만 사용해 항상 유효한 매핑 보장
ranked_names = set(df_ranking['상권_코드_명']) if not df_ranking.empty else set()
df_map_ranked = df_map[df_map['상권_코드_명'].isin(ranked_names)].reset_index(drop=True)
TOTAL_RANKED = len(df_map_ranked)

if not df_map_ranked.empty:
    map_coords = df_map_ranked[['엑스좌표_값', '와이좌표_값']].values
    tree = cKDTree(map_coords)
else:
    tree = None

transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)

def get_coords_from_kakao(address: str):
    """Kakao Geocoding API를 활용하여 주소 -> 좌표 변환"""
    API_KEY = os.environ.get("KAKAO_API_KEY", "")
    if not API_KEY:
        return None

    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {API_KEY}"}

    try:
        res = requests.get(url, headers=headers, params={"query": address}, timeout=5)
        data = res.json()
        if data.get("documents"):
            doc = data["documents"][0]
            return float(doc["y"]), float(doc["x"])  # lat, lon
    except:
        pass
    return None

@app.get("/")
def read_root():
    return {"status": "online", "message": "BlueOcean Finder API is running"}

@app.get("/search")
def search_district(address: str = Query(..., description="검색할 주소")):
    if tree is None:
        raise HTTPException(status_code=500, detail="Data not loaded.")
    
    coords = get_coords_from_kakao(address)
    if coords is None:
        raise HTTPException(status_code=400, detail="주소를 찾을 수 없습니다. 더 구체적인 주소(구·동 포함)를 입력해 주세요.")
    lat, lon = coords
    tm_x, tm_y = transformer.transform(lon, lat)
    _, index = tree.query([tm_x, tm_y], k=1)
    
    target_name = df_map_ranked.iloc[index]['상권_코드_명']
    ranking_row = df_ranking[df_ranking['상권_코드_명'] == target_name]
    
    default_demand = [
        {"subject": "집객시설", "value": 50},
        {"subject": "직장인구", "value": 50},
        {"subject": "소득금액", "value": 50},
        {"subject": "가구수",   "value": 50},
        {"subject": "검색지수", "value": 50},
        {"subject": "지하철",   "value": 50},
    ]

    if ranking_row.empty:
        return {
            "address": address,
            "district_name": target_name,
            "ranking": None,
            "total_ranked": TOTAL_RANKED,
            "quadrant": None,
            "sales_prediction": None,
            "tea_shop_count": 0,
            "is_blue_ocean": False,
            "demand_factors": default_demand,
        }

    res = ranking_row.iloc[0]
    # 분기 매출 → 월 환산
    cafe_store_count = float(res.get('카페음료_점포수', 1)) or 1
    sales_total = float(res['매출_latest']) / 3
    sales_per_store = float(res.get('cafe_revenue_per_store', res['매출_latest'] / cafe_store_count)) / 3

    # 사분면에 맞는 내부 순위 계산
    quadrant = str(res['사분면'])
    if quadrant == 'Q1_검증시장공백':
        qrank = int(res['q1_rank']) if not pd.isna(res.get('q1_rank')) else None
        qtotal = Q1_TOTAL
    elif quadrant == 'Q2_잠재수요미실현':
        qrank = int(res['q2_rank']) if not pd.isna(res.get('q2_rank')) else None
        qtotal = Q2_TOTAL
    else:
        qrank = None
        qtotal = None

    return {
        "address": address,
        "district_name": target_name,
        "ranking": qrank,
        "total_ranked": qtotal,
        "quadrant": quadrant,
        "sales_total": sales_total,       # 상권 내 카페음료 업종 전체 월매출 합산
        "sales_per_store": sales_per_store,  # 점포당 월평균 매출
        "sales_prediction": sales_total,  # 하위 호환용 (기존 필드 유지)
        "cafe_store_count": int(cafe_store_count),
        "tea_shop_count": int(res['찻집수_latest']),
        "supply_shortage": round(float(res.get('supply_shortage', 0)) * 100, 1),  # 0~1 → 0~100%
        "is_blue_ocean": bool(res.get('구조적블루오션', False)),
        "demand_factors": [
            {"subject": "집객시설", "value": round(float(res.get('집객시설_수_pct', 50)), 1)},
            {"subject": "직장인구", "value": round(float(res.get('총_직장_인구_수_pct', 50)), 1)},
            {"subject": "소득금액", "value": round(float(res.get('월_평균_소득_금액_pct', 50)), 1)},
            {"subject": "가구수",   "value": round(float(res.get('총_가구_수_pct', 50)), 1)},
            {"subject": "검색지수", "value": round(float(res.get('카페_검색지수_pct', 50)), 1)},
            {"subject": "지하철",   "value": round(float(res.get('지하철_노선_수_pct', 50)), 1)},
        ],
    }

@app.get("/scatter")
def get_scatter_data():
    """2D 매트릭스 scatter plot용 전체 상권 데이터"""
    cols = ['상권_코드_명', 'supply_shortage', 'residual_latest', '사분면']
    if df_ranking.empty:
        return {"points": [], "threshold_x": 0.999, "threshold_y": 0.0}

    sub = df_ranking[[c for c in cols if c in df_ranking.columns]].copy()
    sub = sub.dropna(subset=['supply_shortage', 'residual_latest'])

    # supply_shortage는 대부분 1.0에 몰려있어서 시각적 jitter 추가 (seed 고정)
    rng = np.random.default_rng(42)
    sub['x'] = sub['supply_shortage'] + rng.uniform(-0.025, 0.025, len(sub))
    sub['y'] = sub['residual_latest']

    return {
        "points": sub[['상권_코드_명', 'x', 'y', '사분면']].to_dict(orient='records'),
        "threshold_x": 0.999,
        "threshold_y": 0.0,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
