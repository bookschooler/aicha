import pandas as pd

# 1. 파일 불러오기
# 주소록 (Master) -> cp949
df_master = pd.read_csv('to_map.csv', encoding='utf-8')
# 매출장부 (Sales) -> utf-8
df_sales = pd.read_csv('sales.csv', encoding='utf-8')

# ---------------------------------------------------------
# 🚨 [쏘피의 발견!] 이름표 바꾸기 (Rename)
# sales 파일의 'TRDAR_CD'를 '상권_코드'로 변경합니다.
# ---------------------------------------------------------
df_sales.rename(columns={'TRDAR_CD': '상권_코드'}, inplace=True)


# 2. [주소록]에서 필요한 정보만 쏙 골라내기
cols_to_keep = ['상권_코드', '상권_코드_명', '자치구_코드_명', '행정동_코드_명', '엑스좌표_값', '와이좌표_값']
# 혹시 주소록 파일 컬럼명이 다르면 여기서도 에러날 수 있으니 확인!
# 만약 주소록도 영어라면(TRDAR_CD_NM 등) 그것도 rename 해주거나 cols_to_keep을 영어로 바꿔야 해.
# 일단 쏘피가 '상권_코드'라고 했으니 한글이라 믿고 진행할게!

df_master_clean = df_master[cols_to_keep]
df_master_clean = df_master_clean.drop_duplicates(subset=['상권_코드'])

# 3. 대망의 Merge (합치기!)
# 이제 둘 다 '상권_코드'라는 명찰을 달고 있으니 서로 알아보고 합체 가능!
df_final = pd.merge(df_sales, df_master_clean, on='상권_코드', how='left')

# 4. 결과 확인
print(f"합치기 전 매출 데이터 개수: {len(df_sales)}개")
print(f"합친 후 최종 데이터 개수: {len(df_final)}개")
print("-" * 30)
# 컬럼 이름이 바뀌었으니 확인해봐!
print(df_final[['상권_코드', '상권_코드_명', '행정동_코드_명', '점포당_평균_매출']].head())

# 5. 파일로 저장
df_final.to_csv('merged_sales.csv', index=False, encoding='utf-8-sig')
print("✅ 'merged_sales.csv' 저장 완료! 고생했어 쏘피!")