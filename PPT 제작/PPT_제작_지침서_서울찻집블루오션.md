# 🍵 서울 찻집 블루오션 상권 분석 — PPT 제작 완전 지침서

> **목적:** 이 문서는 pptxgenjs 기반 코드 작성 시 참고할 완전한 제작 사양서입니다.  
> **총 슬라이드:** 18장 | **발표 시간:** 20분 | **대상:** 학교 수업 (교수님 포함)  
> **최종 업데이트:** 2026-03-09

---

## 🎨 전체 디자인 시스템

### 컬러 팔레트

| 역할 | 색상명 | HEX | 사용처 |
|---|---|---|---|
| **Primary Dark** | Deep Forest | `1B3A2D` | 표지 배경, 섹션 헤더 배경 |
| **Primary Mid** | Sage Green | `2D6A4F` | 슬라이드 좌측 accent bar, 강조 텍스트 |
| **Accent Blue** | Steel Blue | `1B4F8A` | Q1 안전전략 색상, 하이라이트 |
| **Accent Red** | Crimson | `C0392B` | Q2 선점전략 색상, 경고 박스 |
| **Neutral Light** | Ivory | `F8F6F1` | 콘텐츠 슬라이드 배경 |
| **Neutral Mid** | Cool Gray | `64748B` | 본문 텍스트, 캡션 |
| **White** | Pure White | `FFFFFF` | 카드 배경, 텍스트 on dark |
| **Border** | Light Gray | `E2E8F0` | 구분선, 카드 테두리 |
| **Q3 Gray** | Muted Gray | `9E9E9E` | 매트릭스 Q3 점 |
| **Q4 Light** | Light Gray | `BDBDBD` | 매트릭스 Q4 점 |

### 폰트 시스템

| 요소 | 폰트 | 크기 | 속성 |
|---|---|---|---|
| 슬라이드 대제목 | Georgia | 36–40pt | Bold |
| 영문 서브타이틀 | Calibri Light | 14pt | Italic, color: `64748B` |
| 섹션 헤더 | Calibri | 20–22pt | Bold |
| 본문 텍스트 | Calibri | 13–15pt | Regular |
| 강조 텍스트 | Calibri | 13–15pt | Bold, color: `2D6A4F` 또는 `1B4F8A` |
| 캡션/주석 | Calibri | 10–11pt | Regular, color: `64748B` |
| 수식/코드 | Consolas | 12pt | Regular |

### 레이아웃 규칙

- **슬라이드 크기:** 16:9 (10" × 5.625")
- **여백:** 상 0.5" / 하 0.45" / 좌 0.55" / 우 0.55"
- **헤더 영역:** y=0 ~ 0.6" (높이 0.6")
- **콘텐츠 영역:** y=0.7" ~ 5.1"
- **푸터 영역:** y=5.15" ~ 5.625"

### 반복 디자인 모티프

