"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
24_merge_trend.py — 트렌드 지표를 최종 데이터셋에 병합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  지금까지 만든 수요+공급 통합 데이터에 트렌드 지표 4개 최종 추가
  → 모든 지표가 담긴 최종 분석 데이터셋 완성

입력: y_demand_supply_merge.csv (150열 기존 데이터)
      trend_index.csv            (트렌드 지표 4개, 23번 산출)
출력: y_demand_supply_trend_merge.csv (154열 최종 데이터셋, 9,760행)
"""

import os  # 운영체제(OS) 관련 기능 (파일 경로, 작업 디렉토리 등) 제공
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈 (별도 설치 불필요)
#    · os.chdir(경로): 현재 작업 디렉토리(cwd) 변경
#    · os.path.join(), os.path.exists() 등 경로 관련 함수 포함
#    · os.environ[]: 환경변수 접근
#    · 이 스크립트에서는 aicha 폴더를 cwd로 지정해 파일명만으로 CSV 접근 가능하게 함

import pandas as pd  # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · 엑셀처럼 행/열 구조의 DataFrame을 파이썬에서 다룰 수 있게 해줌
#    · CSV 읽기/쓰기, 필터링, 그룹화, 병합 등 데이터 처리의 핵심
#    · 이 파일에서는 두 DataFrame을 읽어 LEFT JOIN으로 합치고 저장하는 데 사용
#    · 설치: pip install pandas

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경
#  └ os.chdir(경로)
#    · 기본문법: os.chdir(path)
#    · 이후 pd.read_csv('파일명.csv') 처럼 파일명만 써도 이 폴더에서 찾음
#    · 변경하지 않으면 스크립트 실행 위치(터미널 cwd)에서 파일을 찾아 오류 발생
#    · 한 번만 설정하면 이 스크립트 실행 동안 계속 유효


# ══════════════════════════════════════════════════════
# 파일 로드
# ══════════════════════════════════════════════════════
print("▶ 파일 로드 중...")
base  = pd.read_csv('y_demand_supply_merge.csv')  # 수요+공급 통합 데이터 (150열)
#  └ pd.read_csv(파일경로, encoding=None, sep=',', header=0, index_col=None)
#    · CSV 파일을 읽어 DataFrame으로 반환
#    · encoding 미지정 시 기본값 'utf-8' 사용 (BOM 없는 UTF-8)
#    · sep=',': 구분자는 쉼표(기본값)
#    · header=0: 첫 번째 행을 컬럼명으로 사용(기본값)
#    · index_col=None: 별도 인덱스 열 지정 없음 (기본값, 0부터 자동 부여)
#    · 반환: DataFrame (행×열 표 형태)

trend = pd.read_csv('trend_index.csv')  # 트렌드 지표 4개 (23번 산출)
#  └ pd.read_csv('trend_index.csv')
#    · 위와 동일한 방식으로 CSV 읽기
#    · 컬럼: 기준_년분기_코드, 상권_코드, 카페_검색지수, 검색량_성장률, 카페_개업률, 유동인구_성장률

# 병합 키 컬럼의 데이터 타입을 정수형으로 통일 (타입 불일치 시 JOIN 실패 방지)
base['기준_년분기_코드']  = base['기준_년분기_코드'].astype(int)   # 기준 데이터 분기코드
#  └ Series.astype(dtype)
#    · 기본문법: Series.astype(int) / Series.astype(str) / Series.astype(float)
#    · 해당 Series(컬럼)의 데이터 타입을 지정 타입으로 변환한 새 Series 반환
#    · 원본을 바꾸려면 다시 할당해야 함: series = series.astype(int)
#    · 병합(merge) 시 키 컬럼의 타입이 일치해야 JOIN이 정확하게 작동
#    · 예: base의 '기준_년분기_코드'가 int64, trend가 object(문자열)이면
#      같은 값(20231)이어도 병합 시 매칭 안 됨 → 양쪽 모두 명시적으로 int 변환
#    · CSV에서 읽으면 기본적으로 int64지만, 파일마다 타입이 달라질 수 있어 명시적 변환 권장

base['상권_코드']        = base['상권_코드'].astype(int)           # 기준 데이터 상권코드
trend['기준_년분기_코드'] = trend['기준_년분기_코드'].astype(int)  # 트렌드 데이터 분기코드
trend['상권_코드']       = trend['상권_코드'].astype(int)          # 트렌드 데이터 상권코드

print(f"  base : {base.shape}")   # (행수, 열수) 튜플 출력
#  └ df.shape
#    · 기본문법: DataFrame.shape (괄호 없는 속성)
#    · (행 수, 열 수) 형태의 튜플 반환
#    · 예: (9760, 150) → 9,760행, 150열
#    · 데이터 로드 직후 확인해 행/열 수가 예상과 맞는지 검증
#    · df.shape[0]: 행 수만, df.shape[1]: 열 수만

print(f"  trend: {trend.shape}")  # (9760, 6) 예상


# ══════════════════════════════════════════════════════
# 병합
# ══════════════════════════════════════════════════════
merged = base.merge(trend, on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ df.merge(other, on=None, how='inner', left_on=None, right_on=None)
#    · 기본문법: df.merge(합칠_DataFrame, on=[키컬럼목록], how=조인방식)
#    · on=['기준_년분기_코드', '상권_코드']: 두 컬럼의 조합(복합 키)으로 매칭
#    · how='left': 왼쪽(base)의 모든 9,760행을 유지
#      → trend에 해당 분기+상권 조합이 없으면 NaN으로 채움
#    · how='inner': 양쪽 모두에 있는 키만 유지 (기본값)
#    · how='right': 오른쪽 모든 행 유지
#    · how='outer': 양쪽 모두 유지, 없는 쪽은 NaN
#    · 병합 결과: base의 150열 + trend의 새 4열 = 154열 최종 데이터셋 완성
#    · 이 시점에서 Y변수 + 수요지표 + 공급지표 + 트렌드지표 모두 포함

print(f"\n▶ 병합 결과: {merged.shape}")  # (9760, 154) 예상


# ══════════════════════════════════════════════════════
# 저장
# ══════════════════════════════════════════════════════
merged.to_csv('y_demand_supply_trend_merge.csv', index=False, encoding='utf-8-sig')
#  └ df.to_csv(파일경로, sep=',', index=True, encoding=None)
#    · 기본문법: df.to_csv(path_or_buf, sep=',', index=True, encoding=None)
#    · DataFrame을 CSV 파일로 저장
#    · index=False: 행 번호(0,1,2...)를 CSV에 포함하지 않음
#      → index=True(기본)면 첫 번째 열에 0,1,2... 인덱스가 추가됨
#    · encoding='utf-8-sig': BOM(Byte Order Mark) 포함 UTF-8
#      → 한글을 엑셀로 열 때 깨지지 않도록 BOM 포함
#      → 순수 UTF-8('utf-8')은 BOM 없음 → 엑셀에서 한글 깨질 수 있음
#    · 이 파일이 이후 EDA와 회귀분석의 기준 파일이 됨

print("✅ y_demand_supply_trend_merge.csv 저장 완료")


# ══════════════════════════════════════════════════════
# 검증
# ══════════════════════════════════════════════════════
print(f"\n[컬럼 목록 (마지막 10개)]")
print(merged.columns.tolist()[-10:])
#  └ df.columns
#    · 기본문법: DataFrame.columns (괄호 없는 속성)
#    · DataFrame의 컬럼명들을 담은 Index 객체 반환
#    · Index 객체는 리스트와 비슷하지만 변경 불가(immutable)
#
#  └ .tolist()
#    · Index 객체를 파이썬 일반 리스트로 변환
#    · 변환 후에는 일반 리스트 메서드(슬라이싱, append 등) 사용 가능
#
#  └ [-10:]
#    · 리스트 슬라이싱: 끝에서 10번째부터 끝까지의 요소 반환
#    · 양수 인덱스: 앞에서부터 (0, 1, 2...)
#    · 음수 인덱스: 뒤에서부터 (-1=마지막, -10=뒤에서 10번째)
#    · [시작:끝]: 시작 포함, 끝 미포함 / 생략 시 처음/끝까지

print(f"\n[트렌드 컬럼 결측 현황]")
trend_cols = ['카페_검색지수', '검색량_성장률', '카페_개업률', '유동인구_성장률']
print(merged[trend_cols].isnull().sum())
#  └ df[컬럼목록]
#    · 특정 컬럼들만 선택해 새 DataFrame 반환 (이중 대괄호 사용)
#    · merged[trend_cols]: trend_cols 리스트에 담긴 컬럼들만 선택
#
#  └ .isnull()
#    · 기본문법: DataFrame.isnull() 또는 DataFrame.isna() (동일)
#    · 각 원소가 NaN이면 True, 값이 있으면 False인 Boolean DataFrame 반환
#    · isnull()과 isna()는 완전히 동일한 함수 (별칭 관계)
#
#  └ .sum()
#    · Boolean DataFrame에서 .sum(): True=1로 취급해 컬럼별 합산
#    · 결과: 각 컬럼별 NaN 개수 → 결측 현황을 한눈에 파악

print(f"\n[샘플 5행]")
print(merged[['기준_년분기_코드', '상권_코드'] + trend_cols].head(5).to_string(index=False))
#  └ merged[['기준_년분기_코드', '상권_코드'] + trend_cols]
#    · 리스트 덧셈: ['기준_년분기_코드', '상권_코드'] + ['카페_검색지수', ...]
#      → 두 리스트를 이어붙여 하나의 컬럼 목록 생성
#    · 키 컬럼 + 트렌드 컬럼만 선택해 검증에 필요한 내용만 표시
#
#  └ .head(5)
#    · 상위 5행만 반환 (기본값은 5, 괄호 안에 숫자로 변경 가능)
#    · df.tail(n): 마지막 n행 반환
#
#  └ .to_string(index=False)
#    · DataFrame을 출력용 문자열로 변환
#    · index=False: 행 번호(0,1,2...) 없이 데이터만 출력
