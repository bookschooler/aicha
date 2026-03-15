"""
32_lasso_elasticnet.py
[코드 공부용: 왼쪽에서 오른쪽 직독직해 해석본 (줄바꿈 적용)]

목적:
수요 변수 9개 중에서 모델 성능에 가장 기여하는 '알짜 변수'만 남기기
(Lasso, ElasticNet 모델 사용)
"""

import os
import warnings
warnings.filterwarnings('ignore') 
# warnings(경고모듈아) . filterwarnings(필터링해라) 
# ( 'ignore'(사소한 경고창은 무시하도록) )

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from sklearn.linear_model import LassoCV, ElasticNetCV, lasso_path 
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ── 경로 설정 ──
BASE_DIR = 'c:/Users/user/Desktop/STA_track/pypjt/aicha'
os.chdir(BASE_DIR)
# os(운영체제모듈아) . chdir(경로를바꿔라) 
# ( BASE_DIR(이 주소로) )


# ══════════════════════════════════════════════════════
# 1. 데이터 로드
# ══════════════════════════════════════════════════════
df = pd.read_csv('y_demand_supply_trend_merge.csv', encoding='utf-8-sig')
# df(데이터프레임 변수는) = pd(판다스야) . read_csv(csv파일을 읽어와라) 
# ( '파일명', encoding='이 한글 언어설정으로' )

myeongdong = df[df['상권_코드_명'].str.contains('명동 남대문', na=False)]['상권_코드'].unique()
# myeongdong(명동 상권코드만 담을 변수는) = df(데이터프레임의) 
# [ 이 조건에 맞는 행만 골라라: df의['상권_코드_명'] 컬럼이 
#   . str(문자열로서) . contains(포함하는가?) 
#   ('명동 남대문'을, na=결측치는 무시하고) ] 
# 그 후 ['상권_코드'] 컬럼만 떼어내서 
# . unique(중복없이 고유값만 가져와라) ()

df = df[~df['상권_코드'].isin(myeongdong)].copy()
# df(데이터프레임은 다 덮어써라) = df의 
# [ 이 조건에 맞는 행만: ~(아닌 것들만) df의['상권_코드'] 가 
#   . isin(안에 포함되는가?) (myeongdong 리스트에) ] 
# 그리고 그 결과를 . copy(완전히 독립된 복사본으로 만들어라) ()


# ══════════════════════════════════════════════════════
# 2. 결측치 처리 (그룹별 전략)
# ══════════════════════════════════════════════════════
b1 = set(df[df['총_직장_인구_수'].isna()]['상권_코드'].unique())
# b1(변수는) = set(집합으로 만들어라) 
# ( df의 [ 이 조건행: df의['총_직장_인구_수'] 가 
#   . isna(결측치, 즉 비어있는 값인지?) () ] 에서 
#   ['상권_코드'] 만 뽑아내서 . unique(중복제거) () 한 것을 )

b2 = set(df[df['총_상주인구_수'].isna()]['상권_코드'].unique())
# b2(변수는) = (위와 동일하게 총_상주인구_수 컬럼에 대해 
# 결측치 상권코드를 뽑아 집합으로 만듦)

remove_b = b1 | b2
# remove_b(제거대상 변수는) = b1(집합과) |(합집합해라) b2(집합을)

df = df[~df['상권_코드'].isin(remove_b)].copy()
# df(는) = df에서 
# [ ~(아닌행만) df의['상권_코드'] 가 
#   . isin(포함된) (remove_b 리스트 변수 안에) ] 
# . copy(복사해서 새 프레임으로 생성) ()

c1 = set(df[df['월_평균_소득_금액'].isna()]['상권_코드'].unique())
# c1(변수는) = (월_평균_소득이 결측치인 상권 코드를 
# 중복제거하여 집합으로 생성)

remove_c = c1 - remove_b 
# remove_c(변수는) = c1(집합에서) -(빼라, 차집합) 
# remove_b(이미 지울 대상들 집합을)

df = df[~df['상권_코드'].isin(remove_c)].copy()
# df(는) = (remove_c에 해당하지 않는 상권들만 추출해 
# 다시 df에 덮어씀)

