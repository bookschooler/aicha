import pandas as pd
import numpy as np

df = pd.read_csv('work/34_oof_residuals.csv', encoding='utf-8-sig')
latest = df['기준_년분기_코드'].max()
df_l = df[df['기준_년분기_코드'] == latest].copy()

# 예측값 상위 20% = 고매출 상권
top20_threshold = df_l['oof_pred'].quantile(0.8)
df_high = df_l[df_l['oof_pred'] >= top20_threshold].copy()

# 과소예측 Top10 (잔차 가장 음수)
under = df_high.sort_values('oof_residual').head(10)[['상권_코드_명', 'oof_pred', 'oof_residual']]

lines = ['=== 고매출 상권 중 과소예측 Top10 (잔차 음수 큰 순) ===']
for _, r in under.iterrows():
    lines.append(f"{r['상권_코드_명']:<30} 예측(log)={r['oof_pred']:.2f}  잔차={r['oof_residual']:+.3f}")

lines.append('')
lines.append('=== 전체 고매출 상권 잔차 통계 ===')
lines.append(f"고매출 상권 수: {len(df_high)}개")
lines.append(f"잔차 평균: {df_high['oof_residual'].mean():+.3f}")
lines.append(f"잔차 음수 비율: {(df_high['oof_residual'] < 0).mean()*100:.1f}%")

with open('work/tmp_underpredict.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done')
