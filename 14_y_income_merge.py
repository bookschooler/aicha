import pandas as pd  # 판다스 라이브러리를 pd라는 이름으로 불러옵니다.

# 1. 데이터 불러오기
print("📂 데이터를 불러오는 중...")  # 작업 시작을 알립니다.
try:  # 먼저 utf-8 인코딩으로 읽기를 시도합니다.
    df_y = pd.read_csv('y_final.csv', encoding='utf-8')  # y_final 파일을 읽어서 df_y에 저장합니다.
    df_income = pd.read_csv('income.csv', encoding='utf-8')  # income 파일을 읽어서 df_income에 저장합니다.
except:  # 에러가 나면 윈도우 기본 인코딩인 cp949로 다시 읽습니다.
    df_y = pd.read_csv('y_final.csv', encoding='cp949')  # y_final 파일을 cp949로 읽습니다.
    df_income = pd.read_csv('income.csv', encoding='cp949')  # income 파일을 cp949로 읽습니다.

# 2. 병합을 위한 열쇠(Key) 설정
keys = ['기준_년분기_코드', '상권_코드']  # 두 표를 연결할 공통 기준 열들을 리스트로 묶습니다.

# 3. 오른쪽 테이블(income) 중복 제거 방어막 (행 뻥튀기 방지!)
print("🛡️ 오른쪽 데이터의 중복 열쇠를 검사하고 제거합니다...")  # 방어 작업 시작을 알립니다.
df_income_clean = df_income.drop_duplicates(subset=keys, keep='first')  # 열쇠가 똑같은 행이 여러 개면 첫 번째만 남기고 지웁니다.

# 4. 대망의 LEFT JOIN 병합
print("🔗 y_final을 기준으로 LEFT JOIN을 실행합니다...")  # 병합 시작을 알립니다.
df_merged = pd.merge(left=df_y, right=df_income_clean, on=keys, how='left')  # df_y를 왼쪽에 두고 df_income_clean을 열쇠 기준으로 갖다 붙입니다.

# 5. 병합 전후 행 개수 검사 (무결성 체크)
print("\n=== 병합 결과 확인 ===")  # 결과 확인창 제목을 출력합니다.
print(f"✅ 원본 y_final 행 개수: {len(df_y)}개")  # 원래 기둥의 길이를 출력합니다.
print(f"✅ 병합된 데이터 행 개수: {len(df_merged)}개")  # 합쳐진 후의 길이를 출력합니다.

if len(df_y) == len(df_merged):  # 원래 길이와 합쳐진 길이가 똑같으면,
    print("🎉 성공! 행 개수가 완벽하게 유지되었습니다.")  # 성공 메시지를 띄웁니다.
else:  # 만약 길이가 달라졌다면,
    print("⚠️ 경고! 행 개수가 달라졌습니다. 데이터를 다시 확인해야 합니다.")  # 경고 메시지를 띄웁니다.

# 6. 최종 파일 저장

output_filename = 'merged_y_income.csv'  # 저장할 파일 이름을 정합니다.
df_merged.to_csv(output_filename, index=False, encoding='utf-8-sig')  # 합쳐진 데이터를 한글이 안 깨지게 저장합니다.
print(f"💾 '{output_filename}' 파일이 성공적으로 저장되었습니다!")  # 저장 완료를 알립니다.