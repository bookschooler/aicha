"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
27b_eda_correlation_nooutlier.py — 이상치 제거 버전 상관관계 EDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  27번과 동일하나 매출 상위 5% (이상치) 제거 후 분석
  → 극단값이 상관관계에 미치는 영향 제거
  이상치 기준: 매출 95퍼센타일 초과 제외

입력: y_demand_supply_trend_merge.csv
출력: eda_correlation_table_nooutlier.csv (이상치 제거 순위표)
      eda_scatter_top20_nooutlier.png (산점도)
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리 변경

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · np.isfinite(x): x가 유한한 실수이면 True (NaN, inf, -inf이면 False)
#    · np.linspace(시작, 끝, 개수): 시작~끝을 개수만큼 균등 분할한 배열 반환
#      - 예: np.linspace(0, 10, 5) → [0.0, 2.5, 5.0, 7.5, 10.0]

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(파일명): CSV → DataFrame 반환
#    · Series.quantile(q): 하위 q% 경계값(분위수) 반환
#      - q=0.95: 상위 5% 기준값 (이 값 이상이 상위 5% 이상치)
#      - q=0.25: Q1 (하위 25%), q=0.5: 중앙값, q=0.75: Q3 (상위 25%)
#    · Series.notna(): NaN이 아니면 True인 Boolean Series
#    · pd.DataFrame(리스트): 딕셔너리 리스트 → DataFrame 변환
#    · df.sort_values('컬럼', ascending=False): 내림차순 정렬
#    · df.to_csv(경로, index=False, encoding='utf-8-sig'): CSV 저장

import matplotlib.pyplot as plt    # 데이터 시각화(그래프) 라이브러리
#  └ [matplotlib.pyplot 라이브러리]
#    · pip install matplotlib 로 설치
#    · plt.subplots(행, 열, figsize): 서브플롯 격자 생성
#      - 반환: (fig, axes) — fig=전체 캔버스, axes=개별 그래프 배열
#    · axes.flatten(): 2D 배열 → 1D 배열 변환 (for 루프 순회용)
#    · ax.scatter(x, y, alpha, s, color): 산점도 그리기
#      - alpha: 점 투명도 (0=투명, 1=불투명)
#      - s: 점 크기
#    · ax.plot(x, y, color, linewidth): 선 그래프 (추세선)
#    · ax.set_title/xlabel/ylabel(문자열, fontsize): 제목/축 이름 설정
#    · ax.tick_params(labelsize): 축 눈금 숫자 크기 설정
#    · plt.suptitle(문자열, fontsize, y): 전체 Figure 제목 설정
#    · plt.tight_layout(): 서브플롯 간격 자동 조정
#    · plt.savefig(경로, dpi, bbox_inches): 이미지 파일로 저장
#    · plt.close(): Figure를 메모리에서 해제 (메모리 누수 방지)

import koreanize_matplotlib         # matplotlib 한글 폰트 자동 설정 라이브러리
#  └ [koreanize_matplotlib 라이브러리]
#    · pip install koreanize-matplotlib 로 설치
#    · import만 해도 matplotlib 한글 폰트(NanumGothic) 자동 등록
#    · 없으면 그래프 한글이 □□□ 처럼 깨짐

from scipy import stats             # 과학/통계 계산 라이브러리
#  └ [scipy.stats 모듈]
#    · pip install scipy 로 설치
#    · stats.pearsonr(x, y): 피어슨 상관계수(r)와 p-value 동시 반환
#      - r: -1(완전 음의 상관) ~ 0(무관) ~ 1(완전 양의 상관)
#      - p: 귀무가설(상관없음) 기각 확률 (p < 0.05: 통계적으로 유의)
#      - R² = r²: Y분산 중 X가 설명하는 비율
#    · stats.linregress(x, y): 단순 선형 회귀 (기울기, 절편 계산)
#      - 반환: (slope, intercept, r_value, p_value, std_err)
#      - *_로 나머지 값 무시 가능

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경


