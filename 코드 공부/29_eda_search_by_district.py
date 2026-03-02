"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
29_eda_search_by_district.py — 상권별 카페_검색지수 vs 매출 상관관계 분석
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  매출 상위 100개 상권을 골라 각 상권별로
  카페_검색지수와 매출의 상관관계(Pearson r, p-value)를 계산
  → 검색지수가 매출에 영향을 주는 상권 vs 아닌 상권 구분

입력: y_demand_supply_trend_merge.csv
출력: eda_search_corr_by_district.csv
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리 변경

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(파일명): CSV → DataFrame 반환
#    · Series.str.contains(문자열, na=False): 문자열 포함 여부 Boolean Series
#      - na=False: NaN인 행은 False로 처리 (오류 방지)
#    · df[~조건]: 조건이 False인 행만 선택 (NOT 연산)
#      - ~: 비트 NOT 연산자 → Boolean Series 반전
#    · np.log1p(x) (numpy) 대신 np.log1p은 아래 numpy에서
#    · df.groupby(컬럼)[대상].mean().sort_values().head(100).index:
#      - 그룹별 평균 → 내림차순 정렬 → 상위 100개 → 인덱스(상권코드) 추출
#    · Series.isin(목록): 값이 목록에 있으면 True인 Boolean Series
#    · df.groupby(컬럼): 그룹별 반복 처리
#    · DataFrame.dropna(): NaN 포함 행 제거
#    · DataFrame.iloc[0]: 첫 번째 행 (위치 기반 인덱싱)
#    · Series.mean() / Series.median(): 평균 / 중앙값
#      - median(): 중앙값 (정렬 시 정중앙 값) — mean()과 달리 이상치 영향 적음
#    · df.nlargest(n, 컬럼): 지정 컬럼 기준 상위 n개 행 반환
#      - df.sort_values(ascending=False).head(n)과 동일하지만 더 간결
#    · df.nsmallest(n, 컬럼): 지정 컬럼 기준 하위 n개 행 반환
#    · df.to_csv(경로, index=False, encoding='utf-8-sig'): CSV 저장

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · np.log1p(x): log(1 + x) 계산
#      - log1p = log + 1 (1을 더한 후 로그)
#      - x=0일 때 log(1+0) = log(1) = 0 → 안전 (np.log(0)은 -∞)
#      - 매출이 0인 경우도 안전하게 처리 가능
#      - np.log()와 달리 0 이하 값 제거 전처리 불필요

from scipy import stats             # 과학/통계 계산 라이브러리
#  └ [scipy.stats 모듈]
#    · pip install scipy 로 설치
#    · stats.pearsonr(x, y): 피어슨 상관계수(r)와 p-value 동시 반환
#      - r: -1(완전 음의 상관) ~ 0(무관) ~ 1(완전 양의 상관)
#      - p: 귀무가설(상관없음) 기각 확률 (p < 0.05: 통계적으로 유의)
#      - 여기서는 상권별로 9개 분기 데이터로 상관계수 계산

os.chdir('/teamspace/studios/this_studio/aicha')


# ══════════════════════════════════════════════════════
# 1. 데이터 로드 및 전처리
# ══════════════════════════════════════════════════════
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')

# 명동 관광특구 제외 (이상치 — 매출이 비정상적으로 높아 분석 왜곡)
MYEONGDONG_CODE = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
#  └ Series.str.contains(문자열, na=False)
#    · 기본문법: Series.str.contains(pat, na=None)
#    · 각 문자열 값에 pat가 포함되면 True인 Boolean Series 반환
#    · na=False: NaN인 행은 False로 처리 (True면 NaN도 포함되어 오류 위험)
#    · '명동 남대문': 명동 관광특구 상권명에 포함된 문자열

df_clean = df[~df['상권_코드'].isin(MYEONGDONG_CODE)].copy()
#  └ ~(tilde): Boolean Series 반전 연산자
#    · df['상권_코드'].isin(MYEONGDONG_CODE): 명동 코드이면 True
#    · ~(...): True → False, False → True (명동 제외 = 명동 아닌 것만)
#    · .copy(): 필터링 후 독립 복사본 (SettingWithCopyWarning 방지)

