import pandas as pd
import re

_LINE_NAMES = r'(\d+호선|경의중앙선|신분당선|경춘선|수인분당선|공항철도|경강선|서해선)'

def _format_subway(raw) -> str:
    if not raw or (isinstance(raw, float) and raw != raw):
        return ''
    tokens = re.findall(_LINE_NAMES + r'\s+(\S+역)', str(raw))
    seen, result = set(), []
    for line, station in tokens:
        key = f"{line} {station}"
        if key not in seen:
            seen.add(key)
            result.append(key)
    return ', '.join(result)

df = pd.read_csv('api/unified_ranking.csv')
sample = df[df['지하철_역_목록'].notna()][['상권_코드_명', '지하철_역_목록']].head(10)

results = []
for _, row in sample.iterrows():
    raw = row['지하철_역_목록']
    formatted = _format_subway(raw)
    results.append(f"{row['상권_코드_명']}: {formatted or '(파싱 실패)'}")

with open('test_subway_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))
print('Done')
