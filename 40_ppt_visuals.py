# 40_ppt_visuals.py
# PPT용 추가 시각화 생성 (방법론 신뢰성 검증)
#
# 생성 항목:
#   1. 모델 성능 비교 바차트   (XGBoost R²=0.90 vs OLS R²=0.44)
#   2. 잔차 진단 차트 4종     (QQ plot / 히스토그램 / 잔차 vs 적합값 / 잔차 vs 순서)
#   3. 최종 6개 변수 상관행렬  (y_log 포함)
#   4. 단변량 R² Top10       (왜 카페음료_점포수가 1위인지 시각화)
#   5. 명동 포함/제외 계수 비교 (OLS 재실행)
#
# 입력: 33_analysis_ready.csv, 34_oof_residuals.csv,
#        34_model_coefficients.csv, 27b_eda_correlation_table_nooutlier.csv
# 출력: 40_model_comparison.png, 40_residual_diagnostics.png,
#        40_corr_matrix_6vars.png, 40_univariate_r2_top10.png,
#        40_myeongdong_coef_comparison.png, 40_ppt_visuals_log.txt

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy import stats
import statsmodels.api as sm
import os

BASE    = os.path.dirname(os.path.abspath(__file__))
logs    = []

# 한글 폰트
for font_name in ['Malgun Gothic', 'NanumGothic', 'AppleGothic', 'DejaVu Sans']:
    try:
        fp = fm.findfont(fm.FontProperties(family=font_name))
        if font_name.lower() in fp.lower() or 'malgun' in fp.lower():
            plt.rcParams['font.family'] = font_name
            break
    except Exception:
        continue
plt.rcParams['axes.unicode_minus'] = False

# ─────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────
df33 = pd.read_csv(os.path.join(BASE, '33_analysis_ready.csv'), encoding='utf-8-sig')
df34 = pd.read_csv(os.path.join(BASE, '34_oof_residuals.csv'),  encoding='utf-8-sig')
dfc  = pd.read_csv(os.path.join(BASE, '34_model_coefficients.csv'), encoding='utf-8-sig')
dfe  = pd.read_csv(os.path.join(BASE, '27b_eda_correlation_table_nooutlier.csv'), encoding='utf-8-sig')

DEMAND_VARS = ['집객시설_수', '총_직장_인구_수', '월_평균_소득_금액',
               '총_가구_수', '카페_검색지수', '지하철_노선_수']
SCALED_VARS = [v + '_scaled' for v in DEMAND_VARS]
DUMMY_COLS  = [c for c in df33.columns if c.startswith('Q_') or c.startswith('TYPE_')]
X_COLS      = SCALED_VARS + DUMMY_COLS

logs.append(f"데이터 로드 완료: df33={df33.shape}, df34={df34.shape}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 모델 성능 비교 바차트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
fig, ax = plt.subplots(figsize=(8, 5))

models = ['XGBoost\n(공급+수요 포함)', 'Track A OLS\n(수요 변수만)']
r2s    = [0.9047, 0.4413]
colors = ['#e74c3c', '#2980b9']
bars   = ax.bar(models, r2s, color=colors, width=0.4, edgecolor='white', linewidth=1.5)

for bar, val in zip(bars, r2s):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
            f'R² = {val:.4f}', ha='center', va='bottom', fontsize=13, fontweight='bold')

ax.set_ylim(0, 1.1)
ax.set_ylabel('OOF R² (5-Fold CV)', fontsize=12)
ax.set_title('모델 성능 비교\n(Track A의 낮은 R²는 의도된 설계)', fontsize=13, fontweight='bold')
ax.axhline(y=0.4413, color='#2980b9', linestyle='--', alpha=0.4, linewidth=1)
ax.grid(axis='y', alpha=0.3)

