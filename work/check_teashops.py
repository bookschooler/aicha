import pandas as pd
df = pd.read_csv('api/teashops.csv')
print('컬럼:', list(df.columns))
print()
# 강남역 상권 찻집
sample = df[df['상권_코드_명'] == '강남역']
print(f'강남역 찻집: {len(sample)}개')
print(sample[['가게명','도로명주소']].to_string())
print()
# 홍대소상공인상점가
sample2 = df[df['상권_코드_명'] == '홍대소상공인상점가']
print(f'홍대소상공인상점가 찻집: {len(sample2)}개')
print(sample2[['가게명','도로명주소']].to_string())
with open('station_check.txt', 'w', encoding='utf-8') as f:
    f.write(f"컬럼: {list(df.columns)}\n\n")
    f.write(f"강남역 찻집:\n{sample[['가게명','도로명주소']].to_string()}\n\n")
    f.write(f"홍대소상공인상점가 찻집:\n{sample2[['가게명','도로명주소']].to_string()}\n")
