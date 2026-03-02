"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
27_eda_correlation.py — 전체 X변수 vs LOG(당월_매출_금액) 상관관계 EDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  최신 분기(20253) 기준으로 모든 수치형 X변수와
  log(매출) 사이의 Pearson 상관계수, R², p-value 계산
  → R² 순위표 출력 + 상위 20개 산점도 저장

입력: y_demand_supply_trend_merge.csv
출력: eda_correlation_table.csv (상관계수 순위표)
      eda_scatter_top20.png (산점도)
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리 변경

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · np.log(x): 자연로그 ln(x) 계산 (밑=e≈2.718)
#      - 매출처럼 극단적으로 큰 값을 로그 변환하면 분포가 정규분포에 가까워짐
#      - 예: 매출 1억(1e8) → log(1e8) ≈ 18.4 (다루기 쉬운 범위로 압축)
#      - log(0) = -∞ → 0 이하 값은 사전에 제거해야 함
#    · np.isfinite(x): x가 유한한 실수이면 True (NaN, inf, -inf이면 False)
#      - isnan()은 NaN만 잡음, isfinite()는 NaN + inf 모두 잡음
#    · np.linspace(시작, 끝, 개수): 시작~끝 사이를 개수만큼 균등 분할한 배열 반환
#      - 예: np.linspace(0, 10, 5) → [0.0, 2.5, 5.0, 7.5, 10.0]
#      - 추세선 x좌표 생성 등에 활용

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(파일명): CSV → DataFrame 반환
#    · df[조건].copy(): 조건 필터링 후 독립 복사본 생성
#    · Series.quantile([0.25, 0.5, 0.75]): 1사분위(Q1), 중앙값, 3사분위(Q3) 반환
#      - quantile(0.5) = 중앙값(median): 데이터를 크기순 정렬 시 정중앙 값
#      - quantile(0.25) = Q1: 하위 25% 경계값
#      - quantile(0.75) = Q3: 상위 25% 경계값
#    · Series.notna(): NaN이 아니면 True인 Boolean Series
#    · Series.mean(): 평균값 계산
#    · pd.DataFrame(리스트): 딕셔너리 리스트 → DataFrame 변환
#    · df.sort_values('컬럼', ascending=False): 내림차순 정렬
#    · df.to_csv(경로, index=False, encoding='utf-8-sig'): CSV 저장

import matplotlib.pyplot as plt    # 데이터 시각화(그래프) 라이브러리
#  └ [matplotlib.pyplot 라이브러리]
#    · pip install matplotlib 로 설치
#    · 파이썬의 가장 기본적인 시각화 라이브러리
#    · plt.subplots(행, 열, figsize=(가로, 세로)):
#      - 여러 그래프를 격자(grid) 형태로 배치할 Figure와 Axes 배열 생성
#      - 반환: (fig, axes) — fig=전체 캔버스, axes=개별 그래프 배열
#      - figsize: 인치 단위 전체 크기 (가로, 세로)
#      - 예: plt.subplots(4, 5, figsize=(24, 18)) → 4행×5열=20개 그래프 공간
#    · axes.flatten():
#      - 2D 배열([[ax1,ax2],[ax3,ax4]]) → 1D 배열([ax1,ax2,ax3,ax4]) 변환
#      - for 루프로 순서대로 접근하기 위해 사용
#    · ax.scatter(x, y, alpha, s, color):
#      - 산점도(scatter plot) 그리기
#      - alpha: 점 투명도 (0=완전투명, 1=불투명) → 겹치는 점 구분용
#      - s: 점 크기 (기본값 약 20)
#      - color: 점 색상 (문자열 또는 hex코드)
#    · ax.plot(x, y, color, linewidth):
#      - 선 그래프 그리기 (추세선에 사용)
#    · ax.set_title(문자열, fontsize): 개별 그래프 제목 설정
#    · ax.set_xlabel/set_ylabel(문자열, fontsize): x/y축 이름 설정
#    · ax.tick_params(labelsize): 축 눈금 숫자 크기 설정
#    · plt.suptitle(문자열, fontsize, y): 전체 Figure의 제목 설정
#      - y: 제목 세로 위치 (1.0=Figure 상단, 1.01=살짝 위)
#    · plt.tight_layout(): 서브플롯 간격/여백 자동 조정 (겹침 방지)
#    · plt.savefig(경로, dpi, bbox_inches):
#      - 그래프를 이미지 파일로 저장
#      - dpi: 해상도 (150~300이 적당, 높을수록 파일 크고 선명)
#      - bbox_inches='tight': 여백 최소화해서 저장
#    · plt.close(): 현재 Figure를 메모리에서 해제 (메모리 누수 방지)
#      - 여러 그래프를 반복 생성할 때 꼭 필요

