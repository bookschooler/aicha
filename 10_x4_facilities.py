import requests
import pandas as pd
import time

def get_seoul_facilities(api_key):
    # -----------------------------------------------------
    # 1. 타겟 설정 (집객시설)
    # -----------------------------------------------------
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "VwsmTrdarFcltyQq"  # 집객시설 서비스명
    file_type = "json"
    
    # 수집 기간: 23년 3분기 ~ 25년 3분기
    target_quarters = [
        20233, 20234, 
        20241, 20242, 20243, 20244,
        20251, 20252, 20253
    ]
    
    all_data_rows = [] 
    
    print(f"🏫 '{service_name}' (집객시설) 데이터 수집 시작!")
    print(f"📅 목표 구간: {target_quarters[0]} ~ {target_quarters[-1]}")

    # -----------------------------------------------------
    # 2. 데이터 무한 수집 (Pagination Loop)
    # -----------------------------------------------------
    for quarter in target_quarters:
        print(f"\n⏳ [ {quarter} 분기 ] 데이터 요청 중...", end="")
        
        start_index = 1
        step = 1000
        quarter_count = 0
        
        while True:
            end_index = start_index + step - 1
            
            url = f"{base_url}/{api_key}/{file_type}/{service_name}/{start_index}/{end_index}/{quarter}"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                # 에러/종료 체크
                if service_name not in data:
                    if 'RESULT' in data and data['RESULT']['CODE'] == 'INFO-200':
                        break  # 데이터 끝
                    elif 'RESULT' in data and data['RESULT']['CODE'] in ['INFO-000', 'ERROR-336']:
                        print(f" -> ❌ 데이터 없음 (Skip)")
                        break
                    else:
                        print(f"\n⚠️ 서버 응답 이상: {data}")
                        break
                
                # 데이터 확보
                rows = data[service_name]['row']
                all_data_rows.extend(rows)
                quarter_count += len(rows)
                print(".", end="") # 진행바
                
                # 1000개 미만이면 마지막 페이지
                if len(rows) < step:
                    break
                
                start_index += step
                
            except Exception as e:
                print(f"\n❌ 접속 중 에러: {e}")
                break
        
        if quarter_count > 0:
            print(f" 완료! ({quarter_count}개)")

    return pd.DataFrame(all_data_rows)

# ======================================================
# 🚀 실행 및 한글 변환
# ======================================================
MY_API_KEY = "4c536c536c736f7034346e5a556264" 

# 1. 데이터 수집
df_facilities = get_seoul_facilities(MY_API_KEY)

if not df_facilities.empty:
    print("=" * 40)
    print(f"🎉 수집 완료! 총 {len(df_facilities)}행")
    
    # -----------------------------------------------------
    # 3. 쏘피의 한글 번역기 가동! (Mapping)
    # -----------------------------------------------------
    rename_map = {
        # [기본 정보]
        'STDR_YYQU_CD': '기준_년분기_코드',
        'TRDAR_SE_CD': '상권_구분_코드',
        'TRDAR_SE_CD_NM': '상권_구분_코드_명',
        'TRDAR_CD': '상권_코드',
        'TRDAR_CD_NM': '상권_코드_명',
        
        # [집객시설 수 - 주요 시설]
        'VIATR_FCLTY_CO': '집객시설_수',
        'PBLOFC_CO': '관공서_수',
        'BANK_CO': '은행_수',
        'GEHSPT_CO': '종합병원_수',
        'GNRL_HSPTL_CO': '일반_병원_수',
        'PARMACY_CO': '약국_수',
        
        # [교육 시설]
        'KNDRGR_CO': '유치원_수',
        'ELESCH_CO': '초등학교_수',
        'MSKUL_CO': '중학교_수',
        'HGSCHL_CO': '고등학교_수',
        'UNIV_CO': '대학교_수',
        
        # [상업/문화 시설]
        'DRTS_CO': '백화점_수',
        'SUPMK_CO': '슈퍼마켓_수',
        'THEAT_CO': '극장_수',
        'STAYNG_FCLTY_CO': '숙박_시설_수',
        
        # [교통 시설] (이거 진짜 중요! ⭐)
        'ARPRT_CO': '공항_수',
        'RLROAD_STATN_CO': '철도_역_수',
        'BUS_TRMINL_CO': '버스_터미널_수',
        'SUBWAY_STATN_CO': '지하철_역_수',
        'BUS_STTN_CO': '버스_정거장_수'
    }
    
    print("🔄 컬럼 이름을 한글로 변경 중...")
    df_facilities.rename(columns=rename_map, inplace=True)
    
    # -----------------------------------------------------
    # 4. 저장 (facilities.csv)
    # -----------------------------------------------------
    output_name = 'facilities.csv'
    df_facilities.to_csv(output_name, index=False, encoding='utf-8-sig')
    
    print(f"💾 '{output_name}' 저장 완료!")
    
    # 결과 확인: 교통/상업 시설 위주로 잘 들어왔나 보자!
    cols_to_show = ['기준_년분기_코드', '상권_코드_명', '집객시설_수', '지하철_역_수', '관공서_수']
    # 혹시 컬럼 없을까 봐 안전장치
    valid_cols = [c for c in cols_to_show if c in df_facilities.columns]
    print(df_facilities[valid_cols].head())

else:
    print("😭 데이터를 못 가져왔어. 서버 상태를 확인해줘!")