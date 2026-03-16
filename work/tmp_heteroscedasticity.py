import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('work/34_oof_residuals.csv', encoding='utf-8-sig')

# 전체 데이터
resid_all = df['oof_residual'].dropna()
pred_all = df['oof_pred'].dropna()

# 강남역, 서초동성당 제외
exclude = ['강남역', '서초동성당']
df_ex = df[~df['상권_코드_명'].isin(exclude)].copy()
resid_ex = df_ex['oof_residual'].dropna()
pred_ex = df_ex['oof_pred'].dropna()

# Breusch-Pagan 대신 간단히: 예측값 구간별 잔차 분산 비교
def variance_by_quartile(pred, resid, label):
    lines = [f'=== {label} ===']
    q25 = pred.quantile(0.25)
    q50 = pred.quantile(0.50)
    q75 = pred.quantile(0.75)

    g1 = resid[pred <= q25]
    g2 = resid[(pred > q25) & (pred <= q50)]
    g3 = resid[(pred > q50) & (pred <= q75)]
    g4 = resid[pred > q75]

    lines.append(f'  Q1(저매출) 잔차 표준편차: {g1.std():.3f}')
    lines.append(f'  Q2        잔차 표준편차: {g2.std():.3f}')
    lines.append(f'  Q3        잔차 표준편차: {g3.std():.3f}')
    lines.append(f'  Q4(고매출) 잔차 표준편차: {g4.std():.3f}')
    lines.append(f'  고매출/저매출 분산 비율: {g4.std()/g1.std():.2f}배')
    return lines

lines = []
lines += variance_by_quartile(pred_all, resid_all, '전체 데이터')
lines.append('')
lines += variance_by_quartile(pred_ex, resid_ex, '강남역 + 서초동성당 제외')

with open('work/tmp_heteroscedasticity.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done')
