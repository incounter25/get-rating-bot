from flask import Flask, request, jsonify
import requests
import random
from googletrans import Translator
import os

#flask 앱 인스턴스 생성
app = Flask(__name__)
#rawg api키 
RAWG_API_KEY = "75edf1b452c140aca6020bf4ed3c4799"
#구글 번역용
translator = Translator()

#---------------------------------------------------
#한글을 영어로 번역하는 함수
#---------------------------------------------------
def translate_to_english(text):
    result = translator.translate(text, src='ko', dest='en')
    return result.text


#---------------------------------------------------
#게임이름 받고 rawg 에 검색하는
#---------------------------------------------------
def get_game_review(game_name):
    translated_name = translate_to_english(game_name)
    print(f" 번역된 이름: {translated_name}")

    url = "https://api.rawg.io/api/games"
    params = {
        "search": translated_name,
        "key": RAWG_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("results"):
        game = data["results"][0] #첫번째 결과 사용
        name = game.get("name", translated_name)
        rating = game.get("rating", "정보 없음")
        released = game.get("released", "출시일 미정")
        genres = ", ".join([g["name"] for g in game.get("genres", [])])

        return f"{name}은 {released}에 출시된 {genres} 장르의 게임입니다. 평점은 {rating}점이에요."
    else:
        return f"{game_name}에 대한 정보를 찾을 수 없어요 "


#---------------------------------------------------
#장르 추천시 랜덤하게 3개 추천해주는 코드
#---------------------------------------------------
def get_genre_recommendations(genre_ko):
    translated = translate_to_english(genre_ko)
    print(f"🌐 번역된 장르: {translated}")

    url = "https://api.rawg.io/api/games"
    params = {
        "genres": translated.lower(),
        "page_size": 10,   #10개 받아서 랜덤 추출
        "key": RAWG_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("results"):
        games = data["results"]
        sampled = random.sample(games, min(3, len(games))) #3개 선택
        titles = [game["name"] for game in sampled]

        return f"{genre_ko} 장르의 추천 게임은 다음과 같아요: {', '.join(titles)}"
    else:
        return f"{genre_ko} 장르에 대한 추천 정보를 찾지 못했어요 "

#---------------------------------------------------
#dialogflow fulfillment 웹훅 엔드포인트
#---------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName")
    print(" 인텐트:", intent)
    #intent에서 serchgamerating 일 경우에 처리
    if intent == "serchgamerating":
        full_query = req.get("queryResult", {}).get("queryText", "").strip()
        print("사용자 입력:", full_query)
        #형태:"[게임명]의 평점 알려줘" 의 구조
        if "의" in full_query:
            game_name = full_query.split("의", 1)[0].strip()
            response_text = get_game_review(game_name)

        #형태2:"[게임명] 평점 알려줘" 의 구조
        elif "평점" in full_query and full_query.index("평점") > 0:
            game_name = full_query.split("평점")[0].strip()
            response_text = get_game_review(game_name)

       #형태3:장르 추천시 구조
        elif "추천" in full_query:

            #장르 후보 리스트
            genre_candidates = ["액션", "전략", "롤플레잉", "슈팅", "퍼즐", "레이싱", "스포츠", "시뮬레이션", "인디", "어드벤처"]
            found_genre = next((g for g in genre_candidates if g in full_query), None)
            
            
            if found_genre:
                response_text = get_genre_recommendations(found_genre)
            else:
                response_text = "어떤 장르를 추천받고 싶은지 말씀해주세요! 예: 액션, 전략, 롤플레잉 등"

        #전부 아닐ㄸ 
        else:
            response_text = "게임 이름을 가장 앞에 써서 '[게임이름]의 평점 알려줘'처럼 질문해주세요 "

        return jsonify({
            "fulfillmentText": response_text
        })
    #등록 x intent의 경우
    return jsonify({
        "fulfillmentText": "알 수 없는 요청입니다."
    })


#---------------------------------------------------
#앱 실행 (render를 사용하기 위한 추가함수)
#---------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
