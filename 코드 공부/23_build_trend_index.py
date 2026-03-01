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

import os            # 작업 디렉토리 변경 (17번에서 상세 설명)
import pandas as pd  # 데이터프레임 (17번에서 상세 설명)
import numpy as np   # 수치 계산 (17번에서 상세 설명)

os.chdir('/teamspace/studios/this_studio/aicha')


# ══════════════════════════════════════════════════════
# 1. 검색 트렌드 로드 (카페_검색지수 + 검색량_성장률)
# ══════════════════════════════════════════════════════
print("▶ 검색 트렌드 로드...")
search = pd.read_csv('search_trend_index.csv')  # 22번 산출 결과

search['기준_년분기_코드'] = search['기준_년분기_코드'].astype(int)  # 분기코드 정수형으로
search['상권_코드']       = search['상권_코드'].astype(int)          # 상권코드 정수형으로
#  └ Series.astype(int): 데이터 타입을 정수로 변환 (21번에서 상세 설명)
#    · 병합 시 키 컬럼의 타입이 일치해야 JOIN이 정확하게 작동
#    · CSV에서 읽으면 기본적으로 int64지만, 확인 차 명시적으로 변환

print(f"  {search.shape} | 분기: {sorted(search['기준_년분기_코드'].unique())}")
#  └ Series.unique(): 고유값 배열 반환 (22번에서 상세 설명)


# ══════════════════════════════════════════════════════
# 2. 카페 개업률
# ══════════════════════════════════════════════════════
print("▶ 카페 개업률 로드 (competitor.csv)...")
comp = pd.read_csv('competitor.csv')  # 분기별 경쟁업체 데이터

comp = comp[['기준_년분기_코드', '상권_코드', '개업_율']].copy()  # 필요한 컬럼만 추출
comp.rename(columns={'개업_율': '카페_개업률'}, inplace=True)      # 컬럼명 변경
#  └ df.rename(columns={기존: 새이름}, inplace=True)
#    · inplace=True: 새 DataFrame 반환 없이 원본을 직접 수정
#    · inplace=False(기본): 변경된 새 DataFrame 반환, 원본 유지

comp['기준_년분기_코드'] = comp['기준_년분기_코드'].astype(int)  # 타입 통일
comp['상권_코드']       = comp['상권_코드'].astype(int)
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
#    · 파일 전체를 읽지 않고 지정한 컬럼만 읽음 (메모리 절약)
#    · 파일이 150개 컬럼인데 3개만 필요할 때 특히 유용

ydm['기준_년분기_코드'] = ydm['기준_년분기_코드'].astype(int)
ydm['상권_코드']       = ydm['상권_코드'].astype(int)

ydm = ydm.sort_values(['상권_코드', '기준_년분기_코드'])  # 상권별, 분기 오름차순 정렬
#  └ df.sort_values([컬럼1, 컬럼2])
#    · 여러 컬럼 기준으로 정렬 (앞 컬럼이 우선)
#    · pct_change() 계산 전 반드시 정렬해야 이전/현재 분기 순서가 맞음

ydm['유동인구_성장률'] = (
    ydm.groupby('상권_코드')['총_유동인구_수']  # 상권별로 유동인구_수 그룹화
       .pct_change() * 100                      # 이전 분기 대비 % 변화율
)
#  └ groupby('상권_코드').pct_change()
#    · 그룹 내에서만 이전 값 대비 변화율 계산
#    · 그룹 없이 pct_change()하면 다른 상권 간 변화율이 계산되는 오류 발생
#    · 첫 분기는 이전 값 없음 → NaN (구조적 결측)

ydm = ydm[['기준_년분기_코드', '상권_코드', '유동인구_성장률']]  # 필요한 컬럼만 유지
print(f"  {ydm.shape}")


# ══════════════════════════════════════════════════════
# 4. 병합 — 검색지수 + 개업률 + 유동인구 성장률
# ══════════════════════════════════════════════════════
print("▶ 병합 중...")
trend = search.merge(comp, on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ 검색지수(search) 기준으로 개업률(comp) 병합
#    · how='left': search의 모든 행 유지 (개업률 없는 경우 NaN)

trend = trend.merge(ydm,  on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ 한 번 더 병합하여 유동인구 성장률 추가
#    · 연속 merge: A.merge(B).merge(C) → A, B, C 순서로 LEFT JOIN

cols_order = ['기준_년분기_코드', '상권_코드',
              '카페_검색지수', '검색량_성장률',
              '카페_개업률', '유동인구_성장률']

trend = trend[cols_order].sort_values(['상권_코드', '기준_년분기_코드']).reset_index(drop=True)
#  └ trend[cols_order]: 컬럼 순서를 원하는 순서로 재배열
#  └ .sort_values().reset_index(drop=True): 정렬 후 인덱스 재설정


# ══════════════════════════════════════════════════════
# 5. 저장 + 결측 요약
# ══════════════════════════════════════════════════════
trend.to_csv('trend_index.csv', index=False, encoding='utf-8-sig')
print(f"\n✅ trend_index.csv 저장 완료: {trend.shape}")
print(trend.head(18).to_string(index=False))  # 상위 18행 (2개 상권 × 9분기) 미리보기

print("\n[결측치 현황]")
print(trend.isnull().sum())
#  └ df.isnull(): 각 원소가 NaN이면 True인 Boolean DataFrame 반환
#  └ .sum(): 컬럼별 True(=NaN) 개수 합산 → 결측 현황 한눈에 파악
