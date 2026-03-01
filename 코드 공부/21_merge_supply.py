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

import os               # 작업 디렉토리 변경 (17번에서 상세 설명)
import pandas as pd     # 데이터프레임 라이브러리 (17번에서 상세 설명)
import warnings         # 경고 메시지 제어 라이브러리
#  └ [warnings 라이브러리 (내장 모듈)]
#    · 파이썬 실행 중 발생하는 경고(Warning) 메시지를 제어
#    · warnings.filterwarnings('ignore'): 모든 경고 숨김
#    · 경고는 오류는 아니지만 주의가 필요한 상황에서 발생 (예: 형변환, 복사 경고 등)

warnings.filterwarnings('ignore')  # 경고 메시지 숨김 (출력 깔끔하게 유지)

os.chdir('/teamspace/studios/this_studio/aicha')  # 작업 디렉토리를 aicha로 변경


# ══════════════════════════════════════════════════════
# 1. 기준 데이터 로드
# ══════════════════════════════════════════════════════
base = pd.read_csv('y_demand_merge.csv')  # 수요지표가 담긴 기존 패널 데이터
print(f"기준 데이터: {base.shape}")
#  └ df.shape: (행 수, 열 수) 튜플 반환 (예: (9760, 140))


# ══════════════════════════════════════════════════════
# 2. 원지표 3개 병합
# ══════════════════════════════════════════════════════

# ── 2-1. 카페음료_점포수 (분기별 데이터 → 분기 기준으로 병합) ──
comp = pd.read_csv('competitor.csv')  # 분기별 카페 경쟁업체 데이터

cafe = comp[['기준_년분기_코드', '상권_코드', '점포_수']].rename(
    columns={'점포_수': '카페음료_점포수'}  # 컬럼명을 의미 있는 이름으로 변경
)
#  └ df[['컬럼1', '컬럼2', '컬럼3']]: 필요한 컬럼만 선택
#  └ .rename(columns={'기존명': '새이름'}): 컬럼명 변경 (20번에서 상세 설명)

base = base.merge(cafe, on=['기준_년분기_코드', '상권_코드'], how='left')
#  └ df.merge(다른df, on=[컬럼1, 컬럼2], how='left')
#    · 두 컬럼을 동시에 키로 사용해 병합 (복합 키 JOIN)
#    · on=['기준_년분기_코드', '상권_코드']: 같은 분기 + 같은 상권만 매칭
#    · how='left': 기준(base) 데이터의 모든 행 유지 (없으면 NaN)
#    · 패널 데이터의 핵심: 상권코드 하나만으로 JOIN하면 분기가 뒤섞이므로 주의!

print(f"카페음료_점포수 병합 → {base.shape} | 결측: {base['카페음료_점포수'].isna().sum()}행")
#  └ Series.isna(): NaN이면 True, 아니면 False (isnull()과 동일)
#  └ .sum(): True의 개수 = NaN인 행 수

# ── 2-2. 찻집_수 (단면 데이터 → 모든 분기에 동일하게 적용) ──
tea = pd.read_csv('tea_shop_count.csv')[['상권_코드', '찻집_수']]
#  └ pd.read_csv(...)[['컬럼1', '컬럼2']]: 읽으면서 바로 필요한 컬럼만 선택

base = base.merge(tea, on='상권_코드', how='left')
#  └ on='상권_코드'만 키로 사용 → 분기별로 같은 찻집_수 값 반복 적용
#    · 찻집_수는 특정 시점 데이터 (단면)이므로 분기 구분 없이 병합
#    · 1개 상권코드 → 9개 분기 행 모두에 동일한 찻집_수 값이 들어감

base['찻집_수'] = base['찻집_수'].fillna(0).astype(int)  # NaN → 0, float → int
print(f"찻집_수 병합       → {base.shape}")

# ── 2-3. 스타벅스_리저브_수 (단면 → 전 분기 동일) ──
sb = pd.read_csv('starbucks_reserve_count.csv')[['상권_코드', '스타벅스_리저브_수']]
base = base.merge(sb, on='상권_코드', how='left')
base['스타벅스_리저브_수'] = base['스타벅스_리저브_수'].fillna(0).astype(int)
print(f"스타벅스_리저브_수 병합 → {base.shape}")


