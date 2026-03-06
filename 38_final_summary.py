# 38_final_summary.py
# 최종 분석 보고서 생성 (Markdown)
#
# 입력:
#   36_q1_ranked.csv / 36_q2_ranked.csv
#   37_demand_profile.csv
#   37_profile_log.txt
#
# 출력:
#   38_final_report.md

import pandas as pd
import os

BASE     = os.path.dirname(os.path.abspath(__file__))
IN_Q1    = os.path.join(BASE, '36_q1_ranked.csv')
IN_Q2    = os.path.join(BASE, '36_q2_ranked.csv')
IN_PROF  = os.path.join(BASE, '37_demand_profile.csv')
OUT_MD   = os.path.join(BASE, '38_final_report.md')

# ─── 데이터 로드 ──────────────────────────────
df_q1   = pd.read_csv(IN_Q1,  encoding='utf-8-sig')
df_q2   = pd.read_csv(IN_Q2,  encoding='utf-8-sig')
df_prof = pd.read_csv(IN_PROF, encoding='utf-8-sig')

DEMAND_VARS = ['집객시설_수', '총_직장_인구_수', '월_평균_소득_금액',
               '총_가구_수', '카페_검색지수', '지하철_노선_수']
VAR_LABELS  = ['집객시설', '직장인구', '소득', '가구수', '검색지수', '지하철노선']

def pct_bar(pct, width=10):
    """분위수를 ASCII 바 차트로 표현 (pct=0~1)"""
    filled = round(pct * width)
    return '█' * filled + '░' * (width - filled) + f' {pct*100:.0f}%'

def district_section(row, label):
    name   = row['상권_코드_명']
    typ    = row.get('상권유형', '')
    res    = row['residual_latest']
    spct   = row['supply_pct']
    lines  = []
    lines.append(f"#### {label} — {name}  `{typ}`")
    lines.append(f"")
    lines.append(f"| 지표 | 값 | 전체 상권 대비 |")
    lines.append(f"|------|-----|-------------|")
    for v, lbl in zip(DEMAND_VARS, VAR_LABELS):
        val  = row.get(v, float('nan'))
        pct  = row.get(f'{v}_pct', float('nan'))
        if pd.isna(val):
            lines.append(f"| {lbl} | — | — |")
        else:
            bar = pct_bar(pct)
            lines.append(f"| {lbl} | {val:,.0f} | {bar} |")
    lines.append(f"")
    lines.append(f"> 잔차: `{res:+.3f}` &nbsp; 공급점수: `{spct:.3f}`")
    lines.append(f"")
    return "\n".join(lines)

# ─── Markdown 생성 ────────────────────────────
md = []

md.append("# 서울 찻집 블루오션 상권 분석 — 최종 보고서")
md.append("")
md.append("> **작성일:** 2026-03-06  ")
md.append("> **목적:** 서울시 찻집 창업을 위한 블루오션 상권 데이터 기반 추천  ")
md.append("> **분석 기간:** 2023Q3 ~ 2025Q3 (9분기)")
md.append("")
md.append("---")
md.append("")

# ── 1. 프로젝트 개요 ──────────────────────────
md.append("## 1. 프로젝트 개요")
md.append("")
md.append("단순히 매출이 높은 상권이 아니라, **\"수요는 충분한데 찻집이 없는 상권\"** 을 발굴하는 것이 목표.")
md.append("")
md.append("```")
md.append("데이터:  서울시 1,139개 상권 × 9분기 패널 (원본 9,760행 / 155개 변수)")
md.append("목표:    찻집 창업 최적 상권 추천 (블루오션 = 수요 있음 + 찻집 없음)")
md.append("```")
md.append("")
md.append("---")
md.append("")

