"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
30_eda_advanced2.py — 심화 EDA 3종 (VIF / 블루오션 / 자치구)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  ① VIF(분산팽창지수) — 변수 간 다중공선성 수치화
  ② 블루오션 후보 상권 스크리닝 — 수요↑ 공급↓ 조건 필터
  ③ 자치구별 매출 분포 바 차트

입력: y_demand_supply_trend_merge.csv, to_map.csv
출력: eda_vif_table.csv, eda_blueocean_candidates.csv
      eda_vif.png, eda_blueocean.png, eda_gu_sales.png
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리 변경

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(파일명): CSV → DataFrame 반환
#    · Series.rank(pct=True): 각 값의 백분위 순위(0.0~1.0) 반환
#      - pct=True: 0~1 사이 비율로 반환 (pct=False이면 1,2,3... 정수 순위)
#      - 예: [10, 30, 20].rank(pct=True) → [0.33, 1.0, 0.67]
#      - 높은 값일수록 1.0에 가까운 순위 부여
#    · df.groupby(컬럼).agg(이름=(대상컬럼, 함수)): 명명된 집계
#      - agg(상권수=('상권_코드', 'count')) → '상권수'라는 컬럼명으로 집계
#      - 여러 집계를 한 번에 처리 가능
#      - 기본문법: df.groupby(key).agg(새이름=(컬럼, 함수또는lambda))
#    · Series.quantile(q): 하위 q% 경계값(분위수) 반환
#      - q=0.20: 전체의 20%가 이 값 이하 (하위 20% 경계)
#      - q=0.90: 전체의 90%가 이 값 이하 (상위 10% 기준)
#    · DataFrame.drop_duplicates('컬럼'): 해당 컬럼 기준 중복 제거 (첫 번째 유지)
#    · df.reset_index(drop=True): 기존 인덱스 버리고 0,1,2... 재지정

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · np.log1p(x): log(1 + x) — x=0이어도 안전

import matplotlib.pyplot as plt    # 데이터 시각화(그래프) 라이브러리
#  └ [matplotlib.pyplot 라이브러리]
#    · pip install matplotlib 로 설치
#    · plt.subplots(행, 열, figsize): 서브플롯 격자 생성
#    · ax.bar(x, height, color, alpha, label): 세로 막대 그래프
#      - 기본문법: ax.bar(x=카테고리, height=높이값, color=색, alpha=투명도)
#      - ax.barh(): 가로 막대 (h=horizontal)
#    · ax.scatter(x, y, c=, cmap=, alpha, s, zorder): 산점도
#      - c=배열: 각 점의 색을 배열 값에 따라 자동 배정
#      - cmap='RdYlGn': Red-Yellow-Green 컬러맵 (낮은 값=빨강, 높은 값=초록)
#      - zorder=정수: 그리는 순서 (숫자 클수록 위에 그림, 겹칠 때 앞으로)
#    · ax.annotate(텍스트, xy, xytext, textcoords, fontsize, alpha): 점에 레이블 추가
#      - 기본문법: ax.annotate(text, xy=(x좌표, y좌표), xytext=(오프셋), textcoords=기준)
#      - xy: 화살표/텍스트가 가리키는 데이터 좌표
#      - xytext=(4, 2): 데이터 좌표로부터 (오른쪽4, 위쪽2) 픽셀 만큼 이동
#      - textcoords='offset points': xytext를 픽셀(포인트) 단위 오프셋으로 해석
#    · ax.axvline(x, color, linestyle, alpha, label): 수직 점선 추가
#      - 기본문법: ax.axvline(x=값, color=색, linestyle='--')
#      - axvline: axis vertical line — 특정 X값에 세로 기준선 표시
#      - ax.axhline(): 가로 기준선 (h=horizontal)
#    · plt.colorbar(scatter객체, ax=, label=): 컬러바(색상 범례) 추가
#      - 기본문법: plt.colorbar(mappable, ax=ax, label=레이블)
#      - mappable: scatter()의 반환값 (색상 정보 포함)
#      - 색이 의미하는 값 범위를 옆에 막대로 표시
#    · ax.tick_params(axis='x', rotation=45): X축 눈금 레이블 45도 회전
#    · ax.legend(): 범례 표시

