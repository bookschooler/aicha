import requests
import pandas as pd
import time

# ======================================================
# 1. 함수 정의 (여기가 있어야 'NameError'가 안 나요!)
# ======================================================
def get_latest_store_data(api_key):
    """
    서울시 점포(상권) API를 끝까지 순회하여 '커피-음료' 데이터만 수집하는 함수
    """
    base_url = "http://openapi.seoul.go.kr:8088"
    service_name = "TbgisTrdarStor"
    file_type = "json"
    
    all_data = [] 
    start_index = 1
    step = 1000
    
    print(f"📡 API 서버에 접속을 시작합니다... (서비스명: {service_name})")

    while True:
        end_index = start_index + step - 1
        url = f"{base_url}/{api_key}/{file_type}/{service_name}/{start_index}/{end_index}/"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            # 종료 조건
            if service_name not in data:
                if 'RESULT' in data and data['RESULT']['CODE'] == 'INFO-200':
                    print("✅ 모든 데이터 수집 완료! (End of Data)")
                    break
                else:
                    print(f"⚠️ 에러 발생: {data}")
                    break
            
            # 데이터 꺼내기
            rows = data[service_name]['row']
            
            # '커피-음료'만 필터링
            current_batch_count = 0
            for row in rows:
                if row['SVC_INDUTY_CD_NM'] == '커피-음료':
                    all_data.append(row)
                    current_batch_count += 1
            
            print(f"🚀 {start_index}~{end_index} 구간 스캔 중... (커피숍 {current_batch_count}개 발견 / 누적 {len(all_data)}개)")
            
            start_index += step
            # time.sleep(0.1) # 필요시 주석 해제
            
        except Exception as e:
            print(f"❌ 접속 오류: {e}")
            break

    if not all_data:
        return None
        
    return pd.DataFrame(all_data)

# ======================================================
# 2. 실행 구역 (쏘피 키 입력 완료!)
# ======================================================

MY_API_KEY = "4c536c536c736f7034346e5a556264" 

# 함수 호출
df_store = get_latest_store_data(MY_API_KEY)

# 결과 처리
if df_store is not None:
    print("-" * 30)
    print(f"📥 수집된 전체 커피 점포 데이터: {len(df_store)}개")
    
    # [기간 필터링] 23년 3분기 ~ 25년 3분기
    df_store['STDR_YYQU_CD'] = pd.to_numeric(df_store['STDR_YYQU_CD'])
    
    start_date = 20233
    end_date = 20253
    
    df_final = df_store[
        (df_store['STDR_YYQU_CD'] >= start_date) & 
        (df_store['STDR_YYQU_CD'] <= end_date)
    ]
    
    print(f"✂️ 기간 필터링({start_date}~{end_date}) 결과: {len(df_final)}개")
    
    # 필요한 컬럼 선택 및 저장
    cols_needed = ['TRDAR_CD', 'TRDAR_CD_NM', 'STDR_YYQU_CD', 'SVC_INDUTY_CD_NM', 'SIMILR_INDUTY_STOR_CO']
    available_cols = [c for c in cols_needed if c in df_final.columns]
    df_final = df_final[available_cols]
    
    df_final.rename(columns={
        'TRDAR_CD': '상권_코드',
        'TRDAR_CD_NM': '상권_코드_명',
        'STDR_YYQU_CD': '기준_분기_코드',
        'SVC_INDUTY_CD_NM': '서비스_업종_코드_명',
        'SIMILR_INDUTY_STOR_CO': '점포수'
    }, inplace=True)

    df_final.to_csv('store_api_final.csv', index=False, encoding='utf-8-sig')
    print(f"💾 'store_api_final.csv' 저장 완료!")
    
    # 2025년 데이터 확인
    print("\n=== [데이터에 포함된 분기 목록] ===")
    print(sorted(df_final['기준_분기_코드'].unique()))