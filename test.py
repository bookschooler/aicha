import pandas as pd

# sales.csv 파일 읽기 (인코딩은 아까 성공한 utf-8로!)
df_sales = pd.read_csv('sales.csv', encoding='utf-8')

print("=== [sales.csv]의 모든 컬럼 이름 ===")
print(df_sales.columns.tolist())  # 리스트 형태로 전체 출력