miss_jip = df[df['집객시설_수'].isna()].groupby('상권_코드').size()
# miss_jip(변수는) = df에서 
# [ df의['집객시설_수'] 부분이 . isna(결측치인) () 열만 고르고 ] 
# . groupby(그룹으로 묶어라) ('상권_코드' 단위로) 묶은 뒤 
# . size(그 크기, 즉 비어있는 행의 개수를 세어라) ()

structural_jip = set(miss_jip[miss_jip >= 9].index)
# structural_jip(구조적결측 변수는) = set(집합생성) 
# ( miss_jip결과 중에서 
#   [ 해당하는걸 골라라: miss_jip(개수가) >= 9 (9개 넘는것) ] 의 
#   . index(그 인덱스값, 즉 상권코드 이름들을) )

remove_d = structural_jip - remove_b - remove_c
# remove_d(변수는) = (구조적결측 상권코드에서 
# 이미 지울 예정인 b, c 집합 상권들을 차집합으로 뺀 결과)

df = df[~df['상권_코드'].isin(remove_d)].copy()
# df(는) = (remove_d에 해당하지 않는 깨끗한 행만 뽑아 복사본으로 만듦)

df = df.sort_values(['상권_코드', '기준_년분기_코드'])
# df(는) = df를 . sort_values(정렬해라 기준값으로) 
# ( ['상권_코드'별로 먼저 묶고, 그 안에서 '기준_년분기_코드' 시간순으로] )

df['집객시설_수'] = (
    df.groupby('상권_코드')['집객시설_수']
    .transform(lambda x: x.ffill().bfill())
)
# df의['집객시설_수'] 컬럼(을 어떻게 덮어쓸거냐면) = (
#    df를 . groupby(그룹화해라) ('상권_코드'별로) 묶은 뒤 
#    ['집객시설_수'] 컬럼만 떼어내서
#    . transform(동일크기로 일괄 변환 적용해라) 
#    ( lambda x(임시변수x, 즉 해당그룹 데이터셋에 대해): 
#      x . ffill(위에서 아래로 이전 분기값으로 결측치 채워라) () 한 다음 
#      이어서 . bfill(아래에서 위로 다음 분기값으로 결측치 채워라) () 한 결과로 )
# )

DEMAND_VARS = [
    '집객시설_수', '총_직장_인구_수', '월_평균_소득_금액',
    '지출_총금액', '총_가구_수', '카페_검색지수',
    '총_상주인구_수', '여가_지출_총금액', '지하철_노선_수',
]
# 변수목록 (그냥 리스트 형태로 컬럼 이름 문자열들을 한데 모아 저장)


# ══════════════════════════════════════════════════════
# 3. 피처 엔지니어링 (더미변수 + 표준화)
# ══════════════════════════════════════════════════════
df = df[df['당월_매출_금액'] > 0].copy()
# df(는) = df에서 
# [ 조건: df의['당월_매출_금액'] > 0 (0보다 큰 정상매출) ] 행들만 
# 남겨서 복사본 생성

y = np.log1p(df['당월_매출_금액'].values) 
# y(목표값 배열은) = np(넘파이야) 
# . log1p(로그를 씌워라, log(x+1) 공식으로 비대칭을 맞춰줌) 
# ( df의['당월_매출_금액'] 의 . values(순수 수치값 배열만 가져와서) )

quarters = sorted(df['기준_년분기_코드'].unique())
# quarters(변수는) = sorted(정렬해라) 
# ( df의['기준_년분기_코드'] 컬럼의 
#   . unique(고유값, 중복제거한 분기 종류들만) () 뽑은 것을 )

for q in quarters[1:]:
    df[f'Q_{q}'] = (df['기준_년분기_코드'] == q).astype(int) 
# for(반복해라) q(현재 분기를) 
# in (안에서) quarters의[1: (두번째요소부터 끝까지 리스트 자른거)] :
#    df의[ f'Q_문자열{q를넣어서}' 즉, 'Q_20233' 같은 새 컬럼명 ] = 
#    ( 결과값이: df의['기준_년분기_코드'] ==(같은가?) q(현재반복값과) ) 의 
#    True/False 결과를 . astype(타입바꿔라) (int(정수 0이나 1로))

