# 39_sensitivity.py
# 복합 공급지수 가중치 민감도 분석
#
# 질문: 가중치를 0.5/0.5가 아닌 다른 값으로 바꾸면 추천 결과가 바뀌나?
# 방법: w1(찻집희소성) vs w2(점포당매출) 비율을 9단계로 변화
#       각 가중치 조합에서 Q1/Q2 Top5 추출 → 일치율 계산
#
# 입력: 34_district_residuals.csv, 34_oof_residuals.csv
# 출력:
#   39_sensitivity_results.csv - Q1+Q2 Top5 × 가중치 조합 통합 매트릭스
#   39_sensitivity_overlap.png - 기준(0.5/0.5) 대비 상위권 일치율 시각화
#   39_sensitivity_log.txt    - 실행 로그

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

BASE     = os.path.dirname(os.path.abspath(__file__))
IN_DIST  = os.path.join(BASE, '34_district_residuals.csv')
IN_OOF   = os.path.join(BASE, '34_oof_residuals.csv')
OUT_RESULTS = os.path.join(BASE, '39_sensitivity_results.csv')
OUT_PLOT    = os.path.join(BASE, '39_sensitivity_overlap.png')
OUT_LOG     = os.path.join(BASE, '39_sensitivity_log.txt')

logs = []

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
# 1. 데이터 로드 (35번과 동일)
# ─────────────────────────────────────────────
df = pd.read_csv(IN_DIST, encoding='utf-8-sig')
df_oof = pd.read_csv(IN_OOF, encoding='utf-8-sig')
latest_q = df_oof['기준_년분기_코드'].max()
cafe_store = (
    df_oof[df_oof['기준_년분기_코드'] == latest_q]
    [['상권_코드', '카페음료_점포수']]
)
df = df.merge(cafe_store, on='상권_코드', how='left')

df['cafe_revenue_per_store'] = df['매출_latest'] / (df['카페음료_점포수'] + 1)
df['supply_pct_v1']   = df['supply_shortage'].rank(pct=True, ascending=True)
df['supply_pct_cafe'] = df['cafe_revenue_per_store'].rank(pct=True, ascending=True)
df['residual_pct']    = df['residual_latest'].rank(pct=True, ascending=True)

# 사분면 (35번과 동일 기준)
median_supply = df['supply_shortage'].median()
df['is_supply_scarce'] = df['supply_shortage'] >= median_supply
df['is_q1'] = (df['residual_latest'] >= 0) & df['is_supply_scarce']
df['is_q2'] = (df['residual_latest'] <  0) & df['is_supply_scarce']

logs.append(f"데이터 로드: {len(df)}개 상권")
logs.append(f"Q1 후보: {df['is_q1'].sum()}개 / Q2 후보: {df['is_q2'].sum()}개\n")

# ─────────────────────────────────────────────
# 2. 가중치 조합 9단계 설정
# ─────────────────────────────────────────────
weights = [
    (0.1, 0.9),
    (0.2, 0.8),
    (0.3, 0.7),
    (0.4, 0.6),
    (0.5, 0.5),   # ← 기준 (현재 모델)
    (0.6, 0.4),
    (0.7, 0.3),
    (0.8, 0.2),
    (0.9, 0.1),
]

TOP_N = 5

# 기준(0.5/0.5) Top5 미리 추출
def get_top5(df_subset, score_col, n=TOP_N):
    return list(df_subset.sort_values(score_col, ascending=False).head(n)['상권_코드_명'])

df['supply_base'] = 0.5 * df['supply_pct_v1'] + 0.5 * df['supply_pct_cafe']
df['q1_base'] = df['residual_pct'] + df['supply_base']
df['q2_base'] = (1 - df['residual_pct']) + df['supply_base']

base_q1_top5 = get_top5(df[df['is_q1']], 'q1_base')
base_q2_top5 = get_top5(df[df['is_q2']], 'q2_base')

logs.append(f"[기준(0.5/0.5) Top5]")
logs.append(f"  Q1: {base_q1_top5}")
logs.append(f"  Q2: {base_q2_top5}\n")

# ─────────────────────────────────────────────
# 3. 민감도 분석 실행
# ─────────────────────────────────────────────
results_q1 = []  # {'label': ..., 'top5': [...], 'overlap': ...}
results_q2 = []

logs.append(f"{'가중치(찻집희소성/점포당매출)':<30} {'Q1 Top5':<60} {'일치율':>6}   {'Q2 Top5':<60} {'일치율':>6}")
logs.append("-" * 170)

