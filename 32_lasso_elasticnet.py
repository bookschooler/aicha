"""
32_lasso_elasticnet.py
Track A 수요 변수 최종 선별 — Lasso / ElasticNet

목적:
  - 9개 수요 변수 후보에서 다중공선성 고려한 최종 변수 확정
  - Lasso: 변수 자동 제거 (L1 정규화)
  - ElasticNet: Lasso + Ridge 혼합 (상관 변수 그룹 처리에 유리)
  - 선택된 변수의 VIF 확인 → Ridge vs OLS 선택 기준 제공

전처리 (그룹별 결측 전략):
  그룹 B — 구조적 전체 결측 상권 제거
           총_직장_인구_수 결측 상권 (2개)
           총_상주인구_수 / 총_가구_수 결측 상권 (6개)
  그룹 C — 소득 미연계 상권 제거
           월_평균_소득_금액 / 여가_지출_총금액 / 지출_총금액 동시 결측 상권 (23개)
  그룹 D — 집객시설_수 구조적 결측 상권 제거 (13개) + 부분 결측 forward-fill (7개)
  그룹 E — 아파트_평균_시가 변수 자체 제외 (7.2% 결측, 대체 불가)

모델 구조:
  Y = log1p(당월_매출_금액)
  X = 9개 수요 변수(표준화) + 분기 더미 8개 + 상권유형 더미

산출물:
  32_lasso_path.png         : Lasso 정규화 경로 (alpha별 계수 변화)
  32_coef_comparison.png    : Lasso vs ElasticNet 계수 비교
  32_selected_vars.csv      : 최종 선택 변수 목록 (Lasso 기준)
  32_vif_final.csv          : 선택 변수 VIF 테이블
  32_preprocessing_log.txt  : 결측 처리 상권 수 로그
"""

import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from sklearn.linear_model import LassoCV, ElasticNetCV, lasso_path
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ── 경로 설정 ──
BASE_DIR = 'c:/Users/Administrator/Desktop/pypjt/aicha'
os.chdir(BASE_DIR)

# ── 한글 폰트 ──
font_candidates = [
    'C:/Windows/Fonts/malgun.ttf',          # 맑은 고딕 (Windows)
    'C:/Windows/Fonts/NanumGothic.ttf',
    '/system/conda/miniconda3/envs/cloudspace/lib/python3.12/site-packages/koreanize_matplotlib/fonts/NanumGothic.ttf',
]
for fp in font_candidates:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
        plt.rcParams['font.family'] = fm.FontProperties(fname=fp).get_name()
        break
plt.rcParams['axes.unicode_minus'] = False

# ══════════════════════════════════════════════════════
# 1. 데이터 로드
# ══════════════════════════════════════════════════════
print("=" * 65)
print("1. 데이터 로드")
print("=" * 65)

df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
print(f"원본: {df.shape[0]:,}행 × {df.shape[1]}열  |  상권 {df['상권_코드'].nunique():,}개")

# 명동 관광특구 제외 (이상치)
myeongdong = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
df = df[~df['상권_코드'].isin(myeongdong)].copy()
print(f"명동 제외 후: {df.shape[0]:,}행  |  상권 {df['상권_코드'].nunique():,}개")

# ══════════════════════════════════════════════════════
# 2. 결측치 처리 (그룹별 전략)
# ══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("2. 결측치 처리")
print("=" * 65)

log_lines = []  # 처리 로그

# ── 그룹 B: 구조적 전체 결측 상권 제거 ──
# 총_직장_인구_수 결측 상권 (2개)
b1 = set(df[df['총_직장_인구_수'].isna()]['상권_코드'].unique())
# 총_상주인구_수 / 총_가구_수 결측 상권 (6개, 동일 집합)
b2 = set(df[df['총_상주인구_수'].isna()]['상권_코드'].unique())

remove_b = b1 | b2
df = df[~df['상권_코드'].isin(remove_b)].copy()
msg = f"[그룹 B] 구조적 결측 상권 제거: {len(remove_b)}개 상권 ({len(remove_b)*9}행)"
print(msg); log_lines.append(msg)

# ── 그룹 C: 소득 미연계 상권 제거 ──
# 월_평균_소득_금액 / 여가_지출_총금액 / 지출_총금액 동시 결측 (23개, 동일 집합)
c1 = set(df[df['월_평균_소득_금액'].isna()]['상권_코드'].unique())
remove_c = c1 - remove_b  # 이미 B에서 제거된 것 제외
df = df[~df['상권_코드'].isin(remove_c)].copy()
msg = f"[그룹 C] 소득 미연계 상권 제거: {len(remove_c)}개 상권 ({len(remove_c)*9}행)"
print(msg); log_lines.append(msg)