quarter_dummies = [f'Q_{q}' for q in quarters[1:]]
# quarter_dummies(분기더미 리스트는) = 
# [ f'Q_{q}' 라는문자열들을 하나씩 모아라 
#   for(q를반복하며) in( quarters[1:] (리스트 안에서) ) ]

type_col = '상권_구분_코드_명_x'
types = sorted(df[type_col].dropna().unique())
# types(상권유형 변수는) = sorted(정렬해라) 
# ( df의[type_col 문자열변수의 컬럼] 에서 
#   . dropna(결측치는빼고) () 
#   . unique(중복없는 고유값만) () )

for t in types[1:]:
    safe_name = t.replace(' ', '_').replace('/', '_') 
    # safe_name(안전한이름 변수는) = t(임시문자열을) 
    # . replace(대체해라) (' '(공백)을, '_'(언더바로)) 하고 
    # 연달아 . replace(대체해라) ('/'(슬래쉬)를, '_'(언더바로))
    df[f'TYPE_{safe_name}'] = (df[type_col] == t).astype(int)
    # 위 분기 더미 변수 생성 코드와 동일한 원리 (해당 상권이면 1, 아니면 0 표시)

type_dummies = [c for c in df.columns if c.startswith('TYPE_')]
# type_dummies(상권유형튜플 리스트는) = 
# [ c(이름을모아라) for c in ( df의 . columns(컬럼들 명단을 반복돌며) ) 
#   if (만약) c(컬럼문자열이) . startswith(시작하는가?) ('TYPE_'(라는글자로)) ]


scaler = StandardScaler() 
# scaler(변수는) = StandardScaler(표준화기계 객체를 생성해서 할당) ()

X_demand_scaled = scaler.fit_transform(df[DEMAND_VARS].values)
# X_demand_scaled(스케일완료배열은) = scaler(표준화기계야) 
# . fit_transform(데이터들의기준점(평균,편차)을잡고(fit) 바로그기준에맞춰변환(transform)해라) 
# ( 변환할 데이터는 df의[DEMAND_VARS 컬럼명단 리스트]의 . values(순수한값배열) )

X_demand_df = pd.DataFrame(X_demand_scaled, columns=DEMAND_VARS, index=df.index)
# X_demand_df(새로운표는) = pd(판다스야) . DataFrame(다시 표로 만들어라) 
# ( 데이터는 X_demand_scaled 숫자배열로, 
#   columns(컬럼이름표는) = DEMAND_VARS 이름들로, 
#   index(고유한 행번호표는) = df의.index(기존인덱스를 그대로 붙여서) )

X = pd.concat([X_demand_df, df[quarter_dummies + type_dummies].reset_index(drop=True).set_index(X_demand_df.index)], axis=1)
# X(가장 큰 최종 독립변수 표는) = pd(판다스야) . concat(표를 이어 붙여라) 
# ( [ 
#    첫번째 표는 X_demand_df(수요변수 스케일링 된 표), 
#    두번째 표는 df에서[ 더미변수 컬럼리스트 두개를 + (더해서 하나의 리스트로 만들어서) 
#                      컬럼들을 추출한 표 ] 를 
#    . reset_index(인덱스를 초기화하고) ( drop=True(기존 인덱스 숫자열은 버리고) ) 한 뒤 
#    . set_index(다시 새 인덱스를 똑같이 세팅해라) ( X_demand_df 의 . index 번호로 ) 한 표 
#   ], 
#   axis=1 (가로방향, 즉 열들을 좌우 옆으로 이어 붙여라) )

mask = ~X.isna().any(axis=1) & ~pd.isna(y)
# mask(필터조건 변수는) = 
# ~ (아닌 행들: X가 . isna(결측치가) () 
#   . any(하나라도 존재하는가?) (axis=1 가로행방향으로) )  
# & (그리고 둘 다 True여야 진짜 True:)  
# ~ (아닌 행들: pd가 . isna(결측치인지 판단) ( y 정답 데이터가 ) )

