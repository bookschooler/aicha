import requests, os, time, json
from dotenv import load_dotenv
load_dotenv('/teamspace/studios/this_studio/aicha/.env')

CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
headers = {
    'X-Naver-Client-Id': CLIENT_ID,
    'X-Naver-Client-Secret': CLIENT_SECRET,
    'Content-Type': 'application/json'
}

def datalab_avg(keywords):
    url = 'https://openapi.naver.com/v1/datalab/search'
    body = {
        'startDate': '2023-01-01',
        'endDate': '2024-12-31',
        'timeUnit': 'month',
        'keywordGroups': [{'groupName': kw, 'keywords': [kw]} for kw in keywords]
    }
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=5)
    if r.status_code != 200:
        print('ERROR:', r.status_code, r.text[:100])
        return {}
    results = {}
    for item in r.json().get('results', []):
        avg = sum(d['ratio'] for d in item['data']) / len(item['data'])
        results[item['title']] = round(avg, 2)
    return results

pairs = [
    ('연남동 카페', '홍대 카페'),
    ('성수동 카페', '성수 카페'),
    ('이태원동 카페', '이태원 카페'),
    ('삼청동 카페', '경복궁 카페'),
    ('인사동 카페', '종로3가 카페'),
]

print(f'{"키워드1":22s} {"지수1":>6s}  |  {"키워드2":22s} {"지수2":>6s}  →  승자')
print('-'*80)
for k1, k2 in pairs:
    res = datalab_avg([k1, k2])
    v1, v2 = res.get(k1, 0), res.get(k2, 0)
    print(f'{k1:22s} {v1:>6.2f}  |  {k2:22s} {v2:>6.2f}  →  {k1 if v1>=v2 else k2}')
    time.sleep(0.3)
