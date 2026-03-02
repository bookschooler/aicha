"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
31_feature_selection_xgb_shap.py — XGBoost + SHAP 변수 선택
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  22개 대표 변수에서 매출 설명력 높은 변수 선별 + 변수 간 조합 효과 발굴
  XGBoost로 비선형 중요도 계산 → SHAP으로 방향(양/음) 및 상호작용 시각화

Y변수: log(당월_매출_금액 + 1)

입력: y_demand_supply_trend_merge.csv
출력: fs_xgb_feature_importance.csv  — XGBoost 변수 중요도
      fs_shap_values.csv             — 상권×변수 SHAP값 (전체)
      fs_shap_summary.png            — SHAP 요약 (beeswarm)
      fs_xgb_importance.png          — XGBoost 변수 중요도 바 차트
      fs_shap_interaction_top.png    — 상위 변수 쌍 조합 효과
"""

import os                           # 파일 경로, 작업 디렉토리 관련 내장 모듈
import warnings
warnings.filterwarnings('ignore')   # 경고 메시지 숨기기 (FutureWarning 등)

import pandas as pd                 # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · pip install pandas 로 설치
#    · pd.read_csv(), df.groupby(), Series.isnull().sum() 등 전처리

import numpy as np                  # 다차원 수치 배열 계산 라이브러리
#  └ [numpy 라이브러리]
#    · pip install numpy 로 설치
#    · np.log1p(x): log(1+x) — x=0이어도 안전
#    · np.abs(배열): 각 원소의 절대값
#      - np.abs(shap_values): SHAP 값의 방향(부호) 제거 → 크기(영향력)만 추출
#    · 배열.mean(axis=0): 열 방향(변수별) 평균
#      - axis=0: 행들을 따라 내려가며 평균 → 각 컬럼(변수)의 평균값 반환
#      - axis=1: 열들을 따라 가로로 평균 → 각 행(샘플)의 평균값 반환

import matplotlib.pyplot as plt    # 데이터 시각화(그래프) 라이브러리
#  └ [matplotlib.pyplot 라이브러리]
#    · pip install matplotlib 로 설치
#    · plt.subplots(행, 열, figsize): 서브플롯 격자 생성
#    · ax.barh(y, width, color): 가로 막대 그래프
#    · ax.text(x, y, 문자열, va, fontsize): 임의 위치에 텍스트 추가
#    · plt.tight_layout(): 서브플롯 간격 자동 조정
#    · plt.savefig(경로, dpi): 이미지 파일 저장
#    · plt.close(): Figure 메모리 해제

import matplotlib.font_manager as fm  # matplotlib 폰트 관리 모듈
#  └ [matplotlib.font_manager 모듈]
#    · fm.fontManager.addfont(경로): 사용자 폰트 파일 등록
#    · plt.rcParams['font.family']: 기본 폰트 전역 설정
#    · plt.rcParams['axes.unicode_minus']: 음수 기호(−) 깨짐 방지

import shap                         # SHAP(SHapley Additive exPlanations) 라이브러리
#  └ [shap 라이브러리]
#    · pip install shap 로 설치
#    · SHAP이란?
#      - 게임이론의 샤플리(Shapley) 값 개념을 머신러닝에 적용
#      - 각 변수가 예측값에 얼마나 기여했는지 수치로 분해
#      - 예: 예측 log매출=18.5, 평균=17.0 → SHAP값 합=+1.5
#        - 총_직장_인구_수: +0.8, 공급갭_지수: +0.5, 찻집_수: -0.3, ...
#    · shap.TreeExplainer(모델): 트리 기반 모델용 SHAP 계산기
#      - 기본문법: shap.TreeExplainer(학습된모델)
#      - 트리(XGBoost, RandomForest 등)에 최적화 → 빠른 계산
#      - 선형 모델: shap.LinearExplainer, 일반 모델: shap.KernelExplainer
#    · explainer.shap_values(X): X의 각 샘플×변수에 대한 SHAP값 행렬 반환
#      - 기본문법: explainer.shap_values(DataFrame 또는 2D배열)
#      - 반환: (샘플수, 변수수) shape의 NumPy 배열
#      - 양수: 예측값을 평균보다 높이는 방향으로 기여
#      - 음수: 예측값을 평균보다 낮추는 방향으로 기여
#    · shap.summary_plot(shap_values, X, feature_names, plot_type, show, max_display):
#      - 기본문법: shap.summary_plot(shap_values, X)
#      - 변수별 SHAP 값 분포를 Beeswarm 플롯으로 시각화
#      - plot_type='dot': 각 샘플을 점으로 표시 (기본값)
#      - plot_type='bar': 평균 |SHAP| 막대 그래프
#      - show=False: 화면 출력 없이 plt 객체에만 저장 (파일 저장 목적)
#      - max_display=22: 표시할 변수 개수 상한
#    · shap.dependence_plot(feature_idx, shap_values, X, feature_names, ax, interaction_index):
#      - 기본문법: shap.dependence_plot(변수인덱스, shap_values, X)
#      - 특정 변수의 SHAP값 vs 변수값 산점도 (의존성 플롯)
#      - 비선형 효과 확인: 변수값이 커질수록 SHAP 값이 어떻게 변하는지
#      - interaction_index='auto': 가장 강하게 상호작용하는 변수를 자동 선택해 점 색으로 표시
#      - ax=ax: 특정 subplot에 그리기

from xgboost import XGBRegressor    # XGBoost 회귀 모델
#  └ [xgboost 라이브러리]
#    · pip install xgboost 로 설치
#    · XGBoost란?
#      - eXtreme Gradient Boosting: 여러 결정트리를 순차적으로 쌓아 앙상블하는 알고리즘
#      - 잔차(오차)를 줄이는 방향으로 트리를 계속 추가 → 매우 높은 정확도
#      - tree_method='hist': 결측치 자동 처리 + 빠른 학습
#    · XGBRegressor(n_estimators, max_depth, learning_rate, subsample, colsample_bytree,
#                   random_state, n_jobs, tree_method):
#      - 기본문법: XGBRegressor(n_estimators=500, max_depth=5, learning_rate=0.05)
#      - n_estimators=500: 결정트리 500개 순차 학습
#      - max_depth=5: 각 트리의 최대 깊이 (깊을수록 복잡, 과적합 위험)
#      - learning_rate=0.05: 각 트리의 기여도 축소 비율 (작을수록 안정적)
#      - subsample=0.8: 각 트리 학습 시 데이터의 80%만 랜덤 사용 (과적합 방지)
#      - colsample_bytree=0.8: 각 트리 학습 시 변수의 80%만 랜덤 사용
#      - n_jobs=-1: CPU 코어 전부 사용 (병렬 학습)
#      - tree_method='hist': 히스토그램 기반 학습 → NaN 자동 처리
#    · model.fit(X, y): 모델 학습
#    · model.predict(X): 예측
#    · model.feature_importances_: 변수별 중요도 배열 (합계=1)
#    · model.get_booster().get_score(importance_type='gain'):
#      - 딕셔너리 형태: {'f0': 중요도, 'f1': 중요도, ...}
#      - gain: 해당 변수로 분기할 때 얻는 평균 정보 이득 (클수록 중요)
#      - weight: 해당 변수가 분기에 사용된 횟수

from sklearn.model_selection import cross_val_score, KFold  # 교차검증 도구
#  └ [sklearn.model_selection 모듈]
#    · pip install scikit-learn 로 설치
#    · KFold(n_splits, shuffle, random_state): K-Fold 교차검증 분할 설정
#      - 기본문법: KFold(n_splits=5, shuffle=True, random_state=42)
#      - n_splits=5: 데이터를 5등분 → 5번 학습/검증 반복
#      - shuffle=True: 분할 전 데이터 셔플 (순서 편향 방지)
#      - random_state=42: 셔플 재현성 보장 (같은 값이면 항상 같은 결과)
#    · cross_val_score(모델, X, y, cv, scoring, n_jobs):
#      - 기본문법: cross_val_score(estimator, X, y, cv=5, scoring='r2')
#      - cv=kf: KFold 객체 → 어떻게 분할할지 지정
#      - scoring='r2': R² 점수로 평가 (1.0 = 완벽, 0 = 평균 예측과 동일)
#      - n_jobs=-1: 병렬 처리
#      - 반환: 각 fold의 점수 배열 → .mean()으로 평균 성능

from sklearn.metrics import r2_score  # R² 계산 함수
#  └ [sklearn.metrics 모듈]
#    · r2_score(y_true, y_pred): 실제값과 예측값의 R² 계산
#      - 기본문법: r2_score(실제값배열, 예측값배열)
#      - 반환: float (1.0=완벽, 0=평균 예측, 음수=평균 예측보다 나쁨)
#      - R² = 1 - (잔차제곱합 / 전체분산)

os.chdir('/teamspace/studios/this_studio/aicha')

# ── 한글 폰트 ──
font_path = '/system/conda/miniconda3/envs/cloudspace/lib/python3.12/site-packages/koreanize_matplotlib/fonts/NanumGothic.ttf'
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False


# ══════════════════════════════════════════════════════
# 1. 데이터 준비
# ══════════════════════════════════════════════════════
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')

# 명동 관광특구 제외 (이상치)
myeongdong = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
df = df[~df['상권_코드'].isin(myeongdong)].copy()

# Y변수: 로그변환
df['log_매출'] = np.log1p(df['당월_매출_금액'])
#  └ np.log1p(x): log(1 + x)
#    · 매출이 0인 상권도 안전하게 처리 (np.log(0) = -∞ 방지)
#    · 로그 변환: 오른쪽으로 치우친 분포(오른쪽 꼬리) → 정규분포에 가깝게 변환
#    · 회귀 모델의 예측 안정성 향상

# ── 22개 대표 변수 ──
FEATURES = [
    # 수요 — 인구
    '총_유동인구_수',
    '총_직장_인구_수',
    '총_상주인구_수',
    '총_가구_수',
    # 수요 — 소비
    '월_평균_소득_금액',
    '여가_지출_총금액',
    '지출_총금액',
    '아파트_평균_시가',
    # 수요 — 인프라
    '집객시설_수',
    # 공급
    '찻집_수',
    '카페음료_점포수',
    '스타벅스_리저브_수',
    # 조합지표
    '공급갭_지수',
    '유동밀도_지수',
    '상주밀도_지수',
    '여가소비_지수',
    # 트렌드
    '카페_검색지수',
    '검색량_성장률',
    '카페_개업률',
    '유동인구_성장률',
    # 접근성
    '지하철_역_수',
    '지하철_노선_수',
]

# 분석용 데이터 (결측 있는 행은 XGBoost가 자체 처리)
X = df[FEATURES].copy()
y = df['log_매출'].copy()

# 완전 결측 행 제거 (Y 결측)
mask = y.notna()
X, y = X[mask], y[mask]
#  └ Boolean 인덱싱으로 Y에 결측 없는 행만 선택
#    · X[mask]: mask가 True인 행만 필터링
#    · y.notna(): y(log_매출)가 NaN이 아닌 행 → True

print(f"분석 데이터: {len(X):,}행 × {len(FEATURES)}개 변수")
print(f"결측치 현황:")
print(X.isnull().sum()[X.isnull().sum() > 0])
#  └ DataFrame.isnull().sum(): 컬럼별 NaN 개수
#    · [X.isnull().sum() > 0]: 결측이 하나라도 있는 컬럼만 표시


# ══════════════════════════════════════════════════════
# 2. XGBoost 학습
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("XGBoost 학습")
print("="*60)

model = XGBRegressor(
    n_estimators=500,      # 결정트리 500개
    max_depth=5,           # 각 트리 최대 깊이 5
    learning_rate=0.05,    # 학습률 (작을수록 과적합 위험↓, 학습 느림)
    subsample=0.8,         # 데이터 80%로 각 트리 학습
    colsample_bytree=0.8,  # 변수 80%로 각 트리 학습
    random_state=42,       # 재현성 보장
    n_jobs=-1,             # CPU 전코어 사용
    tree_method='hist',    # 결측치 자동 처리 + 빠른 학습
)

# K-Fold 교차검증 (5-fold)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
#  └ KFold: 데이터를 5등분 → 1개를 검증, 나머지 4개로 학습 → 5번 반복
#    · 예: 1000개 데이터 → 800학습+200검증 × 5번 (겹치지 않게)
#    · shuffle=True: 순서대로 나누면 연도 편향 생길 수 있으므로 먼저 섞기

cv_scores = cross_val_score(model, X, y, cv=kf, scoring='r2', n_jobs=-1)
#  └ cross_val_score(모델, X, y, cv, scoring)
#    · 5번 학습/검증 → R² 5개 반환
#    · .mean(): 5개 R²의 평균 → 모델의 일반화 성능
#    · .std(): 표준편차 → 성능이 fold마다 얼마나 들쭉날쭉한지

print(f"5-Fold CV R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"  각 fold: {[round(s,4) for s in cv_scores]}")

# 전체 데이터로 재학습 (SHAP 값 계산용)
model.fit(X, y)
y_pred = model.predict(X)
print(f"전체 데이터 R²: {r2_score(y, y_pred):.4f}")
#  └ 전체 데이터 R² > CV R²: 과적합 정도 가늠 가능
#    · CV R²이 낮으면 모델이 새 데이터에 잘 맞지 않음

# ── XGBoost 변수 중요도 (feature_importances_ 방식) ──
fi_series = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
#  └ model.feature_importances_: NumPy 배열 (변수별 중요도, 합=1)
#    · FEATURES 순서와 동일 → pd.Series(값, index=변수명)으로 이름 부여
#    · sort_values(ascending=False): 중요도 높은 순 정렬

importance_df2 = pd.DataFrame({'변수명': fi_series.index, '중요도': fi_series.values})
importance_df2.index = range(1, len(importance_df2)+1)  # 1부터 시작하는 순위

print("\n[ XGBoost 변수 중요도 (feature_importances_) ]")
print(importance_df2.to_string())
importance_df2.to_csv('fs_xgb_feature_importance.csv', encoding='utf-8-sig')


# ══════════════════════════════════════════════════════
# 3. SHAP 분석
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("SHAP 분석")
print("="*60)

explainer = shap.TreeExplainer(model)
#  └ shap.TreeExplainer(모델): 트리 기반 모델용 SHAP 계산기 생성
#    · 기본문법: shap.TreeExplainer(학습된XGBoost모델)
#    · 트리 구조를 직접 순회하며 SHAP값 계산 → KernelExplainer보다 훨씬 빠름

shap_values = explainer.shap_values(X)
#  └ explainer.shap_values(X): 모든 샘플의 SHAP값 계산
#    · 기본문법: explainer.shap_values(DataFrame 또는 2D배열)
#    · 반환: (n_samples, n_features) shape의 NumPy 2D 배열
#      - 행: 각 상권 (샘플)
#      - 열: 각 변수 (feature)
#      - 값: 해당 샘플에서 해당 변수가 예측값에 기여한 양(양수=↑, 음수=↓)

# SHAP 값 저장
shap_df = pd.DataFrame(shap_values, columns=FEATURES)
shap_df.to_csv('fs_shap_values.csv', index=False, encoding='utf-8-sig')
print("SHAP 값 저장 완료: fs_shap_values.csv")

# 변수별 평균 |SHAP| (전체 영향력 순위)
mean_shap = pd.DataFrame({
    '변수명': FEATURES,
    '평균_절대SHAP': np.abs(shap_values).mean(axis=0)
    #  └ np.abs(shap_values): 부호 제거 → 방향과 상관없이 영향력 크기만 추출
    #    · .mean(axis=0): 행 방향(샘플들)의 평균 → 변수별 평균 영향력
    #    · 결과: 각 변수가 평균적으로 예측값을 얼마나 바꾸는지
}).sort_values('평균_절대SHAP', ascending=False).reset_index(drop=True)
mean_shap.index += 1  # 1부터 시작하는 순위

print("\n[ SHAP 평균 절대값 순위 ]")
print(mean_shap.to_string())


# ══════════════════════════════════════════════════════
# 4. 시각화
# ══════════════════════════════════════════════════════

# ── (A) XGBoost 변수 중요도 바 차트 ──
fig, ax = plt.subplots(figsize=(10, 8))
colors = ['#e74c3c' if i < 5 else ('#f39c12' if i < 10 else '#3498db')
          for i in range(len(importance_df2))]
#  └ 리스트 컴프리헨션: 상위 5개=빨강, 상위 10개=주황, 나머지=파랑
#    · i: 0부터 시작하는 순위 인덱스 (정렬 후이므로 0=가장 중요)

bars = ax.barh(importance_df2['변수명'][::-1], importance_df2['중요도'][::-1], color=colors[::-1])
#  └ [::-1]: 파이썬 슬라이싱 — 전체를 역순으로 뒤집기
#    · 기본문법: 배열[시작:끝:간격] → [::-1] = 끝부터 처음까지 역순
#    · barh는 아래→위 순서로 그리므로, 역순으로 넣으면 상위 항목이 위에 표시됨

ax.set_xlabel('중요도 (feature_importances_)')
ax.set_title('XGBoost 변수 중요도\n(빨강=상위5, 주황=상위10, 파랑=나머지)', fontsize=13)
for bar, v in zip(bars, importance_df2['중요도'][::-1]):
    ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
            f'{v:.4f}', va='center', fontsize=8)
plt.tight_layout()
plt.savefig('fs_xgb_importance.png', dpi=150)
plt.close()
print("\n→ fs_xgb_importance.png 저장 완료")


# ── (B) SHAP Summary Plot (Beeswarm) ──
fig, ax = plt.subplots(figsize=(11, 9))
shap.summary_plot(shap_values, X, feature_names=FEATURES,
                  plot_type='dot', show=False, max_display=22)
#  └ shap.summary_plot(shap_values, X, ...)
#    · 기본문법: shap.summary_plot(shap_values, X)
#    · plot_type='dot': Beeswarm 플롯 — 각 샘플을 점으로 표시
#      - X축: SHAP값 (오른쪽=매출↑ 기여, 왼쪽=매출↓ 기여)
#      - 점 색: 해당 샘플에서 변수 값이 높으면 빨강, 낮으면 파랑
#      - 예: 총_직장_인구_수가 높은 상권(빨강)이 오른쪽에 분포 → 직장인구 많으면 매출↑
#    · show=False: plt.show() 호출 안 함 → plt.savefig()로 파일만 저장
#    · max_display=22: 최대 22개 변수 표시 (전체 변수 수 = 22)
#    · feature_names: 변수명 레이블 (FEATURES 리스트)

plt.title('SHAP Summary Plot\n(점 색: 변수값 높음=빨강, 낮음=파랑 / X축: 매출에 미치는 영향)', fontsize=12)
plt.tight_layout()
plt.savefig('fs_shap_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("→ fs_shap_summary.png 저장 완료")


# ── (C) SHAP 상위 변수 의존성 플롯 (상위 4개) ──
top4 = mean_shap['변수명'].head(4).tolist()
#  └ Series.head(4): 상위 4개 행 반환
#    · .tolist(): Series → 파이썬 리스트 변환

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
for ax, feat in zip(axes.flatten(), top4):
    feat_idx = FEATURES.index(feat)
    #  └ list.index(값): 리스트에서 값의 위치(인덱스) 반환
    #    · FEATURES.index('총_유동인구_수') → 0 (FEATURES[0]이 총_유동인구_수이므로)
    #    · shap.dependence_plot()의 첫 번째 인자로 필요

    shap.dependence_plot(
        feat_idx, shap_values, X,
        feature_names=FEATURES,
        ax=ax, show=False,
        interaction_index='auto'
    )
    #  └ shap.dependence_plot(ind, shap_values, X, feature_names, ax, interaction_index)
    #    · 기본문법: shap.dependence_plot(변수인덱스, shap_values, X)
    #    · ind=feat_idx: 몇 번째 변수를 X축으로 볼지
    #    · X축: 해당 변수의 실제 값 (예: 총_직장_인구_수 실제 수치)
    #    · Y축: 해당 변수의 SHAP값 (매출 기여도)
    #    · 점 색: interaction_index 변수의 값 (상호작용 효과 시각화)
    #    · interaction_index='auto': SHAP과 가장 강하게 상호작용하는 변수 자동 선택
    #      - 예: 총_직장_인구_수 SHAP이 공급갭_지수에 따라 달라지면 공급갭으로 채색
    #    · show=False: 화면 출력 않고 ax에만 그리기
    #    · 해석: Y축 기울기가 있으면 비선형 효과 존재
    #      - 직장인구가 적을 때 기여도↑, 많을 때 기여도 정체 → 수확체감

    ax.set_title(f'{feat}', fontsize=11)

plt.suptitle('SHAP 의존성 플롯 — 상위 4개 변수\n(점 색=상호작용 변수값, 기울기=비선형 효과)', fontsize=12)
plt.tight_layout()
plt.savefig('fs_shap_interaction_top.png', dpi=150, bbox_inches='tight')
plt.close()
print("→ fs_shap_interaction_top.png 저장 완료")


# ══════════════════════════════════════════════════════
# 5. 최종 요약
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("최종 요약")
print("="*60)
print(f"\n모델 성능: CV R² = {cv_scores.mean():.4f} (5-fold 평균)")
print("\n[ SHAP 기준 중요도 상위 10개 ]")
print(mean_shap.head(10).to_string())
print("\n[ 중요도 낮은 변수 (제거 후보) ]")
print(mean_shap.tail(5).to_string())
#  └ DataFrame.tail(n): 마지막 n개 행 반환 (head()의 반대)
#    · SHAP 중요도가 낮은 변수 → 회귀 모델에서 제거 고려
print("\n산출물:")
print("  fs_xgb_feature_importance.csv")
print("  fs_shap_values.csv")
print("  fs_xgb_importance.png")
print("  fs_shap_summary.png")
print("  fs_shap_interaction_top.png")
