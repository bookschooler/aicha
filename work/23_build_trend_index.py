#!/usr/bin/env python3
"""
23_build_trend_index.py

트렌드 지표 4개 통합 → trend_index.csv
  1. 카페_검색지수     : search_trend_index.csv (22번 산출)
  2. 검색량_성장률     : search_trend_index.csv (QoQ, %)
  3. 카페_개업률       : competitor.csv 의 개업_율 컬럼
  4. 유동인구_성장률   : y_demand_supply_merge.csv 의 총_유동인구_수 QoQ 성장률 (%)
"""

import os
import pandas as pd
import numpy as np

os.chdir('/teamspace/studios/this_studio/aicha')

# ── 1. 검색 트렌드 로드 ──────────────────────────────────────────
print("▶ 검색 트렌드 로드...")
search = pd.read_csv('search_trend_index.csv')
search['기준_년분기_코드'] = search['기준_년분기_코드'].astype(int)
search['상권_코드']       = search['상권_코드'].astype(int)
print(f"  {search.shape} | 분기: {sorted(search['기준_년분기_코드'].unique())}")

# ── 2. 카페 개업률 ───────────────────────────────────────────────
print("▶ 카페 개업률 로드 (competitor.csv)...")
comp = pd.read_csv('competitor.csv')
comp = comp[['기준_년분기_코드', '상권_코드', '개업_율']].copy()
comp.rename(columns={'개업_율': '카페_개업률'}, inplace=True)
comp['기준_년분기_코드'] = comp['기준_년분기_코드'].astype(int)
comp['상권_코드']       = comp['상권_코드'].astype(int)
print(f"  {comp.shape}")

# ── 3. 유동인구 성장률 ───────────────────────────────────────────
print("▶ 유동인구 성장률 산출 (y_demand_supply_merge.csv)...")
ydm = pd.read_csv('y_demand_supply_merge.csv',
                  usecols=['기준_년분기_코드', '상권_코드', '총_유동인구_수'])
ydm['기준_년분기_코드'] = ydm['기준_년분기_코드'].astype(int)
ydm['상권_코드']       = ydm['상권_코드'].astype(int)
ydm = ydm.sort_values(['상권_코드', '기준_년분기_코드'])
ydm['유동인구_성장률'] = (
    ydm.groupby('상권_코드')['총_유동인구_수']
       .pct_change() * 100
)
ydm = ydm[['기준_년분기_코드', '상권_코드', '유동인구_성장률']]
print(f"  {ydm.shape}")

# ── 4. 병합 ─────────────────────────────────────────────────────
print("▶ 병합 중...")
trend = search.merge(comp, on=['기준_년분기_코드', '상권_코드'], how='left')
trend = trend.merge(ydm,  on=['기준_년분기_코드', '상권_코드'], how='left')

cols_order = ['기준_년분기_코드', '상권_코드',
              '카페_검색지수', '검색량_성장률',
              '카페_개업률', '유동인구_성장률']
trend = trend[cols_order].sort_values(['상권_코드', '기준_년분기_코드']).reset_index(drop=True)

# ── 5. 저장 ─────────────────────────────────────────────────────
trend.to_csv('trend_index.csv', index=False, encoding='utf-8-sig')
print(f"\n✅ trend_index.csv 저장 완료: {trend.shape}")
print(trend.head(18).to_string(index=False))

# 결측 요약
print("\n[결측치 현황]")
print(trend.isnull().sum())
