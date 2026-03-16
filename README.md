🍵 서울시 찻집 창업 블루오션 상권 분석 프로젝트
본 프로젝트는 서울시 내 1,139개 상권을 대상으로 데이터 기반의 "수요는 높지만 공급은 부족한" 블루오션 상권을 발굴하는 것을 목표로 합니다.

🚀 분석 파이프라인 (Analysis Pipeline)

1단계: 데이터 수집 및 통합 (Data Collection & Merging)
핵심 역할: 서울시 열린데이터광장, 카카오 API, 네이버 데이터랩 등 산재된 소스로부터 분석에 필요한 원천 데이터를 수집하고 정제합니다.

주요 파일:

1_collect_sales_data.py ~ 6_join_sales_stores.py
: 매출 및 점포 데이터 수집/결합

7_x1_income.py ~ 13_x7_competitor.py
: 수요 변수(인구, 소득, 시설) 수집

18_crawl_tea_shops.py ~ 20_crawl_starbucks_reserve.py
: 서울시 찻집 및 스타벅스 점포 관련 상세 데이터 크롤링

21_merge_supply.py ~ 24_merge_trend.py
: 최종 패널 데이터셋 구축 연합

=== 
2단계: 탐색적 데이터 분석 (EDA)
핵심 역할: 데이터의 분포와 변수 간 상관관계를 시각화하여 이상치를 탐색하고 분석 가설을 검증합니다.

주요 파일:

25_eda.py
: 매출(Y) 분포 확인 및 로그 변환 필요성 진단

27_eda_correlation.py
: 변수 간 상관성 분석

27b_eda_correlation_nooutlier.py
: 명동 등 이상치 제거 전후 비교

30_eda_advanced2.py
: 다중공선성(VIF) 1차 진단 및 상권유형별 특성 분석

=== 

3단계: 데이터 전처리 및 변수 선별 (Preprocessing & Feature Selection)
핵심 역할: 모델의 정확도를 높이기 위해 불필요한 변수를 제거하고, 데이터의 규모를 정규화합니다.

주요 파일:

31_feature_selection_xgb_shap.py
: SHAP 기반 변수 중요도 추출

32_lasso_elasticnet.py
: Lasso 회귀를 통한 핵심 수요 변수 선별

33_preprocessing.py
: [핵심 정제] 이상치 상권 제거, 데이터 표준화(Scaling), 더미변수(분기/유형) 생성

=== 

4단계: 실제 모델링 및 잔차 분석 (Actual Analysis)
핵심 역할: 통계 모델을 통해 '기대 매출'을 예측하고, 실제값과의 차이(잔차)를 통해 저평가된 시장 신호를 추출합니다.

주요 파일:

34_ols.py
: [핵심 분석] Pooled OLS 모델 실행 및 GroupKFold OOF 잔차 추출

34_oof_residuals.csv
: 상권별 수요 대비 성과(Residual) 데이터 생성

=== 

5단계: 결과 도출 및 시각화 (Result Derivation & Reporting)
핵심 역할: 도출된 잔차와 공급 지수를 결합하여 최종 블루오션 상권 랭킹을 산출하고 리포트화합니다.

주요 파일:

35_blueocean_score.py
: 2D 매트릭스 기반 사분면(Q1~Q4) 분류 및 스코어링

36_unified_ranking.py
: 종합 블루오션 상권 랭킹 도출

37_district_profile.py
: 추천 상권별 상세 수요-공급 프로파일링

38_final_summary.py
: 최종 분석 결과 보고서 생성

41_tableau_prep.py
: 태블로 시각화 대시보드 작성을 위한 데이터 변환

=== 

📊 주요 분석 방법론
2-Track 분석: 수요 예측(Track A)과 공급 희소성(Track B)을 독립적으로 분석 후 결합
OOF 잔차 추출: 데이터 누수 방지를 위해 GroupKFold 방식을 채택하여 객관적인 저평가 상권 선별
통제 변수 활용: 분기(시간) 및 상권유형(공간) 더미변수를 적용하여 순수 수요의 영향력 측정
