import requests
import pandas as pd
import time

def get_seoul_apt_data(api_key):
    # -----------------------------------------------------
    # 1. 타겟 설정 (아파트 - 상권)
    # -----------------------------------------------------
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "InfoTrdarAptQq"  # 아파트 정보 서비스명
    file_type = "json"
    
    # 수집 기간: 23년 3분기 ~ 25년 3분기
    target_quarters = [
        20233, 20234, 
        20241, 20242, 20243, 20244,
        20251, 20252, 20253
    ]
    
    all_data_rows = [] 
    
    print(f"🏢 '{service_name}' (아파트) 데이터 수집 시작!")
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
df_apt = get_seoul_apt_data(MY_API_KEY)

if not df_apt.empty:
    print("=" * 40)
    print(f"🎉 수집 완료! 총 {len(df_apt)}행")
    
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
        
        # [아파트 단지 정보]
        'APT_HSMP_CO': '아파트_단지_수',
        'AVRG_AE': '아파트_평균_면적',
        'AVRG_MKTC': '아파트_평균_시가', # 이게 제일 중요! (집값)
        
        # [면적별 세대 수]
        'AE_66_SQMT_BELO_HSHLD_CO': '아파트_면적_66_제곱미터_미만_세대_수',
        'AE_66_SQMT_HSHLD_CO': '아파트_면적_66_제곱미터_세대_수',
        'AE_99_SQMT_HSHLD_CO': '아파트_면적_99_제곱미터_세대_수',
        'AE_132_SQMT_HSHLD_CO': '아파트_면적_132_제곱미터_세대_수',
        'AE_165_SQMT_HSHLD_CO': '아파트_면적_165_제곱미터_세대_수',
        
        # [가격대별 세대 수] (1억 미만 ~ 6억 이상)
        'PC_1_HDMIL_BELO_HSHLD_CO': '아파트_가격_1_억_미만_세대_수',
        'PC_1_HDMIL_HSHLD_CO': '아파트_가격_1_억_세대_수',
        'PC_2_HDMIL_HSHLD_CO': '아파트_가격_2_억_세대_수',
        'PC_3_HDMIL_HSHLD_CO': '아파트_가격_3_억_세대_수',
        'PC_4_HDMIL_HSHLD_CO': '아파트_가격_4_억_세대_수',
        'PC_5_HDMIL_HSHLD_CO': '아파트_가격_5_억_세대_수',
        'PC_6_HDMIL_ABOVE_HSHLD_CO': '아파트_가격_6_억_이상_세대_수'
    }
    
    print("🔄 컬럼 이름을 한글로 변경 중...")
    df_apt.rename(columns=rename_map, inplace=True)
    
    # -----------------------------------------------------
    # 4. 저장 (apt.csv)
    # -----------------------------------------------------
    output_name = 'apt.csv'
    df_apt.to_csv(output_name, index=False, encoding='utf-8-sig')
    
    print(f"💾 '{output_name}' 저장 완료!")
    
    # 결과 확인: 동네 부자지수(평균시가) 확인해볼까?
    cols_to_show = ['기준_년분기_코드', '상권_코드_명', '아파트_단지_수', '아파트_평균_시가']
    valid_cols = [c for c in cols_to_show if c in df_apt.columns]
    print(df_apt[valid_cols].head())

else:
    print("😭 데이터를 못 가져왔어. 아파트가 없는 동네만 골랐나..?")