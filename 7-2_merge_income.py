import pandas as pd

print("=" * 50, flush=True)
print("  y_final.csv <- income.csv LEFT JOIN 시작", flush=True)
print("=" * 50, flush=True)

# ==========================================
# 1. 파일 불러오기
# ==========================================
print("\n[1/4] y_final.csv 로딩 중...", flush=True)
df_y = pd.read_csv('y_final.csv', encoding='utf-8')
print(f"  OK y_final  : {df_y.shape[0]:,}행 x {df_y.shape[1]}열", flush=True)

print("[1/4] income.csv 로딩 중...", flush=True)
df_income = pd.read_csv('income.csv', encoding='utf-8')
print(f"  OK income   : {df_income.shape[0]:,}행 x {df_income.shape[1]}열", flush=True)

# ==========================================
# 2. income 컬럼 선택
# ==========================================
print("\n[2/4] income 컬럼 정리 중...", flush=True)
income_cols = [
    '기준_년분기_코드', '상권_코드',
    '월_평균_소득_금액', '소득_구간_코드',
    '지출_총금액',
    '식료품_지출_총금액', '의류_신발_지출_총금액', '생활용품_지출_총금액',
    '의료비_지출_총금액', '교통_지출_총금액', '여가_지출_총금액',
    '문화_지출_총금액', '교육_지출_총금액', '유흥_지출_총금액'
]
df_income = df_income[income_cols]
print(f"  OK 선택된 컬럼 {len(income_cols)}개 (키 2개 + 소득/지출 12개)", flush=True)

# ==========================================
# 3. Key 타입 통일
# ==========================================
print("\n[3/4] Key 타입 str 변환 중...", flush=True)
df_y['기준_년분기_코드'] = df_y['기준_년분기_코드'].astype(str)
df_y['상권_코드'] = df_y['상권_코드'].astype(str)
df_income['기준_년분기_코드'] = df_income['기준_년분기_코드'].astype(str)
df_income['상권_코드'] = df_income['상권_코드'].astype(str)
print("  OK 완료", flush=True)

# ==========================================
# 4. Left Join
# ==========================================
print("\n[4/4] LEFT JOIN 수행 중...", flush=True)
df_merged = pd.merge(
    df_y,
    df_income,
    on=['기준_년분기_코드', '상권_코드'],
    how='left'
)
matched = df_merged['월_평균_소득_금액'].notna().sum()
total = len(df_merged)
print(f"  OK 병합 완료: {matched:,} / {total:,} 매칭 ({matched/total*100:.1f}%)", flush=True)

print("\n  저장 중...", flush=True)
df_merged.to_csv('y_final_income.csv', index=False, encoding='utf-8-sig')

print("\n" + "=" * 50, flush=True)
print("  완료!", flush=True)
print(f"  최종 shape : {df_merged.shape[0]:,}행 x {df_merged.shape[1]}열", flush=True)
print("=" * 50, flush=True)
print(f"  저장 파일 : y_final_income.csv", flush=True)
print(df_merged[['기준_년분기_코드', '상권_코드_명', '월_평균_소득_금액', '지출_총금액']].head().to_string(), flush=True)
