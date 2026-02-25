"""
찻집 데이터 수집 스크립트 (카카오 키워드 검색 API)
====================================================
입력 : search_keywords.csv  (17_build_search_keywords.py 출력)
출력 : tea_shops_raw.csv    (수집 원본)
       tea_shops_dedup.csv  (도로명주소 기준 중복 제거)

카카오 API 스펙:
  - 쿼리당 최대 45건 (size=15, page 1~3)
  - 하루 무료 한도 300,000건
  - 예상 호출 수: 검색어 ~3,000개 × 3페이지 = ~9,000회

중단/재시작 지원:
  - 진행 상황을 progress.json 에 저장
  - 재실행하면 이미 수집된 검색어는 건너뜀
"""

import pandas as pd
import numpy as np
import requests
import time
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()   # .env 파일 자동 로드

# =====================================================
# 설정
# =====================================================
KAKAO_API_KEY  = os.environ["KAKAO_API_KEY"]
DATA_PATH      = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_PATH  = os.path.join(DATA_PATH, "search_keywords.csv")
RAW_OUTPUT     = os.path.join(DATA_PATH, "tea_shops_raw.csv")
DEDUP_OUTPUT   = os.path.join(DATA_PATH, "tea_shops_dedup.csv")
PROGRESS_FILE  = os.path.join(DATA_PATH, "crawl_progress.json")

KAKAO_URL   = "https://dapi.kakao.com/v2/local/search/keyword.json"
PAGE_SIZE   = 15      # 카카오 최대
MAX_PAGE    = 3       # 쿼리당 최대 3페이지 (총 45건)
SLEEP_SEC   = 0.2     # 요청 간 딜레이 (초)
SAVE_EVERY  = 100     # N개 검색어마다 중간 저장

# 유효 카테고리: 아래 중 하나로 시작하는 것만 저장
# 테스트 결과 빌라/부동산/인테리어 등 노이즈 제거
VALID_CATEGORY_PREFIXES = (
    "음식점 > 카페",
    "서비스,산업 > 식품 > 음료,주류제조",
)


# =====================================================
# 카카오 키워드 검색 (페이지네이션 포함)
# =====================================================
def search_kakao(query: str, headers: dict) -> list[dict]:
    """
    카카오 키워드 검색으로 최대 45건 수집
    is_end=True이면 다음 페이지 호출 중단
    """
    results = []
    for page in range(1, MAX_PAGE + 1):
        params = {
            "query": query,
            "size" : PAGE_SIZE,
            "page" : page,
        }
        try:
            resp = requests.get(KAKAO_URL, headers=headers, params=params, timeout=5)
            data = resp.json()
        except Exception as e:
            print(f"   ❌ 요청 실패 ({query}, p{page}): {e}")
            break

        docs = data.get("documents", [])
        for d in docs:
            # 카페 계열 카테고리만 저장 (부동산/건설/금융 등 노이즈 제거)
            category = d.get("category_name", "")
            if not category.startswith(VALID_CATEGORY_PREFIXES):
                continue
            results.append({
                "가게명"      : d.get("place_name", ""),
                "카테고리"    : category,
                "지번주소"    : d.get("address_name", ""),
                "도로명주소"  : d.get("road_address_name", ""),
                "전화번호"    : d.get("phone", ""),
                "lon"         : float(d.get("x", 0)) or None,   # WGS84 경도
                "lat"         : float(d.get("y", 0)) or None,   # WGS84 위도
                "카카오_url"  : d.get("place_url", ""),
                "검색어"      : query,
            })

        # 마지막 페이지면 중단
        if data.get("meta", {}).get("is_end", True):
            break

        time.sleep(SLEEP_SEC)

    return results


