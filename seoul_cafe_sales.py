import pandas as pd
import os

# 1. 파일 경로 설정 (안전하게 내 방에서 찾기)
current_folder = os.path.dirname(os.path.abspath(__file__))
input_file = "seoul_market_sales.csv" # 원본 파일
output_file = "seoul_caffe_data.csv"       # 저장할 파일 이름

file_path = os.path.join(current_folder, input_file)
save_path = os.path.join(current_folder, output_file)

# 2. 데이터 불러오기
try:
    df = pd.read_csv(file_path)
    print(f"📂 원본 데이터 불러오기 성공! (총 {len(df)}개)")
    
    # ---------------------------------------------------------
    # ⚡ [핵심] 필터링: "서비스 업종이 '커피-음료'인 것만 골라라!"
    # ---------------------------------------------------------
    # 조건: df['컬럼명'] == '찾는값'
    cafe_df = df[df['SVC_INDUTY_CD_NM'] == '커피-음료']
    cafe_df['SVC_INDUTY_CD_NM'] =  cafe_df['SVC_INDUTY_CD_NM'].replace('커피-음료', '커피음료')
    
    # 3. 결과 확인
    print("-" * 50)
    print(f"☕ 필터링 완료!")
    print(f"   - 남은 데이터 개수: {len(cafe_df)}개")
    
    # 혹시 모르니 진짜 잘 됐는지 상위 3개만 눈으로 확인
    print("\n[미리보기]")
    print(cafe_df[['STDR_YYQU_CD', 'TRDAR_SE_CD_NM', 'SVC_INDUTY_CD_NM', 'THSMON_SELNG_AMT']].head(3))
    
    # 4. 파일로 저장하기
    cafe_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print("-" * 50)
    print(f"💾 '{output_file}' 파일로 저장했어! 이제 분석 준비 끝!")
    
except FileNotFoundError:
    print("🚨 파일을 못 찾겠어! 파일 이름이나 위치를 다시 확인해줘.")