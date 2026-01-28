import pandas as pd

# ---------------------------------------------------------
# 1. 파일 불러오기
# ---------------------------------------------------------
filename = 'income.csv'
print(f"📂 '{filename}' 파일을 불러옵니다...")

try:
    df = pd.read_csv(filename, encoding='utf-8')
except FileNotFoundError:
    print("🚨 파일이 없어요! 아까 income.py 먼저 실행해서 파일을 만들어주세요!")
    exit()

# ---------------------------------------------------------
# 2. 쏘피의 번역 사전 (Mapping)
# ---------------------------------------------------------
# 쏘피가 준 리스트를 파이썬 딕셔너리로 변환했어!
rename_map = {
    # [기본 정보]
    'STDR_YYQU_CD': '기준_년분기_코드',
    'TRDAR_SE_CD': '상권_구분_코드',
    'TRDAR_SE_CD_NM': '상권_구분_코드_명',
    'TRDAR_CD': '상권_코드',
    'TRDAR_CD_NM': '상권_코드_명',
    
    # [소득 정보]
    'MT_AVRG_INCOME_AMT': '월_평균_소득_금액',
    'INCOME_SCTN_CD': '소득_구간_코드',
    
    # [지출 정보 - 총액]
    'EXPNDTR_TOTAMT': '지출_총금액',
    
    # [지출 정보 - 세부 내역]
    'FDSTFFS_EXPNDTR_TOTAMT': '식료품_지출_총금액',
    'CLTHS_FTWR_EXPNDTR_TOTAMT': '의류_신발_지출_총금액',
    'LVSPL_EXPNDTR_TOTAMT': '생활용품_지출_총금액',
    'MCP_EXPNDTR_TOTAMT': '의료비_지출_총금액',
    'TRNSPORT_EXPNDTR_TOTAMT': '교통_지출_총금액',
    'LSR_EXPNDTR_TOTAMT': '여가_지출_총금액',
    'CLTUR_EXPNDTR_TOTAMT': '문화_지출_총금액',
    'EDC_EXPNDTR_TOTAMT': '교육_지출_총금액',
    'PLESR_EXPNDTR_TOTAMT': '유흥_지출_총금액'
}

# ---------------------------------------------------------
# 3. 이름 바꾸기 & 저장
# ---------------------------------------------------------
print("🔄 컬럼 이름을 한글로 변경 중...")
df.rename(columns=rename_map, inplace=True)

# ---------------------------------------------------------
# 4. 결과 확인
# ---------------------------------------------------------
print("-" * 50)
print("✨ 변경된 컬럼 목록:")
print(df.columns.tolist()) 
print("-" * 50)

# 다시 저장 (덮어쓰기)
df.to_csv(filename, index=False, encoding='utf-8-sig')
print(f"💾 '{filename}' 저장 완료! 이제 한글로 편하게 보세요! 👀")