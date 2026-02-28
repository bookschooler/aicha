"""
31_feature_selection_xgb_shap.py
XGBoost + SHAP 기반 Feature Selection

목적: 22개 대표 변수에서 매출 설명력 높은 변수 선별 + 변수 간 조합 효과 발굴
데이터: y_demand_supply_trend_merge.csv (9,760행, 명동 제외)
Y변수: log(당월_매출_금액 + 1)

산출물:
  fs_xgb_feature_importance.csv  — XGBoost 변수 중요도
  fs_shap_values.csv             — 상권×변수 SHAP값 (전체)
  fs_shap_summary.png            — SHAP 요약 (beeswarm)
  fs_xgb_importance.png          — XGBoost 변수 중요도 바 차트
  fs_shap_interaction_top.png    — 상위 변수 쌍 조합 효과
"""

import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import shap
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score

os.chdir('/teamspace/studios/this_studio/aicha')

# ── 한글 폰트 ──
font_path = '/system/conda/miniconda3/envs/cloudspace/lib/python3.12/site-packages/koreanize_matplotlib/fonts/NanumGothic.ttf'
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# ══════════════════════════════════════════
# 1. 데이터 준비
# ══════════════════════════════════════════
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')

# 명동 관광특구 제외 (이상치)
myeongdong = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
df = df[~df['상권_코드'].isin(myeongdong)].copy()

# Y변수: 로그변환
df['log_매출'] = np.log1p(df['당월_매출_금액'])

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

print(f"분석 데이터: {len(X):,}행 × {len(FEATURES)}개 변수")
print(f"결측치 현황:")
print(X.isnull().sum()[X.isnull().sum() > 0])

# ══════════════════════════════════════════
# 2. XGBoost 학습
# ══════════════════════════════════════════
print("\n" + "="*60)
print("XGBoost 학습")
print("="*60)

model = XGBRegressor(
    n_estimators=500,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    tree_method='hist',   # 결측치 자동 처리
)

# K-Fold 교차검증 (5-fold)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=kf, scoring='r2', n_jobs=-1)
print(f"5-Fold CV R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"  각 fold: {[round(s,4) for s in cv_scores]}")

# 전체 데이터로 재학습 (SHAP용)
model.fit(X, y)
y_pred = model.predict(X)
print(f"전체 데이터 R²: {r2_score(y, y_pred):.4f}")

# ── XGBoost Feature Importance ──
importance_df = pd.DataFrame({
    '변수명': FEATURES,
    '중요도_gain': model.get_booster().get_score(importance_type='gain').values()
        if model.get_booster().get_score(importance_type='gain') else [0]*len(FEATURES),
}).sort_values('중요도_gain', ascending=False).reset_index(drop=True)

# get_score 딕셔너리 방식으로 재처리
gain_dict = model.get_booster().get_score(importance_type='gain')
weight_dict = model.get_booster().get_score(importance_type='weight')
importance_rows = []
for f in FEATURES:
    importance_rows.append({
        '변수명': f,
        '중요도_gain': round(gain_dict.get(f'f{FEATURES.index(f)}', 0), 2),
        '중요도_weight': weight_dict.get(f'f{FEATURES.index(f)}', 0),
    })
importance_df = pd.DataFrame(importance_rows).sort_values('중요도_gain', ascending=False).reset_index(drop=True)
importance_df.index += 1

# feature_importances_ 속성 사용 (더 안정적)
fi_series = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
importance_df2 = pd.DataFrame({'변수명': fi_series.index, '중요도': fi_series.values})
importance_df2.index = range(1, len(importance_df2)+1)

print("\n[ XGBoost 변수 중요도 (feature_importances_) ]")
print(importance_df2.to_string())
importance_df2.to_csv('fs_xgb_feature_importance.csv', encoding='utf-8-sig')

# ══════════════════════════════════════════
# 3. SHAP 분석
# ══════════════════════════════════════════
print("\n" + "="*60)
print("SHAP 분석")
print("="*60)

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# SHAP 값 저장
shap_df = pd.DataFrame(shap_values, columns=FEATURES)
shap_df.to_csv('fs_shap_values.csv', index=False, encoding='utf-8-sig')
print("SHAP 값 저장 완료: fs_shap_values.csv")

# 변수별 평균 |SHAP| (전체 영향력)
mean_shap = pd.DataFrame({
    '변수명': FEATURES,
    '평균_절대SHAP': np.abs(shap_values).mean(axis=0)
}).sort_values('평균_절대SHAP', ascending=False).reset_index(drop=True)
mean_shap.index += 1
print("\n[ SHAP 평균 절대값 순위 ]")
print(mean_shap.to_string())

# ══════════════════════════════════════════
# 4. 시각화
# ══════════════════════════════════════════

# ── (A) XGBoost 변수 중요도 ──
fig, ax = plt.subplots(figsize=(10, 8))
colors = ['#e74c3c' if i < 5 else ('#f39c12' if i < 10 else '#3498db')
          for i in range(len(importance_df2))]
bars = ax.barh(importance_df2['변수명'][::-1], importance_df2['중요도'][::-1], color=colors[::-1])
ax.set_xlabel('중요도 (feature_importances_)')
ax.set_title('XGBoost 변수 중요도\n(빨강=상위5, 주황=상위10, 파랑=나머지)', fontsize=13)
for bar, v in zip(bars, importance_df2['중요도'][::-1]):
    ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
            f'{v:.4f}', va='center', fontsize=8)
