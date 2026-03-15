"""
찻집 크롤링용 검색어 조합 생성 스크립트
===========================================
흐름:
  1단계 : to_map.csv TM(EPSG:5181) → WGS84 좌표 변환
  2단계 : 상권코드명에서 역명 추출 → 카카오 API로 역 WGS84 좌표 수집
  3단계 : 상권별 최근접 지하철역 매핑 (scipy KDTree)
  4단계 : 상권코드명에서 랜드마크 추출
  5단계 : 검색어 조합 생성 (행정동명 + 역명 + 랜드마크 + 키워드)
  출력  : search_keywords.csv
"""

import pandas as pd
import numpy as np
import requests
import time
import re
import os
from pyproj import Transformer
from scipy.spatial import cKDTree
from dotenv import load_dotenv

load_dotenv()   # .env 파일 자동 로드

# =====================================================
# 설정
# =====================================================
KAKAO_API_KEY = os.environ["KAKAO_API_KEY"]
DATA_PATH     = os.path.dirname(os.path.abspath(__file__))
TO_MAP_PATH   = os.path.join(DATA_PATH, "to_map.csv")
OUTPUT_PATH   = os.path.join(DATA_PATH, "search_keywords.csv")
STATION_CACHE = os.path.join(DATA_PATH, "station_coords.csv")   # 중간 저장

TEA_KEYWORDS = ["찻집", "티룸", "티하우스", "티카페", "다원"]

# =====================================================
# 1단계: to_map.csv TM → WGS84 좌표 변환
# =====================================================
def convert_tm_to_wgs84(df: pd.DataFrame) -> pd.DataFrame:
    """
    to_map.csv의 엑스좌표_값, 와이좌표_값 (EPSG:5181 TM)
    → 경도(lon), 위도(lat) (WGS84) 로 변환
    """
    print("📍 1단계: TM → WGS84 좌표 변환 중...")
    transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326", always_xy=True)
    lons, lats = transformer.transform(
        df["엑스좌표_값"].values,
        df["와이좌표_값"].values
    )
    df = df.copy()
    df["lon"] = lons
    df["lat"] = lats
    print(f"   ✅ {len(df)}개 상권 변환 완료")
    return df


# =====================================================
# 2단계: 역 좌표 수집 (카카오 키워드 검색 API)
# =====================================================
def extract_station_names(df: pd.DataFrame) -> list[str]:
    """상권코드명에서 유니크 역명 추출"""
    station_set = set()
    for name in df["상권_코드_명"]:
        if "역" in name:
            match = re.match(r"(.+역)\s*\d*번?$", name.strip())
            if match:
                station_set.add(match.group(1))
    return sorted(station_set)


def get_station_coords_kakao(station_names: list[str], api_key: str) -> pd.DataFrame:
    """
    카카오 키워드 검색 API로 역명 → WGS84 좌표 수집
    캐시 파일이 있으면 재사용 (API 절약)
    """
    # 캐시 있으면 바로 반환
    if os.path.exists(STATION_CACHE):
        cached = pd.read_csv(STATION_CACHE, encoding="utf-8-sig")
        print(f"   📦 캐시 로드: {len(cached)}개 역 좌표 (재수집 생략)")
        return cached

    print(f"🚇 2단계: {len(station_names)}개 역 좌표 수집 중...")
    headers = {"Authorization": f"KakaoAK {api_key}"}
    url     = "https://dapi.kakao.com/v2/local/search/keyword.json"

    rows = []
    for i, station in enumerate(station_names, 1):
        params = {"query": station, "size": 1, "category_group_code": "SW8"}  # SW8 = 지하철역
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            data = resp.json()
            docs = data.get("documents", [])
            if docs:
                rows.append({
                    "역명": station,
                    "역_lon": float(docs[0]["x"]),
                    "역_lat": float(docs[0]["y"]),
                })
            else:
                # SW8 카테고리로 못 찾으면 카테고리 없이 재시도
                params2 = {"query": station, "size": 1}
                resp2   = requests.get(url, headers=headers, params=params2, timeout=5)
                docs2   = resp2.json().get("documents", [])
                if docs2:
                    rows.append({
                        "역명": station,
                        "역_lon": float(docs2[0]["x"]),
                        "역_lat": float(docs2[0]["y"]),
                    })
                else:
                    print(f"   ⚠️  좌표 없음: {station}")
        except Exception as e:
            print(f"   ❌ 오류 ({station}): {e}")

        if i % 50 == 0:
            print(f"   {i}/{len(station_names)} 완료...")
        time.sleep(0.2)   # API rate limit 준수

    df_stations = pd.DataFrame(rows)
    df_stations.to_csv(STATION_CACHE, index=False, encoding="utf-8-sig")
    print(f"   ✅ {len(df_stations)}개 역 좌표 수집 완료 → {STATION_CACHE}")
    return df_stations


