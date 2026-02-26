"""
18b_filter_by_blog.py
네이버 블로그 검색 API로 찻집별 찻잎차 vs 한방차 언급 수 집계
→ 찻잎차 언급 0 + 한방차 언급 있으면 제거 후보로 플래그
결과 저장: tea_shops_scored.csv (dedup 파일 수정 없음)
"""
import pandas as pd
import requests
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv('NAVER_CLIENT_ID')
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
HEADERS = {
    'X-Naver-Client-Id':     CLIENT_ID,
    'X-Naver-Client-Secret': CLIENT_SECRET,
}

# 찻잎차 키워드 (높을수록 유지)
LEAF_KEYWORDS = ['녹차', '홍차', '우롱차', '보이차', '백차', '황차', '다원', '티하우스']
# 한방/허브차 키워드 (높을수록 제거 후보)
HERB_KEYWORDS = ['쌍화차', '생강차', '한방차', '대추차', '모과차', '한방']
# 진행 저장 파일
PROGRESS_FILE = 'blog_filter_progress.json'

# ──────────────────────────────────────────
def search_blog_count(query: str) -> int:
    url = 'https://openapi.naver.com/v1/search/blog'
    params = {'query': query, 'display': 1}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('total', 0)
    except Exception:
        pass
    return -1

def score_shop(name: str) -> dict:
    leaf_total = 0
    herb_total = 0

    for kw in LEAF_KEYWORDS:
        cnt = search_blog_count(f'{name} {kw}')
        if cnt > 0:
            leaf_total += cnt
        time.sleep(0.12)

    for kw in HERB_KEYWORDS:
        cnt = search_blog_count(f'{name} {kw}')
        if cnt > 0:
            herb_total += cnt
        time.sleep(0.12)

    return {'leaf_count': leaf_total, 'herb_count': herb_total}

# ──────────────────────────────────────────
# 진행 상황 로드
# ──────────────────────────────────────────
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        progress = json.load(f)
    print(f"이전 진행 로드: {len(progress)}개 완료")
else:
    progress = {}

df = pd.read_csv('tea_shops_dedup.csv')
names = df['가게명'].tolist()

remaining = [n for n in names if n not in progress]
print(f"남은 가게: {len(remaining)}개 / 전체 {len(names)}개")
print(f"예상 소요: 약 {len(remaining) * 15 / 60:.0f}분\n")

# ──────────────────────────────────────────
# 스코어링 실행
# ──────────────────────────────────────────
for i, name in enumerate(remaining, 1):
    result = score_shop(name)
    progress[name] = result

    flag = ''
    if result['leaf_count'] == 0 and result['herb_count'] > 0:
        flag = '⚠️ 제거후보'
    elif result['leaf_count'] == 0 and result['herb_count'] == 0:
        flag = '❓ 정보없음'

    print(f"[{i:3d}/{len(remaining)}] {name:25s} | 찻잎:{result['leaf_count']:6d} | 한방:{result['herb_count']:5d} {flag}")

    if i % 10 == 0:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

# 최종 저장
with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
    json.dump(progress, f, ensure_ascii=False, indent=2)

# ──────────────────────────────────────────
# 결과 정리 & 저장 (tea_shops_scored.csv)
# ──────────────────────────────────────────
df['leaf_count'] = df['가게명'].map(lambda n: progress.get(n, {}).get('leaf_count', -1))
df['herb_count'] = df['가게명'].map(lambda n: progress.get(n, {}).get('herb_count', -1))

def classify(row):
    if row['leaf_count'] > 0:
        return 'KEEP'
    elif row['herb_count'] > 0:
        return 'REMOVE'
    else:
        return 'UNKNOWN'

df['filter_result'] = df.apply(classify, axis=1)

print('\n=== 분류 결과 ===')
print(df['filter_result'].value_counts().to_string())

print('\n[제거 후보]')
print(df[df['filter_result'] == 'REMOVE'][['가게명', 'leaf_count', 'herb_count']].to_string(index=False))

print('\n[정보 없음 (수동 확인 필요)]')
print(df[df['filter_result'] == 'UNKNOWN'][['가게명', 'leaf_count', 'herb_count']].to_string(index=False))

df.to_csv('tea_shops_scored.csv', index=False, encoding='utf-8-sig')
print('\n[저장] tea_shops_scored.csv')