for w1, w2 in weights:
    label = f"w={w1:.1f}/{w2:.1f}"

    df['supply_w'] = w1 * df['supply_pct_v1'] + w2 * df['supply_pct_cafe']
    df['q1_score'] = df['residual_pct']        + df['supply_w']
    df['q2_score'] = (1 - df['residual_pct'])  + df['supply_w']

    q1_top5 = get_top5(df[df['is_q1']], 'q1_score')
    q2_top5 = get_top5(df[df['is_q2']], 'q2_score')

    q1_overlap = len(set(q1_top5) & set(base_q1_top5))
    q2_overlap = len(set(q2_top5) & set(base_q2_top5))

    results_q1.append({'가중치': label, **{f'{i+1}위': q1_top5[i] if i < len(q1_top5) else '' for i in range(TOP_N)}, '기준대비일치(Q1)': q1_overlap})
    results_q2.append({'가중치': label, **{f'{i+1}위': q2_top5[i] if i < len(q2_top5) else '' for i in range(TOP_N)}, '기준대비일치(Q2)': q2_overlap})

    marker = " ← 기준" if w1 == 0.5 else ""
    logs.append(f"{label:<30} {str(q1_top5):<60} {q1_overlap}/5       {str(q2_top5):<60} {q2_overlap}/5{marker}")

# ─────────────────────────────────────────────
# 4. 저장 (Q1+Q2 통합 CSV)
# ─────────────────────────────────────────────
df_q1_res = pd.DataFrame(results_q1).rename(columns={f'{i+1}위': f'Q1_{i+1}위' for i in range(TOP_N)})
df_q2_res = pd.DataFrame(results_q2).rename(columns={f'{i+1}위': f'Q2_{i+1}위' for i in range(TOP_N)})
df_results = df_q1_res.merge(df_q2_res.drop(columns=['가중치']), left_index=True, right_index=True)
df_results.to_csv(OUT_RESULTS, index=False, encoding='utf-8-sig')

# ─────────────────────────────────────────────
# 5. 시각화: 기준 대비 일치율
# ─────────────────────────────────────────────
labels      = [f"{w1:.1f}/{w2:.1f}" for w1, w2 in weights]
q1_overlaps = [r['기준대비일치(Q1)'] for r in results_q1]
q2_overlaps = [r['기준대비일치(Q2)'] for r in results_q2]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, overlaps, title, color in zip(
    axes,
    [q1_overlaps, q2_overlaps],
    ['Q1 (검증시장공백) Top5 일치율', 'Q2 (잠재수요미실현) Top5 일치율'],
    ['#2980b9', '#e74c3c']
):
    bars = ax.bar(labels, overlaps, color=color, alpha=0.7, edgecolor='white')
    ax.set_ylim(0, 5.5)
    ax.set_yticks(range(6))
    ax.set_yticklabels([f'{i}/5' for i in range(6)])
    ax.set_xlabel('가중치 (찻집희소성 / 점포당매출)', fontsize=11)
    ax.set_ylabel('기준(0.5/0.5) 대비 일치 개수', fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.axhline(y=5, color='green', linewidth=1.5, linestyle='--', alpha=0.5, label='완전 일치(5/5)')
    ax.axhline(y=3, color='orange', linewidth=1.5, linestyle='--', alpha=0.5, label='과반 일치(3/5)')

    # 기준 막대 강조
    base_idx = labels.index('0.5/0.5')
    bars[base_idx].set_edgecolor('black')
    bars[base_idx].set_linewidth(2.5)

    for bar, val in zip(bars, overlaps):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{val}/5', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    ax.tick_params(axis='x', rotation=30)

plt.suptitle(
    '공급지수 가중치 민감도 분석 — 기준(0.5/0.5) 대비 Top5 일치율\n'
    '→ 일치율이 높을수록 결과가 가중치 선택에 robust함',
    fontsize=12, fontweight='bold', y=1.02
)
plt.tight_layout()
plt.savefig(OUT_PLOT, dpi=150, bbox_inches='tight')
plt.close()

# ─────────────────────────────────────────────
# 6. 요약
# ─────────────────────────────────────────────
logs.append("\n" + "="*60)
logs.append("=== 민감도 분석 요약 ===")
logs.append("="*60)
logs.append(f"Q1: 9개 가중치 조합 중 기준 대비 평균 일치율 = {sum(q1_overlaps)/len(q1_overlaps):.1f}/5")
logs.append(f"Q2: 9개 가중치 조합 중 기준 대비 평균 일치율 = {sum(q2_overlaps)/len(q2_overlaps):.1f}/5")
logs.append(f"Q1 최솟값: {min(q1_overlaps)}/5  Q1 최댓값: {max(q1_overlaps)}/5")
logs.append(f"Q2 최솟값: {min(q2_overlaps)}/5  Q2 최댓값: {max(q2_overlaps)}/5")

avg_q1 = sum(q1_overlaps) / len(q1_overlaps)
avg_q2 = sum(q2_overlaps) / len(q2_overlaps)
verdict_q1 = "[robust] 평균 4/5 이상" if avg_q1 >= 4 else ("[보통] 평균 3/5" if avg_q1 >= 3 else "[민감] 가중치에 민감")
verdict_q2 = "[robust] 평균 4/5 이상" if avg_q2 >= 4 else ("[보통] 평균 3/5" if avg_q2 >= 3 else "[민감] 가중치에 민감")
logs.append(f"\nQ1 판정: {verdict_q1}")
logs.append(f"Q2 판정: {verdict_q2}")

log_text = "\n".join(logs)
with open(OUT_LOG, 'w', encoding='utf-8') as f:
    f.write(log_text)

print(log_text)
print(f"\n[저장] {OUT_RESULTS}")
print(f"[저장] {OUT_PLOT}")
