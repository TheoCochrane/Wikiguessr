import json
import random
import requests
import uuid
import re  # <--- THIS LINE WAS MISSING!
from flask import Flask, jsonify, render_template, redirect, url_for, request

app = Flask(__name__)

# --- Load the pre-generated locations list ---
try:
    with open('locations.json', 'r') as f:
        LOCATIONS = json.load(f)
    print(f"Successfully loaded {len(LOCATIONS)} locations.")
except FileNotFoundError:
    print("Error: locations.json not found! Using a single fallback location.")
    LOCATIONS = [{"lat": 34.0522, "lng": -118.2437}]

# --- In-Memory Database ---
GAMES = {}

# --- Helper Functions ---
def generate_random_land_location():
    random_location = random.choice(LOCATIONS)
    return random_location['lat'], random_location['lng']

def get_closest_wikipedia_article(lat, lon):
    session = requests.Session()
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query", "list": "geosearch", "gscoord": f"{lat}|{lon}",
        "gsradius": 10000, "gslimit": 1, "format": "json"
    }
    try:
        response = session.get(url=api_url, params=params)
        data = response.json()
        if data['query']['geosearch']:
            return data['query']['geosearch'][0]['title']
    except Exception:
        pass
    return None

def get_first_sentence(title):
    session = requests.Session()
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query", "prop": "extracts", "exintro": True, "explaintext": True,
        "titles": title, "format": "json"
    }
    try:
        response = session.get(url=api_url, params=params)
        data = response.json()
        page_id = list(data['query']['pages'].keys())[0]
        extract = data['query']['pages'][page_id].get('extract', '')
        if extract:
            return extract.split('. ')[0] + '.'
    except Exception:
        pass
    return "Could not retrieve the first sentence for this location."

# --- Game Logic Route ---
def create_new_challenge():
    """
    Creates a new challenge, redacting the main title AND any other
    capitalized proper nouns to make the clue more challenging.
    """
    while True:
        lat, lon = generate_random_land_location()
        title = get_closest_wikipedia_article(lat, lon)
        if title:
            sentence = get_first_sentence(title)
            
            placeholder = "This location"
            redacted_sentence = re.sub(re.escape(title), placeholder, sentence, flags=re.IGNORECASE)
            
            if ',' in title:
                first_part = title.split(',')[0].strip()
                redacted_sentence = re.sub(re.escape(first_part), placeholder, redacted_sentence, flags=re.IGNORECASE)

            words = redacted_sentence.split()
            if not words: 
                continue

            final_words = [words[0]]
            
            for word in words[1:]:
                if len(word) > 1 and word[0].isupper():
                    clean_word = word.strip('.,;?!')
                    punctuation = word[len(clean_word):]
                    final_words.append("[...]" + punctuation)
                else:
                    final_words.append(word)

            final_sentence = " ".join(final_words)

            if "may refer to" not in final_sentence and "is a list of" not in final_sentence:
                return {"sentence": final_sentence, "location": {"lat": lat, "lng": lon}}

# --- All other routes remain exactly the same ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create-game')
def create_game():
    game_id = str(uuid.uuid4())[:8]
    new_game = {"rounds": [create_new_challenge() for _ in range(5)], "scores": []}
    GAMES[game_id] = new_game
    print(f"Created new game with ID: {game_id}")
    return redirect(url_for('play_game', game_id=game_id))

@app.route('/play/<game_id>')
def play_game(game_id):
    if game_id not in GAMES:
        return "Game not found!", 404
    return render_template('play.html', game_id=game_id)

@app.route('/results/<game_id>')
def show_results(game_id):
    if game_id not in GAMES:
        return "Game not found!", 404
    game_data = GAMES[game_id]
    sorted_scores = sorted(game_data['scores'], key=lambda x: x['score'], reverse=True)
    return render_template('results.html', game_id=game_id, scores=sorted_scores)

@app.route('/api/get-game-data/<game_id>')
def get_game_data(game_id):
    if game_id not in GAMES:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(GAMES[game_id]['rounds'])

@app.route('/api/submit-score/<game_id>', methods=['POST'])
def submit_score(game_id):
    if game_id not in GAMES:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json()
    player_name = data.get('name', 'Anonymous')
    player_score = data.get('score', 0)
    GAMES[game_id]['scores'].append({"name": player_name, "score": player_score})
    print(f"Score submitted for game {game_id}: {player_name} - {player_score}")
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)
