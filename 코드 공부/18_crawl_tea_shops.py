"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
18_crawl_tea_shops.py — 찻집 데이터 수집 (카카오 키워드 검색 API)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
입력 : search_keywords.csv  (17번 스크립트 출력)
출력 : tea_shops_raw.csv    (수집 원본, 중복 포함)
       tea_shops_dedup.csv  (도로명주소 기준 중복 제거)

카카오 API 스펙:
  - 쿼리당 최대 45건 (size=15 × 최대 3페이지)
  - 예상 호출 수: 검색어 ~3,000개 × 3페이지 = ~9,000회

중단/재시작 지원:
  - 진행 상황을 progress.json에 저장
  - 재실행하면 이미 수집된 검색어는 자동으로 건너뜀
"""

import pandas as pd   # 데이터프레임 라이브러리 (17번에서 상세 설명)
import numpy as np    # 수치 배열 계산 라이브러리
import requests       # HTTP API 요청 라이브러리 (17번에서 상세 설명)
import time           # API 호출 간격 조절용 (time.sleep)
import json           # JSON 파일 읽기/쓰기 라이브러리
#  └ [json 라이브러리 (내장 모듈)]
#    · JSON 형식의 문자열 ↔ 파이썬 딕셔너리/리스트 간 변환
#    · json.load(파일객체): JSON 파일 읽어서 파이썬 객체로 변환
#    · json.dump(객체, 파일객체): 파이썬 객체를 JSON 파일로 저장
#    · json.loads(문자열): JSON 문자열 → 파이썬 객체
#    · json.dumps(객체): 파이썬 객체 → JSON 문자열

import os             # 파일 경로, 환경변수 관련 (17번에서 상세 설명)
import sys            # 파이썬 인터프리터 관련 기능 라이브러리
#  └ [sys 라이브러리 (내장 모듈)]
#    · sys.exit(코드): 프로그램 즉시 종료 (코드 0=정상, 1=오류)
#    · sys.stdout.write(문자열): print 대신 같은 줄에 출력 덮어쓰기
#    · sys.stdout.flush(): 출력 버퍼를 즉시 화면에 반영

from dotenv import load_dotenv  # .env 파일 환경변수 로드 (17번에서 상세 설명)

load_dotenv()  # .env 파일 읽어서 환경변수로 등록


# ══════════════════════════════════════════════════════
# 설정값 상수 정의
# ══════════════════════════════════════════════════════
KAKAO_API_KEY  = os.environ["KAKAO_API_KEY"]          # 카카오 API 키
DATA_PATH      = os.path.dirname(os.path.abspath(__file__))  # 스크립트 위치 폴더
KEYWORDS_PATH  = os.path.join(DATA_PATH, "search_keywords.csv")   # 검색어 목록 파일
RAW_OUTPUT     = os.path.join(DATA_PATH, "tea_shops_raw.csv")     # 수집 원본 저장 경로
DEDUP_OUTPUT   = os.path.join(DATA_PATH, "tea_shops_dedup.csv")   # 중복 제거 결과
PROGRESS_FILE  = os.path.join(DATA_PATH, "crawl_progress.json")   # 진행 상황 저장 파일

KAKAO_URL  = "https://dapi.kakao.com/v2/local/search/keyword.json"  # 카카오 키워드 검색 API URL
PAGE_SIZE  = 15     # 카카오 API 한 페이지당 최대 15건
MAX_PAGE   = 3      # 최대 3페이지 (총 45건)
SLEEP_SEC  = 0.2    # 요청 간 대기 시간 (초)
SAVE_EVERY = 100    # 100개 검색어마다 중간 저장

# 유효한 카카오 카테고리 (카페 관련만 저장, 부동산/금융 등 노이즈 제거)
VALID_CATEGORY_PREFIXES = (
    "음식점 > 카페",
    "서비스,산업 > 식품 > 음료,주류제조",
)


# ══════════════════════════════════════════════════════
# 카카오 키워드 검색 (페이지네이션 포함)
# ══════════════════════════════════════════════════════
def search_kakao(query: str, headers: dict) -> list[dict]:
    """카카오 키워드 검색으로 최대 45건 수집 (3페이지까지 자동 순회)"""
    results = []
    for page in range(1, MAX_PAGE + 1):  # 1, 2, 3 페이지 순차 호출
        #  └ range(start, stop): start 이상 stop 미만 정수 시퀀스
        #    · range(1, 4) → 1, 2, 3 (stop 값은 포함 안 됨)
        params = {
            "query": query,      # 검색어 (예: "성수 찻집")
            "size" : PAGE_SIZE,  # 한 페이지당 결과 수 (최대 15)
            "page" : page,       # 페이지 번호
        }
        try:
            resp = requests.get(KAKAO_URL, headers=headers, params=params, timeout=5)
            #  └ requests.get(url, headers, params, timeout)
            #    · 카카오 API에 GET 요청 전송 (17번에서 상세 설명)
            #    · params 딕셔너리는 자동으로 URL 쿼리스트링으로 변환됨

            data = resp.json()  # 응답을 JSON → 파이썬 딕셔너리로 변환
            #  └ resp.json()
            #    · requests Response 객체의 메소드
            #    · 응답 body의 JSON 문자열을 파이썬 딕셔너리/리스트로 파싱
            #    · resp.text: 문자열 그대로 / resp.json(): 딕셔너리로 변환

        except Exception as e:
            print(f"   요청 실패 ({query}, p{page}): {e}")
            break  # 예외 발생 시 해당 검색어 루프 중단

        docs = data.get("documents", [])  # 검색 결과 리스트 추출 (없으면 빈 리스트)
        for d in docs:
            category = d.get("category_name", "")  # 카테고리명 (없으면 빈 문자열)
            if not category.startswith(VALID_CATEGORY_PREFIXES):  # 카페 카테고리가 아니면 스킵
                #  └ str.startswith(prefix)
                #    · 문자열이 prefix로 시작하면 True
                #    · 튜플 전달 시 OR 조건: startswith(("a","b")) = a 또는 b로 시작
                continue

            results.append({          # 카페 카테고리 확인된 가게만 결과에 추가
                "가게명"    : d.get("place_name", ""),
                "카테고리"  : category,
                "지번주소"  : d.get("address_name", ""),
                "도로명주소": d.get("road_address_name", ""),
                "전화번호"  : d.get("phone", ""),
                "lon"       : float(d.get("x", 0)) or None,  # 경도 (0이면 None)
                "lat"       : float(d.get("y", 0)) or None,  # 위도
                "카카오_url": d.get("place_url", ""),
                "검색어"    : query,  # 이 결과가 어떤 검색어로 나왔는지 기록
            })

        # 마지막 페이지이면 더 이상 호출하지 않음
        if data.get("meta", {}).get("is_end", True):
            #  └ data.get("meta", {}).get("is_end", True)
            #    · meta 키가 없으면 {} (빈 딕셔너리) 반환
            #    · .get("is_end", True): is_end 없으면 True로 처리 (안전하게 중단)
            break

        time.sleep(SLEEP_SEC)  # 페이지 간 대기

    return results  # 최대 45건의 유효 가게 목록 반환


# ══════════════════════════════════════════════════════
# 진행 상황 저장/로드 (중단 후 재시작 지원)
# ══════════════════════════════════════════════════════
def load_progress() -> set:
    """이전 진행 상황 불러오기 — 완료된 검색어 집합 반환"""
    if os.path.exists(PROGRESS_FILE):  # progress.json 파일 있으면
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            #  └ open(파일경로, mode, encoding)
            #    · 파일을 열어 파일 객체 반환
            #    · mode "r": 읽기, "w": 쓰기(덮어씀), "a": 추가 쓰기
            #    · with 블록: 블록 끝에서 자동으로 파일 닫힘 (f.close() 불필요)
            data = json.load(f)  # JSON 파일 → 파이썬 딕셔너리로 읽기
            #  └ json.load(파일객체)
            #    · 파일에서 JSON을 읽어 파이썬 객체(dict/list)로 변환
            #    · json.loads(문자열)과 다름 — load는 파일, loads는 문자열

        done_queries = set(data.get("done_queries", []))  # 완료된 검색어 → 집합으로 변환
        print(f"   이전 진행 불러오기: {len(done_queries)}개 검색어 완료 상태")
        return done_queries
    return set()  # 파일 없으면 빈 집합 반환 (처음 실행)


def save_progress(done_queries: set):
    """현재 완료된 검색어 목록을 progress.json에 저장"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"done_queries": list(done_queries)}, f, ensure_ascii=False)
        #  └ json.dump(파이썬객체, 파일객체, ensure_ascii=False)
        #    · 파이썬 딕셔너리/리스트를 JSON 형식으로 파일에 저장
        #    · ensure_ascii=False: 한글을 유니코드 이스케이프 없이 그대로 저장


