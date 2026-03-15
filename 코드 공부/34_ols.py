"""
34_ols.py
[코드 공부용: 왼쪽에서 오른쪽 직독직해 해석본 (줄바꿈 최적화)]

목적:
이전 단계(33번)에서 깔끔하게 정돈된 데이터를 가지고
'선형 회귀분석(OLS)' 모델을 돌립니다.
여기서 모델이 '실제 매출액'과 '자기가 예측한 매출액' 간에
얼마나 크게 틀렸는지 그 '오차(잔차, Residual)'를 구합니다.
이 오차가 마이너스(-)로 크게 틀릴수록 "실제 매출은 낮은데 상권 포텐셜은 높은" 
숨겨진 블루오션을 의미하게 됩니다!
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
import os

# ─── 경로 설정 ───────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
# BASE(기본경로) = os.path 
# . dirname(폴더이름만가져와라) 
# ( os.path.abspath(절대경로로바꿔라) 
# ( __file__(현재파이썬파일경로) ) )

IN_PATH      = os.path.join(BASE, '33_analysis_ready.csv')
# IN_PATH(입력데이터경로) = os.path . join(합쳐라) 
# ( BASE(폴더와), '33_analysis_ready.csv' )

OUT_OOF      = os.path.join(BASE, '34_oof_residuals.csv')
# OUT_OOF(행별오차결과경로) = os.path . join(합쳐라) 
# ( BASE(폴더와), '34_oof_residuals.csv' )

OUT_DISTRICT = os.path.join(BASE, '34_district_residuals.csv')
# OUT_DISTRICT(상권별결과경로) = os.path . join(합쳐라) 
# ( BASE, '34_district_residuals.csv' )

OUT_COEF     = os.path.join(BASE, '34_model_coefficients.csv')
# OUT_COEF(최종가중치결과경로) = os.path . join(합쳐라) 
# ( BASE, '34_model_coefficients.csv' )

OUT_LOG      = os.path.join(BASE, '34_ols_log.txt')
# OUT_LOG(작업로그경로) = os.path . join(합쳐라) 
# ( BASE, '34_ols_log.txt' )

logs = []
# logs(기록바구니) = [] (빈리스트)

# ─────────────────────────────────────────────
# 1. 데이터 로드
# ─────────────────────────────────────────────
df = pd.read_csv(IN_PATH, encoding='utf-8-sig')
# df(데이터프레임) = pd 
# . read_csv(csv읽어와라) 
# ( IN_PATH(경로에서), encoding='utf-8-sig'(한글안깨짐) )

logs.append(f"입력 데이터: {df.shape[0]}행 × {df.shape[1]}열")
# logs(바구니에) 
# . append(추가해라) 
# ( f"입력: { df.shape[0](행) }행 × { df.shape[1](열) }열" )

logs.append(f"상권 수: {df['상권_코드'].nunique()}개")
# logs 
# . append(추가해라) 
# ( f"상권: { df['상권_코드'] . nunique(중복없는개수) () }개" )

logs.append(f"분기 수: {df['기준_년분기_코드'].nunique()}개")
# logs 
# . append(추가해라) 
# ( f"분기: { df['기준_년분기_코드'] . nunique() }개" )

DEMAND_SCALED = [
    '집객시설_수_scaled', '총_직장_인구_수_scaled', '월_평균_소득_금액_scaled',
    '총_가구_수_scaled', '카페_검색지수_scaled', '지하철_노선_수_scaled'
]
# DEMAND_SCALED(스케일된수요변수명단) = [ 6개 변수 이름들 ]

QUARTER_DUMMIES = [c for c in df.columns if c.startswith('Q_')]
# QUARTER_DUMMIES(분기더미명단) = [ c(이름을모아라) 
# for c in df.columns(컬럼명단중에서) 
# if c 가 . startswith('Q_')(글자 'Q_'로 시작한다면) ]

TYPE_DUMMIES    = [c for c in df.columns if c.startswith('TYPE_')]
# TYPE_DUMMIES(상권유형더미명단) = [ c(이름을모아라) 
# for c in df.columns(컬럼들중에서) 
# if c 가 . startswith('TYPE_')(글자 'TYPE_'로 시작한다면) ]

X_COLS = DEMAND_SCALED + QUARTER_DUMMIES + TYPE_DUMMIES
# X_COLS(독립변수X전체명단) = DEMAND_SCALED +(합쳐라) 
# QUARTER_DUMMIES +(합쳐라) TYPE_DUMMIES

X      = df[X_COLS].values
# X(모델에넣을X데이터들) = df의 [ X_COLS컬럼들 ] 
# 의 . values(순수숫자배열만뽑아라)

y      = df['y_log'].values
# y(모델이맞출정답데이터) = df의 [ 'y_log'컬럼 ] 
# 의 . values(순수숫자배열만뽑아라)

groups = df['상권_코드'].values
# groups(그룹핑용정답형태) = df의 [ '상권_코드' ] 
# 의 . values(숫자배열)

logs.append(f"\nX 변수 {len(X_COLS)}개:")
logs.append(f"  수요(표준화) : {DEMAND_SCALED}")
logs.append(f"  분기더미     : {QUARTER_DUMMIES}")
logs.append(f"  유형더미     : {TYPE_DUMMIES}")
# (위 4줄은 로그바구니에 명단들을 문자열로 넣는 작업)

# ─────────────────────────────────────────────
# 2. GroupKFold OOF 잔차 추출 (컨닝 방지 모의고사 5세트)
# ─────────────────────────────────────────────
gkf = GroupKFold(n_splits=5)
# gkf(그룹나누기기계) = GroupKFold(컨닝방지묶음기능) 
# ( n_splits=5(5등분해라) )

oof_residuals = np.full(len(y), np.nan)
# oof_residuals(에러점수기록지) = np(넘파이) 
# . full(전부다이거로채워라) 
# ( len(y)(정답개수만큼의크기로), np.nan(일단빈칸으로) )

oof_pred      = np.full(len(y), np.nan)
# oof_pred(모델예측값기록지) = np 
# . full(가득채워라) 
# ( len(y)(정답개수만큼), np.nan(일단빈칸으로) )

fold_r2s      = []
# fold_r2s(모의고사5번의점수함) = [] (빈리스트)

logs.append(f"\n[GroupKFold] n_splits=5, groups=상권_코드")
logs.append(f"  → 같은 상권의 9개 분기가 통째로 train/test 분리 (data leakage 방지)")
# (기록용 텍스트 추가)

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups=groups)):
# for(반복해라) fold(몇번째세트인지번호), 
# (train_idx(학습용문제번호리스트), test_idx(시험용문제번호리스트)) 요렇게짝을지어서 
# in(안에서) enumerate(번호달아주기) 
# ( gkf기계가 . split(나누어준결과들) 
#   ( X(문제집), y(정답지), groups=groups(상권을통째로묶어서) ) 
# ) :

    X_train, X_test = X[train_idx], X[test_idx]
    # X_train(학습용X), X_test(시험용X) 
    # = X[학습번호들], X[시험번호들] 로 나눠가짐

    y_train, y_test = y[train_idx], y[test_idx]
    # y_train(학습용Y정답), y_test(시험용Y정답) 
    # = y[학습번호들], y[시험번호들] 로 나눠가짐

    model = LinearRegression()
    # model(선형회귀기계) = LinearRegression(기본예측모델) ()

    model.fit(X_train, y_train)
    # model(기계야) . fit(학습해라) 
    # ( X_train(이문제들로), y_train(이정답을맞추도록) )

    y_pred     = model.predict(X_test)
    # y_pred(기계가예측한정답지) = model기계가 
    # . predict(시험쳐봐라예측해봐라) 
    # ( X_test(한번도안본새시험문제들로) )

    residuals  = y_test - y_pred  
    # residuals(오차에러점수들) = y_test(원래실제정답) -(빼기) y_pred(기계가예측한결과)
    # 해석: (양수=실제가더높음(좋은곳), 음수=실제가더낮음(저성과, 블루오션후보!))

    oof_pred[test_idx]      = y_pred
    # oof_pred기록지안의 [ 이번시험친번호들칸 ] 에다 = y_pred(예측값들) 을 쑥 채워넣어라

    oof_residuals[test_idx] = residuals
    # oof_residuals오차기록지안의 [ 이번시험친번호들칸 ] 에다 = residuals(계산한오차들) 을 채워넣어라

    fold_r2          = r2_score(y_test, y_pred)
    # fold_r2(이번시험성적표점수) = r2_score(성적계산해주는스킬) 
    # ( y_test(실제정답) 대비, y_pred(제출한답안지) ) 의 점수

    n_test_districts = len(np.unique(groups[test_idx]))
    # n_test_districts(이번에시험친상권개수) = len(길이) 
    # ( np.unique(중복없는고유값만) ( groups안의[이번시험친번호들칸] ) )

    fold_r2s.append(fold_r2)
    # fold_r2s성적함에 . append(추가해라) ( fold_r2(이번시험점수를) )

    logs.append(f"  Fold {fold+1}: test {len(test_idx)}행 ({n_test_districts}개 상권) | R²={fold_r2:.4f}")
    # (몇번째 모의고사에서 점수가 몇점나왔는지 문자열로 기록)

mean_r2 = np.mean(fold_r2s)
# mean_r2(최종평균점수) = np . mean(평균내라) ( fold_r2s(5번의성적들) )

logs.append(f"\n  OOF 평균 R²: {mean_r2:.4f}")
logs.append(f"  잔차 완성: nan 수 = {np.isnan(oof_residuals).sum()}")
# (최종 성적과 빈칸(nan)이 남아있는지 확인해서 로그에 기록)

# ─────────────────────────────────────────────
# 3. 전체 데이터 OLS — 계수 해석용
# ─────────────────────────────────────────────
full_model = LinearRegression()
# full_model(전체학습용기계) = LinearRegression(선형모델생성) ()

full_model.fit(X, y)
# full_model기계가 . fit(전체를다보고학습해라) 
# ( X(모든문제집), y(모든정답지) )

full_r2 = r2_score(y, full_model.predict(X))
# full_r2(전체오픈북시험점수) = r2_score(성적매겨라) 
# ( y(실제정답), full_model기계가 . predict(예측한답) (X) 전체에대해 )

logs.append(f"\n[전체 데이터 OLS] R²={full_r2:.4f} (해석용, OOF 아님)")

coef_df = pd.DataFrame({
    '변수명': X_COLS,
    '계수':   full_model.coef_
}).sort_values('계수', ascending=False)
# coef_df(가중치정리표) = pd.DataFrame(표생성) 
# ( { '변수명'열엔: X_COLS리스트, 
#     '계수(가중치)'열엔: full_model기계가학습한 . coef_(각변수의중요도점수배열) 
# } ) 
# 한 표를 . sort_values(정렬해라) 
# ( '계수'컬럼을기준으로, ascending=False(가장큰숫자부터내림차순으로) )

coef_df.to_csv(OUT_COEF, index=False, encoding='utf-8-sig')
# coef_df표를 . to_csv(csv파일로저장해라) ( OUT_COEF경로에 )

logs.append("\n계수 순위 (전체):")
for _, row in coef_df.iterrows():
# for(반복해라) _(행번호는무시하고), row(각가로줄내용을) 
# in(꺼내면서) coef_df표를 . iterrows(한줄씩반복해주는스킬) () 해서 :

    logs.append(f"  {row['변수명']:40s}: {row['계수']:+.4f}")
    # logs바구니에가중치정보를기록해라!

# ─────────────────────────────────────────────
# 4. 행별 OOF 잔차 저장
# ─────────────────────────────────────────────
df_oof = df[['상권_코드', '상권_코드_명', '기준_년분기_코드',
             '상권_구분_코드_명_x', 'y_log', '당월_매출_금액',
             '찻집_수', '카페음료_점포수']].copy()
# df_oof(결과저장용표) = df에서 
# [ 기본적인상권정보와, 매출결과, 공급수량(찻집수등) 등 필요한컬럼들만 ] 
# 쏙 뽑아서 . copy(독립된새표명세서로복사) ()

df_oof['oof_pred']     = oof_pred
# df_oof표의['oof_pred'새컬럼]에 = oof_pred(아까시험쳐서가득채운예측값들) 을 쏙

df_oof['oof_residual'] = oof_residuals
# df_oof표의['oof_residual'새컬럼]에 = oof_residuals(아까구해둔오차값들) 을 쏙

df_oof.to_csv(OUT_OOF, index=False, encoding='utf-8-sig')
# df_oof결과표를 . to_csv(파일로저장) ( OUT_OOF경로에 )

logs.append(f"\n[저장] 행별 OOF 잔차: {OUT_OOF}")

# ─────────────────────────────────────────────
# 5. 상권별 집계 (최종 블루오션 찾기 작업)
# ─────────────────────────────────────────────
latest_q = int(df['기준_년분기_코드'].max())
# latest_q(가장최신분기번호) = int(정수로바꿔라) 
# ( df의['기준_년분기_코드'] 중에 . max(가장큰숫자) () )

logs.append(f"\n[집계] 최신 분기: {latest_q}")

# 최신 분기만 추려내기
df_latest = df_oof[df_oof['기준_년분기_코드'] == latest_q][
    ['상권_코드', '상권_코드_명', '상권_구분_코드_명_x',
     'oof_residual', 'oof_pred', 'y_log', '당월_매출_금액', '찻집_수']
].copy()
# df_latest(최신데이터표) = df_oof에서 
# [ df_oof의['기준_년분기_코드'] 가 ==(완전똑같은) latest_q(최신분기와) 행들만 ] 
# 뽑은뒤 그중에서 [ 필요한명단컬럼들만 ] 또 뽑아서 . copy() ()

df_latest.columns = [
    '상권_코드', '상권_코드_명', '상권유형',
    'residual_latest', 'pred_latest', 'y_log_latest', '매출_latest', '찻집수_latest'
]
# df_latest의 . columns(컬럼이름들을) = [ 이 직관적인 새로운 이름명단으로 ] 통째로바꿔치기!

# 9개 분기(2년치) 평균 오차 구하기
df_avg = df_oof.groupby('상권_코드').agg(
    residual_avg=('oof_residual', 'mean'),
    residual_std=('oof_residual', 'std'),
    n_quarters  =('oof_residual', 'count'),
).reset_index()
# df_avg(평균오차표) = df_oof를 
# . groupby('상권_코드'별로묶고) 
# . agg(여러가지계산을동시에진행해라) (
#     residual_avg 라는이름으로 = ('oof_residual'컬럼의, 'mean'평균값을),
#     residual_std 라는이름으로 = ('oof_residual'컬럼의, 'std'표준편차를),
#     n_quarters   라는이름으로 = ('oof_residual'컬럼의, 'count'개수를세어라),
# ) 한 표를 . reset_index(인덱스를정상적인열로풀어줘라) ()

# 두 표를 합치기
df_dist = df_latest.merge(df_avg, on='상권_코드', how='left')
# df_dist(합쳐진최종결과표) = df_latest(최신표에다가) 
# . merge(합쳐라병합해라) 
# ( df_avg(평균표를), on='상권_코드'(이컬럼을연결고리기준으로), 
# how='left'(df_latest표를기준으로살려가며) )

# Track B: 공급부족지수 
df_dist['supply_shortage'] = 1 / (df_dist['찻집수_latest'] + 1)
# df_dist표의['supply_shortage'새컬럼]은 
# = 1 을나누기 ( df_dist['찻집수_latest'] 개수에다가 + 1해서 (분모가0이되는걸막기위해) )
# (찻집이 적을수록 분모가 작아지니 공급부족지수는 엄청 커지는 현상!)

# 잔차 일관성 플래그 (계속 마이너스 성과를 냈는가?)
df_dist['residual_consistent'] = (
    (df_dist['residual_latest'] < 0) & (df_dist['residual_avg'] < 0)
)
# df_dist['residual_consistent'진실거짓컬럼]은 = (
#     (최신오차가 < 0보다작은가?) & (그리고교집합) 
#     (2년치평균오차도 < 0보다작은가?) 
# ) 둘다 True면 일관성있는 구조적 블루오션!

# 블루오션 1차 후보 선정 (실적나쁘고 경쟁사없는곳)
df_dist['blueocean_candidate'] = (
    (df_dist['residual_latest'] < 0) &
    (df_dist['찻집수_latest'] <= 1)
)
# df_dist['blueocean_candidate'후보컬럼]은 = (
#     (최신오차가 < 0보다작은저성과인가) & (그리고)
#     (최신찻집수가 <= 1개이하인가)
# )

df_dist = df_dist.sort_values('residual_latest')
# df_dist(는) = df_dist를 
# . sort_values(정렬해라) 
# ( 'residual_latest'최신오차점수를기준으로 (작은수=가장저성과)부터 시작하게 )

df_dist.to_csv(OUT_DISTRICT, index=False, encoding='utf-8-sig')
# df_dist최종표를 . to_csv(csv파일저장) ( OUT_DISTRICT경로에 )

logs.append(f"[저장] 상권별 집계: {OUT_DISTRICT}")

# ─────────────────────────────────────────────
# 6. 요약 로그 작성 (해석 생략)
# ─────────────────────────────────────────────
n_neg       = (df_dist['residual_latest'] < 0).sum()
n_candidate = df_dist['blueocean_candidate'].sum()
n_consist   = df_dist['residual_consistent'].sum()

logs.append("\n" + "="*55)
logs.append("=== OLS + OOF 잔차 추출 완료 ===")
logs.append("="*55)
logs.append(f"OOF 평균 R²  : {mean_r2:.4f}")
logs.append(f"전체 OLS R²  : {full_r2:.4f} (in-sample, 참고용)")
logs.append(f"")
logs.append(f"[잔차 분포 — 최신분기 {latest_q}]")
logs.append(f"  음수(블루오션 방향) : {n_neg}개")
logs.append(f"  양수(레드오션 방향) : {len(df_dist)-n_neg}개")
logs.append(f"")
logs.append(f"[블루오션 1차 후보]  잔차<0 + 찻집수<=1 : {n_candidate}개")
logs.append(f"[구조적 블루오션]    최신·평균 모두 음수  : {n_consist}개")
logs.append(f"")
logs.append(f"다음 단계: 35_blueocean_score.py")
logs.append(f"  → 2D 매트릭스 (X=OOF잔차, Y=공급부족지수) + 최종 랭킹")

log_text = "\n".join(logs)
with open(OUT_LOG, 'w', encoding='utf-8') as f:
    f.write(log_text)

print(log_text)