import koreanize_matplotlib         # matplotlib 한글 폰트 설정 라이브러리
#  └ [koreanize_matplotlib 라이브러리]
#    · pip install koreanize-matplotlib 로 설치
#    · import만 해도 matplotlib의 한글 폰트를 자동 설정
#    · 이 라이브러리 없이 한글을 그래프에 쓰면 □□□ 처럼 깨짐
#    · 내부적으로 NanumGothic 폰트를 matplotlib에 등록

from scipy import stats             # 과학/통계 계산 라이브러리
#  └ [scipy.stats 모듈]
#    · pip install scipy 로 설치
#    · stats.pearsonr(x, y):
#      - 피어슨(Pearson) 상관계수와 p-value를 동시에 반환
#      - 반환: (r, p) — r=상관계수(-1~1), p=유의확률(0~1)
#      - r > 0: 양의 상관 (x 증가 → y 증가)
#      - r < 0: 음의 상관 (x 증가 → y 감소)
#      - |r| > 0.7: 강한 상관, 0.3~0.7: 중간, < 0.3: 약한 상관
#      - p < 0.05: 통계적으로 유의미한 상관 (우연일 확률 5% 미만)
#      - R² = r²: 설명력 (Y변동의 몇 %를 X가 설명하는지)
#    · stats.linregress(x, y):
#      - 단순 선형 회귀 분석 수행
#      - 반환: (slope, intercept, r_value, p_value, std_err)
#      - slope: 기울기 / intercept: 절편 / *_: 나머지 무시(언패킹)
#      - 추세선 y = slope * x + intercept 계산에 사용

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경


# ══════════════════════════════════════════════════════
# 1. 데이터 로드 (최신 분기)
# ══════════════════════════════════════════════════════
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
df = df[df['기준_년분기_코드'] == 20253].copy()  # 최신 분기(20253)만 사용
#  └ 왜 최신 분기만?
#    · 패널 데이터(9분기)에서 상관관계 분석하면 시간 효과가 섞임
#    · 단면(cross-sectional) 분석: 같은 시점에서 상권 간 비교가 더 명확
print(f"분석 데이터: {df.shape[0]}개 상권")


# ══════════════════════════════════════════════════════
# 2. Y 변수: 로그 변환
# ══════════════════════════════════════════════════════
df = df[df['당월_매출_금액'] > 0]  # log(0) = -∞ 방지 → 0 이하 제거
y = np.log(df['당월_매출_금액'])
#  └ np.log(x)
#    · 기본문법: numpy.log(x) — 자연로그 ln(x) 계산
#    · 매출은 수백만 ~ 수십억으로 범위가 극단적 → 로그 변환으로 정규분포화
#    · 로그 변환 전: 매출 분포가 오른쪽으로 극단적으로 치우침 (right-skewed)
#    · 로그 변환 후: 종 모양의 정규분포에 가까워짐 → 회귀분석에 적합


