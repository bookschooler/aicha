# 35_blueocean_score.py
# 2D 매트릭스 블루오션 스코어링 + 최종 랭킹
# ★ Q1 vs Q2 두 가지 접근법 모두 출력
#
# 입력: 34_district_residuals.csv
# 출력:
#   35_blueocean_ranking.csv   - 전체 상권 점수 + 랭킹 (전체 기준)
#   35_q2_top30.csv            - Q2 Top30: 잔차<0 + 찻집없음 (잠재수요 미실현)
#   35_q1_top30.csv            - Q1 Top30: 잔차>=0 + 찻집없음 (검증된시장 공백)
#   35_2d_matrix.png           - 2D scatter 매트릭스 시각화
#   35_blueocean_log.txt       - 실행 로그
#
# ─── 접근법 비교 ────────────────────────────────────────────
#  Q2 (잔차<0  + 찻집없음): 수요지표 대비 매출 저조 + 공급 공백
#                          → 잠재 수요가 숨어 있고 아직 개척되지 않은 곳
#  Q1 (잔차>=0 + 찻집없음): 수요지표 대비 매출 이미 높음 + 공급 공백
#                          → 시장이 이미 검증됐는데 찻집만 없는 틈새
# ─────────────────────────────────────────────────────────────

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

BASE         = os.path.dirname(os.path.abspath(__file__))
IN_PATH      = os.path.join(BASE, '34_district_residuals.csv')
IN_OOF       = os.path.join(BASE, '34_oof_residuals.csv')
OUT_RANK     = os.path.join(BASE, '35_blueocean_ranking.csv')
OUT_Q2_TOP30 = os.path.join(BASE, '35_q2_top30.csv')
OUT_Q1_TOP30 = os.path.join(BASE, '35_q1_top30.csv')
OUT_PLOT     = os.path.join(BASE, '35_2d_matrix.png')
OUT_LOG      = os.path.join(BASE, '35_blueocean_log.txt')

logs = []

# ─────────────────────────────────────────────
# 한글 폰트 설정 (Windows)
# ─────────────────────────────────────────────
font_candidates = ['Malgun Gothic', 'NanumGothic', 'AppleGothic', 'DejaVu Sans']
for font_name in font_candidates:
    try:
        font_path = fm.findfont(fm.FontProperties(family=font_name))
        if font_name.lower() in font_path.lower() or 'malgun' in font_path.lower():
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
logs.append(f"컬럼: {list(df.columns)}")

# 카페음료_점포수 병합 (OOF 잔차 파일 → 최신 분기)
df_oof = pd.read_csv(IN_OOF, encoding='utf-8-sig')
latest_q = df_oof['기준_년분기_코드'].max()
cafe_store = (
    df_oof[df_oof['기준_년분기_코드'] == latest_q]
    [['상권_코드', '카페음료_점포수']]
)
df = df.merge(cafe_store, on='상권_코드', how='left')
logs.append(f"카페음료_점포수 병합 완료 (최신분기: {latest_q})")

# ─────────────────────────────────────────────
# 2. 공급 지수 고도화
#    supply_shortage_v1: 1/(찻집수+1)       — 찻집 직접 경쟁자 희소성
#    cafe_per_revenue:   매출/(카페음료점포수+1) — 카페 전체 포화 대비 시장 크기
#    supply_composite:   두 지표의 평균       — 종합 공급 점수
# ─────────────────────────────────────────────
# 점포당 매출: 높을수록 카페 포화 대비 찻집 수요 크다 → 진입 여지 있음
df['cafe_revenue_per_store'] = df['매출_latest'] / (df['카페음료_점포수'] + 1)

# 분위수 변환 (0~1)
df['residual_pct']       = df['residual_latest'].rank(pct=True, ascending=True)
df['supply_pct_v1']      = df['supply_shortage'].rank(pct=True, ascending=True)          # 찻집수 기반
df['supply_pct_cafe']    = df['cafe_revenue_per_store'].rank(pct=True, ascending=True)   # 점포당매출 기반
df['supply_pct']         = 0.5 * df['supply_pct_v1'] + 0.5 * df['supply_pct_cafe']      # 복합 공급점수

