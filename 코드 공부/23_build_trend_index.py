"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
23_build_trend_index.py — 트렌드 지표 4개 통합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  각각 다른 파일에 흩어져 있는 트렌드 지표들을 하나로 병합

트렌드 지표 4개:
  1. 카페_검색지수     : search_trend_index.csv (22번 산출)
  2. 검색량_성장률     : search_trend_index.csv (QoQ %, 22번 산출)
  3. 카페_개업률       : competitor.csv의 개업_율 컬럼
  4. 유동인구_성장률   : y_demand_supply_merge.csv의 총_유동인구_수 QoQ 성장률

입력: search_trend_index.csv, competitor.csv, y_demand_supply_merge.csv
출력: trend_index.csv (14,850행 × 6열)
"""

import os  # 운영체제(OS) 관련 기능 (파일 경로, 작업 디렉토리 등) 제공
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리(cwd) 변경
#    · os.path.join(), os.path.exists() 등 경로 관련 함수 포함
#    · os.environ[]: 환경변수 접근

import pandas as pd  # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · 엑셀처럼 행/열 구조의 DataFrame을 파이썬에서 다룰 수 있게 해줌
#    · CSV 읽기/쓰기, 필터링, 그룹화, 병합 등 데이터 처리의 핵심
#    · 이 프로젝트에서 거의 모든 데이터 입출력과 가공에 사용됨
#    · 설치: pip install pandas

import numpy as np  # 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · 대규모 수치 배열/행렬 연산을 빠르게 처리 (C언어 기반)
#    · np.array, np.nan 등 수학/통계 함수 제공
#    · pandas 내부도 numpy 배열 기반으로 동작함
#    · 이 파일에서는 직접 호출하지 않지만 pandas 연산 내부에서 사용됨
#    · 설치: pip install numpy

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경
#  └ os.chdir(경로)
#    · 기본문법: os.chdir(path)
#    · 이후 pd.read_csv('파일명.csv') 처럼 파일명만 써도 이 폴더에서 찾음
#    · 변경하지 않으면 스크립트 실행 위치(터미널 cwd)에서 파일을 찾아 오류 발생
#    · 한 번만 설정하면 이 스크립트 실행 동안 계속 유효


# ══════════════════════════════════════════════════════
# 1. 검색 트렌드 로드 (카페_검색지수 + 검색량_성장률)
# ══════════════════════════════════════════════════════
print("▶ 검색 트렌드 로드...")
search = pd.read_csv('search_trend_index.csv')  # 22번 산출 결과
#  └ pd.read_csv(파일경로, encoding=None, sep=',', header=0, index_col=None)
#    · CSV 파일을 읽어 DataFrame으로 반환
#    · encoding 미지정 시 기본값 'utf-8' 사용 (BOM 없는 UTF-8)
#    · sep=',': 구분자는 쉼표(기본값)
#    · header=0: 첫 번째 행을 컬럼명으로 사용(기본값)
#    · index_col=None: 별도 인덱스 열 지정 없음 (기본값, 0부터 자동 부여)
#    · 반환: DataFrame (행×열 표 형태)

search['기준_년분기_코드'] = search['기준_년분기_코드'].astype(int)  # 분기코드 정수형으로
#  └ Series.astype(dtype)
#    · 기본문법: Series.astype(int) / Series.astype(str) / Series.astype(float)
#    · 해당 Series(컬럼)의 데이터 타입을 지정 타입으로 변환한 새 Series 반환
#    · 원본을 바꾸려면 다시 할당해야 함: series = series.astype(int)
#    · 병합(merge) 시 키 컬럼의 타입이 일치해야 JOIN이 정확하게 작동
#    · CSV에서 읽으면 기본적으로 int64지만, 파일마다 타입이 달라질 수 있어 명시적 변환 권장

search['상권_코드']       = search['상권_코드'].astype(int)          # 상권코드 정수형으로

print(f"  {search.shape} | 분기: {sorted(search['기준_년분기_코드'].unique())}")
#  └ Series.unique()
#    · 기본문법: Series.unique()
#    · 해당 Series에 등장하는 고유값들을 NumPy 배열로 반환 (중복 제거)
#    · 등장 순서를 유지한다는 점에서 set()과 차이
#      → set(): 순서 없음, unique(): 처음 등장한 순서 유지
#    · 분기 목록 확인 등 어떤 값들이 있는지 빠르게 파악할 때 사용
#
#  └ sorted(iterable)
#    · 기본문법: sorted(iterable, key=None, reverse=False)
#    · iterable(리스트, 배열 등)을 정렬한 새 리스트 반환 (원본 변경 없음)
#    · list.sort()는 원본을 직접 변경하고 None 반환; sorted()는 새 리스트 반환
#    · 분기 번호를 오름차순(20231, 20232, ...) 정렬해 읽기 쉽게 출력


# ══════════════════════════════════════════════════════
# 2. 카페 개업률
# ══════════════════════════════════════════════════════
print("▶ 카페 개업률 로드 (competitor.csv)...")
comp = pd.read_csv('competitor.csv')  # 분기별 경쟁업체 데이터 (전체 컬럼 로드)

comp = comp[['기준_년분기_코드', '상권_코드', '개업_율']].copy()  # 필요한 컬럼만 추출 + 독립 복사
#  └ df[['컬럼1', '컬럼2', ...]]
#    · 지정한 컬럼들만 선택해 새 DataFrame 반환
#    · 단일 컬럼은 df['컬럼'] → Series 반환
#    · 복수 컬럼은 df[['컬럼1','컬럼2']] → DataFrame 반환 (이중 대괄호 주의)
#
#  └ .copy()
#    · 기본문법: DataFrame.copy(deep=True)
#    · 데이터프레임을 독립적으로 복사 (deep=True: 값까지 복사, 기본값)
#    · copy() 없이 슬라이싱하면 원본의 '뷰(view)'가 될 수 있음
#    · 뷰에 값을 쓰면 원본도 바뀌거나 SettingWithCopyWarning이 발생
#    · copy() 후 수정하면 원본은 절대 변경되지 않아 안전

comp.rename(columns={'개업_율': '카페_개업률'}, inplace=True)  # 컬럼명 변경
#  └ df.rename(columns={기존이름: 새이름}, inplace=False)
#    · 기본문법: df.rename(columns=딕셔너리, index=딕셔너리, inplace=False)
#    · columns 딕셔너리: {기존_컬럼명: 새_컬럼명} 형태로 변경할 컬럼만 지정
#    · inplace=True: 반환값 없이 원본 DataFrame을 직접 수정
#    · inplace=False(기본): 원본은 유지하고 변경된 새 DataFrame을 반환
#      → inplace=False일 때: comp = comp.rename(columns={...}) 처럼 재할당 필요
#    · 여기서는 inplace=True를 사용해 comp 자체를 바로 수정

comp['기준_년분기_코드'] = comp['기준_년분기_코드'].astype(int)  # 타입 통일
comp['상권_코드']       = comp['상권_코드'].astype(int)          # 타입 통일
print(f"  {comp.shape}")


# ══════════════════════════════════════════════════════
# 3. 유동인구 성장률 (QoQ) 계산
# ══════════════════════════════════════════════════════
print("▶ 유동인구 성장률 산출 (y_demand_supply_merge.csv)...")
ydm = pd.read_csv(
    'y_demand_supply_merge.csv',
    usecols=['기준_년분기_코드', '상권_코드', '총_유동인구_수']  # 필요한 3개 컬럼만 읽기
)
#  └ pd.read_csv(파일, usecols=[컬럼목록])
#    · 기본문법: pd.read_csv(filepath, usecols=None)
#    · usecols에 컬럼명 리스트를 주면 해당 컬럼만 읽어 DataFrame 생성
#    · 파일 전체를 읽지 않으므로 메모리와 속도 절약
#    · 파일이 150개 컬럼인데 3개만 필요할 때 특히 효과적
#    · 컬럼명 오타 시 ValueError 발생 → 실제 컬럼명을 먼저 확인해야 함

ydm['기준_년분기_코드'] = ydm['기준_년분기_코드'].astype(int)  # 병합 키 타입 통일
ydm['상권_코드']       = ydm['상권_코드'].astype(int)

ydm = ydm.sort_values(['상권_코드', '기준_년분기_코드'])  # 상권별, 분기 오름차순 정렬
#  └ df.sort_values(by, ascending=True, inplace=False)
#    · 기본문법: df.sort_values(by=컬럼명_또는_리스트, ascending=True)
#    · 단일 컬럼: sort_values('컬럼명')
#    · 복수 컬럼: sort_values(['컬럼1', '컬럼2']) — 앞 컬럼이 우선 기준
#    · ascending=True: 오름차순(기본값), False: 내림차순
#    · pct_change() 계산 전 반드시 정렬해야 이전/현재 분기 순서가 맞음
#      → 정렬 없이 pct_change() 하면 분기 순서가 뒤섞여 엉뚱한 값이 나옴

ydm['유동인구_성장률'] = (
    ydm.groupby('상권_코드')['총_유동인구_수']  # 상권별로 유동인구_수 그룹화
       .pct_change() * 100                      # 이전 분기 대비 % 변화율 계산
)
#  └ df.groupby('컬럼')[다른_컬럼].pct_change()
#    · groupby('상권_코드'): 상권코드별로 데이터를 묶음
#    · ['총_유동인구_수']: 그룹 내에서 이 컬럼에 pct_change() 적용
#    · pct_change(): 이전 행 대비 변화율 계산
#      → 공식: (현재값 - 이전값) / 이전값
#      → 첫 번째 행은 이전값이 없으므로 NaN (구조적 결측)
#    · 그룹 없이 pct_change()만 쓰면 다른 상권 사이 변화율이 계산되는 오류 발생
#      → 예: 상권A의 마지막 분기 → 상권B의 첫 분기 변화율이 계산됨
#    · * 100: 소수 비율(0.05)을 퍼센트(5.0)로 변환

ydm = ydm[['기준_년분기_코드', '상권_코드', '유동인구_성장률']]  # 필요한 컬럼만 유지
print(f"  {ydm.shape}")


# ══════════════════════════════════════════════════════
# 4. 병합 — 검색지수 + 개업률 + 유동인구 성장률
# ══════════════════════════════════════════════════════
print("▶ 병합 중...")
trend = search.merge(comp, on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ df.merge(other, on=None, how='inner', left_on=None, right_on=None)
#    · 기본문법: df.merge(합칠_DataFrame, on=[키컬럼목록], how=조인방식)
#    · on=[...]: 두 DataFrame에 공통으로 있는 키 컬럼 지정
#    · how='left': 왼쪽(search)의 모든 행을 유지
#      → 오른쪽(comp)에 해당 키가 없으면 NaN으로 채움
#    · how='inner': 양쪽 모두에 있는 키만 유지 (기본값)
#    · how='right': 오른쪽 모든 행 유지
#    · how='outer': 양쪽 모두 유지, 없는 쪽은 NaN
#    · 검색지수(search)를 기준으로 개업률(comp) 데이터를 붙임

trend = trend.merge(ydm, on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ 연속 merge: 앞의 merge 결과(trend)에 다시 merge
#    · A.merge(B).merge(C) → A LEFT JOIN B, 그 결과에 LEFT JOIN C
#    · 매번 새 DataFrame이 반환되므로 변수에 재할당 필요

cols_order = ['기준_년분기_코드', '상권_코드',
              '카페_검색지수', '검색량_성장률',
              '카페_개업률', '유동인구_성장률']

trend = trend[cols_order].sort_values(['상권_코드', '기준_년분기_코드']).reset_index(drop=True)
#  └ trend[cols_order]: 컬럼 순서를 원하는 순서로 재배열
#    · 리스트로 컬럼명을 지정하면 그 순서대로 DataFrame이 재구성됨
#    · 불필요한 컬럼 제거 + 원하는 순서로 배치 동시에 처리
#
#  └ .sort_values(['상권_코드', '기준_년분기_코드'])
#    · 상권코드 오름차순 정렬 후, 같은 상권 내에서 분기코드 오름차순 정렬
#
#  └ .reset_index(drop=True)
#    · 기본문법: DataFrame.reset_index(drop=False, inplace=False)
#    · sort_values() 후 인덱스가 뒤섞인 상태(0,3,1,5...)를 0,1,2,3... 순으로 재설정
#    · drop=True: 기존 인덱스를 별도 컬럼으로 추가하지 않고 버림
#    · drop=False(기본): 기존 인덱스를 'index'라는 새 컬럼으로 추가


# ══════════════════════════════════════════════════════
# 5. 저장 + 결측 요약
# ══════════════════════════════════════════════════════
trend.to_csv('trend_index.csv', index=False, encoding='utf-8-sig')
#  └ df.to_csv(파일경로, sep=',', index=True, encoding=None)
#    · 기본문법: df.to_csv(path_or_buf, sep=',', index=True, encoding=None)
#    · DataFrame을 CSV 파일로 저장
#    · index=False: 행 번호(0,1,2...)를 CSV에 포함하지 않음
#      → index=True(기본)면 첫 번째 열에 0,1,2... 인덱스가 추가됨
#    · encoding='utf-8-sig': BOM(Byte Order Mark) 포함 UTF-8
#      → 한글을 엑셀로 열 때 깨지지 않도록 BOM 포함
#      → 순수 UTF-8('utf-8')은 BOM 없음 → 엑셀에서 한글 깨질 수 있음

print(f"\n✅ trend_index.csv 저장 완료: {trend.shape}")
print(trend.head(18).to_string(index=False))  # 상위 18행 (2개 상권 × 9분기) 미리보기
#  └ df.head(n): 상위 n개 행 반환 (기본값 n=5, 괄호 안 숫자 변경 가능)
#  └ df.tail(n): 마지막 n개 행 반환
#  └ df.to_string(index=False): print용 문자열 변환, 행 번호 없이 출력

print("\n[결측치 현황]")
print(trend.isnull().sum())
#  └ df.isnull()
#    · 기본문법: DataFrame.isnull() 또는 DataFrame.isna() (동일)
#    · 각 원소가 NaN이면 True, 값이 있으면 False인 Boolean DataFrame 반환
#    · isnull()과 isna()는 완전히 동일한 함수 (별칭 관계)
#
#  └ .sum()
#    · Boolean DataFrame에서 .sum() 호출: True=1로 취급해 컬럼별 합산
#    · 결과: 각 컬럼별 NaN 개수 → 결측 현황을 한눈에 파악
#    · 예: 카페_개업률 834, 유동인구_성장률 1145 → 해당 컬럼 결측 심각