import matplotlib.font_manager as fm  # matplotlib 폰트 관리 모듈
#  └ [matplotlib.font_manager 모듈]
#    · fm.fontManager.addfont(경로): 사용자 폰트 파일 등록
#    · plt.rcParams['font.family']: 기본 폰트 설정
#    · plt.rcParams['axes.unicode_minus']: 음수 기호(−) 한글폰트 깨짐 방지

import seaborn as sns               # matplotlib 기반 통계 시각화 라이브러리
#  └ [seaborn 라이브러리]
#    · pip install seaborn 로 설치
#    · 이 파일에서는 import만 (직접 사용 없음, 향후 확장 대비)

from statsmodels.stats.outliers_influence import variance_inflation_factor
#  └ [statsmodels 라이브러리 — variance_inflation_factor]
#    · pip install statsmodels 로 설치
#    · statsmodels: 통계 모델(선형회귀, 시계열, 검정 등) 전문 라이브러리
#    · variance_inflation_factor(X_matrix, i): i번째 변수의 VIF 계산
#      - 기본문법: variance_inflation_factor(데이터행렬, 컬럼인덱스)
#      - X_matrix: NumPy 2D 배열 (DataFrame.values로 변환)
#      - i: 몇 번째 컬럼의 VIF를 계산할지 (0-based 인덱스)
#      - 반환: float — VIF 수치 (1=완전 독립, 5~10=주의, >10=다중공선성 위험)
#    · VIF(분산팽창지수)란?
#      - 한 변수가 나머지 변수들로 얼마나 설명되는지 측정
#      - VIF=1: 다른 변수와 전혀 상관 없음 (이상적)
#      - VIF=5: 다른 변수들과 어느 정도 상관 (주의)
#      - VIF>10: 다중공선성 심각 → 회귀계수 불안정 → 제거 권고
#      - 예: 총_직장_인구_수와 여성_직장_인구_수는 높은 상관 → VIF↑

os.chdir('/teamspace/studios/this_studio/aicha')


# ══════════════════════════════════════════════════════
# 1. 데이터 로드
# ══════════════════════════════════════════════════════
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
to_map = pd.read_csv('to_map.csv', encoding='utf-8-sig')

# 명동 관광특구 제외 (이상치)
MYEONGDONG = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
df = df[~df['상권_코드'].isin(MYEONGDONG)].copy()
df['log_매출'] = np.log1p(df['당월_매출_금액'])

# 최신 분기 단일 스냅샷 (VIF, 블루오션 분석용)
df25 = df[df['기준_년분기_코드'] == 20253].copy()
#  └ 패널 데이터(9분기)에서 가장 최신 분기(20253)만 추출
#    · VIF는 상관관계 → 분기별로 큰 차이 없으므로 최신 단면 사용
#    · 블루오션 스크리닝도 현재 시점 기준

print(f"분석 데이터: {len(df25)}개 상권 (20253 기준, 명동 제외)\n")


# ══════════════════════════════════════════════════════
# ① VIF 분석
# ══════════════════════════════════════════════════════
print("=" * 60)
print("① VIF 분석")
print("=" * 60)

# 상관관계 상위 변수 + 주요 지표 선택
VIF_VARS = [
    '카페음료_점포수',
    '공급갭_지수',
    '집객시설_수',
    '총_직장_인구_수',
    '여성_직장_인구_수',
    '여성연령대_50_직장_인구_수',
    '총_유동인구_수',
    '여성_유동인구_수',
    '총_상주인구_수',
    '찻집_수',
    '스타벅스_리저브_수',
    '지하철_노선_수',
    '유동밀도_지수',
    '상주밀도_지수',
    '여가소비_지수',
    '카페_검색지수',
]

# 결측 없는 행만 사용 (VIF 계산은 결측 불가)
vif_df = df25[VIF_VARS].dropna()
print(f"VIF 계산 대상: {len(VIF_VARS)}개 변수, n={len(vif_df)}\n")

