# 37_district_profile.py
# 상위 후보 상권 특성 프로파일링
#
# 입력:
#   36_q1_ranked.csv     - Q1 Top5
#   36_q2_ranked.csv     - Q2 Top5
#   33_analysis_ready.csv - 수요 변수 원본값 + 분기별 데이터
#   34_oof_residuals.csv  - 9분기 OOF 잔차
#
# 출력:
#   37_demand_profile.csv  - 수요 변수 분위수 테이블 (Q1/Q2 Top5)
#   37_residual_trend.png  - 9분기 잔차 추세 (2×5 subplot)
#   37_radar_chart.png     - 수요 변수 레이더 차트
#   37_profile_log.txt     - 텍스트 요약

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

BASE      = os.path.dirname(os.path.abspath(__file__))
IN_Q1     = os.path.join(BASE, '36_q1_ranked.csv')
IN_Q2     = os.path.join(BASE, '36_q2_ranked.csv')
IN_READY  = os.path.join(BASE, '33_analysis_ready.csv')
IN_OOF    = os.path.join(BASE, '34_oof_residuals.csv')
OUT_PROF  = os.path.join(BASE, '37_demand_profile.csv')
OUT_TREND = os.path.join(BASE, '37_residual_trend.png')
OUT_RADAR = os.path.join(BASE, '37_radar_chart.png')
OUT_LOG   = os.path.join(BASE, '37_profile_log.txt')

logs = []

# ─────────────────────────────────────────────
# 한글 폰트
# ─────────────────────────────────────────────
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
# 1. 대상 상권 선정 (Q1 Top5 + Q2 Top5)
# ─────────────────────────────────────────────
df_q1r = pd.read_csv(IN_Q1, encoding='utf-8-sig')
df_q2r = pd.read_csv(IN_Q2, encoding='utf-8-sig')

q1_top5 = df_q1r.head(5)[['상권_코드_명', '상권유형', 'residual_latest', 'supply_pct']].copy()
q1_top5['그룹'] = 'Q1_검증시장공백'
q1_top5['순위'] = range(1, 6)

q2_top5 = df_q2r.head(5)[['상권_코드_명', '상권유형', 'residual_latest', 'supply_pct']].copy()
q2_top5['그룹'] = 'Q2_잠재수요미실현'
q2_top5['순위'] = range(1, 6)

target_names = list(q1_top5['상권_코드_명']) + list(q2_top5['상권_코드_명'])
# 중복 제거
target_names_unique = list(dict.fromkeys(target_names))

logs.append(f"프로파일 대상: Q1 Top5 + Q2 Top5 = {len(target_names_unique)}개 상권")
logs.append(f"  Q1: {list(q1_top5['상권_코드_명'])}")
logs.append(f"  Q2: {list(q2_top5['상권_코드_명'])}")

# ─────────────────────────────────────────────
# 2. 수요 변수 프로파일 (최신 분기 기준)
# ─────────────────────────────────────────────
DEMAND_VARS = ['집객시설_수', '총_직장_인구_수', '월_평균_소득_금액',
               '총_가구_수', '카페_검색지수', '지하철_노선_수']

df_ready = pd.read_csv(IN_READY, encoding='utf-8-sig')
latest_q = df_ready['기준_년분기_코드'].max()
df_latest = df_ready[df_ready['기준_년분기_코드'] == latest_q].copy()

logs.append(f"\n최신 분기: {latest_q}  (전체 상권: {len(df_latest)}개)")

# 전체 상권 기준 분위수 계산
for v in DEMAND_VARS:
    df_latest[f'{v}_pct'] = df_latest[v].rank(pct=True)

# 대상 상권 필터
df_target = df_latest[df_latest['상권_코드_명'].isin(target_names_unique)].copy()

# 분위수 테이블 생성
pct_cols = [f'{v}_pct' for v in DEMAND_VARS]
label_map = {f'{v}_pct': v for v in DEMAND_VARS}

df_prof = df_target[['상권_코드_명', '상권_구분_코드_명_x'] + DEMAND_VARS + pct_cols].copy()
df_prof = df_prof.rename(columns={'상권_구분_코드_명_x': '상권유형'})

# 그룹 + 랭킹 지표 병합
rank_info = pd.concat([
    q1_top5[['상권_코드_명', '그룹', '순위', 'residual_latest', 'supply_pct']],
    q2_top5[['상권_코드_명', '그룹', '순위', 'residual_latest', 'supply_pct']]
]).drop_duplicates(subset='상권_코드_명', keep='first')
df_prof = df_prof.merge(rank_info, on='상권_코드_명', how='left')
df_prof.to_csv(OUT_PROF, index=False, encoding='utf-8-sig')
logs.append(f"\n[저장] 수요 변수 프로파일: {OUT_PROF}  ({len(df_prof)}개 상권)")

# ─────────────────────────────────────────────
# 3. 9분기 잔차 추세 차트 (2행×5열)
# ─────────────────────────────────────────────
df_oof = pd.read_csv(IN_OOF, encoding='utf-8-sig')
quarters = sorted(df_oof['기준_년분기_코드'].unique())
q_labels = [str(q) for q in quarters]

fig_trend, axes = plt.subplots(2, 5, figsize=(22, 8), sharey=False)

q1_color = '#2980b9'
q2_color = '#e74c3c'