1. **좌측 Accent Bar:** 모든 콘텐츠 슬라이드 타이틀 좌측에 `2D6A4F` 색 세로 바 (w=0.07", h=0.5")
2. **상단 헤더 라인:** 슬라이드 최상단 얇은 선 (color: `2D6A4F`, height: 0.05")
3. **푸터:** 좌 "서울 찻집 블루오션 상권 분석" | 중앙 섹션명 | 우 "N / 18" (모두 10pt, `9E9E9E`)
4. **카드 박스:** 둥근 모서리 없이 `RECTANGLE`, fill `FFFFFF`, 테두리 `E2E8F0` 0.75pt, 그림자 (outer, blur 4, offset 2, opacity 0.10)

---

## 📐 슬라이드별 상세 사양

---

### S1. 표지

**파일 필요:** 없음  
**배경:** `1B3A2D` (Deep Forest 단색)  
**레이아웃:** 좌측 콘텐츠 + 우측 하단 서울 지도 실루엣 (반투명 shape으로 표현)

```
[구성 요소 배치]

① 상단 얇은 가로 선 (color: 2D6A4F, opacity 40%)
   x=0, y=0.05, w=10, h=0.03

② 영문 카테고리 레이블
   "DATA-DRIVEN MARKET ANALYSIS PROJECT"
   x=0.6, y=0.55, w=7, h=0.25
   font: Calibri 9pt, color: 97BC62, charSpacing: 4, bold: false

③ 한글 메인 타이틀 (2줄)
   "서울 찻집"
   x=0.6, y=0.85, w=7, h=0.65
   font: Georgia 44pt, bold: true, color: FFFFFF

   "블루오션 상권 분석"
   x=0.6, y=1.5, w=7.5, h=0.65
   font: Georgia 44pt, bold: true
   "블루오션 상권" → color: 97BC62 (강조)
   "분석" → color: FFFFFF

④ 구분선 (accent)
   x=0.6, y=2.28, w=0.8, h=0.055
   fill: C0392B (레드 포인트)

⑤ 부제목
   "수요-공급 갭 기반 데이터 추천 시스템 구축 및 실증"
   x=0.6, y=2.45, w=7, h=0.35
   font: Calibri 16pt, color: D4E6D0

⑥ 데이터 스펙 카드 박스
   x=0.6, y=3.0, w=6.2, h=1.45
   fill: FFFFFF, transparency: 90% → 실제로는 fill color 1B3A2D에 가깝게 투명한 연두빛
   → 구현: fill: 243D33, 테두리: 2D6A4F, width: 1pt

   카드 내부 2열 구성:
   
   [좌열]
   "DATA SCOPE" → Calibri 8pt, color: 97BC62, charSpacing: 2
   "서울 1,139개 상권" → Calibri 13pt, bold, color: FFFFFF
   (구분선 y=3.85 수평)
   "METHODOLOGY"  → Calibri 8pt, color: 97BC62
   "2-Track Framework (Demand + Supply Gap)" → Calibri 12pt, color: D4E6D0

   [우열]
   "TIME PERIOD" → Calibri 8pt, color: 97BC62
   "9개 분기 (2023Q3 ~ 2025Q3)" → Calibri 13pt, bold, color: FFFFFF

⑦ 하단 발표자 정보 바 (3열)
   y=4.7, h=0.5 전체 가로 바
   배경: 14301F (더 어두운 그린)
   
   "DATE" | "2026. 03. 08" (좌)
   "PRESENTER" | "쏘피 (Sophie)" (중)
   "AFFILIATION" | [소속] (우)
   레이블: 8pt, color: 97BC62 / 값: 12pt, color: FFFFFF

⑧ 우측 하단 서울 지도 실루엣 (장식)
   → RECTANGLE shape 여러 개로 추상적 표현 or 반투명 도형
   x=7.5, y=2.0, w=2.3, h=3.2
   fill: 2D6A4F, transparency: 75%
```

---

### S2. 연구 배경과 핵심 질문

**파일 필요:** 없음 (숫자 강조, 텍스트)  
**배경:** `F8F6F1`  
**레이아웃:** 좌측 60% 텍스트 + 우측 40% 숫자 강조 카드

```
[헤더]
좌측 accent bar (2D6A4F, x=0.55, y=0.1, w=0.07, h=0.5)
"연구 배경과 핵심 질문" → Georgia 28pt, bold, color: 1B3A2D, x=0.7, y=0.1
"Problem Definition" → Calibri 13pt, italic, color: 9E9E9E, x=0.7, y=0.42 (우측 정렬)

[좌측 콘텐츠 — 4개 bullet 블록, y=0.75부터 각 블록 간격 0.95"]

블록 1: 카페 시장의 포화 상태
• 헤더: "카페 시장의 포화 상태"
  → 좌측 원형 bullet (fill: 1B3A2D, w=0.13, h=0.13)
  → 텍스트: Calibri 15pt, bold, color: 1B3A2D
• 본문: "서울시 카페 점포 수 지속 증가로 인한 경쟁 심화.
  단순 '매출 높은 상권' 진입은 레드오션 경쟁을 의미함."
  → Calibri 12pt, color: 64748B

블록 2: 기존 상권 분석의 한계
• (블록 1과 동일 형식)
• 본문: "대부분의 분석이 '현재 매출이 높은 곳 = 좋은 곳'으로 귀결.
  이미 임대료와 권리금이 상승한 '검증된 포화 시장'만 추천."

블록 3: 핵심 질문 (Research Question) ← 강조 처리
• 헤더 color: 2D6A4F (그린 강조), 17pt
• 본문: "서울 1,139개 상권 중, 잠재 수요는 충분하지만
  아직 찻집 공급이 부족한 '블루오션'은 어디인가?"
• 배경 박스: fill E8F4F0, 테두리 2D6A4F, 0.5pt

블록 4: 접근 방법: 2-Track Framework
• 본문: "Track A: 시장 수요의 크기와 실현도 예측
  Track B: 찻집 특화 공급 부족 지수 산출"

[우측 카드 패널 — x=6.0, y=0.7, w=3.7, h=4.4]
카드 배경: FFFFFF, 테두리: E2E8F0, 그림자 있음

상단 원형 강조 숫자:
• 큰 원 (OVAL): x=6.8, y=0.9, w=2.2, h=2.2
  fill: 1B3A2D
• 숫자 "1,139": Georgia 46pt, bold, color: FFFFFF, 중앙
• 레이블 "분석 대상 상권": Calibri 11pt, color: 97BC62

구분선: y=3.15, color: E2E8F0

서브 텍스트:
"전통적 핫플레이스뿐만 아니라"
"숨겨진 골목상권까지" (2D6A4F bold)
"전수 조사 수행"
→ Calibri 12pt, color: 64748B, 중앙 정렬

수평 바 비교 (y=3.7부터):
라벨: "서울시 카페" → 바 fill: C0392B, w=3.0 (비율 반영)
숫자: "25,000+" bold
라벨: "서울시 찻집" → 바 fill: 1B4F8A, w=0.29 (비율 반영)  
숫자: "246"
캡션: "*카카오맵 등록 기준 (2025)" → 10pt, color: 9E9E9E

[푸터]
좌: "서울 찻집 블루오션 상권 분석" | 중: "1. Problem Definition" | 우: "2 / 18"
```

---

### S3. 분석 프레임워크 전체 조감 ⭐ (앞으로 이동)

**파일 필요:** 없음 (다이어그램 직접 제작)  
**배경:** `F8F6F1`  
**레이아웃:** 전체 화면 플로우차트

```
[헤더]
"분석 프레임워크 전체 조감도" | "Analysis Framework Overview"

[다이어그램 — 3열 플로우]

열 1: 변수 선택 단계 (x=0.55, y=0.7, w=2.8, h=3.8)
카드 배경: FFFFFF, 테두리 E2E8F0

상단 원형 넘버: "1" (fill: 1B3A2D, 원형, 흰색 숫자)
제목: "변수 스크리닝"
부제: "(Variable Screening)"

내용 bullet:
• 155개 전체 변수 투입
• XGBoost + SHAP 활용
• 비선형 중요도 상위 22개 추출

열 2: Track A + Track B 분기 (x=3.6, y=0.7)
상단 넘버: "2" (fill: 1B3A2D)
제목: "Feature Selection"
부제: "(Linearity Check)"
내용:
• Lasso / ElasticNet 검증
• VIF < 5 다중공선성 제거
• 최종 6개 수요 변수 확정

→ 2-Track Split 화살표 (우측 방향)

[Track A 박스] y=2.3, h=1.4
fill: EBF4FB, 테두리: 1B4F8A, 1pt
레이블 태그: "DEMAND" (fill: 1B4F8A, white text, 9pt)
제목: "Track A: 수요 예측 모델"
• Input: 순수 수요 변수 5종 (공급변수 제외)
• Pooled OLS + GroupKFold (상권단위)
• Output: OOF 잔차 (Residuals)
  → 음수(–) = 수요 대비 매출 저조 (미실현)

[Track B 박스] y=3.8, h=1.4
fill: FDECEC, 테두리: C0392B, 1pt
레이블 태그: "SUPPLY" (fill: C0392B, white text, 9pt)
제목: "Track B: 공급 부족 지수"
• ①절대적 희소성: 1 / (찻집수 + 1)
• ②상대적 경쟁력: 찻집매출 / (카페수 + 1)
• Output: 복합 공급 점수 (Composite Score)

열 3: 통합 결과 (x=7.5, y=0.7, w=2.1, h=4.5)
[통합 박스] fill: 1B3A2D, 텍스트 흰색
제목: "통합 2D 매트릭스 & 추천"
부제: "X축: OOF 잔차 (수요) / Y축: 공급점수 (공급)"

[Strategy 1] fill: 1B4F8A
"Q1 안전 진입"

[Strategy 2] fill: C0392B
"Q2 선점 투자"

[연결 화살표]
열1 → 열2: 수평 화살표 (color: 9E9E9E)
열2 → Track A: 대각 화살표 (color: 1B4F8A)
열2 → Track B: 대각 화살표 (color: C0392B)
Track A + Track B → 열3: 수렴 화살표 (color: 1B3A2D)

[푸터] 섹션: "Framework Overview" | "3 / 18"
```

---

### S4. 데이터 소개 및 수집 방법

**파일 필요:** 없음 (표 + 숫자)  
**배경:** `F8F6F1`  
**레이아웃:** 상단 총계 강조 + 좌측 표 + 우측 3D 큐브 다이어그램

```
[헤더]
"데이터 소개 및 수집 방법" | "Data Overview & Collection"

[상단 강조 바 — x=0.55, y=0.65, w=9.0, h=0.85]
fill: 1B3A2D
내부 텍스트:
"TOTAL DATASET SIZE" → 9pt, color: 97BC62, charSpacing: 2
"9,760 Rows  |  155 Variables" → Georgia 28pt, bold, color: FFFFFF
아이콘 텍스트: "🗂 서울시 1,139개 상권 × 9개 분기 (2023Q3 ~ 2025Q3)"
→ Calibri 12pt, color: D4E6D0

[좌측 데이터 표 — x=0.55, y=1.65, w=5.5, h=3.2]
헤더 행: fill 1B3A2D, 텍스트 FFFFFF
"구분" | "주요 변수 내용" | "데이터 출처"
컬럼 너비: 0.8 | 3.0 | 1.7

행1: "수요" (fill: EBF4FB, badge 1B4F8A)
"인구·소득·인프라 / 유동/직장/상주인구, 월평균소득, 아파트시가, 집객시설수"
"서울시 상권분석서비스 API"

행2: "트렌드" (fill: FFF8E8, badge DAA520)
"관심도·성장성 / 카페 검색량 지수, 검색량 성장률, 업종별 개업률"
"네이버 데이터랩"

행3: "공급" (fill: FDECEC, badge C0392B)
"경쟁 현황 / 찻집 수, 카페 점포수, 스타벅스 리저브 수"
"카카오맵 API (직접 크롤링)"

행4: "접근성" (fill: F0F4FF, badge 1B4F8A)
"교통 환경 / 반경 내 지하철역 수, 노선 수 (좌표 매핑)"
"자체 수집 + 좌표 계산"

행5: "매출(Y)" (fill: E8F4F0, badge 2D6A4F)
"시장 규모 대리변수 / 카페·음료 업종 전체 분기 매출 (log 변환)"
"서울시 상권분석서비스 API"

[우측 3D 패널 큐브 다이어그램 — x=6.3, y=1.65, w=3.3, h=3.2]
→ pptxgenjs shape 조합으로 3D 큐브 표현:

- 높이 축 바 (빨강): w=0.6, h=2.5, fill: E57373
  레이블: "Spatial Units (Height)" → 10pt
- 깊이 축 바 (파랑): w=1.5, h=1.0, fill: 64B5F6
  레이블: "Feature Space (Depth)" → 10pt  
- 너비 축 바 (초록): w=1.2, h=0.6, fill: 81C784
  레이블: "Temporal (Width)" → 10pt
- 중앙 큰 텍스트: "9,760 Observations"
  → Georgia 20pt, bold, color: 1B3A2D
- 하단 레이블: "Variables (155)" | "Districts" | "9 Quarters"
  → Calibri 9pt, color: 64748B

[푸터] 섹션: "2. Data & Methodology" | "4 / 18"
```

---

### S5. Y변수 선택 논리와 분포 분석

**파일 필요:** `25_eda_y_distribution.png` ✅  
**배경:** `F8F6F1`  
**레이아웃:** 상단 3개 설명 카드 + 하단 그래프 이미지 + Key Insight 박스

```
[헤더]
"Y변수 선택 논리와 분포 분석" | "Target Variable Selection & Distribution"

[상단 3개 카드 — y=0.65, 각 카드 w=2.9, h=1.2, 간격 0.15"]

카드 1: 시장 규모 대리 (Market Proxy)
아이콘: 지구본 모양 → 원형 fill 2D6A4F, 텍스트 "🌐"
제목: "시장 규모 대리 (Market Proxy)" → 12pt bold
내용: "찻집만의 매출이 아닌 카페·음료 업종 전체 매출을 Y로 정의.
해당 상권의 '음료 소비 총량(TAM)'을 측정."
→ 11pt, color: 64748B

카드 2: Zero-Inflation 문제 회피
아이콘: ∅ 기호 → 원형 fill 1B4F8A
제목: "Zero-Inflation 문제 회피"
내용: "찻집이 없는 상권은 매출이 0이므로 수요 예측 불가능.
전체 음료시장 데이터로 잠재 수요가 존재함을 입증."

카드 3: Log Transformation
아이콘: 📊 → 원형 fill 8B6914
제목: "Log Transformation"
내용: "원 데이터의 왜도 6.04 → log1p 변환 후 -0.15
선형 회귀 모델의 정규성 가정 충족 및 이상치 영향 완화."

[중앙 그래프 영역 — x=0.55, y=2.0, w=9.0, h=2.6]
카드 박스 (fill: FFFFFF, 테두리: E2E8F0)
이미지 삽입: 25_eda_y_distribution.png
→ sizing: contain, 여백 0.1" 내부 패딩

[하단 Key Insight 박스 — x=0.55, y=4.7, w=9.0, h=0.65]
fill: 1B3A2D
왼쪽 아이콘: 전구 (원형 fill 97BC62, 텍스트 "💡")
텍스트: "Key Insight: 좌측 원본 데이터는 소수 대형 상권(명동, 강남 등)에 의해 극심한 우편향.
로그 변환(중앙) 후 정규분포에 매우 근사한 형태를 띰. 분기별 분포(우) 중앙값과 사분위 범위가 안정적."
→ Calibri 11pt, color: D4E6D0

[푸터] 섹션: "2. Data & Methodology" | "5 / 18"
```

---

### S6. Feature Selection: 155개 → 22개 → 최종 6개

**파일 필요:** `31_fs_shap_summary.png` ✅  
**배경:** `F8F6F1`  
**레이아웃:** 상단 깔때기 흐름 + 좌측 SHAP 플롯 + 우측 최종 6개 변수 헥사곤

```
[헤더]
"Feature Selection: 155개 → 22개 → 최종 6개" | "Variable Selection Process"

[상단 깔때기 흐름 — y=0.65, h=0.7]
3단계 박스 + 화살표:

[박스1] "155개 전체 변수" → fill 64748B, white text, w=2.0
→ 화살표 "1차: XGBoost (22개)" label
[박스2] "22개 대표 변수" → fill 2D6A4F, white text, w=2.0  
→ 화살표 "2차: Lasso" label
[박스3] "최종 6개" → fill 1B3A2D, white text, w=2.0
→ 우측 화살표 "3차: VIF" label
→ 태그 "Linear Validation" fill 1B4F8A

[좌측 절반 — SHAP Summary Plot]
카드 박스 (x=0.55, y=1.45, w=4.5, h=3.4)
헤더: "1차 스크리닝 - SHAP 중요도" → 12pt bold + 태그 "Non-Linear" fill 2D6A4F
이미지: 31_fs_shap_summary.png
→ sizing: contain

[우측 절반 — 최종 6개 변수 카드]
카드 박스 (x=5.2, y=1.45, w=4.4, h=3.4)
헤더: "최종 확정 6개 수요 변수" → 12pt bold + 태그 "Final" fill C0392B

6개 변수 2열 3행 그리드:

행1: 집객시설_수 | 총_직장_인구_수
행2: 월_평균_소득_금액 | 총_가구_수
행3: 카페_검색지수 | 지하철_노선_수

각 변수 카드 (w=2.0, h=0.95):
- fill: FFFFFF, 테두리: E2E8F0
- 아이콘 원형 (fill: 1B3A2D, 14pt emoji)
- 변수명: 13pt bold, color: 1B3A2D
- 서브레이블: 10pt, color: 64748B
  예) "SHAP 2위 | VIF 2.89" / "SHAP 3위 | VIF 1.72"

[푸터] 섹션: "2. Data & Methodology" | "6 / 18"
```

---

### S7. Track A: 수요 예측 모델 설계와 진단

**파일 필요:** `27b_eda_scatter_top20_nooutlier.png` ✅ (산점도), `40_univariate_r2_top10.png` ✅  
**배경:** `F8F6F1`  
**레이아웃:** 좌측 모델 스펙 카드 + 우측 2개 차트 영역

> **참고:** 잔차 진단 4분할 플롯(QQ-plot 등)이 없으므로 우측 하단에 `40_univariate_r2_top10.png`로 대체하고, R² 비교는 텍스트 카드로 표현.

```
[헤더]
"Track A: 수요 예측 모델 설계와 진단" | "Demand Prediction Model Specification & Diagnostics"

[좌측 모델 스펙 카드 — x=0.55, y=0.7, w=3.8, h=4.1]
fill: FFFFFF, 테두리 E2E8F0, 그림자

섹션1: "Model Specification" (아이콘 ≡, 굵은 텍스트)
- Dependent Variable (Y): log1p(카페·음료 업종 전체 매출)
- Independent Variables (X):
  1. 집객시설 수 (Infra)
  2. 총 직장 인구 수 (Work)
  3. 월 평균 소득 금액 (Income)
  4. 총 가구 수 (Resident)
  5. 카페 검색 지수 (Trend)
  6. 지하철 노선 수 (Access)
- Controls: Time FE (분기 더미) + Type FE (상권 유형)

구분선 (y=3.0 위치)

섹션2: "Validation Strategy" (아이콘 ✓, 색상 2D6A4F)
- Algorithm: Pooled OLS (Linear)
- Cross-Validation: GroupKFold
  (Groups = 상권 코드, n_splits=5)
- Objective: OOF Residuals Extraction
  "동일 상권 시계열 누수 차단"

[우측 상단 차트 — R² 비교]
카드 박스 (x=4.55, y=0.7, w=5.0, h=1.9)
태그: "Performance" (fill: 2D6A4F)

2개 숫자 비교:
[공급 포함 XGBoost] R² = 0.9047
→ 큰 바 fill: E2E8F0 (회색, "공급 포함 시")
텍스트: "R² = 0.9047" 22pt bold color: 9E9E9E

[Track A OLS] R² = 0.4413  
→ 작은 바 fill: 1B4F8A (파랑, "Track A의 낮은 의도된 설계")
텍스트: "R² = 0.4413" 22pt bold color: 1B4F8A

박스 하단 설명 (fill: EBF4FB):
"① 모델 성능 비교: Track A의 낮은 R²(0.44)는 공급변수 배제에 따른 의도된 결과임"
→ 11pt, color: 1B4F8A

[우측 하단 차트 — 단변량 R² Top10]
카드 박스 (x=4.55, y=2.7, w=5.0, h=2.1)
태그: "Independence"
이미지: 40_univariate_r2_top10.png (contain)
캡션: "② 공급변수(카페음료점포수) 제외 후, 수요 변수만으로도 유의미한 설명력 확보 (집객시설 R²=0.30)"
→ 10pt, color: 64748B

[푸터] 섹션: "2. Data & Methodology" | "7 / 18"
```

---

### S8. Track B: 복합 공급부족 지수

**파일 필요:** 없음 (텍스트 + 수식)  
**배경:** `F8F6F1`  
**레이아웃:** 좌측 3개 bullet 설명 + 우측 수식 카드 구성

```
[헤더]
"Track B: 복합 공급부족 지수" | "Methodology Detail"

[좌측 — x=0.55, y=0.7, w=5.4, h=4.2]

불릿 블록1: "지수 설계 목적"
• 단순히 '찻집이 없는 곳'을 찾는 것이 아니라,
  ①절대적 부재와 ②상대적 희소성을 동시에 평가하여
  공급 공백의 강도를 입체적으로 측정.

불릿 블록2: "요소 1: 절대적 희소성 (Weight 0.5)"
• 수식: 1 / (찻집수 + 1) → Consolas 12pt
• 찻집이 0개인 곳에 최대 점수 부여.
  가장 직접적인 '부재' 신호 측정.

불릿 블록3: "요소 2: 경쟁 속 성과 (Weight 0.5)"
• 수식: 찻집매출 / (카페점포수 + 1) → Consolas 12pt
• 카페 경쟁이 치열한 곳에서도 찻집이 생존하고 있다면,
  그 희소 가치를 높게 평가 (니치 마켓 검증).

불릿 블록4 (강조 박스): "Rank 변환 및 민감도 검증"
fill: E8F4F0, 테두리: 2D6A4F
• 스케일이 다른 두 지표를 백분위수(Rank)로 변환 후 합산.
  가중치(0.1~0.9) 변화에도 Top5 상권 순위 일관성 확인 (Robustness Check 완료).

[우측 — x=6.1, y=0.7, w=3.6, h=4.2]

[COMPONENT 1 카드] y=0.7, h=1.0
fill: EBF4FB, 좌측 accent bar color: 1B4F8A
레이블: "COMPONENT 1" → 9pt, color: 9E9E9E
수식: "Scarcity Score = Rank [ 1 / (Teahouse + 1) ]"
→ Calibri 13pt, bold, color: 1B4F8A

[COMPONENT 2 카드] y=1.85, h=1.0
fill: EBF4FB, 좌측 accent bar color: 1B4F8A
레이블: "COMPONENT 2"
수식: "Performance Score = Rank [ Sales / (Cafe + 1) ]"
→ Calibri 13pt, bold, color: 1B4F8A

[FINAL 수식 카드] y=2.9, h=0.9
fill: 1B3A2D
레이블: "FINAL SUPPLY GAP INDEX" → 9pt, color: 97BC62
수식: "0.5 ×Scarcity + 0.5 ×Performance"
→ Calibri 16pt, bold, color: FFFFFF

[경고 박스] y=3.95, h=1.0
fill: FFF3F3, 테두리: C0392B, 1pt
아이콘: "⚠" color: C0392B
제목: "Methodological Limitation"
내용: "요소 2의 분자에 '찻집매출'이 포함되어, 찻집이 없는 곳(매출=0)이 오히려 낮은 점수를 받을 위험 존재.
→ Rank 변환 및 요소 1과의 결합으로 상쇄하였으나, 향후 '카페점포수/(찻집수+1)'로 대체 고려."
→ 10pt, color: C0392B

[푸터] 섹션: "2. Data & Methodology" | "8 / 18"
```

---

### S9. 2-Track 통합: 블루오션 정의와 랭킹

**파일 필요:** `35_2d_matrix.png` ✅ (미리보기용 - 작게)  
**배경:** `F8F6F1`  
**레이아웃:** 좌측 축 정의 + 사분면 해석, 우측 매트릭스 미리보기

```
[헤더]
"2-Track 통합: 블루오션 정의와 랭킹" | "Methodology Integration"

[좌측 — x=0.55, y=0.7, w=5.1, h=4.2]

불릿 블록1: "2D 매트릭스 축(Axis) 정의"
X축 (OOF 잔차): 수요 예측 모델의 잔차
  (양수=과성과 / 음수=저성과)
Y축 (공급부족지수): 찻집 희소성 점수
  (높음=공급부족 / 낮음=포화)

불릿 블록2: "4개 사분면(Quadrant) 전략적 의미"
강조 색상으로 구분:
Q1 [파랑]: 검증시장공백 (안전진입) — 수요 검증됨 + 찻집만 없음 (Best)
Q2 [빨강]: 잠재수요미실현 (선점투자) — 잠재력 높음 + 아직 시장 미형성
Q3 [회색]: 저성과·포화 — 수요도 없고 성과도 낮음 (Avoid)
Q4 [연회색]: 레드오션 — 성과는 좋으나 이미 경쟁 치열 (Risk)

불릿 블록3: "컷오프(Cutoff) 기준 정당화"
X축 기준 (0): 모델 예측값과 실제값이 일치하는 자연적 경계선
Y축 기준 (Median): 전체 상권 중 상대적 상위 50% 희소성 확보

[최종 스코어링 박스] fill: E8F4F0, 테두리: 2D6A4F
"최종 스코어링 방법: 각 지표를 분위수(Quantile)로 정규화한 후 0.5씩 가중 합산.
→ 특정 지표의 스케일이 전체 점수를 왜곡하는 현상 방지."

[우측 매트릭스 — x=5.8, y=0.7, w=3.9, h=4.2]
카드 박스 (fill: FFFFFF, 테두리: E2E8F0)
이미지: 35_2d_matrix.png (축소 배치, sizing: contain)
→ 단, 4개 사분면 레이블 텍스트 위에 오버레이:

Q2 좌상단: "Q2 잠재수요미실현 (선점투자) ★"
  → 12pt, bold, color: C0392B
Q1 우상단: "Q1 검증시장공백 (안전진입) ★"
  → 12pt, bold, color: 1B4F8A

[푸터] 섹션: "2. Data & Methodology" | "9 / 18"
```

---

### S10. 핵심 결과: 2D 매트릭스 ⭐ (핵심 슬라이드)

**파일 필요:** `35_2d_matrix.png` ✅  
**배경:** `F8F6F1`  
**레이아웃:** 상단 4개 카운트 카드 + 하단 전체 매트릭스 크게

```
[헤더]
"핵심 결과: 2D 매트릭스" | "Key Findings: 2D Quadrant Analysis"

[상단 4개 카운트 카드 — y=0.65, 각 w=2.3, h=0.95, 간격 0.07"]

카드1: Q2. 잠재수요 미실현 (선점)
fill: C0392B 상단 accent 바 (h=0.1)
"444개 상권" → Georgia 28pt, bold, color: C0392B
"수요 High / 공급 Low (고위험·고수익)" → 10pt, color: 64748B
좌측 별표 "★" → 14pt, C0392B

카드2: Q1. 검증시장 공백 (안전)
fill: 1B4F8A 상단 accent 바
"475개 상권" → 28pt bold, color: 1B4F8A
"수요 High / 공급 Mid-Low (저위험)" → 10pt

카드3: Q3. 저성과·포화
"40개 상권" → 28pt bold, color: 9E9E9E
"수요 Low / 공급 High" → 10pt

카드4: Q4. 레드오션
"77개 상권" → 28pt bold, color: BDBDBD
"수요 Low / 공급 과잉" → 10pt

[메인 매트릭스 이미지 — x=0.3, y=1.72, w=9.4, h=3.7]
카드 박스 (fill: FFFFFF, 테두리: E2E8F0)
이미지: 35_2d_matrix.png
→ sizing: contain, 내부 패딩 0.08"

[푸터] 섹션: "3. Results & Findings" | "10 / 18"
```

---

### S11. Q1 추천 — 안전 진입 전략

**파일 필요:** `37_radar_chart.png` ✅ (좌측 절반, Q1 레이더만 크롭 불가 → 전체 사용)  
**배경:** `F8F6F1`  
**레이아웃:** 상단 전략 카드 + 좌측 Top5 테이블 + 우측 레이더 차트

```
[헤더]
"Q1 추천 — 안전 진입 전략" | "Verified Market Gap Strategy"

[전략 개념 박스 — x=0.55, y=0.65, w=9.0, h=0.75]
fill: EBF4FB, 좌측 두꺼운 바 (fill: 1B4F8A, w=0.06)
아이콘: "🛡" (원형 fill: 1B4F8A)
제목: "전략 개념: 검증된 시장 + 공급 공백 = LOW RISK"
내용: "이미 활성화된 음료 소비 시장(검증됨)이나 찻집 공급만이 부재한 상권.
수요 불확실성이 낮아 안정적 창업을 선호하는 초기 진입자에게 적합."
→ 12pt, color: 1B4F8A

[좌측 Top5 테이블 — x=0.55, y=1.55, w=5.5, h=2.4]
테이블 헤더: fill 1B4F8A, 텍스트 FFFFFF
"Rank" | "상권명" | "OOF잔차" | "공급점수" | "주요 특징"

순위 번호 원형 배지 (fill: 1B4F8A):
1위: 홍대소상공인상점가 | +3.231 | 0.751 | "전통시장, 집객 상위 97%"
2위: 외대앞역 1번       | +3.198 | 0.767 | "골목상권, 지하철 접근성↑"
3위: 성신여대입구역     | +3.179 | 0.771 | "대학가, 직장인구 상위 46%"
4위: 광나루역 1번       | +3.136 | 0.766 | "주거밀집, 소득 상위 21%"
5위: 경향신문사         | +2.966 | 0.765 | "오피스, 직장인구 상위 21%"

[공통 패턴 박스 — x=0.55, y=4.05, w=5.5, h=0.65]
fill: EBF4FB, 테두리: 1B4F8A
"🔍 공통 패턴 분석: 대학가/오피스 배후지의 골목상권 및 전통시장 기반.
상주소비층(직장/거주)이 탄탄하여 평일/주말 매출 방어가 유리한 구조."
→ 11pt, color: 1B4F8A

[우측 레이더 차트 — x=6.2, y=1.55, w=3.5, h=3.15]
카드 박스 (fill: FFFFFF, 테두리: E2E8F0)
이미지: 37_radar_chart.png (전체, Q1+Q2 모두 포함)
→ sizing: contain
하단 캡션: "Q1 상권 수요 강점 (Radar Chart) — 집객시설과 직장인구 비중이 높고, 지하철 접근성이 우수한 특징을 보임."
→ 10pt, color: 64748B, italic

[푸터] 섹션: "3. Results & Findings" | "11 / 18"
```

---

### S12. Q2 추천 — 선점 전략

**파일 필요:** `37_residual_trend.png` ✅  
**배경:** `F8F6F1`  
**레이아웃:** 상단 전략 카드 + 좌측 Top5 테이블 + 우측 잔차 트렌드 차트

```
[헤더]
"Q2 추천 — 선점 전략" | "Preemptive Strategy for High-Potential Markets"

[전략 개념 박스 — x=0.55, y=0.65, w=9.0, h=0.75]
fill: FDECEC, 좌측 두꺼운 바 (fill: C0392B, w=0.06)
아이콘: "🚀" (원형 fill: C0392B)
제목: "전략 개념: 잠재수요 미실현 (High Risk, High Return)"
내용: "수요 지표는 압도적이나 찻집 공급이 없어 아직 매출로 실현되지 않은 상권.
초기 진입 시 독점적 지위를 누릴 수 있으나, 수요 검증이 필요함."
→ 12pt, color: C0392B

[좌측 Top5 테이블 — x=0.55, y=1.55, w=5.5, h=2.4]
헤더: fill C0392B, 텍스트 FFFFFF
순위 번호 배지 (fill: C0392B):
1위: 서울역   | 0.770 | -0.350 | "집각 상위 3%, 직장인구 상위 3%"
2위: 대치역   | 0.769 | -1.005 | "소득 상위 0%, 집각 상위 6%"
3위: 상봉역   | 0.762 | -0.017 | "가구수 상위 9%, 지하철 상위 4%"
4위: 충정로역 | 0.760 | -0.100 | "소득 상위 3%, 직장인구 상위 18%"
5위: 응암역   | 0.758 | -0.095 | "전반적 중상위권 균형형"

[구조적 미실현 판단 박스 — x=0.55, y=4.05, w=5.5, h=0.65]
fill: FDECEC, 테두리: C0392B
"🔍 구조적 미실현 판단 기준:
• 9분기 잔차 밀관성: 일시적 하락이 아닌 지속적 음수 잔차 확인
• 수요 요인 건강성: 유동인구/소득 등 핵심 지표가 상위 10% 이내
• 공급 공백 원인: 임대료나 규제 등 진입 장벽 여부 현장 확인 필요"
→ 11pt, color: C0392B

[우측 잔차 트렌드 차트 — x=6.2, y=1.55, w=3.5, h=3.15]
카드 박스
이미지: 37_residual_trend.png (전체)
→ sizing: contain
캡션: "Q1/Q2 Top5 상권의 9분기 OOF 잔차 추세. Q1(파랑)은 안정적 양수 유지, Q2(빨강)는 지속적 음수."
→ 10pt, color: 64748B, italic

[푸터] 섹션: "3. Results & Findings" | "12 / 18"
```

---

### S13. Q1 vs Q2 전략 비교

**파일 필요:** 없음 (VS 비교 표)  
**배경:** `F8F6F1`  
**레이아웃:** 중앙 VS 도표 + 하단 포트폴리오 제언

```
[헤더]
"리스크 성향별 전략 제언" | "Strategy Recommendation by Risk Profile"

[메인 VS 비교 영역 — y=0.7, h=3.6]

[Q1 카드 — x=0.55, y=0.7, w=4.0, h=3.6]
상단 헤더 바: fill 1B4F8A, h=0.5
텍스트: "Q1 — 안전 진입 전략" white 16pt bold
내용 (fill: EBF4FB):
아이콘 행: "🛡 LOW RISK"

6개 항목 리스트:
잔차 방향: 양수 (+2.9 ~ +3.2)
상권 유형: 골목·전통시장
수요 특성: 상주 소비층 (가구·직장인구)
리스크: 낮음 (시장 검증 완료)
추천 대상: 안정적 창업 선호자
추천 상권: 홍대소상공인, 외대앞역, 성신여대

[VS 구분 — x=4.7, y=1.5, w=0.6, h=2.0]
원형 (OVAL) fill: 1B3A2D
"VS" → Georgia 18pt bold, white

[Q2 카드 — x=5.45, y=0.7, w=4.0, h=3.6]
상단 헤더 바: fill C0392B
텍스트: "Q2 — 선점 전략" white 16pt bold
내용 (fill: FDECEC):
아이콘 행: "🚀 HIGH RETURN"

6개 항목 리스트:
잔차 방향: 음수 (-0.0 ~ -1.0)
상권 유형: 발달상권·교통 허브
수요 특성: 유동·직장인구 압도적
리스크: 높음 (수요 미개척)
추천 대상: 선점 기회 추구자
추천 상권: 서울역, 대치역, 상봉역

[하단 포트폴리오 박스 — y=4.45, h=0.75]
fill: 1B3A2D, 텍스트 white
"💼 균형 전략 제안: Q1 Top3 + Q2 Top2 포트폴리오 검토 |
⚠ 본 분석은 상권 단위. 실제 점포 위치(임대료·건물 유형)는 현장 조사 필수."

[푸터] 섹션: "3. Results & Findings" | "13 / 18"
```

---

### S14. 방법론 신뢰성 검증 — Robustness Check

**파일 필요:** `39_sensitivity_overlap.png` ✅  
**배경:** `F8F6F1`  
**레이아웃:** 좌우 2분할 차트 + 하단 요약 박스

```
[헤더]
"방법론 신뢰성 검증 — Robustness Check" | "Methodology Validation"

[좌측 차트 — x=0.55, y=0.65, w=4.5, h=3.5]
카드 박스
태그: "Parameter Sensitivity" (fill: 2D6A4F)
이미지: 39_sensitivity_overlap.png (좌측 Q1 부분)
→ 만약 Q1/Q2가 한 파일에 있다면 전체 사용

캡션: "공급지수 가중치 (0.1~0.9) 변화 시나리오 테스트.
Q1(안전진입) 상권은 가중치 변화에도 Top5 구성이 80% 이상 일치 → 매우 견고(Robust)함."
→ 11pt, color: 64748B

[우측 차트 — x=5.2, y=0.65, w=4.5, h=3.5]
카드 박스
태그: "Outlier Impact" (fill: C0392B)
이미지: 39_sensitivity_overlap.png (우측 Q2 부분, 혹은 동일 이미지 재사용)

캡션: "명동 이상치 포함/제외 시 수요 변수 계수 변화 비교.
제외 시 수요 변수의 변동폭이 안정되며, 일반 상권에 대한 설명력과 해석 가능성이 개선됨."
→ 11pt, color: 64748B

[하단 요약 박스 — x=0.55, y=4.25, w=9.0, h=0.95]
fill: FFFFFF, 테두리: E2E8F0, 좌측 accent bar (fill: 2D6A4F, w=0.06)
아이콘: "🛡" (원형 fill: 2D6A4F)
제목: "Validation Summary: Robust & Stable" → 14pt bold color: 2D6A4F
내용: "선택한 0.5/0.5 가중치는 극단값이 아닌 안정적 중앙값이며, 이에 따른 추천 결과는 통계적으로 견고함.
명동 이상치 제거는 모델의 일반화 성능을 높이는 합리적 전처리임을 계수 비교를 통해 입증."
→ 12pt, color: 64748B

[푸터] 섹션: "3. Results & Findings" | "14 / 18"
```

---

### S15. 구조적 블루오션 vs 일시적 이상치

**파일 필요:** `40_univariate_r2_top10.png` ✅, `37_residual_trend.png` ✅  
**배경:** `F8F6F1`  
**레이아웃:** 좌측 판별 기준 3가지 + 우측 차트

```
[헤더]
"구조적 블루오션 vs 일시적 이상치" | "Structural Blue Ocean vs. Transient Outliers"

[좌측 — x=0.55, y=0.7, w=4.8, h=4.1]

"▼ 판별 기준 3가지 (Criteria)" → 14pt bold

기준 1 번호 원형 (fill: 1B3A2D):
"9분기 평균 잔차와 최신 분기 상관성"
→ 일시적 매출 급등(이벤트 등)이 아닌, 지속적인 수요 대비 공급 부족 상태인지 확인

기준 2:
"레이더 차트의 근본 수요 강건성"
→ 특정 단일 변수(예: 일시적 유동인구 폭증)에 의존도가 낮고, 직장/주거/소득 등 구조적 기반이 탄탄한지 검증

기준 3:
"상권 유형의 일관성"
→ 해당 상권 유형(골목/발달 등) 내에서 지속적으로 상위 성과를 유지하는지 확인

[구조적 강건성 박스] fill: E8F4F0, 테두리: 2D6A4F
"구조적 강건성(Structural Robustness)의 의미: '분기 변동에도 상위 백분위 유지'
진정한 블루오션은 계절적 요인이나 경기 변동에 불구하고 수요 지표가 꾸준히 공급을 압도하는 곳입니다."

⚠ 경고 박스 (fill: FFF3F3, 테두리 C0392B):
"주의: 경계 케이스(Borderline Cases)는 데이터만으로 판단하기 어려우므로 반드시 임장(현장 검증)을 통해 물리적 제약 요인(경사도, 노후도 등) 확인 권장"

[우측 — x=5.55, y=0.7, w=4.2, h=4.1]
카드 박스
이미지: 40_univariate_r2_top10.png
sizing: contain
하단 캡션: "단변량 R² 분석을 통해 공급 변수(회색) 제외하고도 집객시설, 직장인구 등 수요 변수(파랑)가 매출을 유의미하게 설명함을 확인 → 잔차의 신뢰도 뒷받침"
→ 10pt, color: 64748B

[푸터] 섹션: "3. Results & Findings" | "15 / 18"
```

---

### S16. 핵심 의사결정 요약 — Decision Log

**파일 필요:** 없음 (텍스트 + 플로우)  
**배경:** `F8F6F1`  
**레이아웃:** 좌측 5개 결정 카드 + 우측 Analytic Process Flow 다이어그램

```
[헤더]
"핵심 의사결정 요약" | "Key Decisions & Rationale Summary"

[좌측 5개 결정 카드 — x=0.55, y=0.65, w=5.3, h=4.55]
각 카드 h=0.82, 간격 0.05"
좌측 아이콘 원형 + 카테고리 라벨 + 제목 + 설명

카드1 (아이콘 ✓, fill: 2D6A4F):
라벨: "TARGET VARIABLE" (9pt, color: 9E9E9E)
제목: "Y = 카페·음료 업종 전체 매출 (log1p)"
설명: "찻집 매출 0 문제 해결 및 시장 규모 대리. 로그변환으로 정규성 확보."

카드2 (아이콘 ▼, fill: 1B4F8A):
라벨: "FEATURE SELECTION"
제목: "SHAP Screening → Lasso → VIF (최종 6개)"
설명: "비선형 관련성과 선형 독립성을 교차 검증. 공급 변수 의도적 배제."

카드3 (아이콘 ↔, fill: 2D6A4F):
라벨: "MODELING STRATEGY"
제목: "Pooled OLS + GroupKFold (OOF 잔차)"
설명: "해석 가능성(선형) 우선. 동일 상권 시계열 누수 차단 검증."

카드4 (아이콘 ⚖, fill: C0392B):
라벨: "SCORING LOGIC"
제목: "2-Track: 수요 미실현(잔차) × 공급 부족(지수)"
설명: "수요 예측 오차와 물리적 공급공백을 독립 차원으로 평가."

카드5 (아이콘 🎯, fill: 1B3A2D):
라벨: "FINAL STRATEGY"
제목: "Q1(안전 진입) vs Q2(선점 투자) 이원화"
설명: "창업자의 리스크 성향에 따른 맞춤형 상권 제안."

[우측 Analytic Process Flow — x=6.0, y=0.65, w=3.7, h=4.55]
카드 박스 (fill: FFFFFF, 테두리: E2E8F0)
헤더: "Analytic Process Flow" | 태그 "End-to-End Pipeline"

노드 + 연결선 다이어그램:
Start → Data Prep → Log Trans.
         ↓
      Selection → SHAP (22) → VIF (6)
         ↓
    Track A (Demand) → OLS Model → OOF Residuals
    Track B (Supply) → Scarcity Index
                    → Competition
         ↓
    Integration → 2D Matrix → Q1 Safe
                            → Q2 Opportunity

노드 스타일:
- 원형 (OVAL): fill FFFFFF, 테두리 E2E8F0, 텍스트 12pt
- Track A: fill EBF4FB, 테두리 1B4F8A
- Track B: fill FDECEC, 테두리 C0392B
- 최종 출력: fill 1B3A2D, 텍스트 FFFFFF

[푸터] 섹션: "4. Conclusion — Summary" | "16 / 18"
```

---

### S17. 한계와 향후 과제

**파일 필요:** 없음  
**배경:** `F8F6F1`  
**레이아웃:** 좌우 2분할 (한계 | 향후 과제)

```
[헤더]
"한계와 향후 과제" | "Limitations & Future Work"

[좌측 — 연구의 한계점]
헤더 라벨: "⚠ 연구의 한계점 (Limitations)" → 14pt bold, color: C0392B

카드1: "설명력의 한계 (R² = 0.44)"
fill: FFF8F8, 테두리: E8C5C5
수요 외 56%의 미설명 분산 존재.
공급 변수 외에도 임대료, 건축 규제, 상권 접근성 등 데이터에 없는 미관측 요인이 잔차에 포함될 수 있음.

카드2: "공간 단위의 제약"
서울시 '상권' 단위(1,139개) 집계 데이터 사용.
개별 점포 위치나 도로변/이면도로로 구분 등 미시적 입지 분석은 현장 조사 필수.

카드3: "시간적 외부 타당성"
2025년 3분기 데이터 기준 분석.
분석 시점과 실제 창업 시점 간의 시차 존재.
최신 트렌드 변화 반영을 위한 지속적 업데이트 필요.

[우측 — 향후 과제]
헤더 라벨: "🚀 향후 과제 (Future Work)" → 14pt bold, color: 2D6A4F

카드1 (아이콘 🔄, fill: E8F4F0): "자동 업데이트 파이프라인"
2025Q4 이후 신규 데이터 적재 시 자동 재분석 및 랭킹 갱신 시스템 구축

카드2 (아이콘 📈, fill: E8F4F0): "Cluster SE 적용"
상권별 자기상관을 고려한 견고한 표준오차 추정으로 통계적 신뢰도 향상

카드3 (아이콘 🔧, fill: E8F4F0): "모델 고도화"
상권 유형별 세그먼트 분석 및 변수 간 상호작용(Interaction) 항 추가

카드4 (아이콘 💻, fill: E8F4F0): "Tableau 대시보드 배포"
사용자가 직접 상권을 탐색하고 필터링할 수 있는 인터랙티브 시각화 도구 제공

[최하단 강조 박스 — fill: E8F4F0, 테두리: 2D6A4F]
"✅ 본 연구는 정량적 스크리닝 도구로서의 가치를 가지며,
최종 의사결정은 반드시 현장 정성 평가와 병행되어야 함을 명시."

[푸터] 섹션: "4. Conclusion" | "17 / 18"
```

---

### S18. 예상 질문과 방어 논리 ⭐ (교수님 발표 핵심)

**파일 필요:** 없음  
**배경:** `1B3A2D` (다크 배경, 긴장감 있는 분위기)  
**레이아웃:** 5개 Critique-Defense 쌍, 2열

```
[헤더 — 다크 배경 위]
"예상 질문과 방어 논리" | "Anticipated Critiques & Defense"
색상 반전: 타이틀 FFFFFF, 서브타이틀 97BC62

[5개 Q&A 카드 — 2열 구성]
열1: x=0.55, 열2: x=5.25, 카드 w=4.4, h=0.9, 간격 0.06"

카드 스타일:
- 좌측 비판 라벨: "CRITIQUE 0N" → 9pt, color: C0392B (레드)
- 비판 질문: 12pt bold, color: D4E6D0 (연초록)
- 우측 방어 라벨: "DEFENSE LOGIC" → 9pt, color: 97BC62
- 방어 내용: 11pt, color: FFFFFF
- 구분선: 세로 실선 (color: 2D6A4F, x=중앙)
- 배경: fill 243D33 (약간 밝은 다크 그린)
- 우측 방패 아이콘: 원형 fill 2D6A4F, 텍스트 "🛡"

크리틱 01 (★★★ 최우선):
Q: "왜 Y변수가 '찻집 매출'이 아닌 '카페·음료 전체 매출'인가?"
A: "Zero-Inflation 문제 해결: 찻집이 없는 상권은 매출이 0이므로 Y로 쓸 수 없음.
음료 소비 시장 전체 크기(TAM)를 대리변수로 사용하여 잠재 수요를 측정하는 것이 목적에 부합함."

크리틱 02 (★★★):
Q: "변수 선택과 모델 학습에 동일 데이터를 써서 Leakage 아닌가?"
A: "Screening 목적의 타당성: 정확한 예측 성능 평가가 아닌 '상권 간 상대적 순위 스크리닝'이 목표.
OOF 잔차 추출 시에는 GroupKFold로 누수를 차단했으므로, 순위 도출 결과의 공정성은 확보됨."

크리틱 03 (★★★):
Q: "공급지수 2번째 요소에 찻집이 없으면 점수가 0이 되는 것 아닌가?"
A: "복합 지수의 보완성: 지적은 타당하나, 1번째 항(1/(찻집수+1))이 찻집 0개 상권에 최고점을 부여하여 상쇄함.
민감도 분석 결과, 가중치 변화에도 상권 추천 목록이 일관되게 유지됨(Robustness 확인)."

크리틱 04 (★★):
Q: "패널 데이터에서 Pooled OLS 사용 시 자기상관 문제는?"
A: "GroupKFold 및 Cluster SE 대안: 동일 상권 9개 분기를 통째로 Fold에서 제외하는 GroupKFold로 시계열 누수를 차단함.
향후 연구에서는 Cluster Standard Error를 적용하여 표준오차를 보정할 계획임."

크리틱 05 (★★):
Q: "사분면을 나누는 Cut-off 기준이 임의적이지 않은가?"
A: "자연적 경계 활용: 잔차=0(예측=실제)은 과성과/저성과의 자연스러운 경계이며, 공급지수는 중앙값을 사용함.
핵심은 경계선 부근이 아니라 '사분면 내 상위 랭킹'에 있으므로 추천 결과에는 영향이 제한적임."

[하단 푸터 — 다크 배경 유지]
좌: "서울 찻집 블루오션 상권 분석" (97BC62)
중: "[Sophie의 분석 로그: 파이프라인 25~40번 완비]" (9E9E9E)
우: "18 / 18" (97BC62)
```

---

## 📁 파일 매핑 최종 정리

| 슬라이드 | 사용 파일 | 비고 |
|---|---|---|
| S5 | `25_eda_y_distribution.png` | 3분할 분포 그래프 전체 |
| S6 | `31_fs_shap_summary.png` | SHAP Summary Plot |
| S7 | `40_univariate_r2_top10.png` | 단변량 R² (잔차 진단 대체) |
| S9 | `35_2d_matrix.png` | 축소 미리보기용 |
| S10 | `35_2d_matrix.png` | 전체 크게 배치 |
| S11 | `37_radar_chart.png` | Q1+Q2 전체 (크롭 불필요) |
| S12 | `37_residual_trend.png` | Q1/Q2 9분기 트렌드 |
| S14 | `39_sensitivity_overlap.png` | 민감도 분석 결과 |
| S15 | `40_univariate_r2_top10.png` | 구조적 블루오션 근거 |

**미사용 파일 (참고용으로 보관):**
- `27_eda_scatter_top20.png` — 이상치 포함 산점도 (이상치 제거 비교 설명용)
- `27b_eda_scatter_top20_nooutlier.png` — 발표 중 보조 자료로 활용 가능
- `31_fs_shap_interaction_top.png` — 상호작용 플롯 (Q&A 대비용)
- `27b_eda_correlation_table_nooutlier.csv` — 데이터 원본

---

## ⚙️ pptxgenjs 구현 시 주의사항

### 필수 준수 사항

```javascript
// 1. 색상에 절대 '#' 사용 금지
color: "1B3A2D"   // ✅
color: "#1B3A2D"  // ❌ 파일 손상

// 2. shadow 객체 재사용 금지 → 매번 함수로 생성
const makeShadow = () => ({ 
  type: "outer", blur: 4, offset: 2, 
  color: "000000", opacity: 0.10 
});

// 3. bullet은 반드시 bullet:true 사용
{ text: "내용", options: { bullet: true, breakLine: true } }  // ✅
{ text: "• 내용" }  // ❌ 이중 bullet

// 4. 이미지 삽입 시 sizing 명시
slide.addImage({ 
  path: "35_2d_matrix.png", 
  x: 0.3, y: 1.72, w: 9.4, h: 3.7,
  sizing: { type: "contain", w: 9.4, h: 3.7 }
});
```

### 슬라이드 유형별 배경 처리

```javascript
// 다크 슬라이드 (S1, S18)
slide.background = { color: "1B3A2D" };

// 일반 콘텐츠 슬라이드 (S2~S17)
slide.background = { color: "F8F6F1" };
```

### 공통 헤더 함수 (재사용)

```javascript
function addSlideHeader(slide, pres, title, subtitle, slideNum, sectionName) {
  // 상단 얇은 선
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.05,
    fill: { color: "2D6A4F" }, line: { color: "2D6A4F" }
  });
  // 좌측 accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.55, y: 0.1, w: 0.07, h: 0.5,
    fill: { color: "2D6A4F" }, line: { color: "2D6A4F" }
  });
  // 한글 제목
  slide.addText(title, {
    x: 0.7, y: 0.09, w: 6.5, h: 0.38,
    fontSize: 22, fontFace: "Georgia", bold: true,
    color: "1B3A2D", margin: 0
  });
  // 영문 서브타이틀
  slide.addText(subtitle, {
    x: 7.3, y: 0.09, w: 2.5, h: 0.38,
    fontSize: 12, fontFace: "Calibri", italic: true,
    color: "9E9E9E", align: "right", margin: 0
  });
  // 푸터
  slide.addText("서울 찻집 블루오션 상권 분석", {
    x: 0.3, y: 5.28, w: 3.5, h: 0.2,
    fontSize: 9, color: "BDBDBD"
  });
  slide.addText(sectionName, {
    x: 3.5, y: 5.28, w: 3.0, h: 0.2,
    fontSize: 9, color: "BDBDBD", align: "center"
  });
  slide.addText(`${slideNum} / 18`, {
    x: 8.5, y: 5.28, w: 1.2, h: 0.2,
    fontSize: 9, color: "BDBDBD", align: "right"
  });
}
```

---

## 📋 QA 체크리스트

PPT 생성 후 반드시 확인:

- [ ] 모든 슬라이드에 accent bar와 상단 라인이 있는가
- [ ] 이미지가 카드 박스 경계를 넘치지 않는가
- [ ] 텍스트가 박스 밖으로 잘리지 않는가
- [ ] 다크 슬라이드(S1, S18)에서 텍스트 색상이 흰색/연초록인가
- [ ] 모든 그래프 이미지가 올바른 파일명으로 매핑되었는가
- [ ] 푸터 슬라이드 번호가 순서대로 맞는가
- [ ] Q1 관련 요소는 파랑(1B4F8A), Q2 관련 요소는 빨강(C0392B)으로 일관되는가
- [ ] 카드 shadow 객체가 각 호출마다 새로 생성되는가 (재사용 금지)

---

*작성: 2026-03-09 | 기반 자료: ppt_plan.md, ppt_critique_defense.md, Retrospect.md, 초안 슬라이드 1~17장, 분석 그래프 파일 일체*
