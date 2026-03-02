"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
21_merge_supply.py — 공급지표 전체 병합 + 조합지표 계산
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
목적:
  수요지표가 담긴 기존 패널데이터에 공급지표 3개 추가 병합
  + 조합지표(수요÷공급 형태) 4개 계산

공급지표 3개:
  - 카페음료_점포수: competitor.csv에서 분기별로 가져옴
  - 찻집_수: tea_shop_count.csv (단면 데이터 → 전 분기 동일 적용)
  - 스타벅스_리저브_수: starbucks_reserve_count.csv (단면)

조합지표 4개 (= 수요 / (찻집_수 + 1)):
  - 공급갭_지수: 카페음료_점포수 / (찻집_수 + 1)
  - 유동밀도_지수: 여성_유동인구_수 / (찻집_수 + 1)
  - 상주밀도_지수: 여성_상주인구_수 / (찻집_수 + 1)
  - 여가소비_지수: 여가_지출_총금액 / (찻집_수 + 1)

입력: y_demand_merge.csv, competitor.csv, tea_shop_count.csv, starbucks_reserve_count.csv
출력: composite_indicators.csv (조합지표만)
      y_supply_merge.csv      (전체 병합 데이터)
"""

import os  # 운영체제(OS) 관련 기능 (파일 경로, 작업 디렉토리 등) (내장 모듈)
#  └ [os 라이브러리]
#    · 파이썬 내장 모듈로 별도 설치 불필요
#    · os.chdir(경로): 현재 작업 디렉토리를 지정 경로로 변경
#    · os.path.join(): OS에 맞는 경로 생성 (/ 또는 \를 OS에 맞게 처리)
#    · os.environ[]: 환경변수 접근
#    · os.path.exists(): 파일/폴더 존재 여부 확인

import pandas as pd  # 표 형태 데이터(DataFrame) 다루는 핵심 라이브러리
#  └ [pandas 라이브러리]
#    · 엑셀처럼 행/열 구조의 DataFrame을 파이썬에서 다룰 수 있게 해줌
#    · CSV 읽기/쓰기, 필터링, 그룹화, 병합 등 데이터 처리의 핵심
#    · 이 프로젝트에서 거의 모든 데이터 입출력과 가공에 사용됨
#    · 설치: pip install pandas

import warnings  # 경고 메시지 제어 라이브러리 (내장 모듈)
#  └ [warnings 라이브러리]
#    · 파이썬 실행 중 발생하는 경고(Warning) 메시지를 제어하는 내장 모듈
#    · 경고(Warning)란: 오류(Error)는 아니지만 잠재적 문제가 있을 때 파이썬이 출력하는 알림
#      예) SettingWithCopyWarning: DataFrame 복사본에 값을 쓸 때 원본이 바뀔 수 있다는 경고
#      예) FutureWarning: 향후 버전에서 동작이 바뀔 예정인 기능 사용 시 경고
#      예) DeprecationWarning: 더 이상 권장하지 않는(deprecated) 기능 사용 시 경고
#    · 오류(Error)와의 차이: 경고는 실행이 멈추지 않지만 오류는 실행이 중단됨
#    · warnings.filterwarnings('ignore'): 이 줄 이후 발생하는 모든 경고를 출력하지 않음
#    · 억제 이유: 분석 결과물과 무관한 경고가 출력을 복잡하게 만들 때 가독성 향상 목적
#    · 주의: 실제 문제를 숨길 수 있으므로 개발 중에는 경고를 확인하고, 배포 직전에 억제

warnings.filterwarnings('ignore')  # 이후 발생하는 모든 경고 메시지를 콘솔에 출력하지 않음
#  └ warnings.filterwarnings(action, category=Warning, module='', lineno=0)
#    · action='ignore': 경고를 완전히 무시 (출력 안 함)
#    · action='error' : 경고를 예외(Exception)로 격상 (디버깅 시 유용)
#    · action='always': 항상 출력 (기본값 복구용)
#    · category: 특정 경고 클래스만 필터링 가능 (예: FutureWarning, DeprecationWarning)
#    · 인자 없이 'ignore'만 쓰면 모든 종류의 경고에 적용됨

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha 폴더로 변경
#  └ os.chdir(경로)
#    · 현재 파이썬 프로세스의 작업 디렉토리(Working Directory)를 지정 경로로 변경
#    · 작업 디렉토리: 파일 경로를 상대 경로로 쓸 때 기준이 되는 폴더
#    · 예: os.chdir('/teamspace/studios/this_studio/aicha') 후
#         pd.read_csv('data.csv') → /teamspace/studios/this_studio/aicha/data.csv 를 읽음
#    · Jupyter나 IDE에서 실행 시 cwd가 달라질 수 있어 명시적으로 고정함
#    · os.getcwd()로 현재 작업 디렉토리 확인 가능


# ══════════════════════════════════════════════════════
# 1. 기준 데이터 로드
# ══════════════════════════════════════════════════════
base = pd.read_csv('y_demand_merge.csv')  # 수요지표가 담긴 기존 패널 데이터
#  └ pd.read_csv(파일경로, encoding=None, sep=',', header=0, index_col=None, usecols=None)
#    · CSV(Comma-Separated Values) 파일을 읽어 pandas DataFrame으로 반환
#    · 파일경로: 절대경로 또는 작업 디렉토리 기준 상대경로
#    · encoding=None: 기본값은 시스템 인코딩 사용 (보통 utf-8)
#      encoding='utf-8-sig': BOM(Byte Order Mark) 포함 UTF-8 (한글 엑셀 저장 파일에 필요)
#      encoding='cp949': 윈도우 한글 인코딩 (utf-8-sig로 대부분 대체 가능)
#    · sep=',': 구분자 기본값은 쉼표, TSV 파일이면 sep='\t'
#    · header=0: 첫 번째 행(0번 인덱스)을 컬럼명으로 사용
#    · index_col=None: 별도 인덱스 열 없음, 0,1,2... 자동 부여
#    · usecols=['col1','col2']: 지정 컬럼만 읽기 (대용량 파일에서 메모리 절약)

print(f"기준 데이터: {base.shape}")  # DataFrame의 (행 수, 열 수) 출력
#  └ df.shape
#    · DataFrame의 크기를 (행 수, 열 수) 형태의 튜플로 반환
#    · 예: (9760, 147) → 9,760행 147열
#    · df.shape[0]: 행 수만, df.shape[1]: 열 수만
#    · len(df): 행 수만 반환 (df.shape[0]와 동일)
#    · 병합 전후 shape를 출력해 데이터가 의도대로 결합됐는지 확인


# ══════════════════════════════════════════════════════
# 2. 원지표 3개 병합
# ══════════════════════════════════════════════════════

# ── 2-1. 카페음료_점포수 (분기별 데이터 → 분기 기준으로 병합) ──
comp = pd.read_csv('competitor.csv')  # 분기별 카페 경쟁업체 데이터
#  └ pd.read_csv(파일경로, encoding=None, sep=',', header=0, index_col=None, usecols=None)
#    · competitor.csv: 상권별 분기별 경쟁 점포 수 등이 담긴 CSV
#    · 전체 컬럼을 읽되 이후 필요한 컬럼만 선택

cafe = comp[['기준_년분기_코드', '상권_코드', '점포_수']].rename(
#  └ df[['컬럼1', '컬럼2', '컬럼3']]: 여러 컬럼을 동시에 선택하여 새 DataFrame 반환
#    · df['컬럼']: 단일 컬럼 → Series 반환
#    · df[['컬럼']]: 리스트 안에 하나 → 1열짜리 DataFrame 반환
#    · df[['컬럼1','컬럼2']]: 여러 컬럼 선택 → DataFrame 반환
#    · 원본 df는 변경되지 않고 선택된 컬럼만 담은 새 객체를 반환
#    · 컬럼 순서는 리스트에 명시한 순서를 따름
    columns={'점포_수': '카페음료_점포수'}  # 컬럼명을 의미 있는 이름으로 변경
#  └ df.rename(columns={기존명: 새이름, ...}, index={...}, inplace=False)
#    · columns 딕셔너리: {기존컬럼명: 새컬럼명} 형태로 여러 개 동시 변경 가능
#    · inplace=False(기본): 원본은 유지하고 새 DataFrame 반환
#    · inplace=True: 원본 DataFrame 직접 수정 (반환값 없음)
#    · 딕셔너리에 명시되지 않은 컬럼은 그대로 유지됨
)
base = base.merge(cafe, on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ df.merge(other, on=None, how='inner', left_on=None, right_on=None)
#    · 두 DataFrame을 공통 컬럼(키)을 기준으로 합치는 JOIN 연산
#    · on=['기준_년분기_코드', '상권_코드']: 복합키 — 두 컬럼 모두 일치하는 행끼리 연결
#      단일 키면 on='컬럼명', 복합 키면 on=['컬럼1', '컬럼2'] 리스트로 지정
#    · how='left': LEFT JOIN — base(왼쪽)의 모든 행 유지
#      base에 있지만 cafe에 없는 행 → 카페음료_점포수가 NaN으로 채워짐
#      cafe에만 있고 base에 없는 행 → 결과에 포함되지 않음
#    · how='inner': 양쪽 모두에 있는 행만 (교집합) → 데이터 소실 위험
#    · how='outer': 한쪽이라도 있으면 포함 (합집합)
#    · how='right': 오른쪽(other=cafe)의 모든 행 유지
#    · 패널 데이터 핵심: 상권코드만으로 JOIN하면 분기가 뒤섞이므로 반드시 복합키 사용

print(f"카페음료_점포수 병합 → {base.shape} | 결측: {base['카페음료_점포수'].isna().sum()}행")
#  └ Series.isna()
#    · 각 값이 NaN(결측치)이면 True, 아니면 False인 Boolean Series 반환
#    · pd.isna()와 동일, .isnull()도 동일한 기능
#    · NaN(Not a Number): 값이 없거나 알 수 없을 때의 특수값
#    · LEFT JOIN 후 매칭 안 된 행은 NaN → 결측 수 확인으로 JOIN 품질 점검
#  └ Series.sum()
#    · Series의 모든 값을 합산 (Boolean Series에서 True=1, False=0으로 계산)
#    · .isna().sum() → NaN인 행의 개수를 반환

# ── 2-2. 찻집_수 (단면 데이터 → 모든 분기에 동일하게 적용) ──
tea = pd.read_csv('tea_shop_count.csv')[['상권_코드', '찻집_수']]
#  └ pd.read_csv(파일경로)[['컬럼1','컬럼2']]: 읽자마자 바로 필요한 컬럼만 선택
#    · pd.read_csv()가 반환하는 DataFrame에 바로 [[ ]] 인덱싱 적용
#    · 전체를 읽고 나서 컬럼을 선택하는 것과 동일하지만, 한 줄로 간결하게 표현

base = base.merge(tea, on='상권_코드', how='left')
#  └ df.merge(other, on='상권_코드', how='left')
#    · on='상권_코드': 단일 컬럼을 기준 키로 사용 (리스트 불필요)
#    · how='left': base의 모든 행 유지, 매칭 안 되면 NaN
#    · 찻집_수는 단면 데이터(분기 구분 없음) → 상권_코드로만 JOIN
#    · 9개 분기 × 1,139개 상권 = 9,760행 base에 각 상권 찻집_수가 분기마다 반복 적용

base['찻집_수'] = base['찻집_수'].fillna(0).astype(int)  # NaN → 0, float → int
#  └ Series.fillna(값)
#    · NaN(결측치)을 지정한 값으로 대체한 새 Series 반환
#    · 찻집_수가 NaN인 경우: 해당 상권에 찻집이 0개 (수집 결과 없음)를 의미
#    · 0으로 채우는 이유: "찻집 없음" = 0이므로 의미론적으로 올바름
#    · inplace=True로 원본 수정 가능하지만, 체이닝(.astype(int))을 위해 반환값 사용
#  └ Series.astype(dtype)
#    · Series의 데이터 타입을 지정한 타입으로 변환
#    · astype(int): 실수(0.0) → 정수(0), 문자열 숫자('3') → 정수(3)로 변환
#    · fillna(0) 후 astype(int): NaN→0.0(float)→0(int) 두 단계 변환
#    · 주의: NaN이 남아있는 상태에서 astype(int) 시 ValueError 발생 → fillna 먼저
#    · 자주 쓰는 타입: int, float, str, bool, 'category'

print(f"찻집_수 병합       → {base.shape}")  # 병합 후 크기 확인

# ── 2-3. 스타벅스_리저브_수 (단면 → 전 분기 동일) ──
sb = pd.read_csv('starbucks_reserve_count.csv')[['상권_코드', '스타벅스_리저브_수']]
#  └ pd.read_csv(파일경로)[['컬럼1','컬럼2']]: 읽자마자 바로 필요한 컬럼만 선택

base = base.merge(sb, on='상권_코드', how='left')
#  └ df.merge(other, on='상권_코드', how='left')
#    · 스타벅스_리저브_수도 단면 데이터 → 상권_코드로만 JOIN
#    · 매칭 안 되는 상권(스타벅스 리저브 없는 상권) → NaN

base['스타벅스_리저브_수'] = base['스타벅스_리저브_수'].fillna(0).astype(int)
#  └ Series.fillna(0).astype(int): 결측 = 리저브 없음 = 0개로 처리 후 정수 변환

print(f"스타벅스_리저브_수 병합 → {base.shape}")  # 병합 후 크기 확인


# ══════════════════════════════════════════════════════
# 3. 조합지표 4개 계산
# ══════════════════════════════════════════════════════
denom = base['찻집_수'] + 1  # 분모 = 찻집_수 + 1 (0으로 나누기 방지용 +1 스무딩)
#  └ Series + 1: 벡터화(vectorized) 연산 — Series의 모든 원소에 1을 더함
#    · 파이썬 반복문(for) 없이 C언어 수준으로 빠르게 일괄 처리
#    · 예: pd.Series([0, 2, 5]) + 1 → pd.Series([1, 3, 6])
#    · +1을 더하는 이유 (스무딩, Smoothing):
#      · 찻집_수가 0인 상권에서 0으로 나누면 ZeroDivisionError 또는 inf 발생
#      · +1을 더하면 분모가 최소 1이 되어 나눗셈이 항상 유효
#      · 찻집이 많은 상권에서는 +1의 영향 미미 (예: 300/6 ≈ 300/7, 차이 약 4%)
#      · 찻집이 없는 상권에서는 +1로 의미 있는 지표값 산출 가능 (300/0 → 300/1)
#      · 통계·ML에서 흔히 쓰는 Laplace smoothing 개념과 동일

base['공급갭_지수']   = base['카페음료_점포수']  / denom  # 카페 수요 대비 찻집 공급 부족
#  └ Series / Series: 두 Series의 원소별(element-wise) 나눗셈
#    · 같은 인덱스끼리 대응하여 나눗셈 수행 (파이썬 for 루프 불필요)
#    · 예: pd.Series([10, 20]) / pd.Series([2, 5]) → pd.Series([5.0, 4.0])
#    · 결과는 float Series (정수 / 정수도 float 반환)
#    · 공급갭_지수 해석: 카페음료 점포 수가 많고 찻집이 적을수록 값이 큼
#    · 값이 클수록 → 찻집 공급이 부족한 "갭"이 큰 상권 (블루오션 가능성 높음)

base['유동밀도_지수'] = base['여성_유동인구_수'] / denom  # 찻집당 잠재 워크인 고객 수
#  └ Series / Series: 원소별 나눗셈 (벡터화 연산)
#    · 유동밀도_지수 해석: 찻집 1개당 여성 유동인구가 많을수록 값이 큼
#    · 값이 클수록 → 수요(유동인구)는 많은데 공급(찻집)이 적은 상권

base['상주밀도_지수'] = base['여성_상주인구_수'] / denom  # 찻집당 잠재 단골 고객 수
#  └ Series / Series: 원소별 나눗셈 (벡터화 연산)
#    · 상주밀도_지수 해석: 찻집 1개당 여성 상주인구가 많을수록 값이 큼
#    · 상주인구: 해당 지역에 거주하는 인구 → 단골 고객 잠재력 지표

base['여가소비_지수'] = base['여가_지출_총금액'] / denom  # 찻집당 여가 소비력
#  └ Series / Series: 원소별 나눗셈 (벡터화 연산)
#    · 여가소비_지수 해석: 찻집 1개당 여가 지출이 클수록 값이 큼
#    · 값이 클수록 → 여가 소비력이 높은데 찻집이 부족한 상권

composite_cols = ['공급갭_지수', '유동밀도_지수', '상주밀도_지수', '여가소비_지수']

print(f"\n=== 조합지표 기술통계 ===")
print(base[composite_cols].describe().applymap(lambda x: f'{x:,.1f}'))
#  └ df.describe()
#    · 수치형 컬럼의 기술통계량을 한 번에 계산하여 DataFrame으로 반환
#    · 반환 행: count(값 개수), mean(평균), std(표준편차),
#               min(최솟값), 25%(1사분위), 50%(중앙값), 75%(3사분위), max(최댓값)
#    · count: NaN을 제외한 유효값 개수 → 결측 여부 파악에 유용
#    · std(표준편차): 값이 평균에서 얼마나 퍼져 있는지 나타내는 지표
#    · 사분위수(quartile): 데이터를 4등분하는 경계값
#      · 25%: 하위 25% 경계(Q1), 50%: 중앙값(Q2=median), 75%: 상위 25% 경계(Q3)
#    · include='all': 문자형 컬럼도 포함 (기본은 수치형만)
#  └ df.applymap(함수)
#    · DataFrame의 모든 셀(각 원소)에 함수를 적용하여 새 DataFrame 반환
#    · 행 단위: df.apply(함수, axis=1), 열 단위: df.apply(함수, axis=0)
#    · applymap: 셀 단위 (스칼라 입력 → 스칼라 출력)
#    · 참고: pandas 2.1+에서 applymap은 map으로 변경됨 (기능 동일)
#  └ lambda x: f'{x:,.1f}'
#    · lambda(람다): 이름 없는 익명 함수를 한 줄로 정의하는 문법
#    · 기본 문법: lambda 매개변수: 반환식
#    · def로 쓰면: def f(x): return f'{x:,.1f}'  — 이것과 완전히 동일
#    · lambda x: f'{x:,.1f}' 해석:
#      · x를 입력받아 f'{x:,.1f}' 형식의 문자열을 반환
#      · ,.1f: 천 단위 쉼표(,) + 소수점 1자리(1f) 형식 지정자
#      · 예: 12345.6789 → '12,345.7'
#    · 기술통계 숫자에 포맷 적용해 콘솔 가독성 향상 목적


# ══════════════════════════════════════════════════════
# 4. 파일 1: composite_indicators.csv (조합지표만)
# ══════════════════════════════════════════════════════
key_cols     = ['기준_년분기_코드', '상권_코드', '상권_코드_명']  # 식별 컬럼
df_composite = base[key_cols + ['찻집_수'] + composite_cols].copy()  # 필요한 컬럼만 선택
#  └ list + list: 두 리스트를 이어붙여 새 리스트 생성
#    · ['기준_년분기_코드','상권_코드','상권_코드_명'] + ['찻집_수'] + ['공급갭_지수',...]
#    · 결과: ['기준_년분기_코드','상권_코드','상권_코드_명','찻집_수','공급갭_지수',...]
#    · 원본 리스트는 변경되지 않음, 새 리스트가 반환됨
#  └ df[컬럼리스트]: 리스트로 여러 컬럼을 한 번에 선택 → 새 DataFrame 반환
#    · 위에서 만든 이어붙인 리스트를 대괄호 인덱스로 사용
#    · 선택된 컬럼만 포함하는 DataFrame 반환
#  └ df.copy()
#    · DataFrame을 완전히 독립적으로 복사 (deep copy)
#    · copy() 없이 df_composite = base[...] 하면 base의 뷰(view)가 될 수 있음
#    · 뷰에 값을 쓰면 base도 같이 바뀌거나 SettingWithCopyWarning 경고 발생
#    · copy()로 독립 복사하면 df_composite 수정이 base에 영향 없음

df_composite.to_csv('composite_indicators.csv', index=False, encoding='utf-8-sig')
#  └ df.to_csv(파일경로, index=True, encoding=None, sep=',')
#    · DataFrame을 CSV 파일로 저장
#    · index=False: 행 번호(0,1,2...)를 CSV에 포함하지 않음
#      index=True(기본값): 행 번호 열이 CSV 첫 열로 저장됨 → 불필요한 열 생성
#    · encoding='utf-8-sig': BOM(Byte Order Mark) 포함 UTF-8 인코딩
#      한글이 포함된 파일을 윈도우 엑셀에서 열 때 깨지지 않도록 BOM 추가
#    · sep=',': 구분자 (기본값 쉼표), TSV 저장이면 sep='\t'

print(f"\n[저장] composite_indicators.csv ({df_composite.shape[0]}행 × {df_composite.shape[1]}열)")
#  └ df.shape[0]: 행 수 / df.shape[1]: 열 수

print(df_composite.head(3).to_string(index=False))  # 상위 3행 미리보기
#  └ df.head(n)
#    · DataFrame의 처음 n행을 반환 (기본값 n=5)
#    · df.tail(n): 마지막 n행 반환
#    · 데이터 구조 확인, 저장 결과 검증, 출력 샘플 확인에 자주 사용
#  └ df.to_string(index=False)
#    · DataFrame을 print용 문자열로 변환 (콘솔 너비에 맞춰 truncation 없이 전체 출력)
#    · index=False: 행 번호 열 없이 출력


# ══════════════════════════════════════════════════════
# 5. 파일 2: y_supply_merge.csv (전체 병합 데이터)
# ══════════════════════════════════════════════════════
supply_cols = ['카페음료_점포수', '찻집_수', '스타벅스_리저브_수'] + composite_cols
#  └ list + list: 원지표 3개 리스트 + 조합지표 4개 리스트를 이어붙여 공급지표 전체 컬럼 목록 생성

print(f"\n=== 공급지표 샘플 (상위 3행) ===")
print(base[key_cols + supply_cols].head(3).to_string(index=False))

base.to_csv('y_supply_merge.csv', index=False, encoding='utf-8-sig')  # 전체 데이터 저장
#  └ df.to_csv(파일경로, index=False, encoding='utf-8-sig')
#    · 전체 병합 결과(base)를 CSV로 저장
#    · index=False: 행 번호 열 미포함
#    · encoding='utf-8-sig': 한글 포함 파일 엑셀 호환 저장

print(f"\n[저장] y_supply_merge.csv ({base.shape[0]}행 × {base.shape[1]}열)")
print(f"\n추가된 공급지표 컬럼 ({len(supply_cols)}개): {supply_cols}")