for col_i, (_, row) in enumerate(q1_top5.iterrows()):
    name = row['상권_코드_명']
    sub = df_oof[df_oof['상권_코드_명'] == name].sort_values('기준_년분기_코드')
    ax = axes[0, col_i]
    ax.plot(q_labels[:len(sub)], sub['oof_residual'].values,
            color=q1_color, marker='o', linewidth=2, markersize=5)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.fill_between(q_labels[:len(sub)], sub['oof_residual'].values, 0,
                    where=(sub['oof_residual'].values >= 0),
                    alpha=0.15, color=q1_color)
    ax.set_title(f"Q1-{int(row['순위'])}위\n{name[:10]}", fontsize=9, color=q1_color, fontweight='bold')
    ax.tick_params(axis='x', labelsize=7, rotation=45)
    ax.grid(True, alpha=0.3)

for col_i, (_, row) in enumerate(q2_top5.iterrows()):
    name = row['상권_코드_명']
    sub = df_oof[df_oof['상권_코드_명'] == name].sort_values('기준_년분기_코드')
    ax = axes[1, col_i]
    ax.plot(q_labels[:len(sub)], sub['oof_residual'].values,
            color=q2_color, marker='s', linewidth=2, markersize=5)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.fill_between(q_labels[:len(sub)], sub['oof_residual'].values, 0,
                    where=(sub['oof_residual'].values <= 0),
                    alpha=0.15, color=q2_color)
    ax.set_title(f"Q2-{int(row['순위'])}위\n{name[:10]}", fontsize=9, color=q2_color, fontweight='bold')
    ax.tick_params(axis='x', labelsize=7, rotation=45)
    ax.grid(True, alpha=0.3)

fig_trend.suptitle('Q1/Q2 Top5 상권 — 9분기 OOF 잔차 추세\n(파랑=검증시장공백, 빨강=잠재수요미실현)',
                   fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(OUT_TREND, dpi=150, bbox_inches='tight')
plt.close()
logs.append(f"[저장] 9분기 잔차 추세: {OUT_TREND}")

# ─────────────────────────────────────────────
# 4. 레이더 차트 (Q1 Top5 vs Q2 Top5)
# ─────────────────────────────────────────────
VAR_LABELS = ['집객시설', '직장인구', '소득', '가구수', '검색지수', '지하철노선']
N = len(DEMAND_VARS)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # 폐곡선

fig_radar, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7),
                                      subplot_kw=dict(polar=True))

blues  = ['#1a5276', '#2e86c1', '#5dade2', '#85c1e9', '#aed6f1']
reds   = ['#922b21', '#e74c3c', '#f1948a', '#f5b7b1', '#fadbd8']

def draw_radar(ax, group_df, full_df, colors, title):
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(VAR_LABELS, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7)
    ax.grid(True, alpha=0.3)

    for i, (_, row) in enumerate(group_df.iterrows()):
        name = row['상권_코드_명']
        rank = int(row['순위'])
        sub = full_df[full_df['상권_코드_명'] == name]
        if sub.empty:
            continue
        vals = [float(sub[f'{v}_pct'].iloc[0]) for v in DEMAND_VARS]
        vals += vals[:1]
        ax.plot(angles, vals, color=colors[i], linewidth=1.8,
                label=f"{rank}위 {name[:8]}")
        ax.fill(angles, vals, color=colors[i], alpha=0.08)

    ax.set_title(title, pad=20, fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15), fontsize=8)

draw_radar(ax1, q1_top5, df_prof, blues,  'Q1 검증시장공백 Top5\n수요 변수 분위수')
draw_radar(ax2, q2_top5, df_prof, reds,   'Q2 잠재수요미실현 Top5\n수요 변수 분위수')

plt.suptitle('상권별 수요 변수 강점 분석 (전체 상권 대비 분위수)',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(OUT_RADAR, dpi=150, bbox_inches='tight')
plt.close()
logs.append(f"[저장] 레이더 차트: {OUT_RADAR}")

# ─────────────────────────────────────────────
# 5. 텍스트 프로파일 로그
# ─────────────────────────────────────────────
logs.append("\n" + "="*60)
logs.append("=== Q1 Top5 상권 프로파일 (검증시장공백) ===")
logs.append("="*60)
for _, row in q1_top5.iterrows():
    name = row['상권_코드_명']
    sub  = df_prof[df_prof['상권_코드_명'] == name]
    if sub.empty:
        continue
    s = sub.iloc[0]
    logs.append(f"\n[Q1-{int(row['순위'])}위] {name}  [{row['상권유형']}]")
    logs.append(f"  잔차={s['residual_latest']:+.3f}  공급점수={s['supply_pct']:.3f}")
    for v, lbl in zip(DEMAND_VARS, VAR_LABELS):
        val = s[v]
        pct = s[f'{v}_pct']
        logs.append(f"  {lbl:8s}: {val:>10,.0f}  (상위 {(1-pct)*100:.0f}%)")

logs.append("\n" + "="*60)
logs.append("=== Q2 Top5 상권 프로파일 (잠재수요미실현) ===")
logs.append("="*60)
for _, row in q2_top5.iterrows():
    name = row['상권_코드_명']
    sub  = df_prof[df_prof['상권_코드_명'] == name]
    if sub.empty:
        continue
    s = sub.iloc[0]
    logs.append(f"\n[Q2-{int(row['순위'])}위] {name}  [{row['상권유형']}]")
    logs.append(f"  잔차={s['residual_latest']:+.3f}  공급점수={s['supply_pct']:.3f}")
    for v, lbl in zip(DEMAND_VARS, VAR_LABELS):
        val = s[v]
        pct = s[f'{v}_pct']
        logs.append(f"  {lbl:8s}: {val:>10,.0f}  (상위 {(1-pct)*100:.0f}%)")

log_text = "\n".join(logs)
with open(OUT_LOG, 'w', encoding='utf-8') as f:
    f.write(log_text)

print(log_text)