# ══════════════════════════════════════════════════════
# 3. 조합지표 4개 계산
# ══════════════════════════════════════════════════════
denom = base['찻집_수'] + 1  # 분모 = 찻집_수 + 1 (0으로 나누기 방지용 +1 스무딩)
#  └ +1을 더하는 이유: 찻집_수가 0인 상권에서 0으로 나누면 ZeroDivisionError 발생
#    · 찻집_수=0이면 분모가 1이 되어 계산 가능
#    · 찻집_수가 1개일 때와 0개일 때의 차이를 유지하면서 안정성 확보

base['공급갭_지수']   = base['카페음료_점포수']  / denom  # 카페 수 대비 찻집 공급 부족 지수
base['유동밀도_지수'] = base['여성_유동인구_수'] / denom  # 찻집당 잠재 워크인 고객 수
base['상주밀도_지수'] = base['여성_상주인구_수'] / denom  # 찻집당 잠재 단골 고객 수
base['여가소비_지수'] = base['여가_지출_총금액'] / denom  # 찻집당 여가 소비력
#  └ 벡터 나눗셈: pandas Series끼리 / 연산 → 행별로 자동 대응해서 나눔
#    · base['카페음료_점포수'] / denom: 9760개 행을 한 번에 나눔 (루프 불필요)

composite_cols = ['공급갭_지수', '유동밀도_지수', '상주밀도_지수', '여가소비_지수']

print(f"\n=== 조합지표 기술통계 ===")
print(base[composite_cols].describe().applymap(lambda x: f'{x:,.1f}'))
#  └ df.describe(): 각 컬럼의 기술통계량 반환 (count, mean, std, min, 25%, 50%, 75%, max)
#  └ .applymap(함수): DataFrame의 각 원소에 함수 적용 (원소 단위 변환)
#    · lambda x: f'{x:,.1f}': 숫자를 천 단위 구분자(,)와 소수점 1자리로 포맷팅


# ══════════════════════════════════════════════════════
# 4. 파일 1: composite_indicators.csv (조합지표만)
# ══════════════════════════════════════════════════════
key_cols     = ['기준_년분기_코드', '상권_코드', '상권_코드_명']  # 식별 컬럼
df_composite = base[key_cols + ['찻집_수'] + composite_cols].copy()  # 필요한 컬럼만 선택
#  └ 리스트 + 리스트: 두 리스트를 이어 붙임
#    · ['a', 'b'] + ['c'] + ['d', 'e'] → ['a', 'b', 'c', 'd', 'e']

df_composite.to_csv('composite_indicators.csv', index=False, encoding='utf-8-sig')
print(f"\n[저장] composite_indicators.csv ({df_composite.shape[0]}행 × {df_composite.shape[1]}열)")
#  └ df.shape[0]: 행 수 / df.shape[1]: 열 수

print(df_composite.head(3).to_string(index=False))  # 상위 3행 미리보기
#  └ df.head(n): 상위 n개 행 반환 (기본값 5)
#  └ .to_string(index=False): 행 번호 없이 문자열로 출력


# ══════════════════════════════════════════════════════
# 5. 파일 2: y_supply_merge.csv (전체 병합 데이터)
# ══════════════════════════════════════════════════════
supply_cols = ['카페음료_점포수', '찻집_수', '스타벅스_리저브_수'] + composite_cols
print(f"\n=== 공급지표 샘플 (상위 3행) ===")
print(base[key_cols + supply_cols].head(3).to_string(index=False))

base.to_csv('y_supply_merge.csv', index=False, encoding='utf-8-sig')  # 전체 데이터 저장
print(f"\n[저장] y_supply_merge.csv ({base.shape[0]}행 × {base.shape[1]}열)")
print(f"\n추가된 공급지표 컬럼 ({len(supply_cols)}개): {supply_cols}")
