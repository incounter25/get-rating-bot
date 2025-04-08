from flask import Flask, request, jsonify
import requests
import random
from googletrans import Translator
import os


app = Flask(__name__)
RAWG_API_KEY = "75edf1b452c140aca6020bf4ed3c4799"

translator = Translator()


def translate_to_english(text):
    result = translator.translate(text, src='ko', dest='en')
    return result.text


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
        game = data["results"][0]
        name = game.get("name", translated_name)
        rating = game.get("rating", "정보 없음")
        released = game.get("released", "출시일 미정")
        genres = ", ".join([g["name"] for g in game.get("genres", [])])

        return f"{name}은 {released}에 출시된 {genres} 장르의 게임입니다. 평점은 {rating}점이에요."
    else:
        return f"{game_name}에 대한 정보를 찾을 수 없어요 "


def get_genre_recommendations(genre_ko):
    translated = translate_to_english(genre_ko)
    print(f"🌐 번역된 장르: {translated}")

    url = "https://api.rawg.io/api/games"
    params = {
        "genres": translated.lower(),
        "page_size": 10,
        "key": RAWG_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("results"):
        games = data["results"]
        sampled = random.sample(games, min(3, len(games)))
        titles = [game["name"] for game in sampled]

        return f"{genre_ko} 장르의 추천 게임은 다음과 같아요: {', '.join(titles)}"
    else:
        return f"{genre_ko} 장르에 대한 추천 정보를 찾지 못했어요 "

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName")
    print(" 인텐트:", intent)

    if intent == "serchgamerating":
        full_query = req.get("queryResult", {}).get("queryText", "").strip()
        print("사용자 입력:", full_query)

        if "의" in full_query:
            game_name = full_query.split("의", 1)[0].strip()
            response_text = get_game_review(game_name)

        
        elif "평점" in full_query and full_query.index("평점") > 0:
            game_name = full_query.split("평점")[0].strip()
            response_text = get_game_review(game_name)

       
        elif "추천" in full_query:
            genre_candidates = ["액션", "전략", "롤플레잉", "슈팅", "퍼즐", "레이싱", "스포츠", "시뮬레이션", "인디", "어드벤처"]
            found_genre = next((g for g in genre_candidates if g in full_query), None)
            if found_genre:
                response_text = get_genre_recommendations(found_genre)
            else:
                response_text = "어떤 장르를 추천받고 싶은지 말씀해주세요! 예: 액션, 전략, 롤플레잉 등"

        
        else:
            response_text = "게임 이름을 가장 앞에 써서 '[게임이름]의 평점 알려줘'처럼 질문해주세요 "

        return jsonify({
            "fulfillmentText": response_text
        })

    return jsonify({
        "fulfillmentText": "알 수 없는 요청입니다."
    })
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
