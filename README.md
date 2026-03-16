# 서울 찻집 블루오션 상권 분석

**서울시 1,139개 상권 × 9분기 데이터를 활용해 찻집 창업에 적합한 블루오션 입지를 분석하고, 인터랙티브 웹 서비스로 제공하는 프로젝트입니다.**

🔗 **Live Demo:** [blueocean-finder.vercel.app](https://blueocean-finder.vercel.app)

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 분석 대상 | 서울시 상권 1,139개 × 9분기 (2023Q3 ~ 2025Q3) |
| 원본 데이터 | 9,760행 × 155개 변수 |
| 분석 데이터 | 9,392행 × 1,095개 상권 (결측·이상치 제거 후) |
| 핵심 방법론 | Pooled OLS + GroupKFold OOF 잔차 × 복합 공급부족 지수 |
| 서비스 | FastAPI (Render) + React (Vercel) |

---

## 핵심 방법론: 2-Track 프레임워크

```
Track A — 수요 예측 모델 (Pooled OLS)
  Y = log(카페음료 업종 당월매출)
  X = 수요변수 6개 + 분기 더미 8개 + 상권유형 더미 3개
  → GroupKFold(n_splits=5, groups=상권_코드) OOF 잔차 추출
     잔차 양수 = 수요 대비 매출 과성과 → 시장이 이미 검증된 상권
     잔차 음수 = 수요 대비 매출 저성과

Track B — 복합 공급부족 지수
  = 0.5 × rank(1 / (찻집수 + 1))
  + 0.5 × rank(찻집매출 / (카페음료점포수 + 1))

블루오션 정의 (Q1):
  잔차 ≥ 0 (수요 실증) + 공급부족 지수 상위 (찻집 없음)
  → 카페음료 수요가 데이터로 입증된 상권에 찻집만 없는 상태
```

### 확정 수요변수 6개

| 변수 | SHAP 순위 | VIF | 선택 근거 |
|------|---------|-----|---------|
| 집객시설_수 | 2위 (0.401) | 2.89 | 수요-인프라 대표 |
| 총_직장_인구_수 | 3위 (0.265) | 1.72 | 인구 계열 대표 |
| 월_평균_소득_금액 | 4위 (0.260) | 3.28 | 소비 계열 대표 |
| 총_가구_수 | 7위 (0.136) | 2.37 | 상주 소비층 |
| 카페_검색지수 | 9위 (0.104) | 1.62 | 트렌드 대표 |
| 지하철_노선_수 | 17위 (0.031) | 1.74 | 접근성 유일 대표 |

OOF R² = 0.4413 (수요 전용 모델 기준 — R²가 높으면 잔차에 블루오션 신호 소멸)

---

## 분석 파이프라인

### 1단계 — 데이터 수집 (1~24번)

| 스크립트 | 내용 |
|---------|------|
| `1_collect_sales_data.py` | 서울시 상권분석 API — 카페음료 업종 매출 수집 |
| `2_seoul_cafe_sales.py` | 분기별 카페음료 매출 정제 |
| `3_분기_총_평균매출_구하기.py` | 분기 평균 매출 산출 |
| `4_상권_행정동_join.py` | 상권 코드 × 행정동 매핑 |
| `5_collect_stores.py` | 상권별 점포 수 수집 |
| `6_join_sales_stores.py` | 매출 + 점포 수 병합 |
| `7_x1_income.py` | 월평균 소득 수집 (서울시 API) |
| `8_x2_working_pop.py` | 직장 인구 수 수집 |
| `9_x3_living_pop.py` | 상주 인구·가구 수 수집 |
| `10_x4_facilities.py` | 집객시설 수 수집 |
| `11_x5_floating_pop.py` | 유동 인구 수 수집 |
| `12_x6_apt.py` | 아파트 평균 시가·면적 수집 |
| `13_x7_competitor.py` | 카페음료 업종 경쟁점 수 수집 |
| `14_y_income_merge.py` ~ `16_y_merge_demand.py` | 수요변수 단계별 병합 |
| `17_build_search_keywords.py` | 네이버 데이터랩 검색 키워드 구성 |
| `18_crawl_tea_shops.py` | 카카오맵 찻집 크롤링 |
| `18b_filter_by_blog.py` | 블로그 언급 기반 찻집 필터링 |
| `19_map_tea_shops.py` | 찻집 위치 → 상권 매핑 |
| `20_crawl_starbucks_reserve.py` | 스타벅스 리저브 매장 수집 |
| `21_merge_supply.py` | 공급 변수 최종 병합 |
| `22_collect_trend_datalab.py` | 네이버 데이터랩 카페 검색량 수집 |
| `23_build_trend_index.py` | 상권별 카페 검색지수 생성 |
| `24_merge_trend.py` | 전체 마스터 데이터셋 완성 (9,760행 × 155변수) |

### 2단계 — EDA (25~30번)

| 스크립트 | 내용 |
|---------|------|
| `25_eda.py` | Y변수 분포, log 변환 효과 시각화 |
| `26_add_subway_lines.py` | 지하철 노선 수 피처 추가 |
| `27_eda_correlation.py` | 변수 간 상관관계 분석 |
| `27b_eda_correlation_nooutlier.py` | 이상치 제거 후 상관관계 재분석 |
| `28_eda_advanced.py` | 상권 유형별 매출 분포 분석 |
| `29_eda_search_by_district.py` | 상권별 검색지수 분포 |
| `30_eda_advanced2.py` | 블루오션 후보 1차 스크리닝 |

### 3단계 — Feature Selection (31~32번)

| 스크립트 | 내용 |
|---------|------|
| `31_feature_selection_xgb_shap.py` | XGBoost + SHAP — 변수 중요도 순위 산출 |
| `32_lasso_elasticnet.py` | Lasso / ElasticNet + VIF — 최종 6개 변수 확정 |

### 4단계 — 전처리 + 모델링 (33~34번)

| 스크립트 | 내용 |
|---------|------|
| `33_preprocessing.py` | 결측 처리 · 표준화 · 더미변수 생성 → `33_analysis_ready.csv` |
| `34_ols.py` | Pooled OLS + GroupKFold OOF 잔차 추출 → `34_oof_residuals.csv` |

### 5단계 — 블루오션 스코어링 (35~36번)

| 스크립트 | 내용 |
|---------|------|
| `35_blueocean_score.py` | Track A 잔차 × Track B 공급지수 → 사분면 분류 + Q1/Q2 스코어 |
| `35_blueocean_smoothing.py` | 공간 평활화 (내 상권 70% + 반경 500m 인접 30%) → 최종 통합 랭킹 |
| `36_unified_ranking.py` | Top30 통합 랭킹 추출 + 시각화 |

### 6단계 — 프로파일 분석 (37번)

| 스크립트 | 내용 |
|---------|------|
| `37_district_profile.py` | 상위 후보 상권 수요변수 레이더 차트 + 9분기 추세 시각화 |

### 7단계 — 보고서 + 검증 (38~39번)

| 스크립트 | 내용 |
|---------|------|
| `38_final_summary.py` | 최종 마크다운 보고서 생성 (`38_final_report.md`) |
| `39_sensitivity.py` | 공급지수 가중치 민감도 분석 — 결과 robust성 검증 |

### 8단계 — 시각화 (40번)

| 스크립트 | 내용 |
|---------|------|
| `40_ppt_visuals.py` | 발표용 추가 차트 5종 생성 (잔차 진단, 상관행렬, 단변량 R² 등) |

### 9단계 — 웹 서비스 API 데이터 준비 (41~44번)

| 스크립트 | 내용 |
|---------|------|
| `41_tableau_prep.py` | 태블로/웹용 상권 데이터 정제 (위경도 변환 포함) |
| `42_tableau_geojson.py` | 상권 폴리곤 SHP → GeoJSON 변환 (EPSG:5181 → WGS84) |
| `43_prepare_api_data.py` | API 서빙용 데이터 최종 정제 |
| `44_add_demand_details.py` | 수요변수 실제값(_raw) + 지하철 역 목록 추가 → `api/unified_ranking.csv` |
| `precompute_pct.py` | 수요변수 백분위(_pct) 선계산 — Render 콜드스타트 최적화 |

---

## 최종 추천 결과 (블루오션 Top10)

> 기준: Q1 스코어 = 0.5 × 잔차분위수(양수 방향) + 0.5 × 복합 공급부족 지수

| 순위 | 상권명 | 유형 | 잔차 | 전략 |
|------|--------|------|------|------|
| 1 | 안암역 2번 | 골목상권 | +2.803 | 수요 입증 + 찻집 0개 |
| 2 | 서원동상점가 | 전통시장 | +2.890 | 수요 입증 + 찻집 0개 |
| 3 | 도화동 상점가 | 골목상권 | +2.614 | 수요 입증 + 찻집 0개 |
| 4 | 홍대소상공인상점가 | 전통시장 | +3.231 | 수요 입증 + 찻집 0개 |
| 5 | 시청역_8번 | 발달상권 | +2.569 | 수요 입증 + 찻집 0개 |

**공통 특성:** 카페음료 매출이 수요 대비 이미 높게 실현된 상권 (음료 소비 검증) + 찻집 0개 (공급 공백)

---

## 서비스 아키텍처

```
사용자 검색 (주소 or 순위)
        ↓
Vercel (React + Tailwind + Recharts)
        ↓ REST API
Render (FastAPI)
  - /search  : 주소 → KakaoAPI 좌표 → KDTree 최근접 상권 탐색
  - /rank/{n}: 순위 번호로 상권 직접 조회
  - /scatter : 2D 매트릭스용 전체 상권 데이터
        ↓
api/unified_ranking.csv (1,036개 상권 × 33컬럼)
```

---

## 기술 스택

| 분류 | 사용 기술 |
|------|---------|
| 데이터 수집 | Python, requests, 서울시 공공데이터 API, 카카오맵 API, 네이버 데이터랩 |
| 분석 | pandas, numpy, scikit-learn, statsmodels, XGBoost, SHAP, scipy |
| 시각화 | matplotlib, seaborn |
| 백엔드 | FastAPI, pyproj, scipy (KDTree) |
| 프론트엔드 | React, Tailwind CSS, Recharts, Axios |
| 배포 | Render (백엔드), Vercel (프론트엔드) |

---

## 의사결정 로그

전체 분석 과정의 방법론적 결정 사항은 [`work/Retrospect.md`](work/Retrospect.md)에 Q&A 형식으로 기록되어 있습니다. (Q1~Q33, 약 1,800줄)
