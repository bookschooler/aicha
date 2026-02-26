"""
21_merge_supply.py
공급지표 전체 병합 + 조합지표 계산

[파일 1] composite_indicators.csv
    - 조합지표 4개 (분기 × 상권)
    - 공급갭_지수      = 카페음료_점포수 / (찻집_수 + 1)
    - 유동밀도_지수    = 여성_유동인구_수 / (찻집_수 + 1)
    - 상주밀도_지수    = 여성_상주인구_수 / (찻집_수 + 1)
    - 여가소비_지수    = 여가_지출_총금액 / (찻집_수 + 1)

[파일 2] y_supply_merge.csv
    - y_demand_merge.csv 기준
    + 원지표 3개: 카페음료_점포수, 찻집_수, 스타벅스_리저브_수
    + 조합지표 4개
"""
import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

os.chdir('/teamspace/studios/this_studio/aicha')

# ──────────────────────────────────────────
# 1. 기준 데이터 로드
# ──────────────────────────────────────────
base = pd.read_csv('y_demand_merge.csv')
print(f"기준 데이터: {base.shape}")

# ──────────────────────────────────────────
# 2. 원지표 3개 병합
# ──────────────────────────────────────────

# 2-1. 카페음료_점포수 (분기 매칭)
comp = pd.read_csv('competitor.csv')
cafe = comp[['기준_년분기_코드', '상권_코드', '점포_수']].rename(
    columns={'점포_수': '카페음료_점포수'}
)
base = base.merge(cafe, on=['기준_년분기_코드', '상권_코드'], how='left')
print(f"카페음료_점포수 병합 → {base.shape} | 결측: {base['카페음료_점포수'].isna().sum()}행")

# 2-2. 찻집_수 (단면 → 전 분기 동일)
tea = pd.read_csv('tea_shop_count.csv')[['상권_코드', '찻집_수']]
base = base.merge(tea, on='상권_코드', how='left')
base['찻집_수'] = base['찻집_수'].fillna(0).astype(int)
print(f"찻집_수 병합       → {base.shape}")

# 2-3. 스타벅스_리저브_수 (단면 → 전 분기 동일)
sb = pd.read_csv('starbucks_reserve_count.csv')[['상권_코드', '스타벅스_리저브_수']]
base = base.merge(sb, on='상권_코드', how='left')
base['스타벅스_리저브_수'] = base['스타벅스_리저브_수'].fillna(0).astype(int)
print(f"스타벅스_리저브_수 병합 → {base.shape}")

# ──────────────────────────────────────────
# 3. 조합지표 4개 계산
# ──────────────────────────────────────────
denom = base['찻집_수'] + 1

base['공급갭_지수']   = base['카페음료_점포수']    / denom   # 카페 수요 대비 찻집 공급 부족
base['유동밀도_지수'] = base['여성_유동인구_수']   / denom   # 찻집당 잠재 워크인 고객
base['상주밀도_지수'] = base['여성_상주인구_수']   / denom   # 찻집당 잠재 단골 고객
base['여가소비_지수'] = base['여가_지출_총금액']   / denom   # 찻집당 여가 소비력

composite_cols = ['공급갭_지수', '유동밀도_지수', '상주밀도_지수', '여가소비_지수']

print(f"\n=== 조합지표 기술통계 ===")
print(base[composite_cols].describe().applymap(lambda x: f'{x:,.1f}'))

# ──────────────────────────────────────────
# 4. 파일 1: composite_indicators.csv (조합지표만)
# ──────────────────────────────────────────
key_cols = ['기준_년분기_코드', '상권_코드', '상권_코드_명']
df_composite = base[key_cols + ['찻집_수'] + composite_cols].copy()

df_composite.to_csv('composite_indicators.csv', index=False, encoding='utf-8-sig')
print(f"\n[저장] composite_indicators.csv ({df_composite.shape[0]}행 × {df_composite.shape[1]}열)")
print(df_composite.head(3).to_string(index=False))

# ──────────────────────────────────────────
# 5. 파일 2: y_supply_merge.csv (전체 병합)
# ──────────────────────────────────────────
supply_cols = ['카페음료_점포수', '찻집_수', '스타벅스_리저브_수'] + composite_cols
print(f"\n=== 공급지표 샘플 (상위 3행) ===")
print(base[key_cols + supply_cols].head(3).to_string(index=False))

base.to_csv('y_supply_merge.csv', index=False, encoding='utf-8-sig')
print(f"\n[저장] y_supply_merge.csv ({base.shape[0]}행 × {base.shape[1]}열)")
print(f"\n추가된 공급지표 컬럼 ({len(supply_cols)}개): {supply_cols}")
