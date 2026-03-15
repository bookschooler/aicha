import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
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
    df_ranking = pd.read_csv(os.path.join(DATA_DIR, "unified_ranking.csv"))
except Exception as e:
    print(f"Error loading data: {e}")
    # 파일이 없는 경우 빈 데이터프레임 생성 (테스트용)
    df_map = pd.DataFrame(columns=['상권_코드', '상권_코드_명', '엑스좌표_값', '와이좌표_값'])
    df_ranking = pd.DataFrame()

# KDTree 구성 (최근접 상권 검색용)
if not df_map.empty:
    map_coords = df_map[['엑스좌표_값', '와이좌표_값']].values
    tree = cKDTree(map_coords)
else:
    tree = None

# 좌표 변환기 (WGS84 -> EPSG:5181)
# pyproj transformer는 tree 유무와 관계없이 생성 가능
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)

@app.get("/")
def read_root():
    return {"message": "BlueOcean Finder API is running"}

@app.get("/search")
def search_district(address: str):
    if tree is None:
        raise HTTPException(status_code=500, detail="Data not loaded properly.")
    
    # 1. 주소 -> 좌표 변환 (Vworld API 또는 Kakao API 사용 제안)
    # 여기서는 고정된 좌표 변환 로직 구조만 작성
    
    # 2. 좌표 -> 상권 매핑 (Mock data for demo)
    # 실무에서는 geocoding API 연동 필요
    lat, lon = 37.5908, 127.0560  # 외대앞역 부근 예시
    
    tm_x, tm_y = transformer.transform(lon, lat)
    dist, index = tree.query([tm_x, tm_y], k=1)
    
    target_district_code = df_map.iloc[index]['상권_코드']
    target_district_name = df_map.iloc[index]['상권_코드_명']
    
    # 3. 랭킹 데이터 결합
    if df_ranking.empty:
        return {"district_name": target_district_name, "message": "Ranking data not available."}
        
    ranking_info = df_ranking[df_ranking['상권_코드_명'] == target_district_name].to_dict('records')
    
    if not ranking_info:
        return {
            "address": address,
            "district_name": target_district_name,
            "ranking": "순위권 밖",
            "quadrant": "N/A",
            "message": "해당 주소는 상권 영역에는 포함되나 Top 30 랭킹 데이터에는 없습니다."
        }
    
    res = ranking_info[0]
    return {
        "address": address,
        "district_name": target_district_name,
        "ranking": int(res['통합_순위']),
        "quadrant": res['사분면'],
        "sales_prediction": float(res['매출_latest']),
        "tea_shop_count": int(res['찻집수_latest']),
        "is_blue_ocean": bool(res['구조적블루오션'])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