# ══════════════════════════════════════════════════════
# 중간 저장 (누적 append 방식)
# ══════════════════════════════════════════════════════
def append_to_raw(rows: list[dict]):
    """수집 결과를 RAW_OUTPUT에 누적 저장 (기존 파일에 이어 붙임)"""
    if not rows:  # 저장할 데이터 없으면 종료
        return
    df_new = pd.DataFrame(rows)           # 딕셔너리 리스트 → DataFrame
    if os.path.exists(RAW_OUTPUT):        # 이미 파일이 있으면
        df_new.to_csv(RAW_OUTPUT, mode="a", header=False, index=False, encoding="utf-8-sig")
        #  └ df.to_csv(path, mode="a", header=False)
        #    · mode="a": append(추가) 모드 — 기존 파일 끝에 이어서 씀
        #    · header=False: 컬럼명 행(헤더)을 쓰지 않음
        #    · (처음엔 header=True로 저장했으므로 이후엔 False로 추가만 함)
    else:                                 # 파일 없으면 새로 만들기
        df_new.to_csv(RAW_OUTPUT, index=False, encoding="utf-8-sig")  # header=True(기본값)


# ══════════════════════════════════════════════════════
# 중복 제거 + 최종 저장
# ══════════════════════════════════════════════════════
def deduplicate_and_save():
    """도로명주소 기준 중복 제거 → tea_shops_dedup.csv 저장"""
    print("\n중복 제거 중...")
    df = pd.read_csv(RAW_OUTPUT, encoding="utf-8-sig")  # 수집 원본 로드
    print(f"   수집 원본: {len(df)}건")

    # 중복 키 생성: 도로명주소 우선, 없으면 지번주소+가게명 조합
    df["_dedup_key"] = df.apply(
        lambda r: r["도로명주소"] if pd.notna(r["도로명주소"]) and r["도로명주소"] != ""
                  else f'{r["지번주소"]}_{r["가게명"]}',
        axis=1
    )
    #  └ df.apply(함수, axis=1)
    #    · 각 행(axis=1)에 함수를 적용해 새 Series 반환
    #    · lambda r: ... → 각 행을 r로 받아 조건에 따라 값 반환
    #    · pd.notna(값): NaN이 아니면 True (pd.isna의 반대)
    #    · axis=0이면 열 단위, axis=1이면 행 단위 적용

    df_dedup = df.drop_duplicates(subset="_dedup_key", keep="first").drop(columns="_dedup_key")
    #  └ df.drop_duplicates(subset=컬럼, keep='first')
    #    · 지정 컬럼 기준으로 중복 행 제거
    #    · keep='first': 중복 중 첫 번째 행만 유지 (나머지 제거)
    #    · keep='last': 마지막 행 유지, keep=False: 중복 모두 제거
    #  └ .drop(columns=컬럼명): 해당 컬럼 삭제 (임시로 만든 _dedup_key 제거)

    print(f"   중복 제거 후: {len(df_dedup)}건  (제거: {len(df)-len(df_dedup)}건)")
    df_dedup.to_csv(DEDUP_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"   저장 완료 → {DEDUP_OUTPUT}")

    print("\n[ 카테고리별 분포 (상위 10) ]")
    cat_top = df_dedup["카테고리"].value_counts().head(10)
    #  └ Series.value_counts(): 각 값의 등장 횟수를 내림차순으로 반환
    #  └ .head(n): 상위 n개 행만 반환 (기본값 5)
    print(cat_top.to_string())

    return df_dedup