logs.append(f"\n[공급지수 고도화]")
logs.append(f"  supply_v1 (찻집희소성): 1/(찻집수+1)")
logs.append(f"  cafe_revenue_per_store: 찻집매출/(카페음료점포수+1)")
logs.append(f"  supply_composite: 두 지표 분위수 평균")
logs.append(f"  점포당매출 범위: {df['cafe_revenue_per_store'].min():.0f} ~ {df['cafe_revenue_per_store'].max():.0f}")

# ── Q2 스코어: 잔차 낮을수록(더 음수) + 공급부족 높을수록 좋음 ──────
df['q2_residual_score'] = 1 - df['residual_pct']   # 잔차 음수 방향
df['q2_supply_score']   = df['supply_pct']
df['q2_score']          = 0.5 * df['q2_residual_score'] + 0.5 * df['q2_supply_score']

# ── Q1 스코어: 잔차 높을수록(양수) + 공급부족 높을수록 좋음 ──────────
df['q1_residual_score'] = df['residual_pct']        # 잔차 양수 방향
df['q1_supply_score']   = df['supply_pct']
df['q1_score']          = 0.5 * df['q1_residual_score'] + 0.5 * df['q1_supply_score']

# ─────────────────────────────────────────────
# 3. 사분면 분류
# ─────────────────────────────────────────────
median_residual = df['residual_latest'].median()
median_supply   = df['supply_shortage'].median()

def quadrant(row):
    r = row['residual_latest']
    s = row['supply_shortage']
    if r < 0 and s >= median_supply:
        return 'Q2_잠재수요미실현'    # 잔차<0 + 찻집없음 (원래 블루오션)
    elif r >= 0 and s >= median_supply:
        return 'Q1_검증시장공백'      # 잔차>=0 + 찻집없음 (검증된 틈새)
    elif r < 0 and s < median_supply:
        return 'Q3_저성과포화'
    else:
        return 'Q4_레드오션'

df['사분면'] = df.apply(quadrant, axis=1)

# 구조적 블루오션 (최신+평균 모두 음수)
if 'residual_consistent' in df.columns:
    df['구조적블루오션'] = df['residual_consistent'].astype(bool)
else:
    df['구조적블루오션'] = (df['residual_latest'] < 0) & (df['residual_avg'] < 0)

logs.append(f"\n[사분면 분포]")
for q, cnt in df['사분면'].value_counts().items():
    logs.append(f"  {q}: {cnt}개")
logs.append(f"\n[구조적 블루오션] 최신·평균 모두 음수: {df['구조적블루오션'].sum()}개")

# ─────────────────────────────────────────────
# 4. 저장
# ─────────────────────────────────────────────
save_base = [
    '상권_코드', '상권_코드_명', '상권유형',
    'residual_latest', 'residual_avg', 'supply_shortage',
    'cafe_revenue_per_store', '카페음료_점포수', '찻집수_latest', '매출_latest',
    '사분면', '구조적블루오션'
]

# 전체 랭킹 (Q2 스코어 기준)
df['블루오션_랭킹'] = df['q2_score'].rank(ascending=False, method='min').astype(int)
df_rank = df.sort_values('블루오션_랭킹')

save_cols_full = ['블루오션_랭킹', 'q2_score', 'q1_score',
                  'q2_residual_score', 'q2_supply_score',
                  'q1_residual_score', 'q1_supply_score'] + save_base
save_cols_full = [c for c in save_cols_full if c in df_rank.columns]
df_rank[save_cols_full].to_csv(OUT_RANK, index=False, encoding='utf-8-sig')

# ── Q2 Top30: 잔차<0 + 찻집없음 ──────────────────────────────
df_q2 = df.sort_values('q2_score', ascending=False)
df_q2 = df_q2[df_q2['사분면'] == 'Q2_잠재수요미실현'].head(30)