X_clean = X[mask].values
# X_clean(최종X배열은) = X의 [ mask(조건이 True, 즉 정상인 행만) ] 의 . values(순수 배열로)
y_clean = y[mask]
# 위와 동일 방식 통과된 정답값
groups_clean = df[mask]['상권_코드'].values
# 위와 동일 방식 통과된 상권코드 문자열 배열

feature_names = DEMAND_VARS + quarter_dummies + type_dummies
# 위 세개의 리스트를 + (더하기)로 하나의 기차처럼 길게 이어서 합침


# ══════════════════════════════════════════════════════
# 4. Lasso CV 적용
# ══════════════════════════════════════════════════════
gkf = GroupKFold(n_splits=5) 
# gkf(그룹나누기 기계는) = GroupKFold(그룹형광주리 클래스를 생성) 
# ( n_splits=5 (5개 조각으로 나눈다) )

cv_splits = list(gkf.split(X_clean, y_clean, groups=groups_clean))
# cv_splits(쪼개진 모의고사 세트는) = list(리스트형태로 변환) 
# ( gkf기계가 . split(데이터들을 쪼개라) 
#   ( X_clean데이터와, y_clean정답과, 
#     groups(참고할 그룹의 기준열)=groups_clean('상권_코드'정보) ) 결과를 )

lasso_cv = LassoCV(
    cv=cv_splits,             # cv (교차검증방법은) = 위에서만든 쪼갠세트(cv_splits)로
    max_iter=10000,           # max_iter (최대수학적 연산반복횟수는) = 10000 번
    random_state=42,          # random_state (난수발생 고정값은) = 42 로 (항상 같은결과리턴)
    n_alphas=100,             # n_alphas (알파라는 벌점 규제강도 후보개수는) = 100가지로 실험해라
)
# lasso_cv(내가 학습시킬 라쏘모델은) = LassoCV(라쏘 크로스검증 클래스 생성하고 위 설정값 입력)

lasso_cv.fit(X_clean, y_clean) 
# lasso_cv모델은 . fit(실제 데이터를 넣고 학습해라 마법을 부려라) 
# ( X_clean 문제특성데이터와, y_clean 정답데이터로 )

lasso_coef = pd.Series(lasso_cv.coef_, index=feature_names)
# lasso_coef(라쏘가 계산해낸 가중치결과 변수는) = pd(판다스의) 
# . Series(1차원 시리즈형태로 만들어라) 
# ( 데이터는 lasso_cv학습완료모델의 . coef_(각 변수에 부여된 가중치 속성값들) 을, 
#   index(그 가중치들의 라벨명은) = feature_names 전체변수명단 리스트로 )

lasso_selected = lasso_coef[lasso_coef != 0].sort_values(key=abs, ascending=False)
# lasso_selected(선택된 최종변수는) = lasso_coef시리즈객체에서 
# [ 조건: lasso_coef 값이 !=(다르다) 0과 (즉 0이 되버리지 않은, 살아남은애들) ] 행들만 골라서 
# . sort_values(값을 기준으로 정렬해라) 
# ( key=abs(절댓값 크기를 기준으로), 
#   ascending=False(내림차순, 즉 큰수부터 작은수로) )

lasso_zero = lasso_coef[lasso_coef == 0]
# lasso_zero(버려진 변수들은) = lasso_coef 에서 [ 값이 == 0 인 ] 행들만 모음


# ══════════════════════════════════════════════════════
# 5. ElasticNet CV 적용 (참고 확인용)
# ══════════════════════════════════════════════════════
l1_ratios = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 1.0]
# l1_ratios(변수는) = [ 이런 Lasso와 Ridge의 혼합 비율들의 리스트 ]

enet_cv = ElasticNetCV(
    l1_ratio=l1_ratios, # l1_ratio (라쏘 비중후보는) = l1_ratios 리스트에서 찾아보고
    cv=cv_splits,       # cv (모의고사세트는) = cv_splits 쪼개놓은 세트로 풀고
    max_iter=10000,     # max_iter (계산 최대노력은) = 10000번 반복
    random_state=42,    # random_state (시드는) = 42로 고정
    n_alphas=100,       # n_alphas (벌점 후보개수는) = 100가지로 설정
)
# enet_cv(엘라스틱넷모델은) = ElasticNetCV(위 설정값으로 클래스 생성)

