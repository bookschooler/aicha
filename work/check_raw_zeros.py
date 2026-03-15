import pandas as pd

df = pd.read_csv('api/unified_ranking.csv')

# 소득금액이 가장 낮은 상권 5개
low_income = df.nsmallest(5, '월_평균_소득_금액_raw')[['상권_코드_명', '월_평균_소득_금액_raw', '총_가구_수_raw']]

# 가구수가 가장 낮은 상권 5개
low_household = df.nsmallest(5, '총_가구_수_raw')[['상권_코드_명', '총_가구_수_raw', '월_평균_소득_금액_raw']]

with open('col_check.txt', 'w', encoding='utf-8') as f:
    f.write("=== 소득금액 낮은 상위 5개 ===\n")
    for _, r in low_income.iterrows():
        val = int(r['월_평균_소득_금액_raw'])
        f.write(f"  {r['상권_코드_명']}: {val:,}원 → 월 {val//10000:,}만원 / 가구수={int(r['총_가구_수_raw']):,}\n")

    f.write("\n=== 가구수 낮은 상위 5개 ===\n")
    for _, r in low_household.iterrows():
        val = int(r['총_가구_수_raw'])
        f.write(f"  {r['상권_코드_명']}: {val:,}가구 / 소득={int(r['월_평균_소득_금액_raw'])//10000:,}만원\n")

    # 소득금액 단위 확인
    f.write(f"\n전체 소득금액 중앙값: {df['월_평균_소득_금액_raw'].median()/10000:.0f}만원\n")
    f.write(f"전체 가구수 중앙값: {df['총_가구_수_raw'].median():.0f}가구\n")

print('Done')
