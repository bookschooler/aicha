import pandas as pd

# ---------------------------------------------------------
# 1. 파일 불러오기
# ---------------------------------------------------------
filename = 'sales.csv' 
# (혹시 아까 합친 파일 이름이 'seoul_coffee_Y_final.csv'라면 그걸로 바꿔줘!)

print(f"📂 '{filename}' 데이터를 불러옵니다...")
try:
    df = pd.read_csv(filename, encoding='utf-8')
except:
    # 혹시 인코딩 에러 나면 cp949로 시도
    df = pd.read_csv(filename, encoding='cp949')

# ---------------------------------------------------------
# 2. 쏘피의 한글 번역 사전 (Dictionary)
# ---------------------------------------------------------
rename_map = {
    # [기본 정보]
    'STDR_YYQU_CD': '기준_년분기_코드',
    'TRDAR_SE_CD': '상권_구분_코드',
    'TRDAR_SE_CD_NM': '상권_구분_코드_명',
    'TRDAR_CD': '상권_코드',
    'TRDAR_CD_NM': '상권_코드_명',
    'SVC_INDUTY_CD': '서비스_업종_코드',
    'SVC_INDUTY_CD_NM': '서비스_업종_코드_명',
    
    # [매출 금액 - 전체/요일]
    'THSMON_SELNG_AMT': '당월_매출_금액',
    'THSMON_SELNG_CO': '당월_매출_건수',
    'MDWK_SELNG_AMT': '주중_매출_금액',
    'WKEND_SELNG_AMT': '주말_매출_금액',
    'MON_SELNG_AMT': '월요일_매출_금액',
    'TUES_SELNG_AMT': '화요일_매출_금액',
    'WED_SELNG_AMT': '수요일_매출_금액',
    'THUR_SELNG_AMT': '목요일_매출_금액',
    'FRI_SELNG_AMT': '금요일_매출_금액',
    'SAT_SELNG_AMT': '토요일_매출_금액',
    'SUN_SELNG_AMT': '일요일_매출_금액',
    
    # [매출 금액 - 시간대]
    'TMZON_00_06_SELNG_AMT': '시간대_00~06_매출_금액',
    'TMZON_06_11_SELNG_AMT': '시간대_06~11_매출_금액',
    'TMZON_11_14_SELNG_AMT': '시간대_11~14_매출_금액',
    'TMZON_14_17_SELNG_AMT': '시간대_14~17_매출_금액',
    'TMZON_17_21_SELNG_AMT': '시간대_17~21_매출_금액',
    'TMZON_21_24_SELNG_AMT': '시간대_21~24_매출_금액',
    
    # [매출 금액 - 성별/연령]
    'ML_SELNG_AMT': '남성_매출_금액',
    'FML_SELNG_AMT': '여성_매출_금액',
    'AGRDE_10_SELNG_AMT': '연령대_10_매출_금액',
    'AGRDE_20_SELNG_AMT': '연령대_20_매출_금액',
    'AGRDE_30_SELNG_AMT': '연령대_30_매출_금액',
    'AGRDE_40_SELNG_AMT': '연령대_40_매출_금액',
    'AGRDE_50_SELNG_AMT': '연령대_50_매출_금액',
    'AGRDE_60_ABOVE_SELNG_AMT': '연령대_60_이상_매출_금액',
    
    # [매출 건수 - 전체/요일]
    'MDWK_SELNG_CO': '주중_매출_건수',
    'WKEND_SELNG_CO': '주말_매출_건수',
    'MON_SELNG_CO': '월요일_매출_건수',
    'TUES_SELNG_CO': '화요일_매출_건수',
    'WED_SELNG_CO': '수요일_매출_건수',
    'THUR_SELNG_CO': '목요일_매출_건수',
    'FRI_SELNG_CO': '금요일_매출_건수',
    'SAT_SELNG_CO': '토요일_매출_건수',
    'SUN_SELNG_CO': '일요일_매출_건수',
    
    # [매출 건수 - 시간대] (여기가 오타 수정된 부분! 깔끔하게!)
    'TMZON_00_06_SELNG_CO': '시간대_00~06_매출_건수',
    'TMZON_06_11_SELNG_CO': '시간대_06~11_매출_건수',
    'TMZON_11_14_SELNG_CO': '시간대_11~14_매출_건수',
    'TMZON_14_17_SELNG_CO': '시간대_14~17_매출_건수',
    'TMZON_17_21_SELNG_CO': '시간대_17~21_매출_건수',
    'TMZON_21_24_SELNG_CO': '시간대_21~24_매출_건수',
    
    # [매출 건수 - 성별/연령]
    'ML_SELNG_CO': '남성_매출_건수',
    'FML_SELNG_CO': '여성_매출_건수',
    'AGRDE_10_SELNG_CO': '연령대_10_매출_건수',
    'AGRDE_20_SELNG_CO': '연령대_20_매출_건수',
    'AGRDE_30_SELNG_CO': '연령대_30_매출_건수',
    'AGRDE_40_SELNG_CO': '연령대_40_매출_건수',
    'AGRDE_50_SELNG_CO': '연령대_50_매출_건수',
    'AGRDE_60_ABOVE_SELNG_CO': '연령대_60_이상_매출_건수',

    # [쏘피의 추가 요청]
    'STOR_CO': '점포_수',
    'STORE_CO': '점포_수',       # 아까 우리가 영어로 바꾼 이름도 대비!
    'SALES_PER_STORE': '점포당_평균_매출',
    
    # [좌표/주소 관련 - 혹시 몰라 넣어둠]
    'XCNTS_VALUE': '엑스좌표_값',
    'YDNTS_VALUE': '와이좌표_값',
    'SIGNGU_CD': '자치구_코드',
    'ADSTRD_CD': '행정동_코드'
}

# ---------------------------------------------------------
# 3. 변환 실행
# ---------------------------------------------------------
print("🔄 컬럼 이름을 한글로 변경 중...")
df.rename(columns=rename_map, inplace=True)

# ---------------------------------------------------------
# 4. 저장 및 확인
# ---------------------------------------------------------
# 파일명은 'sales_kor.csv'로 저장해서 원본이랑 헷갈리지 않게 할게!
output_filename = 'y_final.csv'
df.to_csv(output_filename, index=False, encoding='utf-8-sig')

print("-" * 50)
print(f"🎉 변환 완료! '{output_filename}' 저장됨.")
print("✨ [변경된 컬럼 목록 (일부)]")
# 너무 많으니까 앞부분 10개만 보여줄게
print(df.columns[:10].tolist())