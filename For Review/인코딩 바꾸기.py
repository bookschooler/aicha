import pandas as pd

# 1. 원본 파일 읽기 (cp949로 읽어야 함!)
# 파일 이름은 쏘피가 다운로드 받은 그 파일명으로!
file_path = 'to_map.csv' 
df = pd.read_csv(file_path, encoding='cp949')

# 2. 깨끗한 UTF-8로 다시 저장하기 (이름을 바꿔서 저장하자)
# encoding='utf-8-sig'를 쓰면 엑셀에서도 한글 안 깨지고 잘 보여!
new_file_path = 'to_map_clean.csv'
df.to_csv(new_file_path, index=False, encoding='utf-8-sig')

print(f"변환 완료! '{new_file_path}' 파일을 열어보세요. 이제 한글이 잘 보일 거예요! ✨")