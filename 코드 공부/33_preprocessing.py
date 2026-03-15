"""
33_preprocessing.py
[코드 공부용: 왼쪽에서 오른쪽 직독직해 해석본 (줄바꿈 적용)]

목적:
이전 단계(32번)에서 Lasso로 골라낸 최종 6종류의 '알짜 수요 변수'들을
실제 분석(회귀 모델)에 넣기 전, 깨끗하게 다듬고 정규화하여 최종 데이터셋으로 저장합니다.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os

# ─── 경로 설정 ───────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
# BASE(기본 경로 변수는) = os.path(경로관리기능의) 
# . dirname(폴더이름만가져와라) 
# ( os.path.abspath(절대경로로바꿔라) 
# ( __file__(지금실행중인이파이썬파일경로를) ) )

DATA_PATH = os.path.join(BASE, 'y_demand_supply_trend_merge.csv')
# DATA_PATH(데이터경로는) = os.path 
# . join(경로를합쳐라) 
# ( BASE(기본폴더와), 'y_demand_supply_trend_merge.csv'(이 파일명을) )

OUT_PATH   = os.path.join(BASE, '33_analysis_ready.csv')
# OUT_PATH(저장할경로는) = os.path 
# . join(경로를합쳐라) 
# ( BASE(기본폴더와), '33_analysis_ready.csv'(결과파일명) )

LOG_PATH   = os.path.join(BASE, '33_preprocessing_log.txt')
# LOG_PATH(로그파일경로는) = os.path 
# . join(경로를합쳐라) 
# ( BASE(기본폴더와), '33_preprocessing_log.txt'(로그파일명) )

SCALER_PATH = os.path.join(BASE, '33_scaler_params.csv')
# SCALER_PATH(스케일러정보경로는) = os.path 
# . join(경로를합쳐라) 
# ( BASE(기본폴더와), '33_scaler_params.csv'(스케일러파일명) )

# ─── 최종 변수 목록 ───────────────────────────
DEMAND_VARS = [
    '집객시설_수',
    '총_직장_인구_수',
    '월_평균_소득_금액',
    '총_가구_수',
    '카페_검색지수',
    '지하철_노선_수',
]
# DEMAND_VARS(수요변수리스트는) = [ 라쏘 모델이 골라준 최종 알짜배기 변수 6개 명단 ]

TARGET = '당월_매출_금액'
# TARGET(목표정답변수는) = '당월_매출_금액' 문자열

ID_COLS = ['상권_코드', '상권_코드_명', '기준_년분기_코드', '상권_구분_코드_명_x']
# ID_COLS(식별자컬럼리스트는) = [ 상권을 식별할 수 있는 기본 정보 컬럼들 ]

SUPPLY_COLS = ['찻집_수', '카페음료_점포수']  
# SUPPLY_COLS(공급컬럼리스트는) = [ 나중에 Track B에서 쓸 공급 데이터들 명단 ]

logs = []
# logs(빈 리스트 변수) = [] (작업 기록들을 차곡차곡 모아둘 빈 바구니)

# ─────────────────────────────────────────────
# 1. 데이터 로드
# ─────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
# df(데이터프레임은) = pd(판다스의) 
# . read_csv(csv읽어오기) 
# ( DATA_PATH(데이터경로에서), encoding='utf-8-sig'(한글 안깨지게설정) )

logs.append(f"원본 데이터: {df.shape[0]}행 × {df.shape[1]}열")
# logs(바구니에) 
# . append(끝에추가해라) 
# ( f"원본 데이터: { df(데이터의) 
# . shape[0](0번째인 행개수) }행 × { df(데이터의) 
# . shape[1](1번째인 열개수) }열" )

logs.append(f"상권 수: {df['상권_코드'].nunique()}개")
# logs(바구니에) 
# . append(추가해라) 
# ( f"상권 수: { df의['상권_코드']열이 
# . nunique(중복없는종류가몇개냐) () }개" )

logs.append(f"분기: {sorted(df['기준_년분기_코드'].unique())}")
# logs(바구니에) 
# . append(추가해라) 
# ( f"분기: { sorted(정렬해라) 
# ( df의['기준_년분기_코드']가 
# . unique(고유값만뽑은것을) () ) }" )

# ─────────────────────────────────────────────
# 2. 이상치 제거 — 명동 관광특구
# ─────────────────────────────────────────────
myeongdong_mask = (
    df['상권_코드_명'].str.contains('명동', na=False) &
    (df['상권_구분_코드_명_x'] == '관광특구')
)
# myeongdong_mask(명동필터조건 변수는) = ( 
#   df의['상권_코드_명'] 이 
#   . str(문자로서) 
#   . contains(포함하는가) ('명동'을, na=결측치무시하고)
#   & (그리고 둘다 True여야함) 
#   df의['상권_구분_코드_명_x'] 가 
#   ==(완전똑같은가) '관광특구' 와 
# )

myeongdong_codes = df.loc[myeongdong_mask, '상권_코드'].unique()
# myeongdong_codes(명동상권코드들은) = df의 
# . loc(해당위치데이터불러와라) 
# [ myeongdong_mask(필터조건이참인행), '상권_코드'(이열만) ] 
# 의 . unique(중복없는값들만) ()

df = df[~df['상권_코드'].isin(myeongdong_codes)].copy()
# df(는새로덮어써라) = df에서 
# [ ~(아닌행들만) 
# df의['상권_코드'] 가 
# . isin(안에포함된) (myeongdong_codes리스트에) ] 
# 엑기스만 . copy(안전하게 독립된 복사본으로 생성) ()

logs.append(f"\n[이상치 제거] 명동 관광특구: {len(myeongdong_codes)}개 상권 제거")
# logs(에) 
# . append(추가) 
# ( f"[이상치 제거] 명동 관광특구: { len(길이가얼마냐)(myeongdong_codes) }개 상권 제거" )

logs.append(f"  → 잔류: {df.shape[0]}행")
# logs(에) 
# . append(추가) 
# ( f"  → 잔류: { df의 . shape[0](행개수) }행" )

# ─────────────────────────────────────────────
# 3. Y변수 생성
# ─────────────────────────────────────────────
df['y_log'] = np.log1p(df[TARGET])
# df의['y_log']새컬럼은 = np(넘파이의) 
# . log1p(자연로그씌우고 1더해라) 
# ( df의[TARGET('당월_매출_금액')] 데이터들에 )

logs.append(f"\n[Y변수] log1p 변환 완료. 0값 행 수: {(df[TARGET] == 0).sum()}")
# logs(에) 
# . append(추가) 
# ( f"... 0값 행 수: { ( df의[TARGET]이 == 0인조건 ) 
# 의 . sum(그개수를다더하라) () }" )

# ─────────────────────────────────────────────
# 4. 결측 처리
# ─────────────────────────────────────────────
b1 = set(df[df['총_직장_인구_수'].isna()]['상권_코드'].unique())
# b1(직장인구결측상권은) = set(집합으로만들어라) 
# ( df에서 [ df의['총_직장_인구_수'] 가 
# . isna(빈칸인) () ] 
# 의 ['상권_코드'] 를 
# . unique(고유값만) () 한것을 )

b2 = set(df[df['총_가구_수'].isna()]['상권_코드'].unique())
# b2(가구수결측상권은) = set(집합생성) 
# ( df에서 [ df의['총_가구_수'] 가 
# . isna(빈칸인) () ] 
# 의 ['상권_코드'] 를 
# . unique(고유값만) () 한것을 )

remove_b = b1 | b2
# remove_b(제거대상은) = b1(과) |(합집합해라) b2(를)

df = df[~df['상권_코드'].isin(remove_b)].copy()
# df(는) = df에서 
# [ ~(아닌행만) df의['상권_코드']가 
# . isin(포함된) (remove_b에) ] 
# . copy(복사) ()

logs.append(f"\n[그룹 B] 구조적 전체 결측 상권 제거: {len(remove_b)}개")
# logs . append 
# ( f"... 제거: { len(길이)(remove_b) }개" )

logs.append(f"  총_직장_인구_수 결측: {len(b1)}개 / 총_가구_수 결측: {len(b2)}개")
# logs . append 
# ( f"... 직장결측: { len(b1) }개 / 가구결측: { len(b2) }개" )

logs.append(f"  → 잔류: {df.shape[0]}행")
# logs . append 
# ( f"... 잔류: { df.shape[0](행수맞춤) }행" )

c1 = set(df[df['월_평균_소득_금액'].isna()]['상권_코드'].unique())
# c1(소득결측상권) = set(집합) 
# ( df[ df['월_평균_소득_금액'] 
# . isna() ] 
# 의 ['상권_코드'] 
# . unique() )

remove_c = c1 - remove_b
# remove_c(소득만결측상권) = c1(에서) 
# -(차집합빼라) 
# remove_b(이미지울애들)

df = df[~df['상권_코드'].isin(remove_c)].copy()
# df(는) = df에서 
# [ ~(아닌행만) 
# df['상권_코드']가 
# . isin(포함된) (remove_c에) ] 
# . copy() ()

logs.append(f"\n[그룹 C] 소득 미연계 상권 제거: {len(remove_c)}개")
# logs . append 
# ( f"... 제거: { len(remove_c) }개" )

logs.append(f"  → 잔류: {df.shape[0]}행")
# logs . append 
# ( f"... 잔류: { df.shape[0] }행" )

miss_jip = df[df['집객시설_수'].isna()].groupby('상권_코드').size()
# miss_jip(집객시설결측통계) = df에서 
# [ df['집객시설_수'] 
# . isna(빈칸인) () ] 들을 
# . groupby(그룹으로묶어라) ('상권_코드'로) 
# . size(각상권별빈칸개수세어라) ()

structural_jip = set(miss_jip[miss_jip >= 9].index)
# structural_jip(구조적결측상권) = set(집합) 
# ( miss_jip에서 
# [ miss_jip값이 >= 9 인것들 ] 의 
# . index(그상권명단만) )

df = df[~df['상권_코드'].isin(structural_jip)].copy()
# df(는) = df에서 
# [ ~(아닌행만) 
# df['상권_코드']가 
# . isin(포함된) (structural_jip에) ] 
# . copy() ()

logs.append(f"\n[그룹 D] 집객시설_수 구조적 결측 상권 제거: {len(structural_jip)}개")
# logs . append 
# ( f"... 제거: { len(structural_jip) }개" )

before_ffill = df['집객시설_수'].isna().sum()
# before_ffill(채우기전빈칸수) = df의['집객시설_수'] 에서 
# . isna(빈칸인것의) 
# . sum(총합을구해라) ()

df = df.sort_values(['상권_코드', '기준_년분기_코드'])
# df(는) = df를 
# . sort_values(정렬해라) 
# ( ['상권_코드'별로먼저묶고, '기준_년분기_코드'시간순으로] )

df['집객시설_수'] = df.groupby('상권_코드')['집객시설_수'].transform(
    lambda x: x.ffill().bfill()
)
# df의['집객시설_수']는 = df를 
# . groupby('상권_코드'기준으로묶고) 
# ['집객시설_수']에대해 
# . transform(일괄변환적용해라) 
# ( lambda x(각그룹요소별로): x 
# . ffill(위에서아래로과거값채우기) () 
# . bfill(아래서위로미래값채우기) () )

after_ffill = df['집객시설_수'].isna().sum()
# after_ffill(채운후빈칸수) = df의['집객시설_수'] 
# . isna() 
# . sum(총합구해라) ()

logs.append(f"  forward/backward fill: {before_ffill}개 결측 → {after_ffill}개 결측")
# logs . append 
# ( f"... 채우기전 {before_ffill} → 채운후 {after_ffill}" )

logs.append(f"  → 잔류: {df.shape[0]}행")
# logs . append 
# ( f"... 잔류: {df.shape[0]}행" )

remaining_na = df[DEMAND_VARS + ['y_log']].isna().any(axis=1).sum()
# remaining_na(끝까지남은빈칸수) = df의 
# [ DEMAND_VARS리스트 + ['y_log']리스트 를합친전체컬럼들 ] 에대해 
# . isna(빈칸이) () 
# . any(하나라도있는가) (axis=1가로행기준) 의 
# . sum(그런행의개수총합) ()

logs.append(f"\n[최종 결측 확인] 잔여 결측 행: {remaining_na}개 → 제거")
# logs . append 
# ( f"... 잔여결측: {remaining_na}개" )

df = df.dropna(subset=DEMAND_VARS + ['y_log']).copy()
# df(는) = df에서 
# . dropna(빈칸있은행을버려라) 
# ( subset(이기준컬럼들중에비어있으면) = DEMAND_VARS + ['y_log'] ) 
# . copy(안전복사) ()

logs.append(f"  → 최종 잔류: {df.shape[0]}행, {df['상권_코드'].nunique()}개 상권")
# logs . append 
# ( f"... 잔류: {df.shape[0]}행, 
# {df['상권_코드'] . nunique(중복없는상권수) ()}개 상권" )

# ─────────────────────────────────────────────
# 5. 더미변수 생성
# ─────────────────────────────────────────────
quarters = sorted(df['기준_년분기_코드'].unique())
# quarters(분기리스트) = sorted(시간순정렬) 
# ( df의['기준_년분기_코드']가 
# . unique(고유한종류들만) () )

base_quarter = quarters[0]  
# base_quarter(기준분기는) = quarters의 [0]
# (가장첫번째원소, 다중공선성을 막기위해 뺄 기준점)

for q in quarters[1:]:
# for(반복해라) q(각분기를) 
# in(안에서) quarters의[1: (두번째원소부터끝까지)] :

    df[f'Q_{q}'] = (df['기준_년분기_코드'] == q).astype(int)
    # df의[새로운'Q_분기'컬럼]은 = ( df의['기준_년분기_코드']가 
    # ==(동일한지) q(현재루프분기와) ) 판단후 
    # . astype(타입바꿔라) (int(정수로, True는1 False는0))

quarter_dummies = [f'Q_{q}' for q in quarters[1:]]
# quarter_dummies(분기더미명단리스트) = [ f'Q_{q}'텍스트들을모아라 
# for(q를반복하며) in( quarters의[1:]번째부터 ) ]

logs.append(f"\n[더미변수] 분기 더미 {len(quarter_dummies)}개 생성 (기준: {base_quarter})")
# logs . append 
# ( f"... 더미 { len(길이)(quarter_dummies) }개 생성 
# (기준: {base_quarter})" )

logs.append(f"  {quarter_dummies}")
# logs . append 
# ( f"  {quarter_dummies 리스트내용출력}" )

type_col = '상권_구분_코드_명_x'
# type_col(상권유형컬럼이름) = '상권_구분_코드_명_x'

types = df[type_col].unique()
# types(상권유형종류들) = df의[type_col] 에서 
# . unique(고유한것만뽑아라) ()

logs.append(f"\n[더미변수] 상권유형 분포:\n{df[type_col].value_counts().to_string()}")
# logs . append 
# ( f"... 분포:\n{ df의[type_col] 을 
# . value_counts(항목별개수를세어라) () 한뒤 
# . to_string(단순문자열형태로바꿔라) () }" )

for t in ['관광특구', '발달상권', '전통시장']:
# for(반복해라) t(각타입을) 
# in(이3가지에대해서만) ['관광특구', '발달상권', '전통시장'] : 
# ('골목상권'은 기준점이라 뺌)

    df[f'TYPE_{t}'] = (df[type_col] == t).astype(int)
    # df의[새로운'TYPE_유명'컬럼]은 = ( df의[type_col] 이 
    # ==(동일한지) t ) 판단후 
    # . astype(타입바꿔라) (int(숫자 1과0으로))

type_dummies = ['TYPE_관광특구', 'TYPE_발달상권', 'TYPE_전통시장']
# type_dummies(유형더미명단리스트) = ['TYPE_관광특구', 'TYPE_발달상권', 'TYPE_전통시장']

logs.append(f"  유형 더미 {len(type_dummies)}개 생성 (기준: 골목상권)")
# logs . append 
# ( f"  유형 더미 { len(type_dummies) }개 생성" )

# ─────────────────────────────────────────────
# 6. 표준화 (수요 변수만, 더미·Y 변수는 제외!)
# ─────────────────────────────────────────────
scaler = StandardScaler()
# scaler(표준화기계는) = StandardScaler(알맹이기계생성) ()

demand_scaled_cols = [f'{v}_scaled' for v in DEMAND_VARS]
# demand_scaled_cols(스케일컬럼명단리스트) = [ f'{v}_scaled'형태로모아라 
# for(v를반복하며) in( DEMAND_VARS수요변수명단안에서 ) ]

df[demand_scaled_cols] = scaler.fit_transform(df[DEMAND_VARS])
# df의[demand_scaled_cols명단의새컬럼들] 에는 = scaler기계가 
# . fit_transform(평균분산을학습하고스케일숫자로변환해라) 
# ( df의[DEMAND_VARS컬럼들] 데이터배열을 )

scaler_df = pd.DataFrame({
    '변수명': DEMAND_VARS,
    'mean': scaler.mean_,
    'std': scaler.scale_
})
# scaler_df(스케일러정보표) = pd(판다스의) 
# . DataFrame(문서표를만들어라) 
# ( { 딕셔너리형태로 
#     '변수명': DEMAND_VARS명단, 
#     'mean': scaler가학습한.mean_(평균값들배열), 
#     'std': scaler가학습한.scale_(표준편차값들배열) 
# } )

scaler_df.to_csv(SCALER_PATH, index=False, encoding='utf-8-sig')
# scaler_df(정보표)를 
# . to_csv(csv파일로내보내라) 
# ( SCALER_PATH경로에, 
# index=False(행번호열은무시해라), 
# encoding='utf-8-sig'(한글안깨지게) )

logs.append(f"\n[표준화] 수요 변수 {len(DEMAND_VARS)}개 StandardScaler 적용")
# logs . append 
# ( f"... 변수 { len(DEMAND_VARS) }개 적용" )

logs.append(f"  스케일러 파라미터 저장: {SCALER_PATH}")
# logs . append 
# ( f"  스케일러 파라미터 저장: {SCALER_PATH경로}" )


# ─────────────────────────────────────────────
# 7. 최종 컬럼 구성 및 저장
# ─────────────────────────────────────────────
X_COLS = demand_scaled_cols + quarter_dummies + type_dummies
# X_COLS(독립변수x들통합리스트) = demand_scaled_cols(스케일수요명단) 
# +(더해라) quarter_dummies(분기명단) 
# +(더해라) type_dummies(유형명단)

logs.append(f"\n[최종 X 변수] 총 {len(X_COLS)}개:")
# logs . append 
# ( f"... 총 { len(X_COLS) }개:" )

logs.append(f"  수요(표준화): {demand_scaled_cols}")
# logs . append 
# ( f"  수요(표준화): {demand_scaled_cols 리스트목록}" )

logs.append(f"  분기더미: {quarter_dummies}")
# logs . append 
# ( f"  분기더미: {quarter_dummies 리스트목록}" )

logs.append(f"  유형더미: {type_dummies}")
# logs . append 
# ( f"  유형더미: {type_dummies 리스트목록}" )

save_cols = (
    ID_COLS
    + ['y_log', TARGET]
    + DEMAND_VARS           
    + demand_scaled_cols    
    + quarter_dummies
    + type_dummies
    + [c for c in SUPPLY_COLS if c in df.columns]  
)
# save_cols(저장할모든컬럼리스트) = (
#     ID_COLS(상권기본정보) 
#     +(더해라) ['y_log', TARGET](정답데이터두개) 
#     +(더해라) DEMAND_VARS(원본수치데이터들) 
#     +(더해라) demand_scaled_cols(스케일된데이터들) 
#     +(더해라) quarter_dummies(시간더미들) 
#     +(더해라) type_dummies(유형더미들) 
#     +(더해라) [ c(이름을모아라) 
#                 for c in ( SUPPLY_COLS공급명단안에서 ) 
#                 if (만약) c 가 in ( df.columns 이데이터프레임컬럼명단안에존재한다면 ) ]
# )

seen = set()
# seen(이미본컬럼저장소) = set(빈집합생성)

save_cols_dedup = []
# save_cols_dedup(중복제거된최종컬럼명단) = [](빈리스트)

for c in save_cols:
# for(반복해라) c(컬럼하나하나를) 
# in(차례대로) save_cols(기차리스트에서) :

    if c not in seen and c in df.columns:
    # if(만약) c(현재컬럼이) 
    # not in (들어있지않다면) seen(이미본저장소에) 
    # and (그리고) c 가 in (들어있다면) df.columns(실제표의컬럼명단안에) :

        seen.add(c)
        # seen집합에 . add(추가해라지금본걸로) (c를)

        save_cols_dedup.append(c)
        # save_cols_dedup리스트에 . append(끝에추가해라) (c를)

df_out = df[save_cols_dedup].copy()
# df_out(최종출력용표는) = df에서 
# [ save_cols_dedup(중복제거정제된컬럼명단) ] 
# 만싹뽑아서 . copy(안전복제본생성) ()

df_out.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')
# df_out표를 . to_csv(csv파일로저장해라) 
# ( OUT_PATH경로에, 
# index=False(행번호무시), 
# encoding='utf-8-sig'(한글안깨짐) )

logs.append(f"\n[저장 완료] {OUT_PATH}")
# logs . append 
# ( f"... 완료] {OUT_PATH경로명출력}" )

logs.append(f"  출력 형태: {df_out.shape[0]}행 × {df_out.shape[1]}열")
# logs . append 
# ( f"... 형태: { df_out.shape[0] }행 × { df_out.shape[1] }열" )

logs.append(f"  상권 수: {df_out['상권_코드'].nunique()}개")
# logs . append 
# ( f"... 상권 수: { df_out['상권_코드']
# .nunique(중복안쳐추출) () }개" )

logs.append(f"  분기 수: {df_out['기준_년분기_코드'].nunique()}개")
# logs . append 
# ( f"... 분기 수: { df_out['기준_년분기_코드']
# .nunique() }개" )

# ─────────────────────────────────────────────
# 8. 최종 요약 출력
# ─────────────────────────────────────────────
logs.append("\n" + "="*50)
logs.append("=== 전처리 완료 요약 ===")
logs.append("="*50)
logs.append(f"원본:  9,760행 → 최종: {df_out.shape[0]}행")
logs.append(f"상권:  원본 1,139개 → 최종 {df_out['상권_코드'].nunique()}개")
logs.append(f"모델 X: {len(X_COLS)}개 변수 (수요 6개 + 분기더미 {len(quarter_dummies)}개 + 유형더미 {len(type_dummies)}개)")
logs.append(f"모델 Y: y_log (log1p 변환)")
logs.append(f"모델:  Pooled OLS (VIF 최대 3.28 → Ridge 불필요)")
logs.append("")
logs.append("Track A 수요 변수 (표준화 후):")
# (위 줄들은 단순 로그바구니에 텍스트들을 넣는 작업이라 해석 생략)

for i, v in enumerate(DEMAND_VARS, 1):
# for(반복해라) i(순번번호), v(변수명) 을 
# in(안에서뽑아가며) enumerate(번호달아주는기능) 
# ( DEMAND_VARS리스트에대해, 1(번호1번부터시작해라) ) :

    logs.append(f"  {i}. {v}")
    # logs . append ( f"  {i번}. {v이름}" )

log_text = "\n".join(logs)
# log_text(로그최종텍스트문서는) = "\n"(줄바꿈기호)를접착제삼아서 
# . join(다이어붙여라) 
# ( logs리스트안의모든문장들을 )

with open(LOG_PATH, 'w', encoding='utf-8') as f:
# with(작업끝나면자동으로파일닫기) open(파일을열어라) 
# ( LOG_PATH경로파일을, 
# 'w'(덮어쓰기모드로), 
# encoding='utf-8'(한글텍스트로) ) 
# as f (그 열어둔 통로를 임시로 f라고 하자) :

    f.write(log_text)
    # f(바깥으로이어진통로에) 
    # . write(텍스트를써라) ( log_text를 )

print(log_text)
# print(화면에출력해라) ( log_text를 )

print(f"\n저장: {OUT_PATH}")
# print(출력) ( f"저장: {OUT_PATH경로}" )

print(f"로그: {LOG_PATH}")
# print(출력) ( f"로그: {LOG_PATH경로}" )
