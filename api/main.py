import pandas as pd
import numpy as np
import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pyproj import Transformer
from scipy.spatial import cKDTree
import requests
import os
from dotenv import load_dotenv
load_dotenv()  # 로컬: api/.env 읽기 / Render: 환경변수로 대체됨

_LINE_NAMES = r'(\d+호선|경의중앙선|신분당선|경춘선|수인분당선|공항철도|경강선|서해선)'

def _format_subway(raw) -> str:
    """지하철_역_목록 → '2호선 강남역, 9호선 신논현역' 형식으로 정리 (중복 제거)"""
    if not raw or (isinstance(raw, float) and raw != raw):
        return ''
    tokens = re.findall(_LINE_NAMES + r'\s+(\S+역)', str(raw))
    seen, result = set(), []
    for line, station in tokens:
        key = f"{line} {station}"
        if key not in seen:
            seen.add(key)
            result.append(key)
    return ', '.join(result)

def _si(v, d=0):
    """안전한 int 변환 (NaN/None → d)"""
    try:
        f = float(v)
        return d if (f != f) else int(f)  # NaN check
    except:
        return d

def _sf(v, d=0.0):
    """안전한 float 변환 (NaN/None → d)"""
    try:
        f = float(v)
        return d if (f != f) else f
    except:
        return d

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
    # 찻집 위치 데이터 (가게명 조회용)
    df_teashops = pd.read_csv(os.path.join(DATA_DIR, "teashops.csv"))
    
    # NaN 처리
    df_ranking['찻집수_latest'] = df_ranking['찻집수_latest'].fillna(0)
    df_ranking['매출_latest'] = df_ranking['매출_latest'].fillna(0)
    df_ranking['사분면'] = df_ranking['사분면'].fillna('일반 상권')
    df_ranking['블루오션_랭킹'] = pd.to_numeric(df_ranking['블루오션_랭킹'], errors='coerce').fillna(9999)

    # 통합 순위 계산: Q1/Q2 중 더 유리한 점수 기준으로 전체 순위 산정
    df_ranking['unified_score'] = df_ranking[['q1_score', 'q2_score']].max(axis=1)
    df_ranking['unified_rank'] = df_ranking['unified_score'].rank(
        ascending=False, method='min').astype(int)

    # _pct 컬럼은 unified_ranking.csv에 미리 저장됨 (precompute_pct.py로 생성)
    # startup 시 rank 연산 불필요 → Render 콜드 스타트 타임아웃 방지

except Exception as e:
    print(f"Error loading data: {e}")
    df_map = pd.DataFrame(columns=['상권_코드', '상권_코드_명', '엑스좌표_값', '와이좌표_값'])
    df_ranking = pd.DataFrame()
    df_teashops = pd.DataFrame(columns=['가게명', '상권_코드_명'])

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

    quadrant = str(res['사분면'])
    urank = int(res['unified_rank']) if not pd.isna(res.get('unified_rank')) else None

    # 지하철 역 목록 → 'X호선 역명' 형식으로 정리
    subway_str = _format_subway(res.get('지하철_역_목록', ''))
    if not subway_str:
        n_lines = _si(res.get('지하철_노선_수_raw', res.get('지하철_노선_수', 0)))
        subway_str = f'{n_lines}개 노선 (1.5km 내)' if n_lines > 0 else '인근 지하철 없음 (1.5km 내)'

    # 검색지수 상위 % (카페_검색지수_pct 는 0~100 백분위)
    cafe_pct = _sf(res.get('카페_검색지수_pct', 50), 50.0)
    search_upper = max(1, round(100 - cafe_pct))

    # 해당 상권 찻집 이름 목록
    tea_names = []
    if not df_teashops.empty and '상권_코드_명' in df_teashops.columns:
        matched = df_teashops[df_teashops['상권_코드_명'] == target_name]
        tea_names = matched['가게명'].dropna().tolist()

    return {
        "address": address,
        "district_name": target_name,
        "ranking": urank,
        "total_ranked": TOTAL_RANKED,
        "quadrant": quadrant,
        "sales_total": sales_total,
        "sales_per_store": sales_per_store,
        "sales_prediction": sales_total,
        "cafe_store_count": int(cafe_store_count),
        "tea_shop_count": int(res['찻집수_latest']),
        "tea_shop_names": tea_names,
        "supply_shortage": round(float(res.get('supply_shortage', 0)) * 100, 1),
        "is_blue_ocean": quadrant in ('Q1_검증시장공백', 'Q2_잠재수요미실현'),
        "demand_factors": [
            {"subject": "집객시설", "value": round(_sf(res.get('집객시설_수_pct', 50), 50), 1),
             "detail": f"{_si(res.get('집객시설_수_raw', 0)):,}개"},
            {"subject": "직장인구", "value": round(_sf(res.get('총_직장_인구_수_pct', 50), 50), 1),
             "detail": f"{_si(res.get('총_직장_인구_수_raw', 0)):,}명"},
            {"subject": "소득금액", "value": round(_sf(res.get('월_평균_소득_금액_pct', 50), 50), 1),
             "detail": f"월 {_si(res.get('월_평균_소득_금액_raw', 0)) // 10000:,}만원"},
            {"subject": "가구수",   "value": round(_sf(res.get('총_가구_수_pct', 50), 50), 1),
             "detail": f"{_si(res.get('총_가구_수_raw', 0)):,}가구"},
            {"subject": "검색지수", "value": round(cafe_pct, 1),
             "detail": f"서울 내 상위 {search_upper}%"},
            {"subject": "지하철",   "value": round(_sf(res.get('지하철_노선_수_pct', 50), 50), 1),
             "detail": subway_str},
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