# ── 그룹 D: 집객시설_수 결측 처리 ──
# D-1. 구조적 결측 상권: 모든 분기에서 결측인 상권 → 제거
miss_jip = df[df['집객시설_수'].isna()].groupby('상권_코드').size()
structural_jip = set(miss_jip[miss_jip >= 9].index)   # 9분기 모두 결측
partial_jip    = set(miss_jip[miss_jip < 9].index)     # 일부 분기만 결측

remove_d = structural_jip - remove_b - remove_c
df = df[~df['상권_코드'].isin(remove_d)].copy()
msg = f"[그룹 D-1] 집객시설_수 구조적 결측 상권 제거: {len(remove_d)}개 상권"
print(msg); log_lines.append(msg)

# D-2. 부분 결측 → 상권별 forward-fill → backward-fill
df = df.sort_values(['상권_코드', '기준_년분기_코드'])
df['집객시설_수'] = (
    df.groupby('상권_코드')['집객시설_수']
    .transform(lambda x: x.ffill().bfill())
)
n_remain = df['집객시설_수'].isna().sum()
msg = f"[그룹 D-2] 집객시설_수 부분 결측 forward-fill 처리 | 잔여 결측: {n_remain}행"
print(msg); log_lines.append(msg)

# ── 그룹 E: 아파트_평균_시가 → 변수 자체 제외 (로그에만 기록) ──
msg = "[그룹 E] 아파트_평균_시가: 7.2% 결측(아파트 없는 상권) → 변수 제외"
print(msg); log_lines.append(msg)

# ── 최종 결측 잔여 확인 ──
DEMAND_VARS = [
    '집객시설_수', '총_직장_인구_수', '월_평균_소득_금액',
    '지출_총금액', '총_가구_수', '카페_검색지수',
    '총_상주인구_수', '여가_지출_총금액', '지하철_노선_수',
]
print(f"\n처리 후: {df.shape[0]:,}행  |  상권 {df['상권_코드'].nunique():,}개")
print("잔여 결측:")
for col in DEMAND_VARS:
    n = df[col].isna().sum()
    print(f"  {col:30s}: {n}행")

total_removed = len(remove_b) + len(remove_c) + len(remove_d)
msg = f"\n총 제거 상권: {total_removed}개  |  잔류 행수: {df.shape[0]:,}행"
print(msg); log_lines.append(msg)

with open('32_preprocessing_log.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

# ══════════════════════════════════════════════════════
# 3. 피처 엔지니어링 (더미변수 + 표준화)
# ══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("3. 피처 엔지니어링")
print("=" * 65)

# Y변수
df = df[df['당월_매출_금액'] > 0].copy()
y = np.log1p(df['당월_매출_금액'].values)

# ── 분기 더미 (기준: 20233) ──
quarters = sorted(df['기준_년분기_코드'].unique())
base_quarter = quarters[0]  # 20233 기준
for q in quarters[1:]:
    df[f'Q_{q}'] = (df['기준_년분기_코드'] == q).astype(int)
quarter_dummies = [f'Q_{q}' for q in quarters[1:]]
print(f"분기 더미: {len(quarter_dummies)}개  (기준={base_quarter})")

# ── 상권유형 더미 ──
type_col = '상권_구분_코드_명_x'
types = sorted(df[type_col].dropna().unique())
base_type = types[0]
for t in types[1:]:
    safe_name = t.replace(' ', '_').replace('/', '_')
    df[f'TYPE_{safe_name}'] = (df[type_col] == t).astype(int)
type_dummies = [c for c in df.columns if c.startswith('TYPE_')]
print(f"상권유형 더미: {len(type_dummies)}개  (기준={base_type})")
print(f"상권유형 목록: {types}")

# ── 수요 변수 표준화 ──
scaler = StandardScaler()
X_demand_scaled = scaler.fit_transform(df[DEMAND_VARS].values)
X_demand_df = pd.DataFrame(X_demand_scaled, columns=DEMAND_VARS, index=df.index)

# 전체 X 조합 (표준화 수요 + 더미)
X = pd.concat([
    X_demand_df,
    df[quarter_dummies + type_dummies].reset_index(drop=True)
    .set_index(X_demand_df.index)
], axis=1)

# 결측 있는 행 최종 제거
mask = ~X.isna().any(axis=1) & ~pd.isna(y)
X_clean = X[mask].values
y_clean = y[mask]
groups_clean = df[mask]['상권_코드'].values

print(f"\n최종 분석 데이터: {len(y_clean):,}행 × {X_clean.shape[1]}열")
print(f"수요 변수: {len(DEMAND_VARS)}개  |  분기 더미: {len(quarter_dummies)}개  |  유형 더미: {len(type_dummies)}개")

feature_names = DEMAND_VARS + quarter_dummies + type_dummies

# ══════════════════════════════════════════════════════
# 4. Lasso CV
# ══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("4. LassoCV (GroupKFold, groups=상권_코드)")
print("=" * 65)

gkf = GroupKFold(n_splits=5)
cv_splits = list(gkf.split(X_clean, y_clean, groups=groups_clean))

lasso_cv = LassoCV(
    cv=cv_splits,
    max_iter=10000,
    random_state=42,
    n_alphas=100,
)
lasso_cv.fit(X_clean, y_clean)

print(f"최적 alpha: {lasso_cv.alpha_:.6f}")
print(f"CV R² (최적 alpha): {lasso_cv.score(X_clean, y_clean):.4f}")

# 선택된 변수 (계수 != 0)
lasso_coef = pd.Series(lasso_cv.coef_, index=feature_names)
lasso_selected = lasso_coef[lasso_coef != 0].sort_values(key=abs, ascending=False)
lasso_zero = lasso_coef[lasso_coef == 0]

print(f"\n선택된 변수: {len(lasso_selected)}개")
print(lasso_selected.to_string())
print(f"\n제거된 변수: {len(lasso_zero)}개")
if len(lasso_zero) > 0:
    print(lasso_zero.index.tolist())

# ══════════════════════════════════════════════════════
# 5. ElasticNet CV
# ══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("5. ElasticNetCV (l1_ratio 탐색)")
print("=" * 65)

l1_ratios = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 1.0]
enet_cv = ElasticNetCV(
    l1_ratio=l1_ratios,
    cv=cv_splits,
    max_iter=10000,
    random_state=42,
    n_alphas=100,
)
enet_cv.fit(X_clean, y_clean)

