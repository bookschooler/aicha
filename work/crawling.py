import requests # requests라는 이름의 인터넷 통신 도구를 가져와!
import pandas as pd # pandas라는 이름의 데이터 표 관리 도구를 가져오고, 앞으로 pd라고 부를게!
import time # time이라는 이름의 시간 관리 도구를 가져와!

REST_API_KEY = "여기에_본인의_카카오_REST_API_키를_입력하세요" # REST_API_KEY라는 이름의 공간에 "여기에~"라는 글자를 저장해!
headers = {"Authorization": f"KakaoAK {REST_API_KEY}"} # headers라는 공간에 카카오 서버 문지기에게 보여줄 신분증(사전 형태)을 만들어서 저장해!

locations = ["종로", "안국역", "익선동"] # locations라는 이름의 공간에 3개의 지역 이름이 담긴 리스트(바구니)를 만들어!
tea_keywords = ["찻집", "티룸", "티하우스", "티카페"] # tea_keywords라는 공간에 4개의 찻집 종류가 담긴 리스트를 만들어!
result_list = [] # result_list라는 이름의 텅 빈 바구니를 준비해!

for loc in locations: # locations 바구니에서 지역을 하나씩 꺼내서 loc라고 부르면서 아래 들여쓰기 된 코드를 반복해!
    for keyword in tea_keywords: # tea_keywords 바구니에서 찻집 종류를 하나씩 꺼내서 keyword라고 부르면서 아래를 반복해!
        query = f"{loc} {keyword}" # query라는 공간에 지역(loc)과 찻집 종류(keyword)를 띄어쓰기로 합친 진짜 검색어 글자를 만들어!
        print(f"🔍 검색 진행 중: {query}") # 화면에 돋보기 이모티콘과 함께 현재 만들고 있는 검색어를 출력해서 보여줘!
        
        url = "https://dapi.kakao.com/v2/local/search/keyword.json" # url이라는 공간에 카카오맵 검색소의 정확한 인터넷 주소를 저장해!
        params = {"query": query} # params라는 공간에 카카오 서버에 물어볼 구체적인 검색어 조건(사전 형태)을 묶어둬!
        
        response = requests.get(url, headers=headers, params=params) # requests 도구를 써서 url 주소로 신분증(headers)과 조건(params)을 챙겨서 데이터를 달라고 요청(get)한 뒤, 그 대답을 response에 저장해!
        data = response.json() # 서버가 준 대답(response)을 파이썬이 읽기 편한 사전 형태(json)로 번역해서 data에 저장해!
        
        if 'documents' in data: # 만약 data 안에 'documents'(가게 목록)라는 이름의 데이터가 무사히 들어있다면!
            for place in data['documents']: # data의 'documents' 목록 안에서 가게를 하나씩 꺼내서 place라고 부르면서 아래를 반복해!
                shop_info = { # shop_info라는 공간에 아래 6개의 정보를 이름표(키)와 값으로 묶어서 하나의 사전으로 만들어!
                    "검색어": query, # "검색어"라는 이름표에 우리가 아까 만든 검색어 글자를 달아!
                    "가게명": place.get("place_name", ""), # "가게명" 이름표에 place에서 가져온 가게 이름을 달고, 만약 없으면 빈칸("")을 줘!
                    "지번주소": place.get("address_name", ""), # "지번주소" 이름표에 지번 주소를 달아!
                    "도로명주소": place.get("road_address_name", ""), # "도로명주소" 이름표에 도로명 주소를 달아!
                    "X좌표": place.get("x", ""), # "X좌표" 이름표에 경도(가로 위치) 숫자를 달아!
                    "Y좌표": place.get("y", "") # "Y좌표" 이름표에 위도(세로 위치) 숫자를 달아!
                } # (가게 정보 사전 만들기 끝)
                result_list.append(shop_info) # 아까 만들어둔 텅 빈 바구니(result_list)에 방금 묶은 가게 정보(shop_info)를 쏙 집어넣어!
        
        time.sleep(0.5) # 카카오 서버가 우리 때문에 힘들지 않게 0.5초 동안 잠깐 잠을 자면서(sleep) 쉬어!

df_result = pd.DataFrame(result_list) # pd 도구의 DataFrame 기능을 써서 결과 바구니(result_list)에 든 데이터를 예쁜 엑셀 표 형태로 만들고 df_result에 덮어씌워!
df_result = df_result.drop_duplicates(subset=["도로명주소"], keep="first") # df_result 표에서 "도로명주소"가 똑같은 줄이 발견되면 첫 번째 줄만 살리고(keep="first") 나머지는 다 지운(drop_duplicates) 다음 다시 저장해!

print(df_result.head()) # 표의 맨 위 5줄만(head) 화면에 출력해서 어떻게 생겼는지 보여줘!
df_result.to_csv("test_jongno_tea_shops.csv", index=False, encoding="utf-8-sig") # 완성된 표를 "test_jongno_tea_shops.csv"라는 파일로 저장하는데, 맨 앞에 숫자 번호표(index)는 떼고, 한글이 절대 안 깨지게(utf-8-sig) 해!
print("💾 테스트 크롤링 완료! 파일이 성공적으로 저장되었습니다.") # 모든 작업이 끝났다는 안내 메시지를 화면에 출력해!