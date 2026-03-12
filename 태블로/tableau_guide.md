# Tableau 대시보드 구현 가이드
## 찻집 블루오션 상권분석 프로젝트

---

## 필요 파일 목록

| 파일 | 용도 |
|------|------|
| `상권_영역/서울시 상권분석서비스(영역-상권).shp` | 상권 경계 폴리곤 (Spatial File) |
| `41_tableau_sangwon.csv` | 상권별 블루오션 점수 + 중심 좌표 |
| `41_tableau_teashops.csv` | 찻집 위치 (lon/lat) |
| `41_tableau_trend.csv` | 분기별 매출 추세 (Q1/Q2 Top5 + 전체 중간값) |
| `41_tableau_demand_heatmap.csv` | 수요변수 히트맵 (long형) |
| `41_tableau_sensitivity.csv` | 민감도 분석 (long형) |
| `41_tableau_gu_summary.csv` | 자치구별 블루오션 분포 |

---

## 슬라이드 1 — 서울 블루오션 지도 (메인)

**인사이트:** "어디에 찻집이 없고, 수요는 있는가?"

### 데이터 연결
1. **Connect > Spatial File** → `상권_영역/서울시 상권분석서비스(영역-상권).shp` 선택
2. **Add > Text File** → `41_tableau_sangwon.csv` 추가
3. **Join 설정:** `TRDAR_CD` (shapefile) = `상권_코드` (CSV), Inner Join
4. 두 번째 데이터소스: **Connect > Text File** → `41_tableau_teashops.csv`

### 시각화 구성
```
[레이어 1 - 상권 경계]
- Rows/Cols: 자동 (Geometry 더블클릭 시 맵 생성)
- Marks > Map: Geometry 드래그
- Color: 사분면_레이블
  · Q1_검증시장공백 → 파란색 계열
  · Q2_잠재수요미실현 → 초록색 계열
  · Q3/Q4 → 연회색
- Opacity: 70%
- Tooltip: 상권_코드_명, 사분면_레이블, residual_latest, supply_shortage, 찻집수_latest

[레이어 2 - 찻집 위치 점]
- 두 번째 데이터소스 선택
- 계산 필드 생성: MAKEPOINT([lat], [lon]) → 이름: "찻집위치"
- Marks > Circle, Size: 작게 (2~3), Color: 주황색
- Dual Axis (레이어 1과 겹치기)
- Tooltip: 가게명, 도로명주소
```

### 핵심 조작
- Ctrl+클릭으로 Q1/Q2 상권만 필터 → "찻집이 없는 수요 상권" 강조
- 필터: 블루오션여부 = '블루오션'으로 고정 가능

---

## 슬라이드 2 — 2D 매트릭스 산점도 (핵심 방법론)

**인사이트:** "수요 실현도(X) × 공급 부족(Y) → 4개 전략 구역"

### 데이터: `41_tableau_sangwon.csv`

### 시각화 구성
```
- X축: residual_latest (OOF 잔차 = 수요 실현도)
- Y축: supply_shortage (공급부족지수)
- Color: 사분면_레이블
- Size: 매출_latest (버블 크기)
- Label: 통합순위_top30 ≤ 10인 상권만 레이블 표시
- Reference Line: X=0 (수직선), Y=0.5 (수평선) → 4사분면 경계
- 필터: 사분면 선택 가능
```

### 계산 필드
```
// 사분면 경계선 레이블용
IF [residual_latest] >= 0 AND [supply_shortage] >= 0.5
THEN "Q1: 안전진입"
ELSEIF [residual_latest] < 0 AND [supply_shortage] >= 0.5
THEN "Q2: 선점"
ELSEIF [residual_latest] >= 0
THEN "Q3: 포화"
ELSE "Q4: 비추"
END
```

---

## 슬라이드 3 — Q1 vs Q2 Top10 랭킹

**인사이트:** "구체적으로 어떤 상권에 들어가야 하는가?"

### 데이터: `41_tableau_sangwon.csv`

### 시각화 구성 (두 차트를 나란히)

**왼쪽 — Q1 Top10 (안전진입)**
```
- 필터: 사분면 startswith 'Q1'
- 정렬: residual_latest 내림차순 Top 10
- 가로 막대: X = residual_latest, Y = 상권_코드_명
- Color: 연파랑
- Label: residual_latest (소수점 2자리), 자치구_코드_명
```

**오른쪽 — Q2 Top10 (선점)**
```
- 필터: 사분면 startswith 'Q2'
- 정렬: supply_shortage 내림차순 Top 10
- 가로 막대: X = supply_shortage, Y = 상권_코드_명
- Color: 연초록
- Label: supply_shortage (소수점 3자리), 자치구_코드_명
```