vif_results = []
for i, col in enumerate(VIF_VARS):
    #  └ enumerate(리스트): (인덱스, 값) 튜플로 순회
    #    · i: 0부터 시작하는 순번 → variance_inflation_factor의 두 번째 인자로 사용
    #    · col: 변수명 문자열

    vif_val = variance_inflation_factor(vif_df.values, i)
    #  └ variance_inflation_factor(X_matrix, i)
    #    · 기본문법: variance_inflation_factor(데이터행렬, 컬럼인덱스)
    #    · vif_df.values: DataFrame → NumPy 2D 배열 변환
    #      - .values: DataFrame의 데이터를 순수 NumPy 배열로 추출 (인덱스/열명 제거)
    #    · i: 몇 번째 컬럼의 VIF를 계산할지
    #    · 내부적으로: i번째 컬럼을 Y로 놓고 나머지를 X로 OLS 회귀
    #      → R² 계산 → VIF = 1 / (1 - R²)

    vif_results.append({'변수명': col, 'VIF': round(vif_val, 2)})

vif_table = pd.DataFrame(vif_results).sort_values('VIF', ascending=False)
vif_table['위험등급'] = vif_table['VIF'].apply(
    lambda v: '🔴 제거 권고 (>10)' if v > 10 else ('🟡 주의 (5~10)' if v > 5 else '🟢 양호 (<5)')
)
#  └ Series.apply(lambda v: 조건): 각 원소에 함수 적용
#    · lambda v: if/else 삼항 연산자 — VIF 수치에 따라 등급 문자열 반환
#    · VIF > 10: 🔴 제거 권고, VIF > 5: 🟡 주의, 그 외: 🟢 양호

vif_table.to_csv('eda_vif_table.csv', index=False, encoding='utf-8-sig')
print(vif_table.to_string(index=False))


# VIF 시각화
fig, ax = plt.subplots(figsize=(10, 7))
colors = ['#e74c3c' if v > 10 else ('#f39c12' if v > 5 else '#2ecc71')
          for v in vif_table['VIF']]
#  └ 리스트 컴프리헨션 + 중첩 삼항 연산자
#    · VIF > 10: 빨강(#e74c3c), VIF > 5: 주황(#f39c12), 그 외: 초록(#2ecc71)
#    · 각 막대 색을 VIF 수치에 따라 개별 지정

bars = ax.barh(vif_table['변수명'], vif_table['VIF'], color=colors)
#  └ ax.barh(y, width, color): 가로 막대 그래프
#    · 기본문법: ax.barh(y=카테고리, width=막대길이, color=색)
#    · barh: bar horizontal — 막대가 옆으로 뻗음 (변수명 레이블 가독성 향상)
#    · 반환: BarContainer (개별 Patch 객체 리스트)

ax.axvline(5, color='orange', linestyle='--', alpha=0.7, label='주의 (VIF=5)')
ax.axvline(10, color='red', linestyle='--', alpha=0.7, label='제거 권고 (VIF=10)')
#  └ ax.axvline(x, color, linestyle, alpha, label): 수직 기준선 추가
#    · 기본문법: ax.axvline(x=값, color=색, linestyle=선스타일)
#    · x=5: VIF=5 위치에 세로 점선 → 경계 기준 시각화
#    · linestyle='--': 점선 (실선='solid', 점점선='-.')
#    · axvline vs axhline: v=수직(Vertical), h=수평(Horizontal)

for bar, v in zip(bars, vif_table['VIF']):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{v:.1f}', va='center', fontsize=9)
#  └ ax.text(x, y, 문자열): 임의 위치에 텍스트 추가
#    · bar.get_width(): 막대의 X축 끝 좌표 (막대 길이)
#    · bar.get_y() + bar.get_height()/2: 막대 Y축 중앙 좌표
#    · +0.3: 막대 끝에서 약간 오른쪽으로 떨어진 위치에 수치 표시
#    · va='center': 수직 정렬 = 중앙

ax.set_xlabel('VIF (분산팽창지수)')
ax.set_title('다중공선성 VIF 분석\n(빨강=제거권고>10, 주황=주의5~10, 초록=양호<5)', fontsize=13)
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('eda_vif.png', dpi=150)
plt.close()
print("\n→ eda_vif.png 저장 완료")


# ══════════════════════════════════════════════════════
# ② 블루오션 후보 상권 스크리닝
# ══════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("② 블루오션 후보 상권 스크리닝")
print("=" * 60)

# 필요 컬럼 확인 후 결측 제거
SCREEN_COLS = ['상권_코드', '상권_코드_명', '상권_구분_코드_명_x',
               '당월_매출_금액', 'log_매출',
               '공급갭_지수', '찻집_수', '카페음료_점포수',
               '총_직장_인구_수', '여성_직장_인구_수',
               '총_유동인구_수', '여성_유동인구_수',
               '집객시설_수', '지하철_노선_수']