# 로그 매출 변수 생성
df_clean['log_매출'] = np.log1p(df_clean['당월_매출_금액'])
#  └ np.log1p(x)
#    · 기본문법: numpy.log1p(x)
#    · log(1 + x) 계산: x=0이어도 log(1)=0으로 안전
#    · np.log(x): x=0이면 -∞, x<0이면 NaN → 0 이하 값 있으면 오류
#    · 매출이 0인 상권도 처리 가능


# ══════════════════════════════════════════════════════
# 2. 매출 상위 100개 상권 선정
# ══════════════════════════════════════════════════════
top100_codes = (
    df_clean.groupby('상권_코드')['당월_매출_금액']  # 상권별 그룹화 후 매출 선택
    .mean()                                           # 분기별 평균 매출
    .sort_values(ascending=False)                     # 내림차순 정렬 (높은 매출 먼저)
    .head(100)                                        # 상위 100개만
    .index                                            # 상권_코드만 추출 (인덱스)
)
#  └ 메소드 체이닝: 여러 메소드를 연속으로 연결해 한 번에 처리
#    · groupby() → mean() → sort_values() → head() → index
#    · 각 메소드가 반환하는 객체에 다음 메소드를 연속 적용
#    · .index: Series의 인덱스(상권_코드) 추출 → 상위 100개 상권코드 목록

df_top = df_clean[df_clean['상권_코드'].isin(top100_codes)].copy()
#  └ Series.isin(목록): 값이 목록에 있으면 True → 상위 100개 상권만 필터링

print(f"분석 대상: 상위 100개 상권 × 최대 9분기")
print(f"전체 행 수: {len(df_top)}\n")


# ══════════════════════════════════════════════════════
# 3. 상권별 카페_검색지수 vs 매출 상관계수 계산
# ══════════════════════════════════════════════════════
results = []
for code, grp in df_top.groupby('상권_코드'):
    #  └ df.groupby(컬럼): 컬럼값이 같은 행끼리 그룹화
    #    · for code, grp in df.groupby('상권_코드'):
    #      - code: 해당 그룹의 상권_코드 값
    #      - grp: 해당 상권_코드의 모든 행 (9분기 데이터)

    name  = grp['상권_코드_명'].iloc[0]           # 상권명 (첫 번째 행에서 추출)
    type_ = grp['상권_구분_코드_명_x'].iloc[0]    # 상권유형 (첫 번째 행에서 추출)
    #  └ DataFrame.iloc[0]
    #    · 기본문법: DataFrame.iloc[정수]
    #    · 위치(정수) 기반으로 행 선택 → 첫 번째 행
    #    · 같은 상권 9분기 중 어떤 분기든 상권명은 같으므로 첫 행만 사용

    avg_sales = grp['당월_매출_금액'].mean() / 1e8  # 평균 매출 (억원)

    # 결측 제거 (검색지수 NaN 있는 행 제외)
    valid = grp[['카페_검색지수', '당월_매출_금액', 'log_매출']].dropna()
    #  └ DataFrame.dropna()
    #    · 기본문법: DataFrame.dropna(axis=0, how='any', subset=None)
    #    · 하나라도 NaN이 있는 행 제거 (how='any': 하나라도 NaN이면 제거)
    #    · how='all': 모든 값이 NaN인 행만 제거

    n = len(valid)
    if n < 3:  # 3개 미만이면 상관계수 계산 불가
        continue

    # 원매출 vs 검색지수 상관계수
    r_raw, p_raw = stats.pearsonr(valid['카페_검색지수'], valid['당월_매출_금액'])

    # 로그매출 vs 검색지수 상관계수
    r_log, p_log = stats.pearsonr(valid['카페_검색지수'], valid['log_매출'])
    #  └ 원매출보다 로그매출이 정규분포에 가까워 상관계수 해석이 더 안정적

    results.append({
        '상권_코드': code,
        '상권명': name,
        '상권유형': type_,
        '평균매출_억원': round(avg_sales, 2),
        'n분기': n,
        'r_원매출': round(r_raw, 4),
        'p_원매출': round(p_raw, 4),
        'r_로그매출': round(r_log, 4),
        'p_로그매출': round(p_log, 4),
        '유의_원매출': '***' if p_raw < 0.001 else ('**' if p_raw < 0.01 else ('*' if p_raw < 0.05 else '')),
        '유의_로그매출': '***' if p_log < 0.001 else ('**' if p_log < 0.01 else ('*' if p_log < 0.05 else '')),
    })