# =====================================================
# 3단계: 상권별 최근접 지하철역 매핑 (KDTree)
# =====================================================
def map_nearest_station(df_map: pd.DataFrame, df_stations: pd.DataFrame) -> pd.DataFrame:
    """
    각 상권의 WGS84 좌표에서 가장 가까운 지하철역을 찾아
    '최근접_역명', '최근접_역_거리m' 컬럼 추가
    """
    print("🔍 3단계: 최근접 지하철역 매핑 중 (KDTree)...")

    # KDTree용 좌표 배열 (단위: 도 → 거리 근사를 위해 위도 기준 스케일링)
    # 서울 위도 ~37.5° 기준: 경도 1도 ≈ 88.8km, 위도 1도 ≈ 111km
    LAT_REF = 37.5
    LON_SCALE = np.cos(np.radians(LAT_REF))   # 경도 보정 계수

    station_coords = df_stations[["역_lon", "역_lat"]].values.copy()
    station_coords[:, 0] *= LON_SCALE          # 경도 스케일 보정

    map_coords = df_map[["lon", "lat"]].values.copy()
    map_coords[:, 0] *= LON_SCALE

    tree = cKDTree(station_coords)
    dists, idxs = tree.query(map_coords, k=1)

    # 도 단위 거리 → 미터 변환 (위도 1도 ≈ 111,320m)
    dists_m = dists * 111320

    df_result = df_map.copy()
    df_result["최근접_역명"]    = df_stations["역명"].values[idxs]
    df_result["최근접_역_거리m"] = np.round(dists_m).astype(int)

    # 거리 분포 확인
    print(f"   거리 분포: 중앙값={np.median(dists_m):.0f}m  "
          f"75%={np.percentile(dists_m,75):.0f}m  "
          f"최대={dists_m.max():.0f}m")
    far_count = (dists_m > 1000).sum()
    print(f"   ⚠️  1km 초과 상권: {far_count}개 (검색어 품질 주의)")
    print(f"   ✅ 최근접 역 매핑 완료")
    return df_result


# =====================================================
# 4단계: 상권코드명에서 랜드마크 추출
# =====================================================

# 포함 시 유효 랜드마크로 인정 (찻집 검색 맥락에서 의미 있는 장소)
LANDMARK_INCLUDE = [
    "단길", "거리", "마을", "길", "시장", "광장", "공원",
    "궁", "성곽", "미술관", "박물관", "기념관", "수목원",
    "생태", "호수", "숲", "터미널", "대학교", "캠퍼스",
]

# 포함 시 제외 (검색어로 의미 없는 시설/기관)
LANDMARK_EXCLUDE = [
    "초등학교", "중학교", "고등학교", "어린이공원",
    "아파트", "맨션", "래미안", "힐스테이트", "자이", "푸르지오",
    "주민센터", "체육센터", "구청", "동사무소", "파출소", "지구대",
    "경찰서", "소방서", "세무서", "은행", "주차장", "우체국",
    "옆", "앞길", "부근", "근처",
]


def extract_landmarks(df: pd.DataFrame) -> dict[int, list[str]]:
    """
    상권코드명에서 랜드마크 후보 추출
    반환: {상권_코드: [랜드마크명, ...]}

    처리 로직:
      1) 괄호 안 내용 분리 → 메인명 + 괄호내용 각각 후보
      2) 역명/단순 위치명("옆","앞") 제외
      3) INCLUDE 키워드 포함 AND EXCLUDE 키워드 미포함인 것만 채택
    """
    result: dict[int, list[str]] = {}

    for _, row in df.iterrows():
        code = row["상권_코드"]
        name = str(row["상권_코드_명"]).strip()

        # 이미 역명으로 처리되는 상권은 건너뜀
        if re.match(r".+역\s*\d*번?$", name):
            continue

        # 괄호 분리 → [메인명, 괄호내용1, 괄호내용2, ...]
        brackets = re.findall(r"[(\(](.+?)[)\)]", name)
        main     = re.sub(r"[(\(].+?[)\)]", "", name).strip()
        candidates = [main] + brackets

        landmarks = []
        for cand in candidates:
            cand = cand.strip()
            if not cand:
                continue
            # 제외 키워드 체크
            if any(ex in cand for ex in LANDMARK_EXCLUDE):
                continue
            # 포함 키워드 체크
            if any(inc in cand for inc in LANDMARK_INCLUDE):
                landmarks.append(cand)

        if landmarks:
            result[code] = landmarks

    return result


