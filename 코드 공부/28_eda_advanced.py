"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
28_eda_advanced.py — 심화 EDA 3종
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  ① 다중공선성 히트맵: R² 상위 30개 변수 간 상관관계 시각화
  ② 분기별 매출 추이 + 카페 검색지수 연동 (이중 Y축)
  ③ 상권 유형별 주요 변수 박스플롯 비교

입력: y_demand_supply_trend_merge.csv, eda_correlation_table_nooutlier.csv
출력: eda_multicollinearity_heatmap.png
      eda_quarterly_trend.png
      eda_by_district_type.png
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리 변경

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · np.triu(matrix): 행렬의 상삼각(upper triangle) 부분만 남기고 나머지 0으로
#      - triu = upper triangular (upper triangle의 약자)
#      - 히트맵에서 대각선 위쪽만 표시하고 아래는 숨길 때 사용
#    · np.ones_like(array, dtype): array와 같은 shape의 1로 채워진 배열 생성
#      - dtype=bool: True/False 배열 생성
#    · np.triu(np.ones_like(matrix, dtype=bool)):
#      - matrix와 같은 크기의 True 배열 생성 → 상삼각만 True인 마스크 생성
#      - 히트맵의 상삼각 영역을 가려서 중복 정보 제거

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · df.corr(): DataFrame의 모든 수치형 컬럼 간 상관계수 행렬 계산
#      - 반환: (변수 수 × 변수 수) 상관계수 DataFrame
#      - 대각선: 자기 자신과의 상관 = 항상 1.0
#      - 다중공선성: 두 X변수 간 |r| > 0.7이면 문제 가능성
#    · df.groupby(컬럼)[대상컬럼].mean(): 그룹별 평균
#    · df.groupby([컬럼1, 컬럼2])[대상].mean(): 두 컬럼 기준 그룹별 평균
#    · Series.unstack(레벨): MultiIndex Series → DataFrame으로 변환
#      - groupby 두 컬럼 사용 시 결과가 MultiIndex → unstack으로 2D 표 변환
#    · df[컬럼].dropna(): NaN 제거 후 Series 반환
#    · df[컬럼].unique(): 고유값 배열 반환

import matplotlib.pyplot as plt    # 데이터 시각화 라이브러리
#  └ [matplotlib.pyplot 라이브러리]
#    · pip install matplotlib 로 설치
#    · plt.subplots(행, 열, figsize): 서브플롯 격자 생성
#    · ax.plot(x, y, marker, label, linewidth): 선 그래프
#      - marker: 데이터 포인트 모양 ('o'=원, 's'=사각형 등)
#      - label: 범례에 표시될 이름
#    · ax.twinx():
#      - 기존 ax와 x축을 공유하는 새 Axes 생성 (Y축만 오른쪽에 추가)
#      - 서로 다른 스케일의 두 변수를 하나의 그래프에 표시할 때 사용
#      - 예: 왼쪽 Y = 매출(억원), 오른쪽 Y = 검색지수(0~100)
#    · ax.set_ylabel(문자열, color): Y축 이름과 색상 동시 설정
#    · ax.tick_params(axis, labelcolor): 특정 축의 눈금 색상 설정
#      - axis='y': Y축만 / axis='x': X축만 / axis='both': 양쪽
#    · ax.get_legend_handles_labels(): 범례 핸들과 레이블 리스트 반환
#      - 이중 Y축에서 양쪽 범례를 합칠 때 사용
#    · ax.legend(handles, labels, loc): 범례 직접 지정
#    · ax.grid(True, alpha): 격자선 표시 (alpha: 투명도)
#    · ax.boxplot(data, labels, patch_artist, showfliers):
#      - 박스플롯(box plot) 그리기
#      - data: 그룹별 데이터 리스트 [[그룹1값들], [그룹2값들], ...]
#      - labels: 각 박스의 x축 레이블
#      - patch_artist=True: 박스 내부를 색으로 채움 (기본은 선만)
#      - showfliers=False: 이상치 점(outlier)을 표시하지 않음
#    · bp['boxes']: boxplot 반환 딕셔너리에서 박스 객체 리스트
#    · patch.set_facecolor(color): 박스 내부 색상 설정
#    · patch.set_alpha(투명도): 박스 투명도 설정
#    · plt.tight_layout(), savefig(), close(): 27번과 동일

import matplotlib.ticker as mticker # matplotlib 축 눈금 포맷 설정 모듈
#  └ [matplotlib.ticker 모듈]
#    · matplotlib 내장 모듈 (별도 설치 불필요)
#    · 축 눈금 표시 형식을 세밀하게 조정
#    · 이 파일에서는 import만 하고 직접 사용은 안 함