# ══════════════════════════════════════════════════════
# 1. 데이터 로드 (최신 분기)
# ══════════════════════════════════════════════════════
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
df = df[df['기준_년분기_코드'] == 20253].copy()  # 최신 분기(20253)만 사용


# ══════════════════════════════════════════════════════
# 2. 이상치 제거: 매출 상위 5% 제외
# ══════════════════════════════════════════════════════
p95 = df['당월_매출_금액'].quantile(0.95)
#  └ Series.quantile(q)
#    · 기본문법: Series.quantile(q=0.5)
#    · 하위 q 비율의 경계값(분위수) 반환
#    · q=0.95: 전체 데이터의 95%가 이 값 이하 → 상위 5% 기준선
#    · 이상치(outlier): 전체 분포에서 극단적으로 벗어난 값
#    · 명동 관광특구처럼 매출이 비정상적으로 높은 상권이 이상치에 해당

df = df[df['당월_매출_금액'] <= p95].copy()
#  └ 이상치 제거 효과:
#    · 매출 상위 5% 제외 → 극단값 없이 일반적인 상권만 분석
#    · 이상치가 있으면 상관계수가 이상치에 끌려가서 왜곡될 수 있음
#    · 이상치 포함(27번) vs 제외(27b번) 비교로 결과의 안정성 확인

print(f"분석 데이터: {df.shape[0]}개 상권 (상위 5% 제외, 기준: {p95/1e6:.1f}백만원)")
#  └ {p95/1e6:.1f}: p95를 백만(1e6=1,000,000)으로 나눠 소수점 1자리로 표시

y = df['당월_매출_금액']  # 27번과 달리 로그 변환 없이 원매출 사용
#  └ 27번 vs 27b번 차이:
#    · 27번: Y = log(당월_매출_금액) → 로그 변환으로 정규화
#    · 27b번: Y = 당월_매출_금액 → 이상치 제거로 분포 정상화
#    · 두 접근법 비교로 어떤 변환이 상관관계를 더 잘 드러내는지 확인


# ══════════════════════════════════════════════════════
# 3. 분석에서 제외할 컬럼 정의
# ══════════════════════════════════════════════════════
exclude = [
    '기준_년_코드', '기준_분기_코드', '기준_년분기_코드',
    '상권_코드', '상권_구분_코드', '상권_구분_코드_명', '상권_코드_명',
    '당월_매출_금액',
]
x_cols = [
    c for c in df.columns
    if c not in exclude
    and df[c].dtype in ['float64', 'int64']
    and '매출' not in c
    and '평균' not in c
    and 'QUARTER' not in c
]
#  └ 리스트 컴프리헨션 + 다중 조건
#    · 기본문법: [표현식 for 변수 in iterable if 조건]
#    · df[c].dtype: 컬럼의 데이터 타입 ('float64', 'int64', 'object' 등)
#    · '매출' not in c: 컬럼명 문자열에 '매출' 포함 여부 검사
print(f"분석 변수: {len(x_cols)}개\n")


# ══════════════════════════════════════════════════════
# 4. 각 변수별 상관계수 계산
# ══════════════════════════════════════════════════════
results = []
for col in x_cols:
    x = df[col]
    mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    #  └ Boolean 배열 AND(&) 연산: 모든 조건이 True인 행만 선택
    #    · &: 원소별 AND (배열용) — 파이썬 and는 스칼라에만 사용 가능

    n = mask.sum()
    if n < 10:
        continue

    x_valid = x[mask]
    y_valid = y[mask]

    q1, q2, q3 = x_valid.quantile([0.25, 0.5, 0.75])
    #  └ 리스트로 여러 분위수 동시 반환 → 튜플 언패킹

    r, p = stats.pearsonr(x_valid, y_valid)
    #  └ stats.pearsonr(x, y): 피어슨 상관계수(r)와 p-value 반환
    r2 = r ** 2  # R² = r의 제곱

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
        #  └ 중첩 삼항 연산자: p값에 따른 유의성 표시
        #    · *** p<0.001 / ** p<0.01 / * p<0.05 / 빈문자열: 유의하지 않음
    })