save_q2 = ['q2_score', 'q2_residual_score', 'q2_supply_score'] + save_base
save_q2 = [c for c in save_q2 if c in df_q2.columns]
df_q2[save_q2].to_csv(OUT_Q2_TOP30, index=False, encoding='utf-8-sig')

# ── Q1 상위 5%: 잔차>=0 + 찻집없음, 분별력 확보를 위해 Q1 내 상위 5%만 ─
df_q1_all = df[df['사분면'] == 'Q1_검증시장공백'].sort_values('q1_score', ascending=False)
q1_top5pct_n = max(20, int(len(df_q1_all) * 0.05))  # 최소 20개 보장
df_q1 = df_q1_all.head(q1_top5pct_n)

save_q1 = ['q1_score', 'q1_residual_score', 'q1_supply_score'] + save_base
save_q1 = [c for c in save_q1 if c in df_q1.columns]
df_q1[save_q1].to_csv(OUT_Q1_TOP30, index=False, encoding='utf-8-sig')

logs.append(f"\n[저장] 전체 랭킹: {OUT_RANK}")
logs.append(f"[저장] Q2 Top30 (잠재수요미실현): {OUT_Q2_TOP30}  ({len(df_q2)}개)")
logs.append(f"[저장] Q1 Top{q1_top5pct_n} 상위5% (검증시장공백): {OUT_Q1_TOP30}  ({len(df_q1)}개 / Q1전체 {len(df_q1_all)}개 중)")

# ─────────────────────────────────────────────
# 5. 2D 매트릭스 시각화
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 9))

color_map = {
    'Q2_잠재수요미실현': '#e74c3c',  # 빨강
    'Q1_검증시장공백':   '#2980b9',  # 파랑
    'Q3_저성과포화':     '#95a5a6',  # 회색
    'Q4_레드오션':       '#bdc3c7',  # 연회색
}
size_map  = {'Q2_잠재수요미실현': 60, 'Q1_검증시장공백': 60, 'Q3_저성과포화': 15, 'Q4_레드오션': 15}
alpha_map = {'Q2_잠재수요미실현': 0.85, 'Q1_검증시장공백': 0.7, 'Q3_저성과포화': 0.3, 'Q4_레드오션': 0.2}

for q_label in ['Q4_레드오션', 'Q3_저성과포화', 'Q1_검증시장공백', 'Q2_잠재수요미실현']:
    sub = df[df['사분면'] == q_label]
    ax.scatter(
        sub['residual_latest'], sub['supply_shortage'],
        c=color_map[q_label], s=size_map[q_label],
        alpha=alpha_map[q_label],
        label=f"{q_label} ({len(sub)}개)",
        zorder=3 if q_label in ['Q2_잠재수요미실현', 'Q1_검증시장공백'] else 1
    )

# Q2 상위 10개 라벨
for _, row in df_q2.head(10).iterrows():
    name = str(row.get('상권_코드_명', ''))[:8]
    ax.annotate(name, xy=(row['residual_latest'], row['supply_shortage']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=7, color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7))

# Q1 상위 5개 라벨 (파란색)
for _, row in df_q1.head(5).iterrows():
    name = str(row.get('상권_코드_명', ''))[:8]
    ax.annotate(name, xy=(row['residual_latest'], row['supply_shortage']),
                xytext=(5, -12), textcoords='offset points',
                fontsize=7, color='#1a5276',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7))

# 기준선
ax.axvline(x=0, color='black', linewidth=1.2, linestyle='--', alpha=0.6)
ax.axhline(y=median_supply, color='black', linewidth=1.2, linestyle='--', alpha=0.6)

