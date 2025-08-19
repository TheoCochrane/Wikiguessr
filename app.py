import geopandas
import random
import requests
import uuid
from shapely.geometry import Point
from flask import Flask, jsonify, render_template, redirect, url_for, request

app = Flask(__name__)

# --- In-Memory Database ---
# This will store all active games. It will be cleared if the server restarts.
GAMES = {}

# --- Load Shapefile ---
try
    world = geopandas.read_file(zipne_110m_land.zip)
    land_polygons = world.geometry.unary_union
    print(Successfully loaded land shapefile.)
except Exception as e
    print(fError loading shapefile {e})
    print(Please ensure 'ne_110m_land.zip' is in the project directory.)
    land_polygons = None

# --- Helper Functions for Game Logic ---
def generate_random_land_location()
    if not land_polygons return 34.0522, -118.2437 
    while True
        lon, lat = random.uniform(-180, 180), random.uniform(-90, 90)
        if land_polygons.contains(Point(lon, lat))
            return lat, lon

def get_closest_wikipedia_article(lat, lon)
    session = requests.Session()
    api_url = httpsen.wikipedia.orgwapi.php
    params = {
        action query,
        list geosearch,
        gscoord f{lat}{lon},
        gsradius 10000,
        gslimit 1,
        format json
    }
    try
        response = session.get(url=api_url, params=params)
        data = response.json()
        if data['query']['geosearch']
            return data['query']['geosearch'][0]['title']
    except Exception
        pass
    return None

def get_first_sentence(title)
    session = requests.Session()
    api_url = httpsen.wikipedia.orgwapi.php
    params = {
        action query,
        prop extracts,
        exintro True,
        explaintext True,
        titles title,
        format json
    }
    try
        response = session.get(url=api_url, params=params)
        data = response.json()
        page_id = list(data['query']['pages'].keys())[0]
        extract = data['query']['pages'][page_id].get('extract', '')
        if extract
            # Return only the first sentence
            return extract.split('. ')[0] + '.'
    except Exception
        pass
    return Could not retrieve the first sentence for this location.

# --- Game Logic Route ---
def create_new_challenge()
    Generates a single, valid challenge by retrying until a good article is found.
    while True
        lat, lon = generate_random_land_location()
        title = get_closest_wikipedia_article(lat, lon)
        if title
            sentence = get_first_sentence(title)
            # Filter out disambiguation or list pages for a better experience
            if may refer to not in sentence and is a list of not in sentence
                return {sentence sentence, location {lat lat, lng lon}}

# --- Page Routes ---
@app.route('')
def home()
    Serves the homepage where users can start a new game.
    return render_template('home.html')

@app.route('create-game')
def create_game()
    Creates a new 5-round game, stores it, and redirects the player.
    game_id = str(uuid.uuid4())[8] # Generate a short, unique game ID
    new_game = {
        rounds [create_new_challenge() for _ in range(5)],
        scores []
    }
    GAMES[game_id] = new_game
    print(fCreated new game with ID {game_id})
    return redirect(url_for('play_game', game_id=game_id))

@app.route('playgame_id')
def play_game(game_id)
    Serves the main game page for a specific game ID.
    if game_id not in GAMES
        return Game not found!, 404
    return render_template('play.html', game_id=game_id)

@app.route('resultsgame_id')
def show_results(game_id)
    Displays the leaderboard for a completed game.
    if game_id not in GAMES
        return Game not found!, 404
    
    game_data = GAMES[game_id]
    # Sort scores from highest to lowest for the leaderboard
    sorted_scores = sorted(game_data['scores'], key=lambda x x['score'], reverse=True)
    
    return render_template('results.html', game_id=game_id, scores=sorted_scores)

# --- API Endpoints ---
@app.route('apiget-game-datagame_id')
def get_game_data(game_id)
    API endpoint for the frontend to fetch the rounds for a specific game.
    if game_id not in GAMES
        return jsonify({error Game not found}), 404
    # Return only the rounds data, not the scores
    return jsonify(GAMES[game_id]['rounds'])

@app.route('apisubmit-scoregame_id', methods=['POST'])
def submit_score(game_id)
    API endpoint for players to submit their final score.
    if game_id not in GAMES
        return jsonify({error Game not found}), 404
    
    data = request.get_json()
    player_name = data.get('name', 'Anonymous')
    player_score = data.get('score', 0)
    
    GAMES[game_id]['scores'].append({name player_name, score player_score})
    print(fScore submitted for game {game_id} {player_name} - {player_score})
    return jsonify({success True})

if __name__ == '__main__'
    # This part is for local testing only. Render will use Gunicorn instead.
    app.run(debug=True)