# =====================================================
# 진행 상황 저장/로드
# =====================================================
def load_progress() -> tuple[set, list]:
    """이전 진행 상황 불러오기 (재시작 지원)"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        done_queries = set(data.get("done_queries", []))
        print(f"   📦 이전 진행 불러오기: {len(done_queries)}개 검색어 완료 상태")
        return done_queries
    return set()


def save_progress(done_queries: set):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"done_queries": list(done_queries)}, f, ensure_ascii=False)


# =====================================================
# 중간 저장 (누적 append)
# =====================================================
def append_to_raw(rows: list[dict]):
    """수집 결과를 RAW_OUTPUT에 누적 저장"""
    if not rows:
        return
    df_new = pd.DataFrame(rows)
    if os.path.exists(RAW_OUTPUT):
        df_new.to_csv(RAW_OUTPUT, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df_new.to_csv(RAW_OUTPUT, index=False, encoding="utf-8-sig")


# =====================================================
# 중복 제거 + 최종 저장
# =====================================================
def deduplicate_and_save():
    """
    도로명주소 기준 중복 제거
    도로명주소가 없으면 지번주소 + 가게명 조합으로 처리
    """
    print("\n🔧 중복 제거 중...")
    df = pd.read_csv(RAW_OUTPUT, encoding="utf-8-sig")
    print(f"   수집 원본: {len(df)}건")

    # 중복 키 생성: 도로명주소 우선, 없으면 지번주소
    df["_dedup_key"] = df.apply(
        lambda r: r["도로명주소"] if pd.notna(r["도로명주소"]) and r["도로명주소"] != ""
                  else f'{r["지번주소"]}_{r["가게명"]}',
        axis=1
    )
    df_dedup = df.drop_duplicates(subset="_dedup_key", keep="first").drop(columns="_dedup_key")

    print(f"   중복 제거 후: {len(df_dedup)}건  (제거: {len(df)-len(df_dedup)}건)")
    df_dedup.to_csv(DEDUP_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"   💾 저장 완료 → {DEDUP_OUTPUT}")

    # 간단 통계
    print("\n[ 카테고리별 분포 (상위 10) ]")
    cat_top = df_dedup["카테고리"].value_counts().head(10)
    print(cat_top.to_string())

    return df_dedup


# =====================================================
# 메인 크롤링
# =====================================================
def run_crawl():
    # 검색어 로드
    if not os.path.exists(KEYWORDS_PATH):
        print(f"❌ {KEYWORDS_PATH} 없음 → 17_build_search_keywords.py 먼저 실행")
        sys.exit(1)

    df_kw = pd.read_csv(KEYWORDS_PATH, encoding="utf-8-sig")
    queries = df_kw["검색어"].tolist()
    print(f"📋 검색어 수: {len(queries)}개\n")

    # 이전 진행 상황 로드
    done_queries = load_progress()
    remaining    = [q for q in queries if q not in done_queries]
    print(f"   미완료 검색어: {len(remaining)}개 / 전체 {len(queries)}개\n")

    if not remaining:
        print("✅ 모든 검색어 완료 → 중복 제거 단계로 이동")
        deduplicate_and_save()
        return

    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

    # 크롤링 시작
    print("🔍 크롤링 시작...\n")
    buffer    = []    # 중간 저장 버퍼
    total_cnt = 0

    for i, query in enumerate(remaining, 1):
        results = search_kakao(query, headers)
        buffer.extend(results)
        done_queries.add(query)
        total_cnt += len(results)

        # 진행 출력
        sys.stdout.write(
            f"\r   [{i}/{len(remaining)}] "
            f"'{query}' → {len(results)}건 | 누적 {total_cnt}건"
        )
        sys.stdout.flush()

        # 중간 저장
        if i % SAVE_EVERY == 0:
            print(f"\n   💾 중간 저장 ({i}번째)...")
            append_to_raw(buffer)
            save_progress(done_queries)
            buffer = []

        time.sleep(SLEEP_SEC)

    # 나머지 저장
    if buffer:
        append_to_raw(buffer)
    save_progress(done_queries)

    print(f"\n\n✅ 수집 완료: 총 {total_cnt}건 → {RAW_OUTPUT}")

    # 중복 제거
    df_dedup = deduplicate_and_save()

    # 진행 파일 정리
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("   🗑️  progress.json 삭제 완료")

    print(f"\n🎉 최종 결과: {len(df_dedup)}개 찻집 후보 저장 → {DEDUP_OUTPUT}")


# =====================================================
# 실행
# =====================================================
if __name__ == "__main__":
    print("=" * 55)
    print("  찻집 데이터 크롤링 (카카오 키워드 검색 API)")
    print("=" * 55)

    if not KAKAO_API_KEY:
        print("❌ .env 파일에 KAKAO_API_KEY를 설정해주세요!")
        sys.exit(1)

    run_crawl()