# ── 2. 분석 방법론 ────────────────────────────
md.append("## 2. 분석 방법론 — 2-Track 프레임워크")
md.append("")
md.append("```")
md.append("┌─────────────────────────────────────────────────┐")
md.append("│  Track A: 순수 수요 예측 모델 (Pooled OLS)       │")
md.append("│    X = 수요지표 6개 + 분기더미 + 유형더미         │")
md.append("│    Y = log(찻집업종 당월 매출)                    │")
md.append("│    → GroupKFold OOF 잔차 추출                    │")
md.append("│       잔차 양수 = 수요 대비 과성과 (이미 잘 됨)   │")
md.append("│       잔차 음수 = 수요 대비 저성과 (아직 미실현)  │")
md.append("└─────────────────────────────────────────────────┘")
md.append("                      +")
md.append("┌─────────────────────────────────────────────────┐")
md.append("│  Track B: 복합 공급부족 지수 (모델 밖)           │")
md.append("│    = 0.5 × rank(1/(찻집수+1))                   │")
md.append("│    + 0.5 × rank(찻집매출/(카페음료점포수+1))     │")
md.append("└─────────────────────────────────────────────────┘")
md.append("                      ↓")
md.append("┌─────────────────────────────────────────────────┐")
md.append("│  2D 매트릭스 → 사분면 분류                       │")
md.append("│    Q1 (파랑): 잔차>=0 + 찻집없음 = 검증시장공백  │")
md.append("│    Q2 (빨강): 잔차<0  + 찻집없음 = 잠재수요미실현│")
md.append("└─────────────────────────────────────────────────┘")
md.append("```")
md.append("")
md.append("**수요 변수 6개 (XGBoost SHAP → Lasso → VIF 최종 확정)**")
md.append("")
md.append("| 변수 | SHAP 순위 | VIF |")
md.append("|------|---------|-----|")
md.append("| 집객시설_수 | 2위 (0.401) | 2.89 |")
md.append("| 총_직장_인구_수 | 3위 (0.265) | 1.72 |")
md.append("| 월_평균_소득_금액 | 4위 (0.260) | 3.28 |")
md.append("| 총_가구_수 | 7위 (0.136) | 2.37 |")
md.append("| 카페_검색지수 | 9위 (0.104) | 1.62 |")
md.append("| 지하철_노선_수 | 17위 (0.031) | 1.74 |")
md.append("")
md.append("---")
md.append("")

# ── 3. 모델 성능 ──────────────────────────────
md.append("## 3. 모델 성능")
md.append("")
md.append("| 구분 | R² |")
md.append("|------|-----|")
md.append("| **OOF R² (GroupKFold 5-fold)** | **0.4413** |")
md.append("| 전체 OLS R² (in-sample) | 0.4581 |")
md.append("")
md.append("> OOF R²=0.44는 공급변수를 의도적으로 제외한 수요 전용 모델 기준으로 정상.  ")
md.append("> R²이 너무 높으면 잔차가 0에 수렴해 블루오션 신호 소멸. 현재 수준이 최적.")
md.append("")
md.append("---")
md.append("")

# ── 4. 사분면 분포 ────────────────────────────
md.append("## 4. 사분면 분포 (전체 1,036개 상권)")
md.append("")
md.append("| 사분면 | 상권수 | 의미 |")
md.append("|--------|------|------|")
md.append("| Q1 검증시장공백 | 475개 (45.8%) | 잔차>=0 + 찻집없음 → 이미 잘 되는 상권에 찻집만 없음 |")
md.append("| Q2 잠재수요미실현 | 444개 (42.8%) | 잔차<0 + 찻집없음 → 수요 조건은 충분하나 미개척 |")
md.append("| Q4 레드오션 | 77개 (7.4%) | 잔차>=0 + 찻집있음 → 이미 잘 됨 + 경쟁 있음 |")
md.append("| Q3 저성과포화 | 40개 (3.9%) | 잔차<0 + 찻집있음 → 낮은 성과 + 경쟁 있음 |")
md.append("")
md.append("---")
md.append("")

# ── 5. 최종 추천 상권 ─────────────────────────
md.append("## 5. 최종 추천 상권")
md.append("")
md.append("### 전략 A — 안전한 진입 (Q1 검증시장공백, 상위 5%)")
md.append("")
md.append("> **개념:** 카페·음료 시장이 이미 수요 대비 과성과(잔차 양수)인 상권에 찻집만 없음.  ")
md.append("> 시장이 이미 검증됐으므로 리스크가 낮고, 기존 수요를 흡수할 수 있음.")
md.append("")

for _, row in df_q1.head(5).iterrows():
    rank = int(row['Q1_순위'])
    prof_row = df_prof[df_prof['상권_코드_명'] == row['상권_코드_명']]
    if not prof_row.empty:
        md.append(district_section(prof_row.iloc[0], f"Q1 {rank}위"))
    else:
        md.append(f"#### Q1 {rank}위 — {row['상권_코드_명']}")
        md.append(f"> 잔차: `{row['residual_latest']:+.3f}` &nbsp; 공급점수: `{row['supply_pct']:.3f}`")
        md.append("")

