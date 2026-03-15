# 34_ols.py
# Pooled OLS + GroupKFold(n_splits=5) → OOF 잔차 추출
#
# 입력: 33_analysis_ready.csv
# 출력:
#   34_oof_residuals.csv      - 전체 행별 OOF 잔차
#   34_district_residuals.csv - 상권별 집계 (최신분기 + 9분기평균)
#   34_model_coefficients.csv - 전체 데이터 OLS 계수 (해석용)
#   34_ols_log.txt            - 실행 로그
# ─────────────────────────────────────────────

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
import os

BASE = os.path.dirname(os.path.abspath(__file__))
IN_PATH      = os.path.join(BASE, '33_analysis_ready.csv')
OUT_OOF      = os.path.join(BASE, '34_oof_residuals.csv')
OUT_DISTRICT = os.path.join(BASE, '34_district_residuals.csv')
OUT_COEF     = os.path.join(BASE, '34_model_coefficients.csv')
OUT_LOG      = os.path.join(BASE, '34_ols_log.txt')

logs = []

# ─────────────────────────────────────────────
# 1. 데이터 로드
# ─────────────────────────────────────────────
df = pd.read_csv(IN_PATH, encoding='utf-8-sig')
logs.append(f"입력 데이터: {df.shape[0]}행 × {df.shape[1]}열")
logs.append(f"상권 수: {df['상권_코드'].nunique()}개")
logs.append(f"분기 수: {df['기준_년분기_코드'].nunique()}개")

DEMAND_SCALED = [
    '집객시설_수_scaled', '총_직장_인구_수_scaled', '월_평균_소득_금액_scaled',
    '총_가구_수_scaled', '카페_검색지수_scaled', '지하철_노선_수_scaled'
]
QUARTER_DUMMIES = [c for c in df.columns if c.startswith('Q_')]
TYPE_DUMMIES    = [c for c in df.columns if c.startswith('TYPE_')]
X_COLS = DEMAND_SCALED + QUARTER_DUMMIES + TYPE_DUMMIES

X      = df[X_COLS].values
y      = df['y_log'].values
groups = df['상권_코드'].values

logs.append(f"\nX 변수 {len(X_COLS)}개:")
logs.append(f"  수요(표준화) : {DEMAND_SCALED}")
logs.append(f"  분기더미     : {QUARTER_DUMMIES}")
logs.append(f"  유형더미     : {TYPE_DUMMIES}")

# ─────────────────────────────────────────────
# 2. GroupKFold OOF 잔차 추출
# ─────────────────────────────────────────────
gkf = GroupKFold(n_splits=5)
oof_residuals = np.full(len(y), np.nan)
oof_pred      = np.full(len(y), np.nan)
fold_r2s      = []

logs.append(f"\n[GroupKFold] n_splits=5, groups=상권_코드")
logs.append(f"  → 같은 상권의 9개 분기가 통째로 train/test 분리 (data leakage 방지)")

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups=groups)):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred     = model.predict(X_test)
    residuals  = y_test - y_pred  # 양수=과성과, 음수=저성과(블루오션 후보)

    oof_pred[test_idx]      = y_pred
    oof_residuals[test_idx] = residuals

    fold_r2          = r2_score(y_test, y_pred)
    n_test_districts = len(np.unique(groups[test_idx]))
    fold_r2s.append(fold_r2)
    logs.append(f"  Fold {fold+1}: test {len(test_idx)}행 ({n_test_districts}개 상권) | R²={fold_r2:.4f}")

mean_r2 = np.mean(fold_r2s)
logs.append(f"\n  OOF 평균 R²: {mean_r2:.4f}")
logs.append(f"  잔차 완성: nan 수 = {np.isnan(oof_residuals).sum()}")

# ─────────────────────────────────────────────
# 3. 전체 데이터 OLS — 계수 해석용
# ─────────────────────────────────────────────
full_model = LinearRegression()
full_model.fit(X, y)
full_r2 = r2_score(y, full_model.predict(X))
logs.append(f"\n[전체 데이터 OLS] R²={full_r2:.4f} (해석용, OOF 아님)")

coef_df = pd.DataFrame({
    '변수명': X_COLS,
    '계수':   full_model.coef_
}).sort_values('계수', ascending=False)
coef_df.to_csv(OUT_COEF, index=False, encoding='utf-8-sig')