# ══════════════════════════════════════════════════════
# 3. 분석에서 제외할 컬럼 정의
# ══════════════════════════════════════════════════════
exclude = [
    '기준_년_코드', '기준_분기_코드', '기준_년분기_코드',
    '상권_코드', '상권_구분_코드', '상권_구분_코드_명', '상권_코드_명',
    '당월_매출_금액',  # Y 변수 자체
]
# 매출 파생변수 제외 (Y의 부분집합이라 의미 없음)
x_cols = [
    c for c in df.columns          # 전체 컬럼을 순회하면서
    if c not in exclude            # 제외 목록에 없고
    and df[c].dtype in ['float64', 'int64']  # 수치형(실수/정수)이고
    and '매출' not in c            # 컬럼명에 '매출' 없고
    and '평균' not in c            # '평균' 없고
    and 'QUARTER' not in c         # 'QUARTER' 없는 컬럼만
]
#  └ 리스트 컴프리헨션 + 다중 조건 필터링
#    · 기본문법: [표현식 for 변수 in iterable if 조건1 and 조건2 ...]
#    · df[c].dtype: 컬럼의 데이터 타입 확인
#      - 'float64': 실수형 / 'int64': 정수형 / 'object': 문자열
#    · '매출' not in c: 컬럼명(문자열)에 '매출'이 포함되지 않으면 True
print(f"분석 변수: {len(x_cols)}개\n")


# ══════════════════════════════════════════════════════
# 4. 각 변수별 상관계수 계산
# ══════════════════════════════════════════════════════
results = []
for col in x_cols:
    x = df[col]  # 현재 분석 중인 X변수 Series

    # 유효한 행만 사용 (X와 Y 모두 NaN이 없고 무한대가 아닌 행)
    mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    #  └ Boolean 배열 AND 연산
    #    · x.notna(): X가 NaN 아닌 행 → True
    #    · y.notna(): Y가 NaN 아닌 행 → True
    #    · np.isfinite(x): X가 유한한 실수(inf/-inf/NaN 아님) → True
    #    · &: 비트 AND (두 조건 모두 True인 행만 최종 True)
    #    · 주의: 파이썬 and는 스칼라, & 는 배열 원소별 AND 연산

    n = mask.sum()  # 유효 행 수 (True=1, False=0으로 합산)
    if n < 10:      # 유효 데이터가 10개 미만이면 분석 생략
        continue

    x_valid = x[mask]  # 유효한 X값만 추출
    y_valid = y[mask]  # 유효한 Y값만 추출

    # 기초 통계 (Q1, 중앙값, Q3)
    q1, q2, q3 = x_valid.quantile([0.25, 0.5, 0.75])
    #  └ Series.quantile(리스트)
    #    · 기본문법: Series.quantile(q)
    #    · q=0.25: 하위 25% 경계값 (Q1)
    #    · q=0.5: 중앙값 (Q2, median)
    #    · q=0.75: 상위 25% 경계값 (Q3)
    #    · 리스트 전달 시 여러 값 동시 반환 → 언패킹(q1, q2, q3)으로 받기

    # 상관계수 & p-value 계산
    r, p = stats.pearsonr(x_valid, y_valid)
    #  └ stats.pearsonr(x, y)
    #    · 기본문법: scipy.stats.pearsonr(x, y)
    #    · 피어슨 선형 상관계수 r과 p-value 동시 반환
    #    · r: -1(완전 음의 상관) ~ 0(무관) ~ 1(완전 양의 상관)
    #    · p: 귀무가설(상관없음) 기각 확률 (작을수록 통계적으로 유의)

    r2 = r ** 2  # 결정계수 R² = 상관계수의 제곱 (0~1, Y분산 중 X가 설명하는 비율)

    results.append({
        '변수명': col,
        'N': n,
        '평균': round(x_valid.mean(), 2),
        '중앙값': round(q2, 2),
        'Q1': round(q1, 2),
        'Q3': round(q3, 2),
        '상관계수(r)': round(r, 4),
        'R²': round(r2, 4),
        'p-value': round(p, 6),
        '유의': '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
        #  └ 중첩 삼항 연산자 (Ternary Operator)
        #    · 기본문법: 참값 if 조건 else 거짓값
        #    · p < 0.001: '***' (매우 강한 유의) / p < 0.01: '**' / p < 0.05: '*' / 나머지: ''
        #    · 유의수준(significance level): 통계적 우연일 확률 기준값
    })

