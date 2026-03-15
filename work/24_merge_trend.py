#!/usr/bin/env python3
"""
24_merge_trend.py

trend_index.csv + y_demand_supply_merge.csv
→ y_demand_supply_trend_merge.csv (9,760행 × 154열 예상)
"""

import os
import pandas as pd

os.chdir('/teamspace/studios/this_studio/aicha')

# ── 로드 ─────────────────────────────────────────────────────────
print("▶ 파일 로드 중...")
base  = pd.read_csv('y_demand_supply_merge.csv')
trend = pd.read_csv('trend_index.csv')

base['기준_년분기_코드']  = base['기준_년분기_코드'].astype(int)
base['상권_코드']        = base['상권_코드'].astype(int)
trend['기준_년분기_코드'] = trend['기준_년분기_코드'].astype(int)
trend['상권_코드']       = trend['상권_코드'].astype(int)

print(f"  base : {base.shape}")
print(f"  trend: {trend.shape}")

# ── 병합 ─────────────────────────────────────────────────────────
merged = base.merge(trend, on=['기준_년분기_코드', '상권_코드'], how='left')
print(f"\n▶ 병합 결과: {merged.shape}")

# ── 저장 ─────────────────────────────────────────────────────────
merged.to_csv('y_demand_supply_trend_merge.csv', index=False, encoding='utf-8-sig')
print("✅ y_demand_supply_trend_merge.csv 저장 완료")

# ── 검증 ─────────────────────────────────────────────────────────
print(f"\n[컬럼 목록 (마지막 10개)]")
print(merged.columns.tolist()[-10:])

print(f"\n[트렌드 컬럼 결측 현황]")
trend_cols = ['카페_검색지수', '검색량_성장률', '카페_개업률', '유동인구_성장률']
print(merged[trend_cols].isnull().sum())

print(f"\n[샘플 5행]")
print(merged[['기준_년분기_코드', '상권_코드'] + trend_cols].head(5).to_string(index=False))
