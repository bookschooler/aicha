import pandas as pd

df = pd.read_csv("aicha/apt.csv")

# 기본 형태
print("=== shape ===")
print(df.shape)

# 컬럼 타입 및 결측치
print("\n=== info ===")
df.info()

# 수치형 기초 통계
print("\n=== describe ===")
print(df.describe())

# 첫 5행
print("\n=== head ===")
print(df.head())

# 결측치 확인
print("\n=== 결측치 ===")
print(df.isnull().sum())

# 중복행 확인
print("\n=== 중복행 수 ===")
print(df.duplicated().sum())