result_df = pd.DataFrame(results).sort_values('R²', ascending=False)


# ══════════════════════════════════════════════════════
# 5. 순위표 출력 및 CSV 저장
# ══════════════════════════════════════════════════════
print("=" * 80)
print("▶ 전체 변수 R² 순위 (상위 30개) — 이상치 제거 버전")
print("=" * 80)
print(result_df[['변수명', 'R²', '상관계수(r)', 'p-value', '유의', 'N']].head(30).to_string(index=False))

print("\n" + "=" * 80)
print("▶ R² 하위 10개 (관련 없는 변수)")
print("=" * 80)
print(result_df[['변수명', 'R²', '상관계수(r)', 'p-value', '유의']].tail(10).to_string(index=False))
#  └ df.tail(n): 마지막 n개 행 반환 (df.head()의 반대)

result_df.to_csv('eda_correlation_table_nooutlier.csv', index=False, encoding='utf-8-sig')
print(f"\n✅ 전체 순위표 저장: eda_correlation_table_nooutlier.csv")


# ══════════════════════════════════════════════════════
# 6. 상위 20개 변수 산점도 그리기
# ══════════════════════════════════════════════════════
top20 = result_df.head(20)

fig, axes = plt.subplots(4, 5, figsize=(24, 18))
#  └ plt.subplots(행, 열, figsize=(가로, 세로))
#    · 4행×5열=20개 서브플롯 생성
#    · fig: 전체 Figure / axes: (4×5) Axes 배열

axes = axes.flatten()
#  └ ndarray.flatten(): 다차원 배열 → 1차원 배열
#    · [[ax1,...,ax5],[ax6,...,ax10],...] → [ax1,ax2,...,ax20]

for i, (_, row) in enumerate(top20.iterrows()):
    #  └ DataFrame.iterrows(): (인덱스, Series) 튜플로 행 순회
    #    · _: 인덱스 무시 / row: 해당 행 데이터
    col = row['변수명']
    x = df[col]
    mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    x_v, y_v = x[mask], y[mask]

    ax = axes[i]
    ax.scatter(x_v, y_v, alpha=0.3, s=15, color='darkorange')
    #  └ color='darkorange': 27번(steelblue)과 다른 색으로 이상치 제거 버전 구분

    slope, intercept, *_ = stats.linregress(x_v, y_v)
    #  └ stats.linregress(x, y): 선형 회귀 → slope(기울기), intercept(절편)
    #    · *_: 나머지 반환값(r_value, p_value, std_err) 무시

    x_line = np.linspace(x_v.min(), x_v.max(), 100)
    #  └ np.linspace(시작, 끝, 개수): 균등 분할 배열 생성 (추세선용)

    ax.plot(x_line, slope * x_line + intercept, color='red', linewidth=1.5)

    ax.set_title(f"{col}\nR²={row['R²']:.3f}  r={row['상관계수(r)']:.3f}  {row['유의']}", fontsize=8)
    ax.set_xlabel(col, fontsize=7)
    ax.set_ylabel('당월_매출_금액', fontsize=7)
    ax.tick_params(labelsize=6)

plt.suptitle('X변수 vs 당월_매출_금액 산점도 - R² 상위 20개 (이상치 제거, 20253 기준)', fontsize=13, y=1.01)
#  └ plt.suptitle(): 전체 Figure 제목 (개별 서브플롯 제목과 별개)

plt.tight_layout()
#  └ plt.tight_layout(): 서브플롯 간 겹침 자동 조정

plt.savefig('eda_scatter_top20_nooutlier.png', dpi=150, bbox_inches='tight')
#  └ plt.savefig(경로, dpi, bbox_inches): 그래프를 이미지 파일로 저장
#    · dpi=150: 해상도 150 DPI
#    · bbox_inches='tight': 여백 최소화

plt.close()
#  └ plt.close(): Figure 메모리 해제 (반복 생성 시 누수 방지)

print("✅ 산점도 저장: eda_scatter_top20_nooutlier.png")
