# 33_preprocessing.py
# Track A 모델용 전처리: 결측 처리 → 더미변수 → 표준화 → 분석용 데이터셋 저장
#
# 최종 확정 변수 (6개):
#   집객시설_수 / 총_직장_인구_수 / 월_평균_소득_금액
#   총_가구_수 / 카페_검색지수 / 지하철_노선_수
#
# Y: log1p(당월_매출_금액)
# 더미: 분기 8개 (20233 기준) + 상권유형 3개 (골목상권 기준)
# 제외: 명동 관광특구 (이상치)
# 결측 처리: 그룹별 전략 (32번과 동일 로직)
# ─────────────────────────────────────────────

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os

# ─── 경로 설정 ───────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE, 'y_demand_supply_trend_merge.csv')
OUT_PATH   = os.path.join(BASE, '33_analysis_ready.csv')
LOG_PATH   = os.path.join(BASE, '33_preprocessing_log.txt')
SCALER_PATH = os.path.join(BASE, '33_scaler_params.csv')

# ─── 최종 변수 목록 ───────────────────────────
DEMAND_VARS = [
    '집객시설_수',
    '총_직장_인구_수',
    '월_평균_소득_금액',
    '총_가구_수',
    '카페_검색지수',
    '지하철_노선_수',
]

TARGET = '당월_매출_금액'
ID_COLS = ['상권_코드', '상권_코드_명', '기준_년분기_코드', '상권_구분_코드_명_x']
SUPPLY_COLS = ['찻집_수', '카페음료_점포수']  # Track B용으로 함께 저장

logs = []

# ─────────────────────────────────────────────
# 1. 데이터 로드
# ─────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
logs.append(f"원본 데이터: {df.shape[0]}행 × {df.shape[1]}열")
logs.append(f"상권 수: {df['상권_코드'].nunique()}개")
logs.append(f"분기: {sorted(df['기준_년분기_코드'].unique())}")

# ─────────────────────────────────────────────
# 2. 이상치 제거 — 명동 관광특구
# ─────────────────────────────────────────────
# 명동 관광특구: 상권_코드_명에 '명동' 포함 + 관광특구 유형
myeongdong_mask = (
    df['상권_코드_명'].str.contains('명동', na=False) &
    (df['상권_구분_코드_명_x'] == '관광특구')
)
myeongdong_codes = df.loc[myeongdong_mask, '상권_코드'].unique()
df = df[~df['상권_코드'].isin(myeongdong_codes)].copy()
logs.append(f"\n[이상치 제거] 명동 관광특구: {len(myeongdong_codes)}개 상권 제거")
logs.append(f"  → 잔류: {df.shape[0]}행")

# ─────────────────────────────────────────────
# 3. Y변수 생성
# ─────────────────────────────────────────────
df['y_log'] = np.log1p(df[TARGET])
logs.append(f"\n[Y변수] log1p 변환 완료. 0값 행 수: {(df[TARGET] == 0).sum()}")

# ─────────────────────────────────────────────
# 4. 결측 처리 (그룹별 전략)
# ─────────────────────────────────────────────

# ── 그룹 B: 구조적 전체 결측 상권 제거 (총_직장_인구_수, 총_상주인구_수/총_가구_수)
# 주의: 총_상주인구_수는 최종 변수에 없지만, 총_가구_수와 동일 상권 결측 → 총_가구_수로 체크
b1 = set(df[df['총_직장_인구_수'].isna()]['상권_코드'].unique())
b2 = set(df[df['총_가구_수'].isna()]['상권_코드'].unique())
remove_b = b1 | b2
df = df[~df['상권_코드'].isin(remove_b)].copy()
logs.append(f"\n[그룹 B] 구조적 전체 결측 상권 제거: {len(remove_b)}개")
logs.append(f"  총_직장_인구_수 결측: {len(b1)}개 / 총_가구_수 결측: {len(b2)}개")
logs.append(f"  → 잔류: {df.shape[0]}행")

# ── 그룹 C: 소득 미연계 상권 제거 (월_평균_소득_금액 결측 → 동일 상권 전체 분기)
c1 = set(df[df['월_평균_소득_금액'].isna()]['상권_코드'].unique())
remove_c = c1 - remove_b
df = df[~df['상권_코드'].isin(remove_c)].copy()
logs.append(f"\n[그룹 C] 소득 미연계 상권 제거: {len(remove_c)}개")
logs.append(f"  → 잔류: {df.shape[0]}행")

# ── 그룹 D: 집객시설_수 처리
#   구조적 결측(9개 분기 전부 결측) → 상권 제거
#   부분 결측(1~8개 분기 결측) → forward-fill → 잔여는 backward-fill
miss_jip = df[df['집객시설_수'].isna()].groupby('상권_코드').size()
structural_jip = set(miss_jip[miss_jip >= 9].index)
df = df[~df['상권_코드'].isin(structural_jip)].copy()
logs.append(f"\n[그룹 D] 집객시설_수 구조적 결측 상권 제거: {len(structural_jip)}개")

before_ffill = df['집객시설_수'].isna().sum()
df = df.sort_values(['상권_코드', '기준_년분기_코드'])
df['집객시설_수'] = df.groupby('상권_코드')['집객시설_수'].transform(
    lambda x: x.ffill().bfill()
)
after_ffill = df['집객시설_수'].isna().sum()
logs.append(f"  forward/backward fill: {before_ffill}개 결측 → {after_ffill}개 결측")
logs.append(f"  → 잔류: {df.shape[0]}행")

