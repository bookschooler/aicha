import pandas as pd
import os

# 1. 파일 경로 설정
current_folder = os.path.dirname(os.path.abspath(__file__))
file_name = "seoul_cafe_sales.csv" 
file_path = os.path.join(current_folder, file_name)

# 2. 데이터 불러오기
df = pd.read_csv(file_path)
print(f"📂 데이터 로드 완료! (총 {len(df)}개)")

# 3. 분기 추출
df['QUARTER_NUM'] = df['STDR_YYQU_CD'].astype(str).str[-1]

# -------------------------------------------------------------
# 4. [계산] 상권별 분기 평균 & 총 평균 (여긴 똑같아!)
# -------------------------------------------------------------
# (A) 분기별 평균
quarterly_avg = df.pivot_table(
    index='TRDAR_CD', 
    columns='QUARTER_NUM', 
    values='THSMON_SELNG_AMT', 
    aggfunc='mean'
)
quarterly_avg.columns = [f'{c}분기_평균' for c in quarterly_avg.columns]

# (B) 3개년 전체 평균
total_avg = df.groupby('TRDAR_CD')['THSMON_SELNG_AMT'].mean().rename('3개년_총평균')

# (C) 데이터 합치기
df = df.merge(quarterly_avg, on='TRDAR_CD', how='left')
df = df.merge(total_avg, on='TRDAR_CD', how='left')

# -------------------------------------------------------------
# 5. [수정됨] 컬럼 위치 재배치 ('SVC_INDUTY_CD_NM' 옆으로!)
# -------------------------------------------------------------
cols = df.columns.tolist()
new_cols = ['1분기_평균', '2분기_평균', '3분기_평균', '4분기_평균', '3개년_총평균']

# (1) 일단 뒤죽박죽 섞여있는 새 컬럼들을 리스트에서 뺌
for col in new_cols:
    if col in cols: cols.remove(col)

# (2) ⚡ 여기가 핵심! 기준 컬럼을 'SVC_INDUTY_CD_NM'으로 잡기
target_col_name = 'SVC_INDUTY_CD_NM' # 쏘피가 원한 위치!

try:
    target_idx = cols.index(target_col_name)
except ValueError:
    print(f"🚨 '{target_col_name}' 컬럼이 없어! 이름 확인해봐.")
    exit()

# (3) 기준 컬럼 바로 뒤(+1)부터 하나씩 끼워 넣기
for i, col in enumerate(new_cols):
    cols.insert(target_idx + 1 + i, col)

# (4) 순서 적용
df = df[cols]

# [고급] 숫자 데이터만 골라서 0으로 채우기 (문자는 그대로 둠)
# select_dtypes: 숫자 타입(number)인 애들만 골라라
num_cols = df.select_dtypes(include=['number']).columns
df[num_cols] = df[num_cols].fillna(0)

#  -------------------------------------------------------------
# 6. 저장
# -------------------------------------------------------------
save_name = "분기별_3개년별_평균매출.csv"
save_path = os.path.join(current_folder, save_name)

df.to_csv(save_path, index=False, encoding="utf-8-sig")

print("\n" + "="*50)
print(f"✨ 위치 조정 완료! '{target_col_name}' 옆에 평균값들을 붙였어.")
# 확인용 출력 (잘 붙었나 보자!)
check_cols = ['TRDAR_SE_CD_NM', 'SVC_INDUTY_CD_NM'] + new_cols[:2] + ['THSMON_SELNG_AMT']
print(df[check_cols].head())