result_df = pd.DataFrame(results).sort_values('R²', ascending=False)
#  └ R² 기준 내림차순 정렬 → 설명력 높은 변수부터 순위 표시


# ══════════════════════════════════════════════════════
# 5. 순위표 출력 및 CSV 저장
# ══════════════════════════════════════════════════════
print("=" * 80)
print("▶ 전체 변수 R² 순위 (상위 30개)")
print("=" * 80)
print(result_df[['변수명', 'R²', '상관계수(r)', 'p-value', '유의', 'N']].head(30).to_string(index=False))
#  └ df.to_string(index=False)
#    · DataFrame 전체를 잘리지 않고 문자열로 출력 (콘솔 너비 제한 없음)
#    · index=False: 행 번호(0,1,2...) 없이 데이터만 출력

print("\n" + "=" * 80)
print("▶ R² 하위 10개 (관련 없는 변수)")
print("=" * 80)
print(result_df[['변수명', 'R²', '상관계수(r)', 'p-value', '유의']].tail(10).to_string(index=False))
#  └ df.tail(n)
#    · 기본문법: DataFrame.tail(n=5)
#    · 마지막 n개 행 반환 (df.head()의 반대)

result_df.to_csv('eda_correlation_table.csv', index=False, encoding='utf-8-sig')
print(f"\n✅ 전체 순위표 저장: eda_correlation_table.csv")


# ══════════════════════════════════════════════════════
# 6. 상위 20개 변수 산점도 그리기
# ══════════════════════════════════════════════════════
top20 = result_df.head(20)  # R² 상위 20개 변수

fig, axes = plt.subplots(4, 5, figsize=(24, 18))
#  └ plt.subplots(행, 열, figsize=(가로인치, 세로인치))
#    · 기본문법: plt.subplots(nrows=1, ncols=1, figsize=None)
#    · 4행 × 5열 = 20개 서브플롯 생성
#    · fig: 전체 Figure 객체 (도화지)
#    · axes: (4×5) Axes 배열 (각각 하나의 그래프)
#    · figsize=(24, 18): 가로 24인치 × 세로 18인치 크기

axes = axes.flatten()
#  └ numpy.ndarray.flatten()
#    · 기본문법: array.flatten()
#    · 다차원 배열 → 1차원 배열로 변환
#    · axes가 [[ax1,ax2,...],[ax6,...]] 형태 (4×5 2D)이었다가
#      [ax1, ax2, ..., ax20] 형태 (1D)가 됨
#    · 이후 for i, ... in enumerate(top20): axes[i] 로 순서대로 접근 가능

