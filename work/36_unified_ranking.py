# 36_unified_ranking.py
# 사분면별 + 통합 블루오션 순위 산정
#
# 입력: 35_blueocean_ranking.csv
# 출력:
#   36_q1_ranked.csv      - Q1 순위: 잔차 큰 순 (상위 5%, 23개)
#                           이유: 이미 폭발적으로 잘 되는 시장 = 파이 가장 큰 곳
#   36_q2_ranked.csv      - Q2 순위: 복합공급점수 높은 순 (Top30)
#                           이유: 기존 카페들이 돈 버는 시장에 찻집만 없는 곳
#   36_unified_top30.csv  - 통합 순위: 피타고라스 거리 (Q1+Q2, Top30)
#                           이유: 수요or공급 어느 쪽이든 극단적인 상권 포착
#   36_ranking_log.txt    - 실행 로그
#
# ─── 정렬 기준 설계 원칙 ─────────────────────────────────
#  Q1 (검증시장공백):   잔차 큰 순
#    → Q1 조건 자체가 이미 "찻집없음" 보장
#    → 그 안에서 "얼마나 대박이 날 시장인가" = 잔차 크기로 판단
#
#  Q2 (잠재수요미실현): 복합공급점수 높은 순
#    → Q2 조건 자체가 이미 "잠재수요 있음" 보장
#    → 그 안에서 "깃발 꽂았을 때 리턴이 얼마나 큰가" = 공급 점수로 판단
#
#  통합 (Q1+Q2):       피타고라스 거리 = sqrt(residual_pct² + supply_pct²)
#    → "수요가 압도적이거나 공급이 아예 없거나" 둘 중 하나라도 극단적인 상권
#    → Q1 최대 거리: sqrt(2) ≈ 1.41 / Q2 최대 거리: 1.0
#    → Q1이 두 지표 모두 극단이므로 통합 상위에 더 많이 등장
# ──────────────────────────────────────────────────────────

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

BASE     = os.path.dirname(os.path.abspath(__file__))
IN_PATH  = os.path.join(BASE, '35_blueocean_ranking.csv')
OUT_Q1   = os.path.join(BASE, '36_q1_ranked.csv')
OUT_Q2   = os.path.join(BASE, '36_q2_ranked.csv')
OUT_UNI  = os.path.join(BASE, '36_unified_top30.csv')
OUT_PLOT = os.path.join(BASE, '36_quadrant_plot.png')
OUT_LOG  = os.path.join(BASE, '36_ranking_log.txt')

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
# 1. 데이터 로드
# ─────────────────────────────────────────────
df = pd.read_csv(IN_PATH, encoding='utf-8-sig')
logs.append(f"입력: {df.shape[0]}개 상권")
logs.append(f"사분면 분포: {dict(df['사분면'].value_counts())}")

# 분위수 컬럼 복원
# q1_residual_score = rank_pct(residual, ascending) = residual_pct
# q2_supply_score   = composite supply_pct
df['residual_pct'] = df['q1_residual_score']
df['supply_pct']   = df['q2_supply_score']

# 피타고라스 거리 (원점 기준, 0~sqrt(2) 범위)
df['pythagorean_dist'] = (df['residual_pct']**2 + df['supply_pct']**2)**0.5

# ─────────────────────────────────────────────
# 2. Q1 순위: 잔차 큰 순 (상위 5%)
# ─────────────────────────────────────────────
df_q1_all = df[df['사분면'] == 'Q1_검증시장공백'].copy()
df_q1_all = df_q1_all.sort_values('residual_latest', ascending=False)
q1_n = max(20, int(len(df_q1_all) * 0.05))
df_q1 = df_q1_all.head(q1_n).copy()
df_q1.insert(0, 'Q1_순위', range(1, len(df_q1)+1))

q1_cols = ['Q1_순위', '상권_코드_명', '상권유형',
           'residual_latest', 'q1_score', 'supply_pct',
           'supply_shortage', 'cafe_revenue_per_store',
           '카페음료_점포수', '찻집수_latest', '매출_latest',
           '사분면', '구조적블루오션']
q1_cols = [c for c in q1_cols if c in df_q1.columns]
df_q1[q1_cols].to_csv(OUT_Q1, index=False, encoding='utf-8-sig')

# ─────────────────────────────────────────────
# 3. Q2 순위: 복합공급점수 높은 순 (Top30)
# ─────────────────────────────────────────────
df_q2_all = df[df['사분면'] == 'Q2_잠재수요미실현'].copy()
df_q2_all = df_q2_all.sort_values('supply_pct', ascending=False)
df_q2 = df_q2_all.head(30).copy()
df_q2.insert(0, 'Q2_순위', range(1, len(df_q2)+1))

q2_cols = ['Q2_순위', '상권_코드_명', '상권유형',
           'supply_pct', 'q2_score', 'residual_latest',
           'supply_shortage', 'cafe_revenue_per_store',
           '카페음료_점포수', '찻집수_latest', '매출_latest',
           '사분면', '구조적블루오션']
q2_cols = [c for c in q2_cols if c in df_q2.columns]
df_q2[q2_cols].to_csv(OUT_Q2, index=False, encoding='utf-8-sig')

# ─────────────────────────────────────────────
# 4. 통합 순위: 피타고라스 거리 (Q1+Q2, Top30)
# ─────────────────────────────────────────────
df_bo = df[df['사분면'].isin(['Q1_검증시장공백', 'Q2_잠재수요미실현'])].copy()
df_bo = df_bo.sort_values('pythagorean_dist', ascending=False)
df_uni = df_bo.head(30).copy()
df_uni.insert(0, '통합_순위', range(1, len(df_uni)+1))