ylim = ax.get_ylim()
xlim = ax.get_xlim()
ax.text(xlim[0]*0.9, ylim[1]*0.95, '② 잠재수요 미실현 ★', fontsize=12, color='#e74c3c', fontweight='bold')
ax.text(xlim[1]*0.3,  ylim[1]*0.95, '① 검증시장 공백 ★', fontsize=12, color='#2980b9', fontweight='bold')
ax.text(xlim[0]*0.9, ylim[0]*0.5,  '③ 저성과·포화',      fontsize=10, color='#7f8c8d')
ax.text(xlim[1]*0.3,  ylim[0]*0.5,  '④ 레드오션',         fontsize=10, color='#95a5a6')

ax.set_xlabel('OOF 잔차 (음수=수요 대비 저성과 / 양수=수요 대비 과성과)', fontsize=12)
ax.set_ylabel('공급부족지수 1/(찻집수+1)', fontsize=12)
ax.set_title('서울 찻집 블루오션 2D 매트릭스\n②잠재수요미실현(빨강) vs ①검증시장공백(파랑)', fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_PLOT, dpi=150, bbox_inches='tight')
plt.close()
logs.append(f"[저장] 2D 매트릭스 시각화: {OUT_PLOT}")

# ─────────────────────────────────────────────
# 6. 최종 요약
# ─────────────────────────────────────────────
logs.append("\n" + "="*60)
logs.append("=== 블루오션 스코어링 완료 (Q1/Q2 두 접근법) ===")
logs.append("="*60)
logs.append(f"분석 대상: {len(df)}개 상권")
logs.append(f"Q2 잠재수요미실현 사분면: {(df['사분면']=='Q2_잠재수요미실현').sum()}개")
logs.append(f"Q1 검증시장공백   사분면: {(df['사분면']=='Q1_검증시장공백').sum()}개")
logs.append(f"구조적 블루오션(Q2): {df['구조적블루오션'].sum()}개 (9분기 내내 잔차 음수)")

logs.append("\n" + "-"*60)
logs.append("[접근법 비교]")
logs.append("  Q2 (빨강): 잔차<0 + 찻집없음")
logs.append("     -> 수요지표 대비 매출이 아직 낮음 = 잠재 수요 미실현 지역")
logs.append("     -> '아직 발굴 안 된 시장'에 먼저 진입하는 전략")
logs.append("  Q1 (파랑): 잔차>=0 + 찻집없음")
logs.append("     -> 수요지표 대비 매출이 이미 높음 = 시장이 검증된 지역")
logs.append("     -> '이미 잘 되는 동네인데 찻집만 없는' 안전한 진입 전략")

logs.append("\n" + "-"*60)
logs.append("[Q2 Top 10 - 잠재수요 미실현 (빨강)]")
for i, (_, row) in enumerate(df_q2.head(10).iterrows(), 1):
    name   = str(row.get('상권_코드_명', ''))
    type_  = str(row.get('상권유형', ''))
    score  = row['q2_score']
    res    = row['residual_latest']
    supply = row['supply_shortage']
    cha    = int(row.get('찻집수_latest', 0))
    consist = '★구조적' if row.get('구조적블루오션', False) else ''
    logs.append(f"  {i:2d}위 {name[:12]:14s} [{type_[:4]}] "
                f"점수={score:.3f} 잔차={res:+.3f} 공급부족={supply:.3f} 찻집={cha}개 {consist}")

logs.append("\n" + "-"*60)
logs.append(f"[Q1 Top 10 - 검증된 시장 공백 (파랑, 상위 5% = {q1_top5pct_n}개 중 상위 10)]")
for i, (_, row) in enumerate(df_q1.head(10).iterrows(), 1):
    name   = str(row.get('상권_코드_명', ''))
    type_  = str(row.get('상권유형', ''))
    score  = row['q1_score']
    res    = row['residual_latest']
    supply = row['supply_shortage']
    cha    = int(row.get('찻집수_latest', 0))
    logs.append(f"  {i:2d}위 {name[:12]:14s} [{type_[:4]}] "
                f"점수={score:.3f} 잔차={res:+.3f} 공급부족={supply:.3f} 찻집={cha}개")

log_text = "\n".join(logs)
with open(OUT_LOG, 'w', encoding='utf-8') as f:
    f.write(log_text)

print(log_text)