md.append("---")
md.append("")
md.append("### 전략 B — 선점 전략 (Q2 잠재수요미실현, Top5)")
md.append("")
md.append("> **개념:** 수요 지표는 강하지만 아직 찻집이 없어 매출이 낮은 상권.  ")
md.append("> 고위험·고수익 전략. 찻집 자체가 수요를 실현시키는 역할을 함.")
md.append("")

for _, row in df_q2.head(5).iterrows():
    rank = int(row['Q2_순위'])
    prof_row = df_prof[df_prof['상권_코드_명'] == row['상권_코드_명']]
    if not prof_row.empty:
        md.append(district_section(prof_row.iloc[0], f"Q2 {rank}위"))
    else:
        md.append(f"#### Q2 {rank}위 — {row['상권_코드_명']}")
        md.append(f"> 잔차: `{row['residual_latest']:+.3f}` &nbsp; 공급점수: `{row['supply_pct']:.3f}`")
        md.append("")

md.append("---")
md.append("")

# ── 6. 전략 제언 ──────────────────────────────
md.append("## 6. 전략 제언")
md.append("")
md.append("### 리스크 성향별 선택")
md.append("")
md.append("| 성향 | 추천 전략 | 대표 상권 |")
md.append("|------|---------|---------|")
md.append("| 안전 추구 | **Q1** — 검증된 수요 + 공급 공백 | 홍대소상공인상점가, 외대앞역 1번 |")
md.append("| 선점·성장 | **Q2** — 잠재수요 미실현 선점 | 서울역, 대치역 |")
md.append("| 균형 | Q1 Top3 + Q2 Top2 조합 검토 | — |")
md.append("")
md.append("### Q1 상권 특성 요약")
md.append("")
md.append("- 주로 **골목상권·전통시장** (홍대, 외대, 성신여대 등 대학가 인근)")
md.append("- 잔차 +2.5~+3.2 — 같은 수요 조건 상권 대비 매출이 현저히 높음")
md.append("- 집객시설·가구수 지표가 강점 → 상주 소비층 탄탄")
md.append("")
md.append("### Q2 상권 특성 요약")
md.append("")
md.append("- 주로 **발달상권** (서울역, 대치역, 상봉역 등 교통 허브)")
md.append("- 직장인구·집객시설이 전국 상위 3~7% — 압도적 수요 기반")
md.append("- 잔차 -0.1~-1.0 — 수요 대비 찻집 매출이 낮음 = 미실현 잠재력")
md.append("")
md.append("### 주의사항")
md.append("")
md.append("- 본 분석은 **상권 단위** 추천. 실제 점포 위치(도로, 건물 유형, 임대료)는 현장 조사 필요.")
md.append("- OOF R²=0.44 → 수요 외 설명 안 되는 56% 분산 존재. 잔차에 노이즈 포함 가능성.")
md.append("- 분석 기준 분기: 2025Q3. 이후 상권 변화(대규모 개발, 찻집 신규 개업 등) 모니터링 필요.")
md.append("")
md.append("---")
md.append("")
md.append("## 7. 분석 파이프라인 요약")
md.append("")
md.append("| 번호 | 파일 | 내용 |")
md.append("|------|------|------|")
md.append("| 31 | 31_xgboost_shap.py | XGBoost + SHAP 변수 중요도 (CV R²=0.9047) |")
md.append("| 32 | 32_lasso_elasticnet.py | Lasso/ElasticNet + VIF → 변수 9개→6개 확정 |")
md.append("| 33 | 33_preprocessing.py | 결측처리 + 표준화 + 더미변수 → 9,392행 |")
md.append("| 34 | 34_ols.py | Pooled OLS + GroupKFold OOF 잔차 (R²=0.4413) |")
md.append("| 35 | 35_blueocean_score.py | Q1/Q2 사분면 + 복합 공급지수 + 2D 매트릭스 |")
md.append("| 36 | 36_unified_ranking.py | 사분면별 + 피타고라스 통합 순위 |")
md.append("| 37 | 37_district_profile.py | 상위 후보 수요 변수 프로파일 + 9분기 추세 |")
md.append("| 38 | 38_final_summary.py | 최종 보고서 (이 파일) |")
md.append("")
md.append("---")
md.append("")
md.append("*분석: Claude Sonnet 4.6 / 2026-03-06*")

# ─── 저장 ────────────────────────────────────
md_text = "\n".join(md)
with open(OUT_MD, 'w', encoding='utf-8') as f:
    f.write(md_text)

print(f"[저장] 최종 보고서: {OUT_MD}")
print(f"  총 {len(md_text.splitlines())}줄")
