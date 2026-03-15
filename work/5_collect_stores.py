import requests
import pandas as pd
import time

def get_seoul_coffee_master(api_key):
    # -----------------------------------------------------
    # 🏆 쏘피가 찾아낸 '진짜' 정보들 적용
    # -----------------------------------------------------
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "VwsmTrdarStorQq"  # (구버전 Tbgis 아님!)
    file_type = "json"
    
    # 📅 우리가 필요한 분기 리스트 (2023년 3분기 ~ 2025년 3분기)
    # (2025년 데이터가 아직 서버에 없으면 알아서 건너뛰도록 만들었어!)
    target_quarters = [
        20233, 20234, 
        20241, 20242, 20243, 20244,
        20251, 20252, 20253
    ]
    
    all_coffee_rows = [] # 커피 데이터를 차곡차곡 모을 리스트

    print(f"📡 '{service_name}' 서비스 접속 시작! (쏘피가 찾아낸 길! 🛣️)")
    
    # [1] 분기별로 순회 (20233 -> 20234 -> ...)
    for quarter in target_quarters:
        print(f"\n⏳ [ {quarter} 분기 ] 데이터 긁어오는 중...", end="")
        
        start_index = 1
        step = 1000  # 한 번에 요청할 최대 개수
        quarter_count = 0 # 이번 분기에 찾은 커피숍 수
        
        # [2] 페이지 넘기기 무한 루프 (1~1000, 1001~2000 ...)
        while True:
            end_index = start_index + step - 1
            
            # URL 만들기
            url = f"{base_url}/{api_key}/{file_type}/{service_name}/{start_index}/{end_index}/{quarter}"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                # --- 에러 및 종료 조건 체크 ---
                if service_name not in data:
                    # 데이터 없음 (INFO-200): 정상 종료 -> 다음 분기로!
                    if 'RESULT' in data and data['RESULT']['CODE'] == 'INFO-200':
                        break 
                    # 아직 생성 안 된 미래 데이터 (INFO-000 등)
                    elif 'RESULT' in data and data['RESULT']['CODE'] in ['INFO-000', 'ERROR-336']:
                        print(f" -> ❌ 아직 데이터 없음 (Pass)")
                        break
                    else:
                        # 진짜 에러
                        print(f"\n⚠️ 서버 응답 이상: {data}")
                        break
                
                # --- 데이터 꺼내기 ---
                rows = data[service_name]['row']
                
                # --- '커피-음료'만 쏙쏙 골라 담기 ---
                # (API 컬럼명: SVC_INDUTY_CD_NM)
                for row in rows:
                    if row.get('SVC_INDUTY_CD_NM') == '커피-음료':
                        all_coffee_rows.append(row)
                        quarter_count += 1
                
                # 진행 상황 점찍기 (......)
                print(".", end="")
                
                # --- [중요] 다음 페이지로 갈지 결정 ---
                # 만약 받아온 개수가 1000개 미만이면? -> 이게 마지막 페이지라는 뜻!
                if len(rows) < step:
                    break
                
                # 1000개 꽉 채워서 왔으면? -> 다음 페이지가 있다는 뜻!
                start_index += step
                
            except Exception as e:
                print(f"\n❌ 접속 중 에러 발생: {e}")
                break
        
        # 분기 완료 로그
        if quarter_count > 0:
            print(f" 완료! (커피숍 {quarter_count}개 확보)")

    return pd.DataFrame(all_coffee_rows)

# ======================================================
# 🚀 실행 구역
# ======================================================
MY_API_KEY = "6755756445736f703234585370764d" 

# 함수 실행
df_final = get_seoul_coffee_master(MY_API_KEY)

if not df_final.empty:
    print("-" * 30)
    print(f"🎉 대성공! 총 수집된 데이터: {len(df_final)}개")
    
    # 필요한 컬럼만 깔끔하게 정리
    # (쏘피가 확인한 컬럼명 기준)
    cols_to_keep = ['TRDAR_CD', 'TRDAR_CD_NM', 'STDR_YYQU_CD', 'SVC_INDUTY_CD_NM', 'SIMILR_INDUTY_STOR_CO']
    
    # 실제 데이터에 존재하는 컬럼만 선택 (안전장치)
    valid_cols = [c for c in cols_to_keep if c in df_final.columns]
    df_save = df_final[valid_cols]
    
    # 한글 이름표 달아주기
    df_save.rename(columns={
        'TRDAR_CD': '상권_코드',
        'TRDAR_CD_NM': '상권_코드_명',
        'STDR_YYQU_CD': '기준_분기_코드',
        'SVC_INDUTY_CD_NM': '서비스_업종_코드_명',
        'SIMILR_INDUTY_STOR_CO': '점포수'
    }, inplace=True)
    
    # 파일 저장
    df_save.to_csv('stores.csv', index=False, encoding='utf-8-sig')
    print(f"💾 'stores.csv' 저장 완료!")
    
    print("\n[확보된 분기 목록]")
    print(sorted(df_save['기준_분기_코드'].unique()))
    
else:
    print("😭 데이터를 하나도 못 가져왔어... 분기 코드나 키를 다시 확인해봐야 할 것 같아.")