import koreanize_matplotlib         # matplotlib 한글 폰트 자동 설정
#  └ import만 해도 한글 폰트(NanumGothic) 자동 등록

import seaborn as sns               # 통계 시각화 라이브러리
#  └ [seaborn 라이브러리]
#    · pip install seaborn 로 설치
#    · matplotlib 기반으로 더 아름다운 통계 그래프를 쉽게 그릴 수 있는 라이브러리
#    · sns.heatmap(data, mask, annot, fmt, cmap, center, vmin, vmax, ...):
#      - 상관관계 행렬 등을 색상으로 표현하는 히트맵 생성
#      - data: 표시할 데이터 (보통 상관계수 행렬)
#      - mask: True인 셀을 숨김 (np.triu로 상삼각 마스크 생성)
#      - annot=True: 각 셀에 숫자값 표시
#      - fmt='.2f': 숫자 포맷 (소수점 2자리)
#      - cmap='RdYlGn': 색상 팔레트 (Red-Yellow-Green)
#        · 빨강=-1(강한 음의 상관), 초록=1(강한 양의 상관), 노랑=0(무관)
#      - center=0: 색상 중앙값 0 (양/음의 상관 대칭 표현)
#      - vmin=-1, vmax=1: 색상 범위 (-1~1로 고정)
#      - linewidths: 셀 간 구분선 두께
#      - annot_kws={'size': 7}: 셀 내 숫자 글자 크기
#      - ax=ax: 특정 Axes에 그리기

os.chdir('/teamspace/studios/this_studio/aicha')


# ══════════════════════════════════════════════════════
# 데이터 로드
# ══════════════════════════════════════════════════════
df_all = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')  # 전체 분기 데이터
df     = df_all[df_all['기준_년분기_코드'] == 20253].copy()  # 최신 분기 단면 데이터 (①③용)