# =====================================================
# 5단계: 검색어 조합 생성
# =====================================================
def build_search_queries(df: pd.DataFrame) -> pd.DataFrame:
    """
    상권별로 세 축 × 키워드 조합의 검색어 목록 생성
      축 1: 행정동명         (예: 성수동)
      축 2: 최근접 지하철역   (예: 성수역)
      축 3: 랜드마크         (예: 경리단길, 황학동벼룩시장)
    중복 검색어는 제거 (여러 상권이 같은 지역이면 한 번만)
    """
    print("📝 5단계: 검색어 조합 생성 중...")

    # 랜드마크 추출
    landmark_map = extract_landmarks(df)
    total_landmarks = sum(len(v) for v in landmark_map.values())
    print(f"   랜드마크 추출: {len(landmark_map)}개 상권, 총 {total_landmarks}개 후보")

    rows = []
    seen = set()   # 중복 제거용

    for _, r in df.iterrows():
        dong    = str(r["행정동_코드_명"]).strip()
        station = str(r["최근접_역명"]).strip()
        code    = r["상권_코드"]
        landmarks = landmark_map.get(code, [])

        for kw in TEA_KEYWORDS:
            # 축 1: 행정동 기반
            q_dong = f"{dong} {kw}"
            if q_dong not in seen:
                rows.append({
                    "검색어"      : q_dong,
                    "검색어_유형" : "행정동",
                    "기준_지역"   : dong,
                    "키워드"      : kw,
                    "대표_상권코드": code,
                })
                seen.add(q_dong)

            # 축 2: 역 기반
            q_station = f"{station} {kw}"
            if q_station not in seen:
                rows.append({
                    "검색어"      : q_station,
                    "검색어_유형" : "지하철역",
                    "기준_지역"   : station,
                    "키워드"      : kw,
                    "대표_상권코드": code,
                })
                seen.add(q_station)

            # 축 3: 랜드마크 기반
            for lm in landmarks:
                q_lm = f"{lm} {kw}"
                if q_lm not in seen:
                    rows.append({
                        "검색어"      : q_lm,
                        "검색어_유형" : "랜드마크",
                        "기준_지역"   : lm,
                        "키워드"      : kw,
                        "대표_상권코드": code,
                    })
                    seen.add(q_lm)

    df_queries = pd.DataFrame(rows)
    print(f"   행정동 기반  : {(df_queries['검색어_유형']=='행정동').sum()}개")
    print(f"   지하철역 기반: {(df_queries['검색어_유형']=='지하철역').sum()}개")
    print(f"   랜드마크 기반: {(df_queries['검색어_유형']=='랜드마크').sum()}개")
    print(f"   총 검색어 수 : {len(df_queries)}개 (중복 제거 완료)")
    return df_queries


# =====================================================
# 최근접 역 매핑 결과를 to_map에 합쳐서 저장
# =====================================================
def save_map_with_station(df: pd.DataFrame):
    out = os.path.join(DATA_PATH, "to_map_with_station.csv")
    cols = ["상권_코드", "상권_코드_명", "행정동_코드_명", "자치구_코드_명",
            "lon", "lat", "최근접_역명", "최근접_역_거리m"]
    df[cols].to_csv(out, index=False, encoding="utf-8-sig")
    print(f"   💾 상권+역 매핑 저장 → {out}")


# =====================================================
# 실행
# =====================================================
if __name__ == "__main__":
    print("=" * 55)
    print("  찻집 크롤링 검색어 조합 생성기")
    print("=" * 55)

    # 데이터 로드
    df_map = pd.read_csv(TO_MAP_PATH, encoding="utf-8-sig")
    print(f"📂 to_map.csv 로드: {len(df_map)}개 상권\n")

    # 1단계: 좌표 변환
    df_map = convert_tm_to_wgs84(df_map)

    # 2단계: 역 좌표 수집
    station_names = extract_station_names(df_map)
    print(f"   추출된 유니크 역명: {len(station_names)}개")
    df_stations = get_station_coords_kakao(station_names, KAKAO_API_KEY)

    # 3단계: 최근접 역 매핑
    df_map = map_nearest_station(df_map, df_stations)
    save_map_with_station(df_map)

    # 4~5단계: 랜드마크 추출 + 검색어 조합 생성
    df_queries = build_search_queries(df_map)
    df_queries.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"\n✅ 완료! 검색어 목록 저장 → {OUTPUT_PATH}")
    print("\n[ 미리보기 ]")
    print(df_queries.head(10).to_string(index=False))
    print("\n[ 키워드 유형별 요약 ]")
    print(df_queries.groupby(["검색어_유형", "키워드"]).size().unstack(fill_value=0))
