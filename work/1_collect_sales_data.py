import requests
import pandas as pd
import time

# 1. 설정값
api_key = "5641776872736f703131384441734b47"       # 쏘피 인증키 꼭 확인!
service_name = "VwsmTrdarSelngQq"
target_quarters = [f"{p.year}{p.quarter}" for p in pd.period_range('2023Q3', '2025Q3', freq='Q')]

all_data_list = []

print(f"🚀 안정성 강화 버전 시작! (대상 분기: {len(target_quarters)}개)")

try: # [안전장치 1] 전체를 감싸서 중간에 멈춰도 저장은 하게 함
    for quarter in target_quarters:
        start_index = 1
        end_index = 1000
        
        print(f"\n--- [{quarter} 분기 데이터 수집 시작] ---")
        
        while True:
            url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/{service_name}/{start_index}/{end_index}/{quarter}/"
            
            try:
                # -----------------------------------------------------------
                # ⚡ [수정된 부분] timeout=10 추가! (10초 기다리고 없으면 에러)
                # -----------------------------------------------------------
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if service_name in data and "row" in data[service_name]:
                    rows = data[service_name]['row']
                    count = len(rows)
                    all_data_list.extend(rows)
                    
                    print(f"   ✅ {start_index}~{end_index} 구간: {count}건 수집")
                    
                    if count < 1000:
                        print(f"   👋 {quarter} 분기 끝 (마지막 페이지)")
                        break
                    
                    start_index += 1000
                    end_index += 1000
                else:
                    print(f"   ⚠️ 데이터 없음 (종료)")
                    break
                    
            except requests.exceptions.Timeout:
                print("   ⏳ 서버 응답이 너무 늦어서 재시도합니다... (Timeout)")
                time.sleep(2) # 2초 쉬고 다시 시도하게 둠 (continue가 없으면 루프 처음으로 돌아감)
                continue # 다시 while문 처음으로 가서 재요청
                
            except Exception as e:
                print(f"   ❌ 에러 발생: {e}")
                print("   다음 분기로 넘어갑니다.")
                break
                
            time.sleep(0.3) # 서버 부하 방지

except KeyboardInterrupt:
    print("\n\n🛑 사용자가 강제로 중단했습니다! 지금까지 모은 데이터라도 저장합니다.")

# 3. 저장 단계 (중간에 멈춰도 실행됨)
if all_data_list:
    df = pd.DataFrame(all_data_list)
    print("\n" + "="*50)
    print(f"🎉 [결과] 총 {len(df)}건의 데이터를 건졌어!")
    print(df.head())
    print(df.shape)
    print(df.info())
    
    # 여기서 필터링 하고 싶으면 하면 됨
    # target_gu = ['강남구', '서초구', '송파구']
    # if 'SIGNGU_CD_NM' in df.columns:
    #     df = df[df['SIGNGU_CD_NM'].isin(target_gu)]
    
    file_name = "seoul_market_sales_robust.csv"
    df.to_csv(file_name, index=False, encoding="utf-8-sig")
    print(f"💾 '{file_name}' 안전하게 저장 완료.")
else:
    print("수집된 데이터가 없습니다.")