# ── 최종 결측 확인 → 잔여 결측 행 제거
remaining_na = df[DEMAND_VARS + ['y_log']].isna().any(axis=1).sum()
logs.append(f"\n[최종 결측 확인] 잔여 결측 행: {remaining_na}개 → 제거")
df = df.dropna(subset=DEMAND_VARS + ['y_log']).copy()
logs.append(f"  → 최종 잔류: {df.shape[0]}행, {df['상권_코드'].nunique()}개 상권")

# ─────────────────────────────────────────────
# 5. 더미변수 생성
# ─────────────────────────────────────────────

# ── 분기 더미 (기준: 20233 = 2023Q3)
quarters = sorted(df['기준_년분기_코드'].unique())
base_quarter = quarters[0]  # 20233
for q in quarters[1:]:
    df[f'Q_{q}'] = (df['기준_년분기_코드'] == q).astype(int)
quarter_dummies = [f'Q_{q}' for q in quarters[1:]]
logs.append(f"\n[더미변수] 분기 더미 {len(quarter_dummies)}개 생성 (기준: {base_quarter})")
logs.append(f"  {quarter_dummies}")

# ── 상권유형 더미 (기준: 골목상권)
type_col = '상권_구분_코드_명_x'
types = df[type_col].unique()
logs.append(f"\n[더미변수] 상권유형 분포:\n{df[type_col].value_counts().to_string()}")
# 골목상권 기준, 나머지 3개 더미
for t in ['관광특구', '발달상권', '전통시장']:
    df[f'TYPE_{t}'] = (df[type_col] == t).astype(int)
type_dummies = ['TYPE_관광특구', 'TYPE_발달상권', 'TYPE_전통시장']
logs.append(f"  유형 더미 {len(type_dummies)}개 생성 (기준: 골목상권)")

# ─────────────────────────────────────────────
# 6. 표준화 (수요 변수만, 더미·Y 제외)
# ─────────────────────────────────────────────
scaler = StandardScaler()
demand_scaled_cols = [f'{v}_scaled' for v in DEMAND_VARS]
df[demand_scaled_cols] = scaler.fit_transform(df[DEMAND_VARS])

# 스케일러 파라미터 저장 (나중에 역변환/해석용)
scaler_df = pd.DataFrame({
    '변수명': DEMAND_VARS,
    'mean': scaler.mean_,
    'std': scaler.scale_
})
scaler_df.to_csv(SCALER_PATH, index=False, encoding='utf-8-sig')
logs.append(f"\n[표준화] 수요 변수 {len(DEMAND_VARS)}개 StandardScaler 적용")
logs.append(f"  스케일러 파라미터 저장: {SCALER_PATH}")

# ─────────────────────────────────────────────
# 7. 최종 컬럼 구성 및 저장
# ─────────────────────────────────────────────

# 회귀 입력용 X컬럼 목록
X_COLS = demand_scaled_cols + quarter_dummies + type_dummies
logs.append(f"\n[최종 X 변수] 총 {len(X_COLS)}개:")
logs.append(f"  수요(표준화): {demand_scaled_cols}")
logs.append(f"  분기더미: {quarter_dummies}")
logs.append(f"  유형더미: {type_dummies}")

# 저장할 컬럼: ID + Y + X + 원본 수요변수 + Track B용 공급변수
save_cols = (
    ID_COLS
    + ['y_log', TARGET]
    + DEMAND_VARS           # 원본값 (Track B 계산 / 해석용)
    + demand_scaled_cols    # 표준화값 (모델 입력용)
    + quarter_dummies
    + type_dummies
    + [c for c in SUPPLY_COLS if c in df.columns]  # Track B용
)
# 중복 제거 (순서 유지)
seen = set()
save_cols_dedup = []
for c in save_cols:
    if c not in seen and c in df.columns:
        seen.add(c)
        save_cols_dedup.append(c)

df_out = df[save_cols_dedup].copy()
df_out.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')

logs.append(f"\n[저장 완료] {OUT_PATH}")
logs.append(f"  출력 형태: {df_out.shape[0]}행 × {df_out.shape[1]}열")
logs.append(f"  상권 수: {df_out['상권_코드'].nunique()}개")
logs.append(f"  분기 수: {df_out['기준_년분기_코드'].nunique()}개")

# ─────────────────────────────────────────────
# 8. 최종 요약 출력
# ─────────────────────────────────────────────
logs.append("\n" + "="*50)
logs.append("=== 전처리 완료 요약 ===")
logs.append("="*50)
logs.append(f"원본:  9,760행 → 최종: {df_out.shape[0]}행")
logs.append(f"상권:  원본 1,139개 → 최종 {df_out['상권_코드'].nunique()}개")
logs.append(f"모델 X: {len(X_COLS)}개 변수 (수요 6개 + 분기더미 {len(quarter_dummies)}개 + 유형더미 {len(type_dummies)}개)")
logs.append(f"모델 Y: y_log (log1p 변환)")
logs.append(f"모델:  Pooled OLS (VIF 최대 3.28 → Ridge 불필요)")
logs.append("")
logs.append("Track A 수요 변수 (표준화 후):")
for i, v in enumerate(DEMAND_VARS, 1):
    logs.append(f"  {i}. {v}")

log_text = "\n".join(logs)
with open(LOG_PATH, 'w', encoding='utf-8') as f:
    f.write(log_text)

print(log_text)
print(f"\n저장: {OUT_PATH}")
print(f"로그: {LOG_PATH}")
