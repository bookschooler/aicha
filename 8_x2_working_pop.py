import requests
import pandas as pd
import time

def get_seoul_worker_population(api_key):
    # -----------------------------------------------------
    # 1. 쏘피의 타겟 설정 (직장인구)
    # -----------------------------------------------------
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "VwsmTrdarWrcPopltnQq"  # 직장인구 서비스명
    file_type = "json"
    
    # 수집 기간: 23년 3분기 ~ 25년 3분기 (이전과 동일)
    target_quarters = [
        20233, 20234, 
        20241, 20242, 20243, 20244,
        20251, 20252, 20253
    ]
    
    all_data_rows = [] 
    
    print(f"👔 '{service_name}' (직장인구) 데이터 수집 시작!")
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
MY_API_KEY = "534278514d736f703130306a6253566d" 

# 1. 데이터 수집
df_worker = get_seoul_worker_population(MY_API_KEY)

if not df_worker.empty:
    print("=" * 40)
    print(f"🎉 수집 완료! 총 {len(df_worker)}행")
    
    # -----------------------------------------------------
    # 3. 쏘피의 한글 번역기 가동! (Mapping)
    # -----------------------------------------------------
    rename_map = {
        'STDR_YYQU_CD': '기준_년분기_코드',
        'TRDAR_SE_CD': '상권_구분_코드',
        'TRDAR_SE_CD_NM': '상권_구분_코드_명',
        'TRDAR_CD': '상권_코드',
        'TRDAR_CD_NM': '상권_코드_명',
        'TOT_WRC_POPLTN_CO': '총_직장_인구_수',
        'ML_WRC_POPLTN_CO': '남성_직장_인구_수',
        'FML_WRC_POPLTN_CO': '여성_직장_인구_수',
        
        # 연령대 전체
        'AGRDE_10_WRC_POPLTN_CO': '연령대_10_직장_인구_수',
        'AGRDE_20_WRC_POPLTN_CO': '연령대_20_직장_인구_수',
        'AGRDE_30_WRC_POPLTN_CO': '연령대_30_직장_인구_수',
        'AGRDE_40_WRC_POPLTN_CO': '연령대_40_직장_인구_수',
        'AGRDE_50_WRC_POPLTN_CO': '연령대_50_직장_인구_수',
        'AGRDE_60_ABOVE_WRC_POPLTN_CO': '연령대_60_이상_직장_인구_수',
        
        # 남성 연령대 (MAG)
        'MAG_10_WRC_POPLTN_CO': '남성연령대_10_직장_인구_수',
        'MAG_20_WRC_POPLTN_CO': '남성연령대_20_직장_인구_수',
        'MAG_30_WRC_POPLTN_CO': '남성연령대_30_직장_인구_수',
        'MAG_40_WRC_POPLTN_CO': '남성연령대_40_직장_인구_수',
        'MAG_50_WRC_POPLTN_CO': '남성연령대_50_직장_인구_수',
        'MAG_60_ABOVE_WRC_POPLTN_CO': '남성연령대_60_이상_직장_인구_수',
        
        # 여성 연령대 (FAG)
        'FAG_10_WRC_POPLTN_CO': '여성연령대_10_직장_인구_수',
        'FAG_20_WRC_POPLTN_CO': '여성연령대_20_직장_인구_수',
        'FAG_30_WRC_POPLTN_CO': '여성연령대_30_직장_인구_수',
        'FAG_40_WRC_POPLTN_CO': '여성연령대_40_직장_인구_수',
        'FAG_50_WRC_POPLTN_CO': '여성연령대_50_직장_인구_수',
        'FAG_60_ABOVE_WRC_POPLTN_CO': '여성연령대_60_이상_직장_인구_수'
    }
    
    print("🔄 컬럼 이름을 한글로 변경 중...")
    df_worker.rename(columns=rename_map, inplace=True)
    
    # -----------------------------------------------------
    # 4. 저장 (working_pop.csv)
    # -----------------------------------------------------
    output_name = 'working_pop.csv'
    df_worker.to_csv(output_name, index=False, encoding='utf-8-sig')
    
    print(f"💾 '{output_name}' 저장 완료!")
    # 잘 됐는지 헤드만 살짝 볼까?
    cols_to_show = ['기준_년분기_코드', '상권_코드_명', '총_직장_인구_수', '남성_직장_인구_수']
    print(df_worker[cols_to_show].head())

else:
    print("😭 데이터를 못 가져왔어. 잠시 쉬었다 다시 해보자!")