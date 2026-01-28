# 파일명: income.py
import requests
import pandas as pd
import time

def get_seoul_income_consumption(api_key):
    # -----------------------------------------------------
    # 🎯 쏘피의 타겟 설정
    # -----------------------------------------------------
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "trdarNcmCnsmp"
    file_type = "json"             # 파이썬은 json이 편해!
    
    # 수집 기간: 23년 3분기 ~ 25년 3분기
    target_quarters = [
        20233, 20234, 
        20241, 20242, 20243, 20244,
        20251, 20252, 20253
    ]
    
    all_data_rows = [] 
    
    print(f"💰 '{service_name}' (소득/소비) 데이터 수집을 시작합니다!")
    print(f"📅 목표 구간: {target_quarters[0]} ~ {target_quarters[-1]}")

    # [Loop 1] 분기별 순회
    for quarter in target_quarters:
        print(f"\n⏳ [ {quarter} 분기 ] 데이터 요청 중...", end="")
        
        start_index = 1
        step = 1000  # 한 번에 가져올 최대 개수
        quarter_count = 0
        
        # [Loop 2] 페이지 무한 넘기기 (끝까지!)
        while True:
            end_index = start_index + step - 1
            
            # URL 조합
            url = f"{base_url}/{api_key}/{file_type}/{service_name}/{start_index}/{end_index}/{quarter}"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                # --- 응답 상태 체크 ---
                if service_name not in data:
                    # 데이터 없음 (INFO-200) -> 정상 종료
                    if 'RESULT' in data and data['RESULT']['CODE'] == 'INFO-200':
                        break 
                    # 아직 없는 미래 데이터 (INFO-000 등)
                    elif 'RESULT' in data and data['RESULT']['CODE'] in ['INFO-000', 'ERROR-336']:
                        print(f" -> ❌ 데이터 없음 (Skip)")
                        break
                    else:
                        # 진짜 서버 에러
                        print(f"\n⚠️ 서버 응답 이상: {data}")
                        break
                
                # --- 데이터 확보 ---
                rows = data[service_name]['row']
                all_data_rows.extend(rows) # 리스트에 몽땅 추가
                quarter_count += len(rows)
                
                print(".", end="") # 진행바 효과
                
                # --- [탈출 조건] ---
                # 가져온 개수가 1000개 미만이면 마지막 페이지임
                if len(rows) < step:
                    break
                
                # 다음 페이지로
                start_index += step
                
            except Exception as e:
                print(f"\n❌ 접속 중 에러: {e}")
                break
        
        if quarter_count > 0:
            print(f" 완료! ({quarter_count}개)")

    return pd.DataFrame(all_data_rows)

# ======================================================
# 🚀 실행 구역
# ======================================================
MY_API_KEY = "4270744f47736f7036395664466b7a" 

# 1. 데이터 수집
df_final = get_seoul_income_consumption(MY_API_KEY)

# 2. 결과 저장
if not df_final.empty:
    print("=" * 40)
    print(f"🎉 총 수집된 데이터: {len(df_final)}행")
    
    # (선택) 주요 컬럼만 미리 보기
    # 상권코드, 상권명, 기준분기, 월평균소득, 지출총액 등
    cols_check = ['TRDAR_CD', 'TRDAR_CD_NM', 'STDR_YYQU_CD', 'AVRG_MTH_INC', 'EXPNDTR_TOTAMT']
    valid_cols = [c for c in cols_check if c in df_final.columns]
    
    print(df_final[valid_cols].head())
    
    # 파일 저장
    output_name = 'income.csv'
    df_final.to_csv(output_name, index=False, encoding='utf-8-sig')
    print(f"💾 '{output_name}' 저장 완료! 지갑 털기 성공! 💸")
    
else:
    print("😭 데이터를 하나도 못 가져왔어. 서비스명이나 키를 다시 확인해봐!")