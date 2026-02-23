#y + income + 3개 pop 파일 합치기
import pandas as pd  # 파이썬아, 판다스 도구를 가져와서 pd라는 짧은 이름으로 쓸게.

# 1. 뼈대가 될 기준 파일 불러오기
print("📂 기준 파일(merged_y_income.csv)을 불러옵니다...")  # 화면에 진행 상황을 출력해.
try:  # 일단 utf-8 인코딩으로 파일 읽기를 시도해 봐.
    df_master = pd.read_csv('merged_y_income.csv', encoding='utf-8')  # 파일을 읽어서 df_master라는 변수에 저장해.
except:  # 만약 에러가 나면,
    df_master = pd.read_csv('merged_y_income.csv', encoding='cp949')  # 윈도우용 한글 인코딩(cp949)으로 다시 읽어와.

original_row_count = len(df_master)  # 나중에 비교하기 위해 합치기 전의 원래 행(줄) 개수를 저장해 둬.
keys = ['기준_년분기_코드', '상권_코드']  # 표들을 서로 연결할 때 쓸 공통 열쇠 2개를 리스트로 묶어둬.

# 2. 합칠 파일들 명단 만들기
files_to_merge = ['floating_pop.csv', 'living_pop.csv', 'working_pop.csv']  # 우리가 추가로 갖다 붙일 파일 이름 3개를 리스트로 만들어.

# 3. 반복문을 돌면서 하나씩 합치기
for file in files_to_merge:  # 명단에 있는 파일 이름을 하나씩 꺼내서 file이라는 변수에 넣고 아래 작업을 반복해.
    print(f"🔄 '{file}' 데이터를 합치는 중...")  # 지금 어떤 파일을 작업하고 있는지 화면에 알려줘.
    
    try:  # 파일 읽기를 시도해.
        df_right = pd.read_csv(file, encoding='utf-8')  # 지금 꺼낸 파일을 utf-8로 읽어서 df_right에 저장해.
    except:  # 에러가 나면,
        df_right = pd.read_csv(file, encoding='cp949')  # cp949 인코딩으로 다시 읽어.
        
    # 중복 열쇠 제거 (행 뻥튀기 방어!)
    df_right_clean = df_right.drop_duplicates(subset=keys, keep='first')  # df_right에서 열쇠가 똑같은 줄이 있으면 첫 번째만 남기고 다 지워버려.

    # 이미 df_master에 있는 열(키 제외)은 제거 (중복 열 방어!)
    existing_cols = set(df_master.columns) - set(keys)
    cols_to_drop = [c for c in df_right_clean.columns if c in existing_cols]
    df_right_clean = df_right_clean.drop(columns=cols_to_drop)

    # LEFT JOIN 병합
    df_master = pd.merge(left=df_master, right=df_right_clean, on=keys, how='left')  # df_master를 왼쪽에, 방금 정리한 표를 오른쪽에 두고 열쇠 기준으로 합친 다음, 다시 df_master에 덮어씌워.

# 4. 최종 결과 확인 및 저장
print("\n=== 🏁 마스터 병합 완료 ===")  # 결과 확인창 제목을 띄워.
print(f"✅ 원본 행 개수: {original_row_count}개")  # 처음에 저장해둔 원래 줄 개수를 보여줘.
print(f"✅ 최종 행 개수: {len(df_master)}개")  # 다 합치고 난 후의 줄 개수를 보여줘.

if original_row_count == len(df_master):  # 원래 개수랑 최종 개수가 똑같으면,
    print("🎉 완벽해! 행 개수가 하나도 뻥튀기되지 않았어.")  # 칭찬 메시지를 출력해.
else:  # 다르면,
    print("⚠️ 앗! 행 개수가 달라졌어. 데이터를 확인해 봐야 해.")  # 경고 메시지를 띄워.

output_filename = 'y_pop_income.csv'  # 최종적으로 저장할 파일 이름을 정해.
df_master.to_csv(output_filename, index=False, encoding='utf-8-sig')  # 완성된 표를 엑셀에서 한글이 안 깨지게 저장해.
print(f"💾 '{output_filename}' 파일이 성공적으로 저장되었어!")  # 저장 끝났다고 알려줘.