import pandas as pd

# 1. 파일 불러오기
print("📂 'living_pop.csv' 정밀 검사 중...")
df = pd.read_csv('living_pop.csv', encoding='utf-8-sig')

# 2. [검사 1] 분기별 '총 상주인구 합계' 비교
# (이 숫자가 1명이라도 다르면 데이터는 변하고 있는 것!)
print("\n📊 1. 분기별 서울시 총 상주인구 변화 (꿈틀거리는지 확인!)")
print("-" * 50)
quarterly_sum = df.groupby('기준_년분기_코드')['총_상주인구_수'].sum()
print(quarterly_sum)

# 3. [검사 2] 변화량 체크 (Diff)
# (이번 분기 - 저번 분기 = 0 이면 복사한 것임)
print("\n📉 2. 전 분기 대비 변화량 (0이 아니어야 정상!)")
print("-" * 50)
diffs = quarterly_sum.diff()
print(diffs)

# 4. [검사 3] 특정 핫플레이스(예: 강남역 쪽) 콕 집어서 보기
# 상권 코드 하나를 아무거나 잡아서 추적
target_code = df['상권_코드'].iloc[0] # 첫 번째 상권 아무거나
target_name = df[df['상권_코드'] == target_code]['상권_코드_명'].iloc[0]

print(f"\n🕵️‍♀️ 3. '{target_name}' 상권의 시간 흐름 추적")
print("-" * 50)
sample_trend = df[df['상권_코드'] == target_code][['기준_년분기_코드', '총_상주인구_수', '남성_상주인구_수', '여성_상주인구_수']]
print(sample_trend)
