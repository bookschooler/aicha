import requests
import pandas as pd
import time

def get_seoul_store_competitor(api_key):
    # -----------------------------------------------------
    # 1. 타겟 설정 (점포 - 상권)
    # -----------------------------------------------------
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "VwsmTrdarStorQq"  # 점포 데이터 서비스명
    file_type = "json"
    
    # 수집 기간: 23년 3분기 ~ 25년 3분기
    target_quarters = [
        20233, 20234, 
        20241, 20242, 20243, 20244,
        20251, 20252, 20253
    ]
    
    all_data_rows = [] 
    
    print(f"🏪 '{service_name}' (점포 경쟁) 데이터 수집 시작!")
    print(f"☕ 타겟 업종: '커피-음료'만 골라냅니다!")
    print(f"📅 목표 구간: {target_quarters[0]} ~ {target_quarters[-1]}")

    # -----------------------------------------------------
    # 2. 데이터 무한 수집 (일단 다 가져오기)
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

    # DataFrame 변환
    df_raw = pd.DataFrame(all_data_rows)
    
    # -----------------------------------------------------
    # 3. 쏘피의 필터링 요청: '커피-음료'만 남기기!
    # -----------------------------------------------------
    print("\n🔍 '커피-음료' 업종 필터링 중...")
    
    if 'SVC_INDUTY_CD_NM' in df_raw.columns:
        # 정확히 '커피-음료'인 것만 추출
        df_filtered = df_raw[df_raw['SVC_INDUTY_CD_NM'] == '커피-음료'].copy()
        print(f"✨ 필터링 결과: 전체 {len(df_raw)}개 중 -> {len(df_filtered)}개 추출 완료!")
        return df_filtered
    else:
        print("🚨 'SVC_INDUTY_CD_NM' 컬럼이 없어서 필터링을 못 했어!")
        return df_raw

# ======================================================
# 🚀 실행 및 한글 변환
# ======================================================
MY_API_KEY = "4c536c536c736f7034346e5a556264" 

# 1. 데이터 수집 & 필터링
df_competitor = get_seoul_store_competitor(MY_API_KEY)

if not df_competitor.empty:
    print("=" * 40)
    
    # -----------------------------------------------------
    # 4. 쏘피의 한글 번역기 가동! (Mapping)
    # -----------------------------------------------------
    rename_map = {
        # [기본 정보]
        'STDR_YYQU_CD': '기준_년분기_코드',
        'TRDAR_SE_CD': '상권_구분_코드',
        'TRDAR_SE_CD_NM': '상권_구분_코드_명',
        'TRDAR_CD': '상권_코드',
        'TRDAR_CD_NM': '상권_코드_명',
        'SVC_INDUTY_CD': '서비스_업종_코드',
        'SVC_INDUTY_CD_NM': '서비스_업종_코드_명',
        
        # [점포 경쟁 정보] (여기가 핵심!)
        'STOR_CO': '점포_수',
        'SIMILR_INDUTY_STOR_CO': '유사_업종_점포_수', # 경쟁자 수
        'OPBIZ_RT': '개업_율',
        'OPBIZ_STOR_CO': '개업_점포_수',
        'CLSBIZ_RT': '폐업_률',   # 망하는 비율
        'CLSBIZ_STOR_CO': '폐업_점포_수',
        'FRC_STOR_CO': '프랜차이즈_점포_수' # 대기업 침투율
    }
    
    print("🔄 컬럼 이름을 한글로 변경 중...")
    df_competitor.rename(columns=rename_map, inplace=True)
    
    # -----------------------------------------------------
    # 5. 저장 (competitor.csv)
    # -----------------------------------------------------
    output_name = 'competitor.csv'
    df_competitor.to_csv(output_name, index=False, encoding='utf-8-sig')
    
    print(f"💾 '{output_name}' 저장 완료!")
    
    # 결과 확인: 개업률/폐업률/프랜차이즈 수 확인
    cols_to_show = ['기준_년분기_코드', '상권_코드_명', '점포_수', '프랜차이즈_점포_수', '폐업_률']
    valid_cols = [c for c in cols_to_show if c in df_competitor.columns]
    print(df_competitor[valid_cols].head())

else:
    print("😭 데이터를 못 가져왔거나, '커피-음료' 데이터가 없나 봐!")