import pandas as pd
import re

df = pd.read_csv('api/unified_ranking.csv')

# 5개 수요변수 백분위
raw_to_pct = {
    '집객시설_수_raw':       '집객시설_수_pct',
    '총_직장_인구_수_raw':   '총_직장_인구_수_pct',
    '월_평균_소득_금액_raw': '월_평균_소득_금액_pct',
    '총_가구_수_raw':       '총_가구_수_pct',
    '카페_검색지수_raw':     '카페_검색지수_pct',
}
for raw_col, pct_col in raw_to_pct.items():
    if raw_col in df.columns:
        df[pct_col] = df[raw_col].rank(pct=True, na_option='keep') * 100
    else:
        df[pct_col] = 50.0

# 지하철 노선 수 + 백분위
def count_lines(subway_str):
    if not subway_str or (isinstance(subway_str, float) and subway_str != subway_str):
        return 0
    lines = set(re.findall(
        r'(\d+호선|경의중앙선|신분당선|경춘선|수인분당선|공항철도|경강선|서해선)',
        str(subway_str)
    ))
    return len(lines)

if '지하철_역_목록' in df.columns:
    df['지하철_노선_수_raw'] = df['지하철_역_목록'].apply(count_lines)
else:
    df['지하철_노선_수_raw'] = 0
df['지하철_노선_수_pct'] = df['지하철_노선_수_raw'].rank(pct=True, na_option='keep') * 100

df.to_csv('api/unified_ranking.csv', index=False, encoding='utf-8-sig')

with open('precompute_pct_log.txt', 'w', encoding='utf-8') as f:
    f.write(f'저장 완료: {len(df)}행, {len(df.columns)}컬럼\n')
    pct_cols = [c for c in df.columns if '_pct' in c]
    raw_cols = [c for c in df.columns if '_raw' in c]
    f.write(f'pct 컬럼: {pct_cols}\n')
    f.write(f'raw 컬럼: {raw_cols}\n')
    for col in pct_cols:
        f.write(f'  {col}: min={df[col].min():.1f}, max={df[col].max():.1f}, null={df[col].isna().sum()}\n')
print('Done')