logs.append("\n계수 순위 (전체):")
for _, row in coef_df.iterrows():
    logs.append(f"  {row['변수명']:40s}: {row['계수']:+.4f}")

# ─────────────────────────────────────────────
# 4. 행별 OOF 잔차 저장
# ─────────────────────────────────────────────
df_oof = df[['상권_코드', '상권_코드_명', '기준_년분기_코드',
             '상권_구분_코드_명_x', 'y_log', '당월_매출_금액',
             '찻집_수', '카페음료_점포수']].copy()
df_oof['oof_pred']     = oof_pred
df_oof['oof_residual'] = oof_residuals
df_oof.to_csv(OUT_OOF, index=False, encoding='utf-8-sig')
logs.append(f"\n[저장] 행별 OOF 잔차: {OUT_OOF}")

# ─────────────────────────────────────────────
# 5. 상권별 집계
#    메인:  최신 분기(20253) OOF 잔차
#    검증:  9분기 평균 OOF 잔차
# ─────────────────────────────────────────────
latest_q = int(df['기준_년분기_코드'].max())
logs.append(f"\n[집계] 최신 분기: {latest_q}")

# 최신 분기
df_latest = df_oof[df_oof['기준_년분기_코드'] == latest_q][
    ['상권_코드', '상권_코드_명', '상권_구분_코드_명_x',
     'oof_residual', 'oof_pred', 'y_log', '당월_매출_금액', '찻집_수']
].copy()
df_latest.columns = [
    '상권_코드', '상권_코드_명', '상권유형',
    'residual_latest', 'pred_latest', 'y_log_latest', '매출_latest', '찻집수_latest'
]

# 9분기 평균
df_avg = df_oof.groupby('상권_코드').agg(
    residual_avg=('oof_residual', 'mean'),
    residual_std=('oof_residual', 'std'),
    n_quarters  =('oof_residual', 'count'),
).reset_index()

# 병합
df_dist = df_latest.merge(df_avg, on='상권_코드', how='left')

# Track B: 공급부족지수 = 1 / (찻집_수 + 1)
df_dist['supply_shortage'] = 1 / (df_dist['찻집수_latest'] + 1)

# 잔차 일관성 플래그 (최신·평균 모두 음수 = 구조적 블루오션)
df_dist['residual_consistent'] = (
    (df_dist['residual_latest'] < 0) & (df_dist['residual_avg'] < 0)
)

# 블루오션 1차 후보 (잔차 음수 + 찻집 0~1개)
df_dist['blueocean_candidate'] = (
    (df_dist['residual_latest'] < 0) &
    (df_dist['찻집수_latest'] <= 1)
)

df_dist = df_dist.sort_values('residual_latest')
df_dist.to_csv(OUT_DISTRICT, index=False, encoding='utf-8-sig')
logs.append(f"[저장] 상권별 집계: {OUT_DISTRICT}")

# ─────────────────────────────────────────────
# 6. 요약
# ─────────────────────────────────────────────
n_neg       = (df_dist['residual_latest'] < 0).sum()
n_candidate = df_dist['blueocean_candidate'].sum()
n_consist   = df_dist['residual_consistent'].sum()

logs.append("\n" + "="*55)
logs.append("=== OLS + OOF 잔차 추출 완료 ===")
logs.append("="*55)
logs.append(f"OOF 평균 R²  : {mean_r2:.4f}")
logs.append(f"전체 OLS R²  : {full_r2:.4f} (in-sample, 참고용)")
logs.append(f"")
logs.append(f"[잔차 분포 — 최신분기 {latest_q}]")
logs.append(f"  음수(블루오션 방향) : {n_neg}개")
logs.append(f"  양수(레드오션 방향) : {len(df_dist)-n_neg}개")
logs.append(f"")
logs.append(f"[블루오션 1차 후보]  잔차<0 + 찻집수<=1 : {n_candidate}개")
logs.append(f"[구조적 블루오션]    최신·평균 모두 음수  : {n_consist}개")
logs.append(f"")
logs.append(f"다음 단계: 35_blueocean_score.py")
logs.append(f"  → 2D 매트릭스 (X=OOF잔차, Y=공급부족지수) + 최종 랭킹")

log_text = "\n".join(logs)
with open(OUT_LOG, 'w', encoding='utf-8') as f:
    f.write(log_text)

print(log_text)