# 매출 파생변수 제외 컬럼 목록 (27번과 동일 기준)
exclude = [
    '기준_년_코드', '기준_분기_코드', '기준_년분기_코드',
    '상권_코드', '상권_구분_코드', '상권_구분_코드_명_x', '상권_코드_명',
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ① 다중공선성 히트맵 — R² 상위 30개 변수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("① 다중공선성 히트맵 생성 중...")

corr_rank = pd.read_csv('eda_correlation_table_nooutlier.csv', encoding='utf-8-sig')  # 27b번 결과 로드
top30_cols = corr_rank.head(30)['변수명'].tolist()  # R² 상위 30개 변수명 리스트
top30_cols = [c for c in top30_cols if c in df.columns]  # 실제 존재하는 컬럼만 필터링

corr_matrix = df[top30_cols].corr()
#  └ DataFrame.corr()
#    · 기본문법: DataFrame.corr(method='pearson')
#    · 모든 수치형 컬럼 쌍 간의 피어슨 상관계수를 계산해 (변수×변수) 행렬 반환
#    · 대각선: 자기 자신과의 상관 = 1.0
#    · 다중공선성 확인: |r| > 0.7이면 두 변수가 거의 같은 정보를 담고 있음
#      → 회귀분석에서 둘 다 넣으면 계수 추정 불안정

fig, ax = plt.subplots(figsize=(18, 15))  # 크기가 큰 히트맵용 Figure

mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
#  └ np.ones_like(corr_matrix, dtype=bool)
#    · corr_matrix와 같은 (30×30) shape의 True 배열 생성
#  └ np.triu(배열)
#    · 상삼각 행렬(upper triangular): 대각선 위쪽만 남기고 아래는 False
#    · 히트맵에서 상삼각을 숨겨 대칭 정보 중복 제거 (아래쪽만 표시)
#    · 예: 30×30 행렬에서 위쪽 삼각형은 True(숨김), 아래쪽은 False(표시)

sns.heatmap(
    corr_matrix, mask=mask, annot=True, fmt='.2f',
    cmap='RdYlGn', center=0, vmin=-1, vmax=1,
    linewidths=0.5, annot_kws={'size': 7},
    ax=ax
)
#  └ sns.heatmap(...)
#    · 상관계수 행렬을 색상으로 표현하는 히트맵
#    · mask=mask: 상삼각(True)은 숨김 → 하삼각만 표시
#    · annot=True: 각 셀에 상관계수 숫자 표시
#    · fmt='.2f': 소수점 2자리로 표시 (예: 0.73)
#    · cmap='RdYlGn': 빨강(음의 상관) → 노랑(0) → 초록(양의 상관)
#    · center=0: 색상 기준점을 0으로 설정
#    · vmin=-1, vmax=1: 색상 범위 고정 (항상 -1~1로 표현)
#    · linewidths=0.5: 셀 구분선 두께

ax.set_title('X변수 간 다중공선성 히트맵 (R² 상위 30개, 20253 기준)\n|r| > 0.7 이면 다중공선성 주의', fontsize=13)
ax.tick_params(axis='x', labelsize=8, rotation=45)  # X축 레이블 45도 회전
ax.tick_params(axis='y', labelsize=8, rotation=0)   # Y축 레이블 수평 유지
plt.tight_layout()
plt.savefig('eda_multicollinearity_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ eda_multicollinearity_heatmap.png 저장")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ② 분기별 매출 추이 + 카페 검색지수 연동
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("② 분기별 매출 추이 생성 중...")

quarters = sorted(df_all['기준_년분기_코드'].unique())  # 전체 분기 정렬 리스트
quarter_labels = [str(q) for q in quarters]             # 분기 코드 → 문자열 변환 (X축 레이블용)

# 전체 평균 매출 추이 (분기별)
매출_추이 = df_all.groupby('기준_년분기_코드')['당월_매출_금액'].mean() / 1e6
#  └ df.groupby(컬럼)[대상컬럼].mean()
#    · 분기별로 그룹화 후 매출 평균 계산 → 분기별 평균 매출 Series
#    · / 1e6: 원 단위 → 백만원 단위로 변환 (1e6 = 1,000,000)

# 상권 유형별 평균 매출 추이 (분기×유형)
유형별_추이 = df_all.groupby(['기준_년분기_코드', '상권_구분_코드_명_x'])['당월_매출_금액'].mean() / 1e6
유형별_추이 = 유형별_추이.unstack('상권_구분_코드_명_x')
#  └ Series.unstack(레벨)
#    · 기본문법: Series.unstack(level=-1)
#    · MultiIndex Series → 2D DataFrame 변환
#    · groupby 두 컬럼 사용 시 (분기, 유형) MultiIndex Series가 됨
#    · unstack('상권_구분_코드_명_x'): 유형을 컬럼으로 올려서
#      행=분기, 열=상권유형 형태의 DataFrame으로 변환
#    · 예: (20233, 골목상권) → 행:20233, 열:골목상권

# 카페 검색지수 전체 평균 추이
검색_추이 = df_all.groupby('기준_년분기_코드')['카페_검색지수'].mean()

fig, axes = plt.subplots(2, 1, figsize=(14, 10))  # 2행 1열 서브플롯

# 상단: 상권 유형별 매출 추이
ax1 = axes[0]
for col in 유형별_추이.columns:
    ax1.plot(quarter_labels, 유형별_추이[col].values, marker='o', label=col, linewidth=2)
    #  └ ax.plot(x, y, marker='o', label, linewidth)
    #    · marker='o': 각 데이터 포인트에 원 표시
    #    · label: 범례에 표시될 이름 (상권 유형명)
ax1.set_title('상권 유형별 분기별 평균 매출 추이 (백만원)', fontsize=12)
ax1.set_ylabel('평균 매출 (백만원)')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)  # 격자선 표시 (투명도 30%)
ax1.tick_params(axis='x', rotation=30)

# 하단: 전체 매출 vs 카페 검색지수 (이중 Y축)
ax2 = axes[1]
color1, color2 = 'steelblue', 'darkorange'

ax2.plot(quarter_labels, 매출_추이.values, marker='o', color=color1, label='평균 매출(백만원)', linewidth=2)
ax2.set_ylabel('평균 매출 (백만원)', color=color1)
ax2.tick_params(axis='y', labelcolor=color1)
#  └ ax.tick_params(axis='y', labelcolor): Y축 눈금 숫자를 특정 색으로

ax2_twin = ax2.twinx()
#  └ ax.twinx()
#    · 기본문법: Axes.twinx()
#    · 기존 ax2와 X축을 공유하는 새 Axes 생성 (Y축만 오른쪽에 추가)
#    · 완전히 다른 스케일의 두 변수를 같은 그래프에 그릴 때 사용
#    · 예: 매출(왼쪽 Y) + 검색지수(오른쪽 Y)를 같은 X(분기)로 비교

ax2_twin.plot(quarter_labels, 검색_추이.values, marker='s', color=color2,
              label='카페 검색지수', linewidth=2, linestyle='--')
ax2_twin.set_ylabel('카페 검색지수', color=color2)
ax2_twin.tick_params(axis='y', labelcolor=color2)

ax2.set_title('전체 평균 매출 vs 카페 검색지수 분기별 추이', fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.tick_params(axis='x', rotation=30)

# 두 Axes의 범례 합치기
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
#  └ ax.get_legend_handles_labels()
#    · 현재 Axes에 plot된 선들의 핸들(선 객체)과 레이블(이름) 리스트 반환
#    · 이중 Y축은 두 Axes에 각각 범례가 있어 따로 합쳐줘야 함

ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)
#  └ ax.legend(handles, labels): 범례 직접 지정
#    · lines1 + lines2: 두 리스트를 이어붙여 전체 범례 핸들
#    · labels1 + labels2: 두 리스트를 이어붙여 전체 범례 이름

plt.tight_layout()
plt.savefig('eda_quarterly_trend.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ eda_quarterly_trend.png 저장")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ③ 상권 유형별 주요 변수 비교 (박스플롯)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("③ 상권 유형별 비교 생성 중...")

compare_vars = [
    ('당월_매출_금액', '당월 매출 (백만원)', 1e6),  # (컬럼명, 표시이름, 단위변환)
    ('총_직장_인구_수', '직장 인구 수', 1),
    ('총_유동인구_수', '유동 인구 수', 1),
    ('공급갭_지수', '공급갭 지수', 1),
    ('카페_검색지수', '카페 검색지수', 1),
    ('지하철_역_수', '지하철 역 수', 1),
]

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
axes = axes.flatten()  # 2×3 배열 → 1D 배열 (for 루프 순회용)
유형순서 = sorted(df['상권_구분_코드_명_x'].dropna().unique())
#  └ Series.dropna(): NaN 제거 / .unique(): 고유값 배열 / sorted(): 정렬

for i, (col, label, scale) in enumerate(compare_vars):
    #  └ enumerate(iterable): (인덱스, 값) 쌍 반환
    #    · compare_vars 각 원소는 (컬럼명, 표시이름, 스케일) 튜플
    #    · (col, label, scale) = 튜플 언패킹

    ax = axes[i]
    data = [df[df['상권_구분_코드_명_x'] == t][col].dropna() / scale for t in 유형순서]
    #  └ 리스트 컴프리헨션으로 유형별 데이터 리스트 생성
    #    · df[df['상권_구분_코드_명_x'] == t]: 해당 유형의 행만 필터링
    #    · [col].dropna(): 해당 컬럼 값에서 NaN 제거
    #    · / scale: 단위 변환 (매출: ÷1e6으로 백만원 변환)

    bp = ax.boxplot(data, labels=유형순서, patch_artist=True, showfliers=False)
    #  └ ax.boxplot(data, labels, patch_artist, showfliers)
    #    · data: 그룹별 데이터 리스트 [[그룹1값들], [그룹2값들], ...]
    #    · labels: X축의 각 박스 이름
    #    · patch_artist=True: 박스 내부 색상 채우기 활성화
    #    · showfliers=False: 이상치(outlier) 점 숨김 → 깔끔한 시각화
    #    · 박스플롯 구성: 최솟값-Q1-중앙값-Q3-최댓값 (whisker)
    #    · 반환: {'boxes': [...], 'medians': [...], 'whiskers': [...]} 딕셔너리

    colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52']
    for patch, color in zip(bp['boxes'], colors[:len(유형순서)]):
        #  └ zip(리스트1, 리스트2): 두 리스트를 묶어 (원소1, 원소2) 쌍으로 반환
        #    · bp['boxes']: boxplot의 박스 객체 리스트
        #    · colors[:len(유형순서)]: 유형 수만큼만 색상 사용
        patch.set_facecolor(color)  # 박스 내부 색상 설정
        patch.set_alpha(0.7)        # 70% 불투명도 (약간 투명하게)

    ax.set_title(label, fontsize=11)
    ax.set_ylabel(label, fontsize=9)
    ax.tick_params(axis='x', labelsize=8, rotation=15)
    ax.grid(True, alpha=0.3, axis='y')  # Y축 방향 격자선만

plt.suptitle('상권 유형별 주요 변수 분포 비교 (20253 기준, 이상치 제외)', fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig('eda_by_district_type.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ eda_by_district_type.png 저장")

print("\n✅ 전체 완료!")
print("  - eda_multicollinearity_heatmap.png")
print("  - eda_quarterly_trend.png")
print("  - eda_by_district_type.png")
