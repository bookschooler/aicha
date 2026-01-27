import pandas as pd

# 1. 파일 불러오기
# (경로는 쏘피 컴퓨터에 맞춰서!)
# df_master = 상권영역(주소록) 파일
# df_sales = 추정매출(매출장부) 파일
df_master = pd.read_csv('to_map.csv', encoding='cp949')
df_sales = pd.read_csv('sales.csv', encoding='utf-8')

# 2. '상권 코드' 개수 세어보기 (중복 제거하고 유니크한 개수만!)
master_count = df_master['상권_코드'].nunique()
sales_count = df_sales['TRDAR_CD'].nunique()

print(f"서울시 전체 상권 개수(족보): {master_count}개")
print(f"내 매출 파일에 있는 상권 개수: {sales_count}개")

# 3. 누락된 상권이 있는지 확인
# (족보에는 있는데 매출 파일에는 없는 곳 찾기)
missing_areas = set(df_master['상권_코드']) - set(df_sales['TRDAR_CD'])
print(f"매출 데이터가 없는 상권 개수: {len(missing_areas)}개")