# 주석 추가
ax.annotate('공급변수 포함 → 잔차에\n공급 신호 흡수 → 블루오션\n신호 소멸',
            xy=(0, 0.9047), xytext=(0.3, 0.75),
            fontsize=9, color='#c0392b',
            arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
ax.annotate('수요 변수만 → 잔차가\n"공급 공백 신호"로 남음\n→ 블루오션 탐색 가능',
            xy=(1, 0.4413), xytext=(0.7, 0.20),
            fontsize=9, color='#1a5276',
            arrowprops=dict(arrowstyle='->', color='#1a5276', lw=1.2))

plt.tight_layout()
out1 = os.path.join(BASE, '40_model_comparison.png')
plt.savefig(out1, dpi=150, bbox_inches='tight')
plt.close()
logs.append(f"[저장] {out1}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 잔차 진단 차트 4종
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
resid   = df34['oof_residual'].dropna()
fitted  = df34['oof_pred'].dropna()

fig, axes = plt.subplots(2, 2, figsize=(13, 10))

# (1) 잔차 히스토그램
ax = axes[0, 0]
ax.hist(resid, bins=60, color='#3498db', alpha=0.7, edgecolor='white')
mu, sigma = resid.mean(), resid.std()
x_range = np.linspace(resid.min(), resid.max(), 200)
ax.plot(x_range, len(resid) * (resid.max()-resid.min())/60 *
        stats.norm.pdf(x_range, mu, sigma),
        color='#e74c3c', linewidth=2, label=f'정규분포 N({mu:.2f}, {sigma:.2f}²)')
ax.axvline(0, color='black', linestyle='--', alpha=0.5)
ax.set_title('잔차 분포 (히스토그램)', fontsize=12, fontweight='bold')
ax.set_xlabel('OOF 잔차')
ax.set_ylabel('빈도')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

# (2) QQ plot
ax = axes[0, 1]
(osm, osr), (slope, intercept, r) = stats.probplot(resid, dist='norm')
ax.scatter(osm, osr, alpha=0.3, s=8, color='#3498db')
ax.plot(osm, slope * np.array(osm) + intercept, color='#e74c3c', linewidth=2)
ax.set_title(f'Q-Q Plot (정규성 검증)\nr = {r:.4f}', fontsize=12, fontweight='bold')
ax.set_xlabel('이론적 분위수')
ax.set_ylabel('표본 분위수')
ax.grid(alpha=0.3)

# (3) 잔차 vs 적합값
ax = axes[1, 0]
ax.scatter(fitted, resid, alpha=0.15, s=8, color='#2ecc71')
ax.axhline(0, color='#e74c3c', linewidth=1.5, linestyle='--')
# lowess 추세선
from statsmodels.nonparametric.smoothers_lowess import lowess
sorted_idx = np.argsort(fitted.values)
lw = lowess(resid.values[sorted_idx], fitted.values[sorted_idx], frac=0.3)
ax.plot(lw[:, 0], lw[:, 1], color='#e74c3c', linewidth=2, label='LOWESS 추세')
ax.set_title('잔차 vs 적합값 (등분산성 확인)', fontsize=12, fontweight='bold')
ax.set_xlabel('OOF 예측값')
ax.set_ylabel('OOF 잔차')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

# (4) 잔차 스케일-위치 (Scale-Location)
ax = axes[1, 1]
sqrt_abs_resid = np.sqrt(np.abs(resid))
ax.scatter(fitted, sqrt_abs_resid, alpha=0.15, s=8, color='#9b59b6')
ax.axhline(sqrt_abs_resid.mean(), color='#e74c3c', linewidth=1.5, linestyle='--', label='평균')
ax.set_title('Scale-Location Plot (이분산성 확인)', fontsize=12, fontweight='bold')
ax.set_xlabel('OOF 예측값')
ax.set_ylabel('√|잔차|')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

plt.suptitle('OLS 잔차 진단 차트 — Track A 모델 가정 검증', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
out2 = os.path.join(BASE, '40_residual_diagnostics.png')
plt.savefig(out2, dpi=150, bbox_inches='tight')
plt.close()

# Shapiro-Wilk (subsample)
sw_stat, sw_p = stats.shapiro(resid.sample(min(5000, len(resid)), random_state=42))
logs.append(f"[저장] {out2}")
logs.append(f"  잔차 왜도={resid.skew():.3f}, 첨도={resid.kurtosis():.3f}")
logs.append(f"  Shapiro-Wilk (n=5000): stat={sw_stat:.4f}, p={sw_p:.4f}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 최종 6개 변수 상관행렬 (y_log 포함)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vars_for_corr = DEMAND_VARS + ['y_log']
labels_kr = {
    '집객시설_수':       '집객시설',
    '총_직장_인구_수':   '직장인구',
    '월_평균_소득_금액': '소득',
    '총_가구_수':        '가구수',
    '카페_검색지수':     '카페검색',
    '지하철_노선_수':    '지하철노선',
    'y_log':            '찻집매출\n(log)'
}
df_corr = df33[vars_for_corr].rename(columns=labels_kr).corr()

fig, ax = plt.subplots(figsize=(8, 7))
import matplotlib.colors as mcolors
cmap = plt.cm.RdBu_r
im = ax.imshow(df_corr.values, cmap=cmap, vmin=-1, vmax=1)
plt.colorbar(im, ax=ax, shrink=0.8)

labels = list(df_corr.columns)
ax.set_xticks(range(len(labels)))
ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=10)
ax.set_yticklabels(labels, fontsize=10)

for i in range(len(labels)):
    for j in range(len(labels)):
        val = df_corr.values[i, j]
        color = 'white' if abs(val) > 0.5 else 'black'
        ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                fontsize=10, fontweight='bold', color=color)

ax.set_title('최종 수요 변수 6개 + Y(찻집매출) 상관행렬\n(VIF < 5 — 다중공선성 없음 확인)', fontsize=12, fontweight='bold')
plt.tight_layout()
out3 = os.path.join(BASE, '40_corr_matrix_6vars.png')
plt.savefig(out3, dpi=150, bbox_inches='tight')
plt.close()
logs.append(f"[저장] {out3}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 단변량 R² Top10 막대그래프
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
top10 = dfe.nlargest(10, 'R²').sort_values('R²', ascending=True)

# 변수명 줄이기
def shorten(name):
    mapping = {
        '카페음료_점포수':       '카페음료\n점포수',
        '공급갭_지수':           '공급갭\n지수',
        '총_직장_인구_수':       '직장인구',
        '집객시설_수':           '집객시설',
        '월_평균_소득_금액':     '소득',
        '총_가구_수':            '가구수',
        '카페_검색지수':         '카페검색',
        '지하철_노선_수':        '지하철\n노선수',
        '여성연령대50_직장_인구_수': '여성50대\n직장인구',
    }
    for k, v in mapping.items():
        if k in name:
            return v
    return name[:8]

short_names = [shorten(n) for n in top10['변수명']]
r2_vals = top10['R²'].values

# 최종 6개 변수 강조 색
highlight = []
for n in top10['변수명']:
    if any(v in n for v in DEMAND_VARS):
        highlight.append('#2980b9')   # 파랑 = 선택됨
    else:
        highlight.append('#bdc3c7')   # 회색 = 제외됨

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(short_names, r2_vals, color=highlight, edgecolor='white')

for bar, val in zip(bars, r2_vals):
    ax.text(val + 0.003, bar.get_y() + bar.get_height()/2,
            f'{val:.3f}', va='center', fontsize=10)

ax.set_xlabel('단변량 R² (이상치 제외)', fontsize=11)
ax.set_title('단변량 R² Top10\n(파랑=최종 선택 변수 / 회색=제외된 공급·중복 변수)', fontsize=12, fontweight='bold')
ax.set_xlim(0, max(r2_vals) * 1.15)
ax.grid(axis='x', alpha=0.3)

# 범례
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#2980b9', label='최종 선택 (수요 변수)'),
                   Patch(facecolor='#bdc3c7', label='제외 (공급·다중공선성)')]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

plt.tight_layout()
out4 = os.path.join(BASE, '40_univariate_r2_top10.png')
plt.savefig(out4, dpi=150, bbox_inches='tight')
plt.close()
logs.append(f"[저장] {out4}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 명동 포함/제외 OLS 계수 비교
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 명동 관광특구 상권 코드명 확인
myeongdong_mask = df33['상권_코드_명'].str.contains('명동', na=False)
logs.append(f"명동 포함 상권: {df33[myeongdong_mask]['상권_코드_명'].unique().tolist()}")

X_all = sm.add_constant(df33[X_COLS].fillna(0))
y_all = df33['y_log']

# 포함 모델
model_with    = sm.OLS(y_all, X_all).fit()
coef_with     = model_with.params[SCALED_VARS]

# 제외 모델
df_no = df33[~myeongdong_mask]
X_no  = sm.add_constant(df_no[X_COLS].fillna(0))
y_no  = df_no['y_log']
model_without = sm.OLS(y_no, X_no).fit()
coef_without  = model_without.params[SCALED_VARS]

var_labels = ['집객시설', '직장인구', '소득', '가구수', '카페검색', '지하철노선']
x = np.arange(len(SCALED_VARS))
w = 0.35

fig, ax = plt.subplots(figsize=(11, 6))
b1 = ax.bar(x - w/2, coef_with.values,    width=w, label='명동 포함', color='#e74c3c', alpha=0.8)
b2 = ax.bar(x + w/2, coef_without.values, width=w, label='명동 제외', color='#2980b9', alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels(var_labels, fontsize=11)
ax.set_ylabel('OLS 계수 (표준화 변수 기준)', fontsize=11)
ax.set_title('명동 관광특구 포함/제외 시 수요 변수 계수 비교\n(계수가 유사하면 명동 제외가 분석에 영향 없음)', fontsize=12, fontweight='bold')
ax.axhline(0, color='black', linewidth=0.8, alpha=0.5)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)

# 수치 표시
for bar in b1:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + (0.003 if h >= 0 else -0.012),
            f'{h:.3f}', ha='center', va='bottom' if h >= 0 else 'top', fontsize=8)
for bar in b2:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + (0.003 if h >= 0 else -0.012),
            f'{h:.3f}', ha='center', va='bottom' if h >= 0 else 'top', fontsize=8)

plt.tight_layout()
out5 = os.path.join(BASE, '40_myeongdong_coef_comparison.png')
plt.savefig(out5, dpi=150, bbox_inches='tight')
plt.close()

logs.append(f"[저장] {out5}")
logs.append(f"  명동 포함 R²={model_with.rsquared:.4f} / 제외 R²={model_without.rsquared:.4f}")
logs.append(f"  계수 최대 변화: {abs(coef_with - coef_without).max():.4f} ({abs(coef_with - coef_without).idxmax()})")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 로그 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logs.append("\n=== 생성 완료 ===")
logs.append("40_model_comparison.png        : 모델 성능 비교 (XGBoost vs OLS)")
logs.append("40_residual_diagnostics.png    : 잔차 진단 4종 (QQ/히스토/잔차vs적합/Scale-Location)")
logs.append("40_corr_matrix_6vars.png       : 최종 6개 변수 상관행렬")
logs.append("40_univariate_r2_top10.png     : 단변량 R² Top10 (선택/제외 색상 구분)")
logs.append("40_myeongdong_coef_comparison.png : 명동 포함/제외 계수 비교")

log_text = "\n".join(logs)
with open(os.path.join(BASE, '40_ppt_visuals_log.txt'), 'w', encoding='utf-8') as f:
    f.write(log_text)
print(log_text)