# ══════════════════════════════════════════════════════
# 메인 크롤링 함수
# ══════════════════════════════════════════════════════
def run_crawl():
    """전체 검색어를 순회하며 카카오 API 크롤링 실행"""

    if not os.path.exists(KEYWORDS_PATH):  # 검색어 파일 없으면 종료
        print(f"❌ {KEYWORDS_PATH} 없음 → 17_build_search_keywords.py 먼저 실행")
        sys.exit(1)  # 프로그램 종료 (1 = 오류로 인한 종료)
        #  └ sys.exit(종료코드)
        #    · 프로그램을 즉시 종료
        #    · 0 = 정상 종료, 1 이상 = 오류 종료

    df_kw   = pd.read_csv(KEYWORDS_PATH, encoding="utf-8-sig")  # 검색어 목록 로드
    queries = df_kw["검색어"].tolist()                           # '검색어' 컬럼 → 리스트로 변환
    #  └ Series.tolist(): pandas Series를 파이썬 리스트로 변환
    print(f"검색어 수: {len(queries)}개\n")

    done_queries = load_progress()                           # 이전 완료 목록 로드
    remaining    = [q for q in queries if q not in done_queries]  # 미완료 검색어만 필터링
    #  └ [표현식 for 변수 in iterable if 조건]: 리스트 컴프리헨션 (조건부 새 리스트 생성)
    print(f"   미완료 검색어: {len(remaining)}개 / 전체 {len(queries)}개\n")

    if not remaining:  # 모든 검색어 완료 시
        print("✅ 모든 검색어 완료 → 중복 제거 단계로 이동")
        deduplicate_and_save()
        return

    headers   = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}  # 카카오 인증 헤더
    buffer    = []   # 중간 저장 전 임시 버퍼
    total_cnt = 0    # 누적 수집 건수

    print("크롤링 시작...\n")
    for i, query in enumerate(remaining, 1):
        results    = search_kakao(query, headers)  # 해당 검색어로 카카오 API 호출
        buffer.extend(results)                     # 결과를 버퍼에 추가
        #  └ list.extend(iterable): 리스트에 iterable의 모든 원소를 추가
        #    · append는 요소 1개 추가, extend는 리스트를 이어붙임
        #    · buffer += results 와 동일 효과

        done_queries.add(query)   # 완료 목록에 추가
        total_cnt += len(results) # 누적 건수 갱신

        # \r: 커서를 줄 시작으로 이동해 같은 줄을 덮어써서 실시간 진행 표시
        sys.stdout.write(
            f"\r   [{i}/{len(remaining)}] '{query}' → {len(results)}건 | 누적 {total_cnt}건"
        )
        #  └ sys.stdout.write(문자열)
        #    · print()와 달리 줄바꿈 없이 출력
        #    · \r (캐리지 리턴): 같은 줄의 처음으로 커서 이동 → 덮어쓰기 효과

        sys.stdout.flush()  # 버퍼를 즉시 화면에 출력 (지연 없이 실시간 표시)
        #  └ sys.stdout.flush()
        #    · 출력 버퍼를 즉시 화면에 반영
        #    · \r로 덮어쓸 때 flush() 없으면 화면에 바로 안 보일 수 있음

        if i % SAVE_EVERY == 0:  # 100개마다 중간 저장
            print(f"\n   중간 저장 ({i}번째)...")
            append_to_raw(buffer)      # 버퍼의 데이터를 CSV에 저장
            save_progress(done_queries)  # 진행 상황 JSON에 저장
            buffer = []                # 버퍼 초기화

        time.sleep(SLEEP_SEC)  # 요청 간 대기

    # 루프 끝 후 버퍼에 남은 데이터 저장
    if buffer:
        append_to_raw(buffer)
    save_progress(done_queries)

    print(f"\n\n✅ 수집 완료: 총 {total_cnt}건 → {RAW_OUTPUT}")

    df_dedup = deduplicate_and_save()  # 중복 제거 및 최종 저장

    # 진행 파일 정리 (크롤링 완료 후 progress.json 삭제)
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)  # 파일 삭제
        #  └ os.remove(파일경로): 파일 삭제 (폴더는 os.rmdir() 사용)
        print("   progress.json 삭제 완료")

    print(f"\n최종 결과: {len(df_dedup)}개 찻집 후보 저장 → {DEDUP_OUTPUT}")


# ══════════════════════════════════════════════════════
# 실행
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  찻집 데이터 크롤링 (카카오 키워드 검색 API)")
    print("=" * 55)

    if not KAKAO_API_KEY:  # API 키 없으면 종료
        print("❌ .env 파일에 KAKAO_API_KEY를 설정해주세요!")
        sys.exit(1)

    run_crawl()
