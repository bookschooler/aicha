import requests
import pandas as pd
import time

def get_seoul_floating_population(api_key):
    # -----------------------------------------------------
    # 1. 타겟 설정 (유동인구 - 상권)
    # -----------------------------------------------------
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "VwsmTrdarFlpopQq"  # 유동인구 서비스명
    file_type = "json"
    
    # 수집 기간: 23년 3분기 ~ 25년 3분기
    target_quarters = [
        20233, 20234, 
        20241, 20242, 20243, 20244,
        20251, 20252, 20253
    ]
    
    all_data_rows = [] 
    
    print(f"🚶 '{service_name}' (유동인구) 데이터 수집 시작!")
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
df_floating = get_seoul_floating_population(MY_API_KEY)

if not df_floating.empty:
    print("=" * 40)
    print(f"🎉 수집 완료! 총 {len(df_floating)}행")
    
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
        
        # [유동인구 전체/성별]
        'TOT_FLPOP_CO': '총_유동인구_수',
        'ML_FLPOP_CO': '남성_유동인구_수',
        'FML_FLPOP_CO': '여성_유동인구_수',
        
        # [연령대별]
        'AGRDE_10_FLPOP_CO': '연령대_10_유동인구_수',
        'AGRDE_20_FLPOP_CO': '연령대_20_유동인구_수',
        'AGRDE_30_FLPOP_CO': '연령대_30_유동인구_수',
        'AGRDE_40_FLPOP_CO': '연령대_40_유동인구_수',
        'AGRDE_50_FLPOP_CO': '연령대_50_유동인구_수',
        'AGRDE_60_ABOVE_FLPOP_CO': '연령대_60_이상_유동인구_수',
        
        # [시간대별] (Time Zone) - 여기가 핵심! 점심/저녁 장사 구분
        'TMZON_00_06_FLPOP_CO': '시간대_00_06_유동인구_수',
        'TMZON_06_11_FLPOP_CO': '시간대_06_11_유동인구_수',
        'TMZON_11_14_FLPOP_CO': '시간대_11_14_유동인구_수',
        'TMZON_14_17_FLPOP_CO': '시간대_14_17_유동인구_수',
        'TMZON_17_21_FLPOP_CO': '시간대_17_21_유동인구_수',
        'TMZON_21_24_FLPOP_CO': '시간대_21_24_유동인구_수',
        
        # [요일별]
        'MON_FLPOP_CO': '월요일_유동인구_수',
        'TUES_FLPOP_CO': '화요일_유동인구_수',
        'WED_FLPOP_CO': '수요일_유동인구_수',
        'THUR_FLPOP_CO': '목요일_유동인구_수',
        'FRI_FLPOP_CO': '금요일_유동인구_수',
        'SAT_FLPOP_CO': '토요일_유동인구_수',
        'SUN_FLPOP_CO': '일요일_유동인구_수'
    }
    
    print("🔄 컬럼 이름을 한글로 변경 중...")
    df_floating.rename(columns=rename_map, inplace=True)
    
    # -----------------------------------------------------
    # 4. 저장 (floating_pop.csv)
    # -----------------------------------------------------
    output_name = 'floating_pop.csv'
    df_floating.to_csv(output_name, index=False, encoding='utf-8-sig')
    
    print(f"💾 '{output_name}' 저장 완료!")
    
    # 결과 확인: 가장 중요한 '총 유동인구'와 '점심시간(11~14)' 확인
    cols_to_show = ['기준_년분기_코드', '상권_코드_명', '총_유동인구_수', '시간대_11_14_유동인구_수']
    valid_cols = [c for c in cols_to_show if c in df_floating.columns]
    print(df_floating[valid_cols].head())

else:
    print("😭 데이터를 못 가져왔어. 트래픽이 많나 봐!")