---

## 슬라이드 4 — 수요변수 히트맵

**인사이트:** "상위 상권들이 어떤 수요 특성에서 강한가?"

### 데이터: `41_tableau_demand_heatmap.csv`

### 시각화 구성
```
- Rows: 상권_코드_명 (순위 정렬)
- Columns: 변수명 (SHAP순위 정렬)
- Marks > Square
- Color: 분위수 (0~1, 진할수록 높음)
  → 색상: 흰색(낮음) ~ 진파랑(높음), Diverging 권장
- Label: 분위수 표시 (소수점 2자리)
- 필터: 그룹 (Q1_Top5 / Q2_Top5 구분)
```

### 변수명 순서 (SHAP 중요도 순)
집객시설_수 > 총_직장_인구_수 > 월_평균_소득_금액 > 총_가구_수 > 카페_검색지수 > 지하철_노선_수

---

## 슬라이드 5 — 분기별 매출 추세

**인사이트:** "추천 상권은 시간이 지날수록 성장하고 있는가?"

### 데이터: `41_tableau_trend.csv`

### 시각화 구성
```
- X축: 분기 (20233 → '2023Q3' 형식)
- Y축: 당월_매출_금액 (억원 단위 변환)
- Lines: 상권_코드_명별 (Q1/Q2 Top5 + 전체중간값)
- Color: 사분면_레이블
  · Q1 → 파랑 계열, Q2 → 초록 계열, 기준선 → 회색 점선
- Dual Axis: 카페_검색지수 (오른쪽 Y축)
- Mark: Line + Circle (분기 점 표시)
```

### 계산 필드 (억원 변환)
```
[당월_매출_금액] / 100000000
```

---

## 슬라이드 6 — 자치구별 블루오션 분포

**인사이트:** "어느 구에 블루오션 상권이 집중되어 있는가?"

### 데이터: `41_tableau_gu_summary.csv`

### 시각화 구성 (두 가지 옵션)

**옵션 A — 히트맵 (자치구 × 사분면)**
```
- Rows: 자치구_코드_명 (Q1 상권수 내림차순 정렬)
- Columns: 사분면
- Color: 상권수 (연속형, 진할수록 많음)
- Label: 상권수
```

**옵션 B — 누적 가로 막대**
```
- Y축: 자치구_코드_명
- X축: 상권수 (누적)
- Color: 사분면 (Q1=파랑, Q2=초록, Q3/Q4=회색)
- 정렬: Q1+Q2 합계 내림차순
```

---

## 슬라이드 7 — 민감도 분석 (방법론 신뢰성)

**인사이트:** "가중치 0.5/0.5가 특별히 유리하게 설계된 것이 아님을 증명"

### 데이터: `41_tableau_sensitivity.csv`

### 시각화 구성 — 범프 차트 (순위 변화)

```
- X축: w1 (가중치, 0.1 ~ 0.9)
- Y축: 순위 (1위가 위, 5위가 아래) → 역순 정렬
- Lines: 상권명별 (Q1/Q2 각각 5개)
- Color: 상권명
- 필터: 사분면 (Q1 / Q2 탭 전환)
- Reference Band: w1=0.5 (현재 선택 가중치 강조)

또는 히트맵 형태:
- Rows: 상권명, Columns: w1 (가중치)
- Color: 순위 (1위=짙은 파랑, 5위=연한 색)
- 안정적이면 같은 색이 수평으로 이어짐
```

---

## 대시보드 조립 팁

1. **색상 통일:** Q1=`#4C72B0` (파랑), Q2=`#55A868` (초록), 기타=`#CCCCCC`
2. **필터 공유:** 사분면 필터를 슬라이드 1~6에 모두 연결 (Apply to Worksheets > All)
3. **툴팁 강화:** 지도 슬라이드에서 상권 클릭 시 해당 상권의 추세 차트 팝업 (Tooltip > Insert Sheet)
4. **슬라이드 순서:** 1(지도) → 2(매트릭스) → 3(랭킹) → 4(수요프로파일) → 5(추세) → 6(자치구) → 7(민감도)

---

## Shapefile Join 상세 (슬라이드 1)

Shapefile의 join key: `TRDAR_CD` (= 우리 데이터의 `상권_코드`)

```
Tableau 조인 설정:
  Left Table:  서울시 상권분석서비스(영역-상권) [TRDAR_CD]
  Right Table: 41_tableau_sangwon.csv [상권_코드]
  Join Type:   Left Join (경계는 모두 표시, 데이터 없는 상권은 회색)
```

*작성: Claude Sonnet 4.6 / 2026-03-12*