bo = df25[SCREEN_COLS].dropna(subset=['공급갭_지수','총_직장_인구_수','당월_매출_금액']).copy()
#  └ DataFrame.dropna(subset=[컬럼목록]): 특정 컬럼들에만 NaN 검사
#    · subset 미지정: 모든 컬럼에 NaN 있으면 행 제거
#    · subset=['a', 'b']: a 또는 b에 NaN 있는 행만 제거 (다른 컬럼 NaN은 무시)

# 각 지표 백분위 순위 계산
bo['pct_공급갭']    = bo['공급갭_지수'].rank(pct=True)
bo['pct_직장인구']  = bo['총_직장_인구_수'].rank(pct=True)
bo['pct_유동인구']  = bo['총_유동인구_수'].rank(pct=True)
bo['pct_매출']      = bo['당월_매출_금액'].rank(pct=True)
bo['pct_찻집수_inv']= (1 - bo['찻집_수'].rank(pct=True))
#  └ Series.rank(pct=True): 백분위 순위 계산
#    · 기본문법: Series.rank(method='average', pct=False)
#    · pct=True: 0.0~1.0 사이 비율로 반환 (가장 작은 값=0에 가까움, 가장 큰 값=1에 가까움)
#    · pct=False(기본): 1, 2, 3... 정수 순위 반환
#    · method='average'(기본): 동점이면 평균 순위 부여
#      - method='min': 동점 중 작은 순위 / method='max': 큰 순위
#    · (1 - rank(pct=True)): 순위 역전 → 작은 값이 1에 가까워짐 (찻집_수↓ → 블루오션)
#      - 찻집이 적을수록 = 블루오션 가능성 ↑ → pct_찻집수_inv가 높아야 유리

# 블루오션 점수 = 가중 합산
bo['블루오션_점수'] = (
    bo['pct_공급갭'] * 0.30 +      # 공급갭(카페 많은데 찻집 없음) 30% 반영
    bo['pct_직장인구'] * 0.25 +    # 직장인구(수요) 25% 반영
    bo['pct_유동인구'] * 0.15 +    # 유동인구(수요) 15% 반영
    bo['pct_찻집수_inv'] * 0.20 +  # 찻집 적음(공급↓) 20% 반영
    bo['집객시설_수'].rank(pct=True) * 0.10  # 집객시설(인프라) 10% 반영
)
#  └ 가중 합산 공식: 각 지표의 백분위 × 가중치를 더해 최종 점수 산출
#    · 모든 지표가 0~1 사이 → 최종 점수도 0~1 사이 (비교 가능)
#    · 가중치 합계: 0.30 + 0.25 + 0.15 + 0.20 + 0.10 = 1.00

# 매출 필터: 하위 20% 제외 (수요 없는 곳) + 상위 10% 제외 (이미 포화)
매출_하한 = bo['당월_매출_금액'].quantile(0.20)
매출_상한 = bo['당월_매출_금액'].quantile(0.90)
#  └ Series.quantile(q): 분위수(경계값) 반환
#    · 기본문법: Series.quantile(q=0.5)
#    · q=0.20: 전체의 20%가 이 값 이하 → 하위 20% 기준선
#    · q=0.90: 전체의 90%가 이 값 이하 → 상위 10% 기준선

bo_filtered = bo[(bo['당월_매출_금액'] >= 매출_하한) &
                 (bo['당월_매출_금액'] <= 매출_상한)].copy()
#  └ 두 조건 동시 필터링
#    · >= 매출_하한: 수요 자체 없는 최하위 상권 제외
#    · <= 매출_상한: 이미 포화된 레드오션 상권 제외
#    · &: 두 Boolean Series의 원소별 AND

top50 = bo_filtered.nlargest(50, '블루오션_점수').reset_index(drop=True)
top50.index += 1
#  └ DataFrame.nlargest(n, 컬럼): 컬럼 기준 상위 n개 행 반환
#    · .reset_index(drop=True): 필터링 후 0,1,2... 인덱스 재부여
#    · .index += 1: 인덱스를 1부터 시작 (순위 표시용)

# 출력용 정리
top50['당월_매출_억원'] = (top50['당월_매출_금액'] / 1e8).round(2)
top50['블루오션_점수'] = top50['블루오션_점수'].round(4)
top50['pct_매출'] = (top50['pct_매출'] * 100).round(1)  # 0~1 → 0~100%로 변환