print(f"최적 alpha: {enet_cv.alpha_:.6f}")
print(f"최적 l1_ratio: {enet_cv.l1_ratio_:.2f}  (1.0=Lasso, 0.0=Ridge)")
print(f"CV R² (최적): {enet_cv.score(X_clean, y_clean):.4f}")

enet_coef = pd.Series(enet_cv.coef_, index=feature_names)
enet_selected = enet_coef[enet_coef != 0].sort_values(key=abs, ascending=False)
enet_zero = enet_coef[enet_coef == 0]

print(f"\nElasticNet 선택 변수: {len(enet_selected)}개")
print(enet_selected.to_string())

# ══════════════════════════════════════════════════════
# 6. Lasso 정규화 경로 계산
# ══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("6. Lasso 정규화 경로 시각화")
print("=" * 65)

# 수요 변수만으로 경로 계산 (더미 제외 — 시각화 명확성)
X_demand_only = X_clean[:, :len(DEMAND_VARS)]
alphas_path, coefs_path, _ = lasso_path(
    X_demand_only, y_clean, alphas=np.logspace(-4, 1, 100)
)

# ══════════════════════════════════════════════════════
# 7. VIF 분석 (Lasso 선택 변수 기준)
# ══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("7. VIF 분석 (Lasso 선택 수요 변수)")
print("=" * 65)

# 수요 변수 중 Lasso가 선택한 것만
demand_selected_lasso = [v for v in DEMAND_VARS if v in lasso_selected.index]

if len(demand_selected_lasso) >= 2:
    vif_data = df[mask][demand_selected_lasso].dropna()
    vif_rows = []
    for i, col in enumerate(demand_selected_lasso):
        vif_val = variance_inflation_factor(vif_data.values, i)
        vif_rows.append({'변수명': col, 'VIF': round(vif_val, 2)})
    vif_df = pd.DataFrame(vif_rows).sort_values('VIF', ascending=False)
    vif_df['판정'] = vif_df['VIF'].apply(
        lambda v: '제거권고(>10)' if v > 10 else ('주의(5~10)' if v > 5 else '양호(<5)')
    )
    print(vif_df.to_string(index=False))
    vif_df.to_csv('32_vif_final.csv', encoding='utf-8-sig', index=False)
    print("\n→ 32_vif_final.csv 저장")

    max_vif = vif_df['VIF'].max()
    if max_vif < 5:
        print("\n▶ 권고: OLS 사용 가능 (VIF 모두 양호)")
    elif max_vif < 10:
        print("\n▶ 권고: Ridge 권장 (VIF 5~10 변수 존재)")
    else:
        print("\n▶ 권고: Ridge 필수 (VIF > 10 변수 존재)")
else:
    print("선택된 수요 변수가 2개 미만 — VIF 계산 불가")

