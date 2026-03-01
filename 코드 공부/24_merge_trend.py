"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
24_merge_trend.py — 트렌드 지표를 최종 데이터셋에 병합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  지금까지 만든 수요+공급 통합 데이터에 트렌드 지표 4개 최종 추가
  → 모든 지표가 담긴 최종 분석 데이터셋 완성

입력: y_demand_supply_merge.csv (150열 기존 데이터)
      trend_index.csv            (트렌드 지표 4개, 23번 산출)
출력: y_demand_supply_trend_merge.csv (154열 최종 데이터셋, 9,760행)
"""

import os            # 작업 디렉토리 변경 (17번에서 상세 설명)
import pandas as pd  # 데이터프레임 라이브러리 (17번에서 상세 설명)

os.chdir('/teamspace/studios/this_studio/aicha')


# ══════════════════════════════════════════════════════
# 파일 로드
# ══════════════════════════════════════════════════════
print("▶ 파일 로드 중...")
base  = pd.read_csv('y_demand_supply_merge.csv')  # 수요+공급 통합 데이터 (150열)
trend = pd.read_csv('trend_index.csv')             # 트렌드 지표 4개

# 병합 키 컬럼의 데이터 타입을 정수형으로 통일 (타입 불일치 시 JOIN 실패 방지)
base['기준_년분기_코드']  = base['기준_년분기_코드'].astype(int)   # 기준 데이터 분기코드
base['상권_코드']        = base['상권_코드'].astype(int)            # 기준 데이터 상권코드
trend['기준_년분기_코드'] = trend['기준_년분기_코드'].astype(int)   # 트렌드 데이터 분기코드
trend['상권_코드']       = trend['상권_코드'].astype(int)           # 트렌드 데이터 상권코드
#  └ Series.astype(int): 데이터 타입을 정수로 변환 (21번에서 상세 설명)
#    · CSV에서 읽으면 기본 int64지만, 파일마다 타입이 달라질 수 있어 명시적 변환 권장

print(f"  base : {base.shape}")    # (9760, 150) 예상
print(f"  trend: {trend.shape}")   # (9760, 6) 예상


# ══════════════════════════════════════════════════════
# 병합
# ══════════════════════════════════════════════════════
merged = base.merge(trend, on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ df.merge(다른df, on=[키1, 키2], how='left')
#    · 두 DataFrame을 분기코드+상권코드 복합 키로 병합 (21번에서 상세 설명)
#    · how='left': base의 모든 9,760행 유지
#      (trend에 해당 분기+상권 없으면 NaN으로 채움)
#    · 이 시점에서 최종 데이터셋 완성: Y변수 + 수요지표 + 공급지표 + 트렌드지표

print(f"\n▶ 병합 결과: {merged.shape}")  # (9760, 154) 예상


# ══════════════════════════════════════════════════════
# 저장
# ══════════════════════════════════════════════════════
merged.to_csv('y_demand_supply_trend_merge.csv', index=False, encoding='utf-8-sig')
#  └ df.to_csv(경로, index=False, encoding='utf-8-sig')
#    · 최종 데이터셋을 CSV로 저장 (17번에서 상세 설명)
#    · 이 파일이 이후 EDA와 회귀분석의 기준 파일이 됨

print("✅ y_demand_supply_trend_merge.csv 저장 완료")


# ══════════════════════════════════════════════════════
# 검증
# ══════════════════════════════════════════════════════
print(f"\n[컬럼 목록 (마지막 10개)]")
print(merged.columns.tolist()[-10:])
#  └ df.columns: 컬럼명 Index 객체 반환
#  └ .tolist(): Index → 파이썬 리스트로 변환
#  └ [-10:]: 리스트 끝에서 10개 (슬라이싱)

print(f"\n[트렌드 컬럼 결측 현황]")
trend_cols = ['카페_검색지수', '검색량_성장률', '카페_개업률', '유동인구_성장률']
print(merged[trend_cols].isnull().sum())
#  └ df[컬럼목록].isnull().sum(): 각 컬럼별 결측치 수 (23번에서 상세 설명)

print(f"\n[샘플 5행]")
print(merged[['기준_년분기_코드', '상권_코드'] + trend_cols].head(5).to_string(index=False))
#  └ df[[키컬럼들] + [트렌드컬럼들]].head(5): 확인에 필요한 컬럼만 선택해서 미리보기