print(f"\n필터 기준: 매출 하위20%({매출_하한/1e8:.1f}억) 초과 & 상위10%({매출_상한/1e8:.1f}억) 이하")
print(f"후보군: {len(bo_filtered)}개 → 상위 50개 선정\n")
print(top50[['상권_코드_명', '상권_구분_코드_명_x', '블루오션_점수',
            '공급갭_지수', '찻집_수', '총_직장_인구_수', '당월_매출_억원', 'pct_매출']].to_string())

top50.to_csv('eda_blueocean_candidates.csv', index=True, index_label='순위', encoding='utf-8-sig')
print("\n→ eda_blueocean_candidates.csv 저장 완료")


# 블루오션 시각화 — 산점도: 공급갭 vs 직장인구, 색=블루오션점수
fig, ax = plt.subplots(figsize=(12, 8))
sc = ax.scatter(
    bo_filtered['공급갭_지수'],
    bo_filtered['총_직장_인구_수'] / 1000,
    c=bo_filtered['블루오션_점수'],   # 점 색을 블루오션 점수로 매핑
    cmap='RdYlGn',                    # 낮은 값=빨강, 중간=노랑, 높은 값=초록
    alpha=0.6, s=40
)
#  └ ax.scatter(x, y, c=, cmap=, alpha, s)
#    · c=배열: 각 점의 색을 1D 배열 값에 따라 컬러맵으로 매핑
#      - c에 배열을 넣으면 자동으로 min→max를 0→1로 정규화 후 색 지정
#    · cmap='RdYlGn': Red-Yellow-Green 컬러맵
#      - 블루오션 점수 낮음=빨강(레드오션), 높음=초록(블루오션) 직관적 표현
#    · 반환: PathCollection 객체 (plt.colorbar()에 전달할 mappable)

for _, row in top50.head(20).iterrows():
    ax.annotate(
        row['상권_코드_명'],
        (row['공급갭_지수'], row['총_직장_인구_수'] / 1000),
        fontsize=7, alpha=0.85,
        xytext=(4, 2), textcoords='offset points'
    )
#  └ ax.annotate(text, xy, xytext, textcoords, fontsize, alpha)
#    · 기본문법: ax.annotate(텍스트, xy=(x좌표, y좌표), xytext=오프셋, textcoords=기준)
#    · text: 표시할 문자열 (여기서는 상권명)
#    · xy=(공급갭, 직장인구): 텍스트가 가리키는 데이터 좌표 (점의 위치)
#    · xytext=(4, 2): 점으로부터 (오른쪽4, 위쪽2) 픽셀 떨어진 곳에 텍스트 배치
#    · textcoords='offset points': xytext를 데이터 좌표가 아닌 픽셀 오프셋으로 해석
#      - 'offset points': 포인트(pt) 단위 오프셋 — 화면 크기에 비례
#      - 'data': xytext를 데이터 축 단위로 해석 (기본값)
#    · 산점도에서 특정 점에 레이블 붙일 때 scatter()만으로는 불가 → annotate() 사용

plt.colorbar(sc, ax=ax, label='블루오션 점수')
#  └ plt.colorbar(mappable, ax=, label=): 색상 범례(컬러바) 추가
#    · 기본문법: plt.colorbar(mappable, ax=ax, label=레이블문자열)
#    · mappable: scatter() 반환값 (sc) — 색상 정보 포함 객체
#    · ax=ax: 어느 subplot에 컬러바를 붙일지 지정
#    · label=: 컬러바 옆에 표시할 레이블

ax.set_xlabel('공급갭_지수 (카페음료_점포수 / 찻집_수+1)')
ax.set_ylabel('총 직장인구 (천명)')
ax.set_title('블루오션 후보 상권 스크리닝\n(공급갭↑ × 직장인구↑ = 초록이 블루오션)', fontsize=13)
plt.tight_layout()
plt.savefig('eda_blueocean.png', dpi=150)
plt.close()
print("→ eda_blueocean.png 저장 완료")


# ══════════════════════════════════════════════════════
# ③ 자치구별 매출 분포
# ══════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("③ 자치구별 매출 분포")
print("=" * 60)