enet_cv.fit(X_clean, y_clean)
# enet_cv모델은 . fit(실제 학습 시작해라) ( X_clean문제와, y_clean정답으로 )


# ══════════════════════════════════════════════════════
# 6. 정규화 경로(Lasso Path) 시각화 데이터 계산
# ══════════════════════════════════════════════════════
X_demand_only = X_clean[:, :len(DEMAND_VARS)]
# X_demand_only(순수 수요변수 행렬은) = X_clean전체배열에서 
# [ :(모든 행을), :(처음부터 len(DEMAND_VARS) 개수만큼의 열까지만) ] 잘라내서 모아라

alphas_path, coefs_path, _ = lasso_path(
    X_demand_only, y_clean, alphas=np.logspace(-4, 1, 100) 
)
# alphas_path(알파값들), coefs_path(그에따른 계수배열), _(안쓸 버릴값) 
# = lasso_path(그래프용 경로점들을 수학적으로 계산해라) 
# ( X_demand_only특성에 대해, y_clean정답으로, 
#   alphas 파라미터범위는=np의 . logspace(-4승부터, 1승까지, 100개구간으로 쪼갠값들로) )


# ══════════════════════════════════════════════════════
# 7. VIF 분석 (궁극의 다중공선성 점검)
# ══════════════════════════════════════════════════════
demand_selected_lasso = [v for v in DEMAND_VARS if v in lasso_selected.index]
# demand_selected_lasso(살아남은 수요변수 리스트는) = 
# [ v(변수명을 하나씩 모아라) 
#   for v in (DEMAND_VARS 전체 수요명단 안에서 뽑아내며) 
#   if (만약) v 가 in ( lasso_selected.index (라쏘가 끝까지 살려둔 명단) 안에 있다면 ) ]

if len(demand_selected_lasso) >= 2:
# 만약 len(살아남은 변수리스트 길이가) >= (크거나 같다면) 2 (최소 2개는 있어야 서로 중복검사하니까) :

    vif_data = df[mask][demand_selected_lasso].dropna()
    # vif_data(테스트용 실데이터는) = df에서[mask(오류없는 깨끗한 행들만)] 의 
    # [ demand_selected_lasso(살아남은 컬럼만) ] 추출하고 
    # . dropna(혹시 모를 결측치 한번 더 제거) ()
    
    vif_rows = []
    # vif_rows(계산결과를 담을 빈 리스트) = []
    
    for i, col in enumerate(demand_selected_lasso):
    # for(반복해라) i(순서를 나타내는 번호), col(실제 변원이름) 을 
    # in(안에서) enumerate(번호표를 1번부터 붙여서 짝지어 반환) 
    # ( demand_selected_lasso 리스트에 대해 ):
        
        vif_val = variance_inflation_factor(vif_data.values, i) 
        # vif_val(공선성점수는) = 
        # variance_inflation_factor(나머지 변수들로 얘를 설명가능한지 공선성 계산함수 실행) 
        # ( vif_data의.values(전체숫자배열과), i(현재 타겟으로 삼는 컬럼번호를) )
        
        vif_rows.append({'변수명': col, 'VIF': round(vif_val, 2)})
        # vif_rows리스트에 
        # . append(요소를 끝에 추가해라) 
        # ( { 딕셔너리형태로 '변수명': col이름, 'VIF': round(반올림해라)(vif_val점수를, 2째자리까지) } )
    
    vif_df = pd.DataFrame(vif_rows).sort_values('VIF', ascending=False)
    # vif_df(최종 점수표는) = pd(판다스의) 
    # . DataFrame(표 형태로 만들어라) ( vif_rows리스트 데이터들을 ) 
    # 한 뒤 . sort_values(정렬해라) 
    # ( 'VIF'컬럼 점수를 기준으로, ascending=False(내림차순, 즉 심각하게 큰 거부터 위로) )
