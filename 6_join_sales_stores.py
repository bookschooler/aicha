import pandas as pd

# ==========================================
# 1. 파일 불러오기
# ==========================================
print("📂 1. 파일 로딩 중...")
df_sales = pd.read_csv('sales.csv', encoding='utf-8')
df_stores = pd.read_csv('stores.csv', encoding='utf-8')

# ==========================================
# 2. stores 파일에서 필요한 컬럼만 쏙 가져오기
# ==========================================
# (점포수, 년도분기, 상권코드명, 상권코드)
# ※ stores.csv의 실제 컬럼명(한글)을 기준으로 가져옵니다.
selected_cols = ['점포수', '기준_분기_코드', '상권_코드_명', '상권_코드']
df_stores = df_stores[selected_cols]

print(f"✅ 2. 컬럼 선택 완료: {len(df_stores)}행")

# ==========================================
# 3. 컬럼 이름을 sales 테이블 스타일(영어)로 바꾸기
# ==========================================
# sales.csv의 컬럼명: TRDAR_CD(상권코드), STDR_YYQU_CD(분기), TRDAR_CD_NM(이름)
rename_map = {
    '점포수': 'STORE_CO',           # 점포수는 영어로 STORE_CO로 명명
    '기준_분기_코드': 'STDR_YYQU_CD',
    '상권_코드_명': 'TRDAR_CD_NM',
    '상권_코드': 'TRDAR_CD'
}
df_stores.rename(columns=rename_map, inplace=True)

print("✅ 3. 컬럼명 변경 완료 (한글 -> 영어)")

# ==========================================
# 4. Left Join (Merge) 수행
# ==========================================
# 안전한 병합을 위해 Key 컬럼을 문자열(str)로 통일
df_sales['TRDAR_CD'] = df_sales['TRDAR_CD'].astype(str)
df_stores['TRDAR_CD'] = df_stores['TRDAR_CD'].astype(str)
df_sales['STDR_YYQU_CD'] = df_sales['STDR_YYQU_CD'].astype(str)
df_stores['STDR_YYQU_CD'] = df_stores['STDR_YYQU_CD'].astype(str)

print("⚡ 4. 데이터 병합 중 (Left Join)...")

# 쏘피 요청: '상권코드' & '년도분기' 중심으로 합치기
# (이름보다는 코드로 합치는 게 훨씬 정확해서 TRDAR_CD를 사용했어!)
df_merged = pd.merge(
    df_sales, 
    df_stores[['TRDAR_CD', 'STDR_YYQU_CD', 'STORE_CO']], # 이름(NM)은 sales에도 있으니 점포수만 가져옴
    on=['TRDAR_CD', 'STDR_YYQU_CD'], 
    how='left'
)

# [추가] 점포수 NaN 처리 (비어있으면 1로 채움)
df_merged['STORE_CO'] = df_merged['STORE_CO'].fillna(1)
df_merged.loc[df_merged['STORE_CO'] == 0, 'STORE_CO'] = 1

# ==========================================
# 5. 저장하기
# ==========================================
output_filename = 'y_final.csv'
df_merged.to_csv(output_filename, index=False, encoding='utf-8')

print("-" * 30)
print(f"🎉 5. 모든 작업 완료! 파일 저장됨: {output_filename}")
print(df_merged[['STDR_YYQU_CD', 'TRDAR_CD_NM', 'STORE_CO', 'THSMON_SELNG_AMT']].head())