# 자치구 정보 조인 (to_map에서 자치구명 가져오기)
gu_map = to_map[['상권_코드', '자치구_코드_명']].drop_duplicates('상권_코드')
#  └ DataFrame.drop_duplicates('컬럼'): 특정 컬럼 기준 중복 제거
#    · 기본문법: df.drop_duplicates(subset=컬럼 또는 컬럼리스트, keep='first')
#    · 같은 상권_코드가 여러 분기에 걸쳐 반복 → 자치구명은 동일 → 첫 행만 유지

df25_gu = df25.merge(gu_map, on='상권_코드', how='left')
#  └ left join: df25의 모든 행 유지, gu_map에서 자치구_코드_명 가져오기

# 자치구별 집계
gu_stats = df25_gu.groupby('자치구_코드_명').agg(
    상권수=('상권_코드', 'count'),
    평균매출_억원=('당월_매출_금액', lambda x: x.mean() / 1e8),
    중앙매출_억원=('당월_매출_금액', lambda x: x.median() / 1e8),
    총매출_억원=('당월_매출_금액', lambda x: x.sum() / 1e8),
).reset_index().sort_values('평균매출_억원', ascending=False)
#  └ df.groupby(컬럼).agg(새이름=(대상컬럼, 함수)): 명명된 집계(Named Aggregation)
#    · 기본문법: .agg(결과컬럼명=(원본컬럼, 집계함수))
#    · 상권수=('상권_코드', 'count'): '상권_코드' 컬럼을 count → 결과 컬럼명 '상권수'
#    · 평균매출_억원=('당월_매출_금액', lambda x: x.mean() / 1e8):
#      - lambda x: 그룹별 Series를 받아 평균 계산 후 억원 단위로 변환
#    · 여러 집계를 한 번에 → 결과 DataFrame의 각 컬럼명이 명확해짐
#    · .reset_index(): groupby 인덱스(자치구_코드_명)를 일반 컬럼으로 이동

print(gu_stats.to_string(index=False))


# 자치구별 시각화
fig, axes = plt.subplots(2, 1, figsize=(14, 12))
#  └ 2행 1열 = 두 개의 서브플롯 (위아래로 배치)

# (a) 평균 매출 (위쪽 그래프)
ax1 = axes[0]
bars = ax1.bar(gu_stats['자치구_코드_명'], gu_stats['평균매출_억원'],
               color='steelblue', alpha=0.8, label='평균 매출')
#  └ ax.bar(x, height, color, alpha, label): 세로 막대 그래프
#    · 기본문법: ax.bar(x=카테고리배열, height=높이배열, color=색, alpha=투명도)
#    · label='평균 매출': legend()에서 사용할 레이블

ax1.scatter(gu_stats['자치구_코드_명'], gu_stats['중앙매출_억원'],
            color='tomato', zorder=5, s=50, label='중앙값 매출')
#  └ ax.scatter() 위에 점으로 중앙값 표시 (평균 막대와 비교)
#    · zorder=5: 막대(기본 zorder=1) 위에 점이 그려지도록
#      - zorder(z-order): Z축 순서 — 숫자 클수록 앞에 그려짐 (겹칠 때 보임)

ax1.set_ylabel('매출 (억원)')
ax1.set_title('자치구별 상권 평균 매출 (20253, 명동 제외)', fontsize=13)
ax1.tick_params(axis='x', rotation=45)
#  └ ax.tick_params(axis='x', rotation=45): X축 눈금 레이블 45도 회전
#    · 자치구명이 길어서 겹치지 않도록 기울임
ax1.legend()

# (b) 상권 수 (아래쪽 그래프)
ax2 = axes[1]
ax2.bar(gu_stats.sort_values('상권수', ascending=False)['자치구_코드_명'],
        gu_stats.sort_values('상권수', ascending=False)['상권수'],
        color='mediumpurple', alpha=0.8)
ax2.set_ylabel('상권 수')
ax2.set_title('자치구별 상권 수', fontsize=13)
ax2.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('eda_gu_sales.png', dpi=150)
plt.close()
print("\n→ eda_gu_sales.png 저장 완료")

print("\n" + "=" * 60)
print("전체 완료!")
print("  eda_vif_table.csv")
print("  eda_blueocean_candidates.csv")
print("  eda_vif.png")
print("  eda_blueocean.png")
print("  eda_gu_sales.png")
