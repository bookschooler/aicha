import pandas as pd

df = pd.read_csv('y_final.csv', encoding='utf-8')
print(df.head())
print(df.shape)
print('\n'.join(df.columns))
print(df.dtypes)