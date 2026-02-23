import pandas as pd

# 데이터 로드
y_pop = pd.read_csv('y_pop_income.csv')
apt = pd.read_csv('apt.csv')

print("=== y_pop_income.csv ===")
print(f"shape: {y_pop.shape}")
print(f"기준_년분기_코드 범위: {y_pop['기준_년분기_코드'].min()} ~ {y_pop['기준_년분기_코드'].max()}")

print("\n=== apt.csv ===")
print(f"shape: {apt.shape}")
print(f"기준_년분기_코드 범위: {apt['기준_년분기_코드'].min()} ~ {apt['기준_년분기_코드'].max()}")

# apt 중복 행 제거 (동일 데이터가 9번 반복되어 있음)
apt = apt.drop_duplicates()
print(f"\napt 중복 제거 후 shape: {apt.shape}")

# apt 중복 컬럼 제거 (상권_코드_명 등 y_pop에도 있음)
apt_cols_to_drop = [col for col in apt.columns if col in y_pop.columns and col not in ['기준_년분기_코드', '상권_코드']]
apt_clean = apt.drop(columns=apt_cols_to_drop)
print(f"apt에서 제거된 중복 컬럼: {apt_cols_to_drop}")

# 기준_년분기_코드, 상권_코드 기준으로 left join
merged = pd.merge(y_pop, apt_clean, on=['기준_년분기_코드', '상권_코드'], how='left')

print(f"\n=== merge 결과 ===")
print(f"shape: {merged.shape}")
print(f"매칭된 행 수: {merged['아파트_단지_수'].notna().sum()} / {len(merged)}")

# 저장
merged.to_csv('merge_demand.csv', index=False)
print("\n✓ merge_demand.csv 저장 완료")

# ─────────────────────────────────────────────
# facilities.csv → y_demand_merge.csv에 merge
# ─────────────────────────────────────────────

# 데이터 로드
y_demand = pd.read_csv('y_demand_merge.csv')
fac = pd.read_csv('facilities.csv')

print("\n=== y_demand_merge.csv ===")
print(f"shape: {y_demand.shape}")

print("\n=== facilities.csv ===")
print(f"shape: {fac.shape}")

# facilities 중복 행 제거 (동일 데이터가 9번 반복되어 있음)
fac = fac.drop_duplicates()
print(f"\nfacilities 중복 제거 후 shape: {fac.shape}")

# facilities 중복 컬럼 제거
fac_cols_to_drop = [col for col in fac.columns if col in y_demand.columns and col not in ['기준_년분기_코드', '상권_코드']]
fac_clean = fac.drop(columns=fac_cols_to_drop)
print(f"facilities에서 제거된 중복 컬럼: {fac_cols_to_drop}")

# 기준_년분기_코드, 상권_코드 기준으로 left join
y_demand_merged = pd.merge(y_demand, fac_clean, on=['기준_년분기_코드', '상권_코드'], how='left')

print(f"\n=== merge 결과 ===")
print(f"shape: {y_demand_merged.shape}")
print(f"매칭된 행 수: {y_demand_merged['집객시설_수'].notna().sum()} / {len(y_demand_merged)}")

# y_demand_merge.csv에 덮어쓰기
y_demand_merged.to_csv('y_demand_merge.csv', index=False)
print("\n✓ y_demand_merge.csv 저장 완료")
