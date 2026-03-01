"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
17_build_search_keywords.py — 찻집 크롤링용 검색어 조합 생성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
흐름:
  1단계 : to_map.csv TM좌표(EPSG:5181) → WGS84 위경도 변환
  2단계 : 상권명에서 역명 추출 → 카카오 API로 역 WGS84 좌표 수집
  3단계 : 상권별 최근접 지하철역 매핑 (KDTree 사용)
  4단계 : 상권명에서 랜드마크 추출
  5단계 : 검색어 조합 생성 (행정동명 + 역명 + 랜드마크 + 키워드)
  출력  : search_keywords.csv
"""

import pandas as pd  # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · 엑셀처럼 행/열 구조의 DataFrame을 파이썬에서 다룰 수 있게 해줌
#    · CSV 읽기/쓰기, 필터링, 그룹화, 병합 등 데이터 처리의 핵심
#    · 이 프로젝트에서 거의 모든 데이터 입출력과 가공에 사용됨

import numpy as np  # 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · 대규모 수치 배열/행렬 연산을 빠르게 처리 (C언어 기반)
#    · np.array, np.cos, np.round, np.nan 등 수학/통계 함수 제공
#    · pandas 내부도 numpy 배열 기반으로 동작함

import requests  # HTTP 요청(API 호출) 라이브러리
#  └ [requests 라이브러리]
#    · 웹 API에 GET/POST 요청을 보내고 응답을 받아오는 라이브러리
#    · .get(url), .post(url) 메소드로 API 호출
#    · 카카오, 네이버 등 외부 API 호출에 모두 사용

import time  # 시간 관련 함수 제공 (내장 모듈)
#  └ [time 라이브러리]
#    · time.sleep(초): 실행을 지정 시간만큼 멈춤
#    · API 호출 속도 제한(rate limit) 준수에 필수적으로 사용

import re  # 정규표현식(Regular Expression) 라이브러리 (내장 모듈)
#  └ [re 라이브러리]
#    · 문자열에서 특정 패턴을 찾거나 치환하는 도구
#    · re.match(패턴, 문자열): 문자열 시작부터 패턴 매칭
#    · re.findall(패턴, 문자열): 패턴과 일치하는 모든 부분 추출
#    · re.sub(패턴, 대체, 문자열): 패턴 부분을 대체문자열로 치환

import os  # 운영체제(OS) 관련 기능 (파일 경로, 환경변수 등) (내장 모듈)
#  └ [os 라이브러리]
#    · os.path.join(): OS에 맞는 경로 생성
#    · os.path.exists(): 파일/폴더 존재 여부 확인
#    · os.environ[]: 환경변수 접근
#    · os.path.dirname(), os.path.abspath(): 경로 분석

from pyproj import Transformer  # 지리 좌표계 변환 라이브러리
#  └ [pyproj 라이브러리]
#    · 지구 위의 좌표계를 서로 변환해주는 라이브러리
#    · 이 프로젝트에서: 한국 TM좌표(EPSG:5181) ↔ WGS84 위경도(EPSG:4326) 변환
#    · Transformer.from_crs(): 변환기 생성, .transform(): 실제 변환 수행

from scipy.spatial import cKDTree  # 공간 최근접 탐색 라이브러리
#  └ [scipy.spatial 라이브러리]
#    · 과학 계산용 라이브러리 scipy의 공간 분석 모듈
#    · cKDTree: K-Dimensional Tree — 공간 데이터를 트리 구조로 인덱싱
#    · 수백~수천 개 좌표 중 가장 가까운 점을 빠르게 찾을 때 사용
#    · 이 프로젝트에서: 찻집/역 → 가장 가까운 상권/역 찾기에 반복 사용

from dotenv import load_dotenv  # .env 파일 환경변수 로드 라이브러리
#  └ [python-dotenv 라이브러리]
#    · .env 파일에 저장된 API 키 등 민감 정보를 환경변수로 불러옴
#    · API 키를 코드에 직접 쓰지 않고 .env에 분리 관리 (보안상 중요)
#    · .env 파일은 .gitignore에 추가해 GitHub에 올라가지 않도록 해야 함

load_dotenv()  # 현재 디렉토리의 .env 파일을 읽어 환경변수로 등록
#  └ load_dotenv()
#    · 기본문법: load_dotenv(dotenv_path=None, override=False)
#    · .env 파일에 KEY=VALUE 형식으로 저장된 값을 os.environ에 올려줌
#    · 호출 후엔 os.environ["KEY"] 또는 os.getenv("KEY") 로 접근 가능


# ══════════════════════════════════════════════════════
# 설정값 상수 정의
# ══════════════════════════════════════════════════════
KAKAO_API_KEY = os.environ["KAKAO_API_KEY"]  # .env에서 카카오 API 키 가져오기
#  └ os.environ["KEY"]
#    · 환경변수에서 KEY에 해당하는 값을 꺼냄
#    · 없으면 KeyError 발생 (값이 반드시 있어야 할 때 사용)
#    · 없어도 되면 os.getenv("KEY", "기본값") 사용

DATA_PATH   = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트가 있는 폴더 경로
#  └ os.path.abspath(__file__)
#    · __file__ = 현재 파이썬 파일의 상대 경로
#    · abspath()로 절대 경로로 변환 (예: '/teamspace/.../aicha/17_....py')
#  └ os.path.dirname(경로)
#    · 경로에서 파일명을 제외한 폴더 부분만 반환 (예: '/teamspace/.../aicha')

TO_MAP_PATH   = os.path.join(DATA_PATH, "to_map.csv")          # 상권 정보 파일 경로
OUTPUT_PATH   = os.path.join(DATA_PATH, "search_keywords.csv") # 검색어 저장 경로
STATION_CACHE = os.path.join(DATA_PATH, "station_coords.csv")  # 역 좌표 캐시 경로
#  └ os.path.join(경로1, 경로2, ...)
#    · OS에 맞는 구분자(/ 또는 \)로 경로를 이어붙임
#    · 예: join('/aicha', 'to_map.csv') → '/aicha/to_map.csv'
#    · 직접 + 연산으로 합치면 OS 호환성 문제 발생 가능 → join 권장

TEA_KEYWORDS = ["찻집", "티룸", "티하우스", "티카페", "다원"]  # 검색에 사용할 찻집 관련 키워드 목록


# ══════════════════════════════════════════════════════
# 1단계: TM(EPSG:5181) → WGS84(EPSG:4326) 좌표 변환
# ══════════════════════════════════════════════════════
def convert_tm_to_wgs84(df: pd.DataFrame) -> pd.DataFrame:
    """to_map.csv의 엑스좌표_값, 와이좌표_값(TM) → 경도(lon), 위도(lat)(WGS84)로 변환"""
    print("1단계: TM → WGS84 좌표 변환 중...")

    transformer = Transformer.from_crs("EPSG:5181", "EPSG:4326", always_xy=True)
    #  └ Transformer.from_crs(원본좌표계, 목표좌표계, always_xy=True)
    #    · 두 좌표계 간 변환기 생성
    #    · EPSG:5181 = 한국 TM(미터 단위), EPSG:4326 = WGS84(경위도)
    #    · always_xy=True: 항상 (경도, 위도) 순서로 처리 (lat/lon 혼선 방지)

    lons, lats = transformer.transform(
        df["엑스좌표_값"].values,  # TM 엑스좌표(동쪽) NumPy 배열로 전달
        df["와이좌표_값"].values   # TM 와이좌표(북쪽) NumPy 배열로 전달
    )
    #  └ transformer.transform(x_array, y_array)
    #    · NumPy 배열을 한꺼번에 변환 (루프 없이 벡터 연산으로 빠름)
    #    · 반환: (변환된_x배열, 변환된_y배열) → 여기선 (경도배열, 위도배열)

    df = df.copy()  # 원본 DataFrame을 건드리지 않기 위해 복사본 생성
    #  └ df.copy()
    #    · 데이터프레임 전체를 독립적으로 복사
    #    · copy() 없이 수정하면 원본도 바뀌거나 SettingWithCopyWarning 발생

    df["lon"] = lons  # 변환된 경도 컬럼 추가
    df["lat"] = lats  # 변환된 위도 컬럼 추가
    print(f"   {len(df)}개 상권 변환 완료")
    return df


# ══════════════════════════════════════════════════════
# 2단계: 역 좌표 수집 (카카오 키워드 검색 API)
# ══════════════════════════════════════════════════════
def extract_station_names(df: pd.DataFrame) -> list[str]:
    """상권코드명에서 유니크 역명만 추출 (예: '홍대입구역 1번출구' → '홍대입구역')"""
    station_set = set()  # 중복 제거를 위해 집합(set) 사용
    #  └ set()
    #    · 중복 없는 데이터 컬렉션 (순서 없음)
    #    · .add(값): 요소 추가, 이미 있으면 무시
    #    · list보다 중복 제거에 효율적 (O(1) 탐색)

    for name in df["상권_코드_명"]:
        if "역" in name:  # 상권명에 '역'이 포함된 경우만 처리
            match = re.match(r"(.+역)\s*\d*번?$", name.strip())
            #  └ re.match(패턴, 문자열)
            #    · 문자열의 처음부터 패턴이 일치하는지 검사
            #    · 반환: 매치 객체(성공) 또는 None(실패)
            #    · r"(.+역)\s*\d*번?$" 해석:
            #      · (.+역): 1글자 이상 + '역' → 캡처 그룹(역명 부분)
            #      · \s*  : 공백 0개 이상
            #      · \d*  : 숫자 0개 이상 (출구번호)
            #      · 번?  : '번' 있거나 없거나
            #      · $    : 문자열 끝
            if match:
                station_set.add(match.group(1))  # 첫 번째 캡처그룹(역명) 추출
                #  └ match.group(n): n번째 () 캡처그룹에 해당하는 문자열 반환
                #    · group(0) 또는 group(): 전체 매칭 문자열
                #    · group(1): 첫 번째 ()에 해당하는 부분

    return sorted(station_set)  # 집합을 정렬된 리스트로 변환
    #  └ sorted(iterable): 정렬된 새 리스트 반환 (원본 변경 없음)
    #    · list.sort()는 원본을 직접 변경, sorted()는 새 리스트 반환


def get_station_coords_kakao(station_names: list[str], api_key: str) -> pd.DataFrame:
    """카카오 키워드 검색 API로 역명 → WGS84 좌표 수집 (캐시 있으면 재사용)"""

    if os.path.exists(STATION_CACHE):  # 이미 저장된 캐시 파일이 있으면
        #  └ os.path.exists(경로)
        #    · 해당 경로에 파일/폴더가 존재하면 True, 없으면 False
        #    · API 재호출 방지에 자주 활용 (한 번 수집했으면 재사용)
        cached = pd.read_csv(STATION_CACHE, encoding="utf-8-sig")  # 캐시 파일 로드
        #  └ pd.read_csv(파일경로, encoding='utf-8-sig')
        #    · CSV 파일을 읽어 DataFrame으로 반환
        #    · encoding='utf-8-sig': BOM(Byte Order Mark) 포함 UTF-8 (한글 깨짐 방지)
        #    · 주요 파라미터: sep=','(구분자), header=0(컬럼행 위치), index_col=None(인덱스열)
        print(f"   캐시 로드: {len(cached)}개 역 좌표 (재수집 생략)")
        return cached

    print(f"2단계: {len(station_names)}개 역 좌표 수집 중...")
    headers = {"Authorization": f"KakaoAK {api_key}"}  # 카카오 API 인증 헤더 생성
    url     = "https://dapi.kakao.com/v2/local/search/keyword.json"  # 카카오 키워드 검색 API 주소

    rows = []  # 수집 결과를 담을 빈 리스트
    for i, station in enumerate(station_names, 1):  # 인덱스 1부터 시작하며 순회
        #  └ enumerate(iterable, start=0)
        #    · (인덱스, 값) 쌍을 반환하는 반복자
        #    · start=1: 인덱스가 1부터 시작 (기본값은 0)
        #    · 예: enumerate(['a','b'], 1) → (1,'a'), (2,'b')

        params = {"query": station, "size": 1, "category_group_code": "SW8"}
        # SW8 = 카카오 API 지하철역 카테고리 코드
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            #  └ requests.get(url, headers=None, params=None, timeout=None)
            #    · GET 방식 HTTP 요청 전송
            #    · headers: 요청 헤더 딕셔너리 (인증 정보 등)
            #    · params: URL 쿼리스트링으로 자동 변환 (?query=홍대입구역&size=1)
            #    · timeout: 응답 대기 최대 시간(초), 초과 시 Timeout 예외 발생
            #    · 반환: Response 객체 → .json(), .status_code, .text 등 사용

            data = resp.json()             # JSON 응답 → 파이썬 딕셔너리로 변환
            docs = data.get("documents", [])  # 검색 결과 리스트 추출, 없으면 빈 리스트
            #  └ dict.get(키, 기본값)
            #    · 딕셔너리에서 키 값 반환, 없으면 기본값 반환 (KeyError 없음)
            #    · data["documents"]는 없을 때 KeyError 발생 → get() 더 안전

            if docs:
                rows.append({               # 결과가 있으면 딕셔너리로 리스트에 추가
                    "역명"  : station,
                    "역_lon": float(docs[0]["x"]),  # 경도 (문자열 → 실수 변환)
                    "역_lat": float(docs[0]["y"]),  # 위도
                })
            else:
                # SW8 카테고리로 못 찾으면 카테고리 없이 재시도
                params2 = {"query": station, "size": 1}
                resp2   = requests.get(url, headers=headers, params=params2, timeout=5)
                docs2   = resp2.json().get("documents", [])
                if docs2:
                    rows.append({
                        "역명"  : station,
                        "역_lon": float(docs2[0]["x"]),
                        "역_lat": float(docs2[0]["y"]),
                    })
                else:
                    print(f"   좌표 없음: {station}")

        except Exception as e:
            print(f"   오류 ({station}): {e}")  # 예외 발생 시 오류 출력하고 계속 진행

        if i % 50 == 0:
            print(f"   {i}/{len(station_names)} 완료...")

        time.sleep(0.2)  # 요청 간 0.2초 대기 (API rate limit 초과 방지)
        #  └ time.sleep(초)
        #    · 지정한 초만큼 코드 실행을 멈춤
        #    · API를 너무 빠르게 호출하면 서버가 차단하므로 필수

    df_stations = pd.DataFrame(rows)  # 딕셔너리 리스트 → DataFrame 변환
    #  └ pd.DataFrame(리스트[딕셔너리])
    #    · 각 딕셔너리의 키 = 컬럼명, 값 = 행 데이터
    #    · 예: [{'a':1,'b':2}, {'a':3,'b':4}] → 2행 2열 DataFrame

    df_stations.to_csv(STATION_CACHE, index=False, encoding="utf-8-sig")
    #  └ df.to_csv(파일경로, index=False, encoding='utf-8-sig')
    #    · DataFrame을 CSV 파일로 저장
    #    · index=False: 행 번호(0,1,2...) CSV에 포함하지 않음
    #    · encoding='utf-8-sig': 한글 깨짐 방지 (BOM 포함 UTF-8)

    print(f"   {len(df_stations)}개 역 좌표 수집 완료 → {STATION_CACHE}")
    return df_stations


# ══════════════════════════════════════════════════════
# 3단계: 상권별 최근접 지하철역 매핑 (KDTree)
# ══════════════════════════════════════════════════════
def map_nearest_station(df_map: pd.DataFrame, df_stations: pd.DataFrame) -> pd.DataFrame:
    """각 상권에서 가장 가까운 지하철역을 찾아 역명 + 거리(m) 컬럼 추가"""
    print("3단계: 최근접 지하철역 매핑 중 (KDTree)...")

    LAT_REF   = 37.5                          # 서울 평균 위도 기준값
    LON_SCALE = np.cos(np.radians(LAT_REF))   # 경도 거리 보정 계수
    #  └ np.radians(각도): 도(degree) → 라디안 변환 (수학 함수 입력용)
    #  └ np.cos(라디안): 코사인값 반환
    #    · 경도 1도의 실제 거리는 위도에 따라 달라짐 (위도가 높을수록 짧아짐)
    #    · 경도 1도 ≈ 111km × cos(위도), 위도 1도 ≈ 111km (항상 일정)
    #    · 서울 위도 37.5° → cos(37.5°) ≈ 0.793
    #    · 경도에 이 값을 곱해주면 위경도 좌표를 실거리 비례로 보정 가능

    station_coords = df_stations[["역_lon", "역_lat"]].values.copy()  # 역 좌표 NumPy 배열로 추출
    station_coords[:, 0] *= LON_SCALE  # 모든 행의 0번째 열(경도)에 보정 계수 적용

    map_coords = df_map[["lon", "lat"]].values.copy()  # 상권 좌표 배열
    map_coords[:, 0] *= LON_SCALE                       # 상권 경도도 동일하게 보정

    tree = cKDTree(station_coords)  # 역 좌표 배열로 KD트리 구축
    #  └ cKDTree(데이터)
    #    · 공간 데이터를 트리 구조로 인덱싱 → 최근접 탐색을 빠르게 수행
    #    · 브루트포스(모든 쌍 비교) 대비 훨씬 빠름: O(log n) vs O(n)
    #    · 트리 구축은 한 번만 하고, query는 여러 번 재사용 가능

    dists, idxs = tree.query(map_coords, k=1)  # 각 상권에서 가장 가까운 역 1개 탐색
    #  └ tree.query(검색점_배열, k=1)
    #    · 각 검색점에서 트리 내 최근접 k개 점을 찾아 반환
    #    · 반환: (거리배열, 인덱스배열)
    #    · k=1: 가장 가까운 1개만, k=3이면 가까운 3개
    #    · 거리 단위는 트리 구축 시 쓴 좌표 단위와 동일 (여기선 보정된 도 단위)

    dists_m = dists * 111320  # 도 단위 거리 → 미터 변환 (위도 1도 ≈ 111,320m)

    df_result = df_map.copy()
    df_result["최근접_역명"]    = df_stations["역명"].values[idxs]  # idxs로 해당 역명 매핑
    df_result["최근접_역_거리m"] = np.round(dists_m).astype(int)   # 미터 단위로 반올림 후 정수 변환

    print(f"   거리 분포: 중앙값={np.median(dists_m):.0f}m  "
          f"75%={np.percentile(dists_m, 75):.0f}m  최대={dists_m.max():.0f}m")
    far_count = (dists_m > 1000).sum()  # 조건(True/False) 배열 합산 → True 개수
    print(f"   1km 초과 상권: {far_count}개 (검색어 품질 주의)")
    return df_result


# ══════════════════════════════════════════════════════
# 4단계: 상권명에서 랜드마크 추출
# ══════════════════════════════════════════════════════

LANDMARK_INCLUDE = [  # 이 키워드 포함 시 유효 랜드마크로 인정
    "단길", "거리", "마을", "길", "시장", "광장", "공원",
    "궁", "성곽", "미술관", "박물관", "기념관", "수목원",
    "생태", "호수", "숲", "터미널", "대학교", "캠퍼스",
]

LANDMARK_EXCLUDE = [  # 이 키워드 포함 시 제외 (찻집 검색어로 의미 없는 시설)
    "초등학교", "중학교", "고등학교", "어린이공원",
    "아파트", "맨션", "래미안", "힐스테이트", "자이", "푸르지오",
    "주민센터", "체육센터", "구청", "동사무소", "파출소", "지구대",
    "경찰서", "소방서", "세무서", "은행", "주차장", "우체국",
    "옆", "앞길", "부근", "근처",
]


def extract_landmarks(df: pd.DataFrame) -> dict[int, list[str]]:
    """상권코드명에서 랜드마크 후보 추출 → {상권_코드: [랜드마크명, ...]}"""
    result: dict[int, list[str]] = {}

    for _, row in df.iterrows():  # 데이터프레임을 행 단위로 순회
        #  └ df.iterrows()
        #    · 각 행을 (인덱스, Series) 형태로 반환하는 반복자
        #    · _: 인덱스 (사용 안 할 때 관례적으로 _ 사용)
        #    · row: 해당 행의 Series (row['컬럼명']으로 값 접근)
        #    · 주의: 매우 느림 → 벡터 연산 불가능한 경우에만 사용

        code = row["상권_코드"]
        name = str(row["상권_코드_명"]).strip()  # 문자열 변환 후 양쪽 공백 제거

        if re.match(r".+역\s*\d*번?$", name):  # 역명으로만 된 상권이면 랜드마크 아님
            continue  # 다음 행으로 건너뜀

        brackets = re.findall(r"[(\(](.+?)[)\)]", name)  # 괄호 안 내용 모두 추출
        #  └ re.findall(패턴, 문자열)
        #    · 패턴과 일치하는 모든 부분을 리스트로 반환
        #    · () 캡처그룹이 있으면 그룹 내용만 반환
        #    · [(\(] : '(' 또는 '（'(전각 괄호) 매칭
        #    · (.+?): 내용 (비탐욕적: 가장 짧게 매칭)
        #    · [)\)] : ')' 또는 '）'

        main       = re.sub(r"[(\(].+?[)\)]", "", name).strip()  # 괄호 부분 제거한 메인명
        #  └ re.sub(패턴, 대체문자열, 문자열)
        #    · 패턴과 일치하는 모든 부분을 대체문자열로 치환
        #    · "" 로 치환 = 해당 부분 삭제 효과

        candidates = [main] + brackets  # 메인명 + 괄호 내용들을 후보 리스트로 합침

        landmarks = []
        for cand in candidates:
            cand = cand.strip()
            if not cand:
                continue
            if any(ex in cand for ex in LANDMARK_EXCLUDE):  # 제외 키워드 포함 시 스킵
                #  └ any(조건 for x in iterable)
                #    · iterable 중 하나라도 조건이 True면 True 반환 (단락 평가로 빠름)
                continue
            if any(inc in cand for inc in LANDMARK_INCLUDE):  # 포함 키워드 있으면 채택
                landmarks.append(cand)

        if landmarks:
            result[code] = landmarks

    return result


# ══════════════════════════════════════════════════════
# 5단계: 검색어 조합 생성
# ══════════════════════════════════════════════════════
def build_search_queries(df: pd.DataFrame) -> pd.DataFrame:
    """상권별 행정동명 / 역명 / 랜드마크 × TEA_KEYWORDS 조합으로 검색어 생성"""
    print("5단계: 검색어 조합 생성 중...")

    landmark_map    = extract_landmarks(df)  # {상권코드: [랜드마크명,...]} 딕셔너리
    total_landmarks = sum(len(v) for v in landmark_map.values())  # 전체 랜드마크 수 합산
    print(f"   랜드마크 추출: {len(landmark_map)}개 상권, 총 {total_landmarks}개 후보")

    rows = []
    seen = set()  # 이미 만든 검색어를 기억하는 집합 (중복 방지용)

    for _, r in df.iterrows():
        dong      = str(r["행정동_코드_명"]).strip()   # 행정동명 (예: 연남동)
        station   = str(r["최근접_역명"]).strip()      # 가장 가까운 역명 (예: 홍대입구역)
        code      = r["상권_코드"]
        landmarks = landmark_map.get(code, [])          # 해당 상권의 랜드마크 (없으면 빈 리스트)

        for kw in TEA_KEYWORDS:
            # 축 1: 행정동 + 키워드
            q_dong = f"{dong} {kw}"            # 예: "연남동 찻집"
            if q_dong not in seen:             # 아직 추가 안 한 검색어면 추가
                rows.append({
                    "검색어"      : q_dong,
                    "검색어_유형" : "행정동",
                    "기준_지역"   : dong,
                    "키워드"      : kw,
                    "대표_상권코드": code,
                })
                seen.add(q_dong)               # 추가했음을 기록해 중복 방지

            # 축 2: 역명 + 키워드
            q_station = f"{station} {kw}"      # 예: "홍대입구역 티카페"
            if q_station not in seen:
                rows.append({
                    "검색어"      : q_station,
                    "검색어_유형" : "지하철역",
                    "기준_지역"   : station,
                    "키워드"      : kw,
                    "대표_상권코드": code,
                })
                seen.add(q_station)

            # 축 3: 랜드마크 + 키워드
            for lm in landmarks:
                q_lm = f"{lm} {kw}"            # 예: "경리단길 다원"
                if q_lm not in seen:
                    rows.append({
                        "검색어"      : q_lm,
                        "검색어_유형" : "랜드마크",
                        "기준_지역"   : lm,
                        "키워드"      : kw,
                        "대표_상권코드": code,
                    })
                    seen.add(q_lm)

    df_queries = pd.DataFrame(rows)  # 모아둔 딕셔너리 리스트 → DataFrame
    print(f"   행정동 기반  : {(df_queries['검색어_유형']=='행정동').sum()}개")
    print(f"   지하철역 기반: {(df_queries['검색어_유형']=='지하철역').sum()}개")
    print(f"   랜드마크 기반: {(df_queries['검색어_유형']=='랜드마크').sum()}개")
    print(f"   총 검색어 수 : {len(df_queries)}개 (중복 제거 완료)")
    return df_queries


def save_map_with_station(df: pd.DataFrame):
    """상권 + 최근접역 정보를 to_map_with_station.csv로 저장"""
    out  = os.path.join(DATA_PATH, "to_map_with_station.csv")
    cols = ["상권_코드", "상권_코드_명", "행정동_코드_명", "자치구_코드_명",
            "lon", "lat", "최근접_역명", "최근접_역_거리m"]
    df[cols].to_csv(out, index=False, encoding="utf-8-sig")  # 필요한 컬럼만 선택해서 저장
    print(f"   상권+역 매핑 저장 → {out}")


# ══════════════════════════════════════════════════════
# 실행 (스크립트 직접 실행할 때만 동작)
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    # __name__ == "__main__": 직접 실행 시에만 True (import 시엔 False → 실행 안 됨)
    print("=" * 55)
    print("  찻집 크롤링 검색어 조합 생성기")
    print("=" * 55)

    df_map = pd.read_csv(TO_MAP_PATH, encoding="utf-8-sig")  # to_map.csv 로드
    print(f"to_map.csv 로드: {len(df_map)}개 상권\n")

    df_map        = convert_tm_to_wgs84(df_map)                             # 1단계: 좌표 변환
    station_names = extract_station_names(df_map)                           # 역명 목록 추출
    print(f"   추출된 유니크 역명: {len(station_names)}개")
    df_stations   = get_station_coords_kakao(station_names, KAKAO_API_KEY)  # 2단계: 역 좌표 수집

    df_map = map_nearest_station(df_map, df_stations)  # 3단계: 최근접 역 매핑
    save_map_with_station(df_map)                      # to_map_with_station.csv 저장

    df_queries = build_search_queries(df_map)          # 4~5단계: 랜드마크 추출 + 검색어 생성
    df_queries.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")  # 최종 검색어 저장

    print(f"\n완료! 검색어 목록 저장 → {OUTPUT_PATH}")
    print("\n[ 미리보기 ]")
    print(df_queries.head(10).to_string(index=False))
    print("\n[ 키워드 유형별 요약 ]")
    print(df_queries.groupby(["검색어_유형", "키워드"]).size().unstack(fill_value=0))
    #  └ df.groupby(컬럼명): 지정 컬럼 기준으로 그룹 묶기
    #  └ .size(): 각 그룹의 행 수 반환
    #  └ .unstack(컬럼): 행 인덱스 → 열로 피벗 변환
    #  └ fill_value=0: 해당 조합 없을 때 NaN 대신 0 채움