# ══════════════════════════════════════════════════════
# 8. 최종 변수 목록 저장
# ══════════════════════════════════════════════════════
selected_df = pd.DataFrame({
    '변수명': lasso_selected.index,
    'Lasso_계수': lasso_selected.values,
    'ElasticNet_계수': [enet_coef.get(v, 0) for v in lasso_selected.index],
    '수요변수여부': ['수요' if v in DEMAND_VARS else '더미' for v in lasso_selected.index],
})
selected_df.to_csv('32_selected_vars.csv', encoding='utf-8-sig', index=False)
print("\n→ 32_selected_vars.csv 저장")

# ══════════════════════════════════════════════════════
# 9. 시각화
# ══════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(20, 7))

# ── (A) Lasso 정규화 경로 (수요 변수) ──
ax = axes[0]
colors = plt.cm.tab10(np.linspace(0, 1, len(DEMAND_VARS)))
for i, (name, color) in enumerate(zip(DEMAND_VARS, colors)):
    ax.semilogx(alphas_path, coefs_path[i], label=name, color=color, linewidth=1.8)
ax.axvline(lasso_cv.alpha_, color='black', linestyle='--', linewidth=1.5,
           label=f'최적 alpha={lasso_cv.alpha_:.5f}')
ax.set_xlabel('Alpha (정규화 강도)')
ax.set_ylabel('계수')
ax.set_title('Lasso 정규화 경로\n(수요 변수, alpha 커질수록 계수→0)', fontsize=11)
ax.legend(fontsize=7, loc='upper right')
ax.grid(True, alpha=0.3)

# ── (B) Lasso vs ElasticNet 수요 변수 계수 비교 ──
ax = axes[1]
demand_lasso_coef  = [lasso_coef.get(v, 0) for v in DEMAND_VARS]
demand_enet_coef   = [enet_coef.get(v, 0) for v in DEMAND_VARS]
x_pos = np.arange(len(DEMAND_VARS))
width = 0.35
bars1 = ax.bar(x_pos - width/2, demand_lasso_coef, width, label='Lasso',      color='steelblue',  alpha=0.8)
bars2 = ax.bar(x_pos + width/2, demand_enet_coef,  width, label='ElasticNet', color='darkorange', alpha=0.8)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xticks(x_pos)
ax.set_xticklabels(DEMAND_VARS, rotation=45, ha='right', fontsize=8)
ax.set_ylabel('표준화 계수')
ax.set_title('Lasso vs ElasticNet 수요 변수 계수 비교\n(0 = 해당 모델이 제거)', fontsize=11)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# ── (C) VIF 바 차트 ──
ax = axes[2]
if len(demand_selected_lasso) >= 2:
    vif_colors = ['#e74c3c' if v > 10 else ('#f39c12' if v > 5 else '#2ecc71')
                  for v in vif_df['VIF']]
    bars = ax.barh(vif_df['변수명'], vif_df['VIF'], color=vif_colors)
    ax.axvline(5,  color='orange', linestyle='--', alpha=0.7, label='주의 (VIF=5)')
    ax.axvline(10, color='red',    linestyle='--', alpha=0.7, label='제거권고 (VIF=10)')
    for bar, v in zip(bars, vif_df['VIF']):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                f'{v:.1f}', va='center', fontsize=9)
    ax.set_xlabel('VIF')
    ax.set_title('Lasso 선택 수요 변수 VIF\n(초록=양호, 주황=주의, 빨강=제거권고)', fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis='x')
else:
    ax.text(0.5, 0.5, 'VIF 계산 불가\n(선택 변수 < 2개)',
            ha='center', va='center', transform=ax.transAxes)

plt.suptitle('Track A 수요 변수 선별 — Lasso / ElasticNet', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('32_coef_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n→ 32_coef_comparison.png 저장")

# ══════════════════════════════════════════════════════
# 10. 최종 요약
# ══════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("최종 요약")
print("=" * 65)
print(f"\n[분석 데이터]  {len(y_clean):,}행  |  상권 {len(np.unique(groups_clean)):,}개")
print(f"\n[Lasso]  alpha={lasso_cv.alpha_:.6f}  |  R²={lasso_cv.score(X_clean, y_clean):.4f}")
print(f"  → 수요 변수 선택: {demand_selected_lasso}")
print(f"\n[ElasticNet]  alpha={enet_cv.alpha_:.6f}  l1_ratio={enet_cv.l1_ratio_:.2f}")
print(f"  → 수요 변수 선택: {[v for v in DEMAND_VARS if enet_coef.get(v, 0) != 0]}")
if len(demand_selected_lasso) >= 2:
    print(f"\n[VIF]  최대 VIF = {vif_df['VIF'].max():.1f}")
    print(f"  → {'Ridge 권장' if vif_df['VIF'].max() >= 5 else 'OLS 사용 가능'}")
print("\n[산출물]")
print("  32_preprocessing_log.txt")
print("  32_selected_vars.csv")
print("  32_vif_final.csv")
print("  32_coef_comparison.png")