for i, (_, row) in enumerate(top20.iterrows()):
    #  └ DataFrame.iterrows()
    #    · 기본문법: DataFrame.iterrows()
    #    · 각 행을 (인덱스, Series) 튜플로 반환하는 이터레이터
    #    · _: 인덱스(사용 안 함) / row: 해당 행의 Series
    #    · enumerate(iterable): (인덱스, 값) 쌍으로 반환

    col = row['변수명']
    x = df[col]
    mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    x_v, y_v = x[mask], y[mask]

    ax = axes[i]  # i번째 서브플롯 선택

    ax.scatter(x_v, y_v, alpha=0.3, s=15, color='steelblue')
    #  └ ax.scatter(x, y, alpha, s, color)
    #    · 기본문법: Axes.scatter(x, y, s=None, c=None, alpha=None)
    #    · 각 (x, y) 쌍을 점으로 그려 산점도 생성
    #    · alpha=0.3: 30% 불투명도 → 점이 겹쳐도 밀도 파악 가능
    #    · s=15: 점 크기 15 (작게 해서 많은 점이 안 겹치도록)
    #    · color='steelblue': 파란색 계열 색상

    # 추세선 그리기
    slope, intercept, *_ = stats.linregress(x_v, y_v)
    #  └ stats.linregress(x, y)
    #    · 기본문법: scipy.stats.linregress(x, y)
    #    · 단순 선형 회귀: y = slope * x + intercept
    #    · 반환: (slope, intercept, r_value, p_value, std_err)
    #    · *_: 나머지 값들을 무시하고 언패킹 (r_value, p_value, std_err)
    #    · slope(기울기): x가 1 증가할 때 y 변화량
    #    · intercept(절편): x=0일 때 y값

    x_line = np.linspace(x_v.min(), x_v.max(), 100)
    #  └ np.linspace(시작, 끝, 개수)
    #    · 기본문법: numpy.linspace(start, stop, num=50)
    #    · 시작~끝 사이를 100개로 균등 분할한 배열 반환
    #    · 추세선을 부드럽게 그리기 위한 x 좌표 100개 생성

    ax.plot(x_line, slope * x_line + intercept, color='red', linewidth=1.5)
    #  └ ax.plot(x, y, color, linewidth)
    #    · 기본문법: Axes.plot(x, y, color=None, linewidth=None)
    #    · 선 그래프 (추세선 = 빨간 직선)
    #    · y = slope * x + intercept: 회귀 직선 방정식

    ax.set_title(f"{col}\nR²={row['R²']:.3f}  r={row['상관계수(r)']:.3f}  {row['유의']}", fontsize=8)
    #  └ :.3f: 소수점 3자리까지 표시하는 포맷 지정자
    ax.set_xlabel(col, fontsize=7)
    ax.set_ylabel('LOG(매출)', fontsize=7)
    ax.tick_params(labelsize=6)
    #  └ ax.tick_params(labelsize)
    #    · 축 눈금 숫자(tick label)의 글자 크기 설정

plt.suptitle('X변수 vs LOG(당월_매출_금액) 산점도 - R² 상위 20개 (20253 기준)', fontsize=13, y=1.01)
#  └ plt.suptitle(문자열, fontsize, y)
#    · 기본문법: plt.suptitle(t, fontsize=None, y=None)
#    · 전체 Figure(모든 서브플롯 포함)의 상단 제목 설정
#    · ax.set_title()은 개별 서브플롯 제목 / plt.suptitle()은 전체 제목
#    · y=1.01: 제목을 Figure 상단보다 약간 위에 배치 (겹침 방지)

plt.tight_layout()
#  └ plt.tight_layout()
#    · 기본문법: plt.tight_layout(pad=1.08, h_pad=None, w_pad=None)
#    · 서브플롯 간 겹침을 자동으로 조정해 여백 최적화
#    · tight_layout() 없으면 제목/축 레이블이 서로 겹칠 수 있음

plt.savefig('eda_scatter_top20.png', dpi=150, bbox_inches='tight')
#  └ plt.savefig(경로, dpi, bbox_inches)
#    · 기본문법: plt.savefig(fname, dpi=None, bbox_inches=None)
#    · 현재 Figure를 이미지 파일로 저장
#    · dpi=150: 해상도 150 DPI (화면용 96, 인쇄용 300)
#    · bbox_inches='tight': 여백 최소화해서 저장 (빈 공백 잘라냄)
#    · 파일 확장자로 형식 자동 결정 (.png, .jpg, .pdf 등)

plt.close()
#  └ plt.close()
#    · 기본문법: plt.close(fig=None)
#    · 현재 활성 Figure를 메모리에서 해제
#    · 반복문에서 그래프를 여러 개 생성할 때 close() 없으면 메모리 누수
#    · plt.show()는 화면에 표시 (주피터 등), close()는 해제 (스크립트)

print("✅ 산점도 저장: eda_scatter_top20.png")