plt.tight_layout()
plt.savefig('fs_xgb_importance.png', dpi=150)
plt.close()
print("\n→ fs_xgb_importance.png 저장 완료")

# ── (B) SHAP Summary Plot (beeswarm) ──
fig, ax = plt.subplots(figsize=(11, 9))
shap.summary_plot(shap_values, X, feature_names=FEATURES,
                  plot_type='dot', show=False, max_display=22)
plt.title('SHAP Summary Plot\n(점 색: 변수값 높음=빨강, 낮음=파랑 / X축: 매출에 미치는 영향)', fontsize=12)
plt.tight_layout()
plt.savefig('fs_shap_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("→ fs_shap_summary.png 저장 완료")

# ── (C) SHAP 상위 변수 의존성 플롯 (상위 4개) ──
top4 = mean_shap['변수명'].head(4).tolist()
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
for ax, feat in zip(axes.flatten(), top4):
    feat_idx = FEATURES.index(feat)
    shap.dependence_plot(
        feat_idx, shap_values, X,
        feature_names=FEATURES,
        ax=ax, show=False,
        interaction_index='auto'   # 자동으로 가장 상호작용 강한 변수 선택
    )
    ax.set_title(f'{feat}', fontsize=11)
plt.suptitle('SHAP 의존성 플롯 — 상위 4개 변수\n(점 색=상호작용 변수값, 기울기=비선형 효과)', fontsize=12)
plt.tight_layout()
plt.savefig('fs_shap_interaction_top.png', dpi=150, bbox_inches='tight')
plt.close()
print("→ fs_shap_interaction_top.png 저장 완료")

# ══════════════════════════════════════════
# 5. 최종 요약
# ══════════════════════════════════════════
print("\n" + "="*60)
print("최종 요약")
print("="*60)
print(f"\n모델 성능: CV R² = {cv_scores.mean():.4f} (5-fold 평균)")
print("\n[ SHAP 기준 중요도 상위 10개 ]")
print(mean_shap.head(10).to_string())
print("\n[ 중요도 낮은 변수 (제거 후보) ]")
print(mean_shap.tail(5).to_string())
print("\n산출물:")
print("  fs_xgb_feature_importance.csv")
print("  fs_shap_values.csv")
print("  fs_xgb_importance.png")
print("  fs_shap_summary.png")
print("  fs_shap_interaction_top.png")