uni_cols = ['통합_순위', '상권_코드_명', '상권유형', '사분면',
            'pythagorean_dist', 'residual_pct', 'supply_pct',
            'residual_latest', 'supply_shortage',
            '찻집수_latest', '매출_latest', '구조적블루오션']
uni_cols = [c for c in uni_cols if c in df_uni.columns]
df_uni[uni_cols].to_csv(OUT_UNI, index=False, encoding='utf-8-sig')

logs.append(f"\n[저장] Q1 순위 (잔차 큰 순, 상위 5%): {OUT_Q1}  ({len(df_q1)}개 / Q1 전체 {len(df_q1_all)}개)")
logs.append(f"[저장] Q2 순위 (공급점수 높은 순):       {OUT_Q2}  ({len(df_q2)}개 / Q2 전체 {len(df_q2_all)}개)")
logs.append(f"[저장] 통합 Top30 (피타고라스 거리):     {OUT_UNI}  ({len(df_uni)}개)")

# ─────────────────────────────────────────────
# 5. 시각화: Q1/Q2 순위 버블 차트
# ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

for ax, (df_plot, title, color, x_col, x_label, rank_col) in zip(axes, [
    (df_q1, 'Q1 검증시장공백 Top{} (잔차 기준)'.format(q1_n),
     '#2980b9', 'residual_latest', 'OOF 잔차 (양수=과성과)', 'Q1_순위'),
    (df_q2, 'Q2 잠재수요미실현 Top30 (공급점수 기준)',
     '#e74c3c', 'supply_pct', '복합공급점수 분위수', 'Q2_순위'),
]):
    scatter = ax.scatter(
        df_plot[x_col],
        df_plot['supply_pct'] if x_col != 'supply_pct' else df_plot['residual_latest'],
        c=color, s=100, alpha=0.8
    )
    for _, row in df_plot.head(10).iterrows():
        name = str(row.get('상권_코드_명', ''))[:8]
        x = row[x_col]
        y = row['supply_pct'] if x_col != 'supply_pct' else row['residual_latest']
        ax.annotate(
            f"{int(row[rank_col])}. {name}",
            xy=(x, y), xytext=(5, 5), textcoords='offset points',
            fontsize=7, color=color,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7)
        )
    ax.set_xlabel(x_label, fontsize=11)
    ax.set_ylabel('공급점수' if x_col != 'supply_pct' else 'OOF 잔차', fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)

plt.suptitle('Q1/Q2 사분면별 순위 (새 기준 적용)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUT_PLOT, dpi=150, bbox_inches='tight')
plt.close()
logs.append(f"[저장] 순위 시각화: {OUT_PLOT}")

# ─────────────────────────────────────────────
# 6. 최종 로그 출력
# ─────────────────────────────────────────────
logs.append("\n" + "="*60)
logs.append("=== 사분면별 + 통합 순위 산정 완료 ===")
logs.append("="*60)

logs.append("\n" + "-"*60)
logs.append(f"[Q1 Top 10 - 검증시장공백 (잔차 큰 순, 상위 5%={q1_n}개 중)]")
for i, (_, row) in enumerate(df_q1.head(10).iterrows(), 1):
    name   = str(row.get('상권_코드_명', ''))
    type_  = str(row.get('상권유형', ''))
    res    = row['residual_latest']
    spct   = row['supply_pct']
    cha    = int(row.get('찻집수_latest', 0))
    cafe   = int(row.get('카페음료_점포수', 0))
    logs.append(f"  {i:2d}위 {name[:12]:14s} [{type_[:4]}] "
                f"잔차={res:+.3f} 공급점수={spct:.3f} 찻집={cha}개 카페={cafe}개")

logs.append("\n" + "-"*60)
logs.append(f"[Q2 Top 10 - 잠재수요미실현 (공급점수 높은 순, Top30 중)]")
for i, (_, row) in enumerate(df_q2.head(10).iterrows(), 1):
    name   = str(row.get('상권_코드_명', ''))
    type_  = str(row.get('상권유형', ''))
    res    = row['residual_latest']
    spct   = row['supply_pct']
    cha    = int(row.get('찻집수_latest', 0))
    cafe   = int(row.get('카페음료_점포수', 0))
    consist = '★구조적' if row.get('구조적블루오션', False) else ''
    logs.append(f"  {i:2d}위 {name[:12]:14s} [{type_[:4]}] "
                f"공급점수={spct:.3f} 잔차={res:+.3f} 찻집={cha}개 카페={cafe}개 {consist}")

logs.append("\n" + "-"*60)
logs.append("[통합 Top 10 - 피타고라스 거리 기준 (Q1+Q2 합산)]")
q1_cnt = (df_uni['사분면'] == 'Q1_검증시장공백').sum()
q2_cnt = (df_uni['사분면'] == 'Q2_잠재수요미실현').sum()
logs.append(f"  Top30 구성: Q1={q1_cnt}개 / Q2={q2_cnt}개")
logs.append(f"  (Q1 최대거리=sqrt(2)=1.41, Q2 최대거리=1.0 → Q1이 상위에 많음)")
for i, (_, row) in enumerate(df_uni.head(10).iterrows(), 1):
    name   = str(row.get('상권_코드_명', ''))
    type_  = str(row.get('상권유형', ''))
    quad   = str(row.get('사분면', ''))
    dist   = row['pythagorean_dist']
    res    = row['residual_latest']
    spct   = row['supply_pct']
    cha    = int(row.get('찻집수_latest', 0))
    logs.append(f"  {i:2d}위 {name[:12]:14s} [{type_[:4]}] [{quad[:2]}] "
                f"거리={dist:.3f} 잔차={res:+.3f} 공급={spct:.3f} 찻집={cha}개")

log_text = "\n".join(logs)
with open(OUT_LOG, 'w', encoding='utf-8') as f:
    f.write(log_text)

print(log_text)
