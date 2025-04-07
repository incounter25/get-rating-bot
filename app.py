from flask import Flask, request, jsonify
import requests
from googletrans import Translator

app = Flask(__name__)


RAWG_API_KEY = 


translator = Translator()


def translate_to_english(text):
    result = translator.translate(text, src='ko', dest='en')
    return result.text


def get_game_review(game_name):
    translated_name = translate_to_english(game_name)
    print(f"번역된 이름: {translated_name}")

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
        return f"{game_name}에 대한 정보가 없습니다"


@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName")
    print("들어온 인텐트:", intent)

    if intent == "serchgamerating":
        full_query = req.get("queryResult", {}).get("queryText", "").strip()
        print("사용자 입력:", full_query)

        # 조건 1: "[게임명]의" 로 시작하는 경우
        if "의" in full_query:
            game_name = full_query.split("의", 1)[0].strip()
            response_text = get_game_review(game_name)

        # 조건 2: "[게임명] 평점 알려줘" 형태
        elif "평점" in full_query and full_query.index("평점") > 0:
            game_name = full_query.split("평점")[0].strip()
            response_text = get_game_review(game_name)

        # 조건 3: 인식 실패
        else:
            response_text = "게임 이름을 가장 앞에 써서 '[게임이름]의 평점 알려줘'처럼 질문해주세요"

        return jsonify({
            "fulfillmentText": response_text
        })

    return jsonify({
        "fulfillmentText": "알 수 없는 요청입니다."
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
