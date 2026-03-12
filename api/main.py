import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pyproj import Transformer
from scipy.spatial import cKDTree
import requests
import os

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
    
except Exception as e:
    print(f"Error loading data: {e}")
    df_map = pd.DataFrame(columns=['상권_코드', '상권_코드_명', '엑스좌표_값', '와이좌표_값'])
    df_ranking = pd.DataFrame()

# KDTree 구성
if not df_map.empty:
    map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values
    tree = cKDTree(map_coords)
else:
    tree = None

transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)

def get_coords_from_vworld(address: str):
    """Vworld Geocoding API를 활용하여 주소 -> 좌표 변환"""
    API_KEY = "7E5E3E6A-9B3B-3B3B-3B3B-3B3B3B3B3B3B" # Placeholder
    url = f"http://api.vworld.kr/req/address?service=address&request=getcoord&version=2.0&crs=epsg:4326&address={address}&refine=true&simple=false&format=json&type=road&key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
        if data.get("response", {}).get("status") == "OK":
            coords = data["response"]["result"]["point"]
            return float(coords["y"]), float(coords["x"])
    except:
        pass
    
    # Fallback for demo
    if "영등포" in address: return 37.520, 126.910
    if "회기" in address: return 37.590, 127.056
    return 37.566, 126.978

@app.get("/")
def read_root():
    return {"status": "online", "message": "BlueOcean Finder API is running"}

@app.get("/search")
def search_district(address: str = Query(..., description="검색할 주소")):
    if tree is None:
        raise HTTPException(status_code=500, detail="Data not loaded.")
    
    lat, lon = get_coords_from_vworld(address)
    tm_x, tm_y = transformer.transform(lon, lat)
    _, index = tree.query([tm_x, tm_y], k=1)
    
    target_name = df_map.iloc[index]['상권_코드_명']
    ranking_row = df_ranking[df_ranking['상권_코드_명'] == target_name]
    
    if ranking_row.empty:
        return {
            "address": address,
            "district_name": target_name,
            "ranking": "순위권 밖",
            "quadrant": "일반 상권",
            "sales_prediction": 0,
            "tea_shop_count": 0,
            "is_blue_ocean": False
        }
    
    res = ranking_row.iloc[0]
    return {
        "address": address,
        "district_name": target_name,
        "ranking": int(res['블루오션_랭킹']) if res['블루오션_랭킹'] < 9999 else "순위권 밖",
        "quadrant": str(res['사분면']),
        "sales_prediction": float(res['매출_latest']),
        "tea_shop_count": int(res['찻집수_latest']),
        "is_blue_ocean": bool(res['구조적블루오션']),
        "demand_factors": [
            {"subject": "직장인구", "value": float(res.get('q2_supply_score', 0.5)) * 100},
            {"subject": "가구수", "value": float(res.get('q1_supply_score', 0.5)) * 100},
            {"subject": "소득금액", "value": float(res.get('q2_residual_score', 0.5)) * 100},
            {"subject": "지하철", "value": float(res.get('q1_residual_score', 0.5)) * 100},
            {"subject": "집객시설", "value": float(res.get('q1_score', 0.5)) * 100},
            {"subject": "검색지수", "value": float(res.get('q2_score', 0.5)) * 100}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