result_df = pd.DataFrame(results).sort_values('평균매출_억원', ascending=False)


# ══════════════════════════════════════════════════════
# 4. 저장 및 출력
# ══════════════════════════════════════════════════════
result_df.to_csv('eda_search_corr_by_district.csv', index=False, encoding='utf-8-sig')
print("저장 완료: eda_search_corr_by_district.csv\n")

# 전체 요약
print("=" * 60)
print("[ 전체 요약 ]")
print(f"분석 상권 수: {len(result_df)}개")

pos_sig = result_df[(result_df['r_로그매출'] > 0) & (result_df['p_로그매출'] < 0.05)]
neg_sig = result_df[(result_df['r_로그매출'] < 0) & (result_df['p_로그매출'] < 0.05)]
insig   = result_df[result_df['p_로그매출'] >= 0.05]
#  └ 복합 Boolean 조건 필터링
#    · (조건1) & (조건2): 두 조건 모두 True인 행만
#    · 괄호 필수: & 연산자가 > 보다 우선순위가 높아 괄호 없으면 오류

print(f"  양(+)의 유의한 상관 (p<0.05): {len(pos_sig)}개")
print(f"  음(-)의 유의한 상관 (p<0.05): {len(neg_sig)}개")
print(f"  유의하지 않음:                {len(insig)}개")

print(f"\n로그매출 기준 r 평균: {result_df['r_로그매출'].mean():.4f}")
print(f"로그매출 기준 r 중앙값: {result_df['r_로그매출'].median():.4f}")
#  └ Series.median(): 중앙값 (정렬 시 정중앙 값)
#    · mean()과 달리 극단값에 영향 받지 않아 대표값으로 더 안정적

# 상관 높은 상위 10개
print("\n" + "=" * 60)
print("[ 검색지수↑ → 매출↑  상위 10개 상권 (log매출 기준) ]")
top_pos = result_df.nlargest(10, 'r_로그매출')[
    ['상권명', '상권유형', '평균매출_억원', 'r_로그매출', 'p_로그매출', '유의_로그매출']
]
#  └ DataFrame.nlargest(n, 컬럼)
#    · 기본문법: DataFrame.nlargest(n, columns)
#    · 지정 컬럼 기준 상위 n개 행 반환
#    · df.sort_values('r_로그매출', ascending=False).head(10) 과 동일하지만 간결
print(top_pos.to_string(index=False))

# 상관 낮은(음) 하위 10개
print("\n" + "=" * 60)
print("[ 검색지수↑ → 매출↓  하위 10개 상권 (log매출 기준) ]")
top_neg = result_df.nsmallest(10, 'r_로그매출')[
    ['상권명', '상권유형', '평균매출_억원', 'r_로그매출', 'p_로그매출', '유의_로그매출']
]
#  └ DataFrame.nsmallest(n, 컬럼)
#    · 기본문법: DataFrame.nsmallest(n, columns)
#    · 지정 컬럼 기준 하위 n개 행 반환 (nlargest의 반대)
print(top_neg.to_string(index=False))

# 유의한 상관 전체 목록
print("\n" + "=" * 60)
print("[ 유의한 상관 (p<0.05) 상권 전체 ]")
sig_all = result_df[result_df['p_로그매출'] < 0.05].sort_values('r_로그매출', ascending=False)
print(sig_all[['상권명', '상권유형', '평균매출_억원', 'r_로그매출', 'p_로그매출', '유의_로그매출']].to_string(index=False))
