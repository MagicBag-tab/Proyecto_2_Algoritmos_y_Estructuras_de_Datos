from flask import Blueprint, request, jsonify
from neo4j_driver import get_driver
from urllib.parse import unquote
import json

preferences_bp = Blueprint('preferences', __name__)

# Helper function to update users.json
def update_users_json(correo, game_name, preference_type):
    try:
        with open('users.json', 'r', encoding='utf-8') as file:
            users = json.load(file)
    except FileNotFoundError:
        print("Error: users.json not found.")
        return False
    except json.JSONDecodeError:
        print("Error: users.json has invalid format.")
        return False

    user_found = False
    for user in users:
        if user["correo"] == correo:
            user_found = True
            # Map preference type to the corresponding list
            preference_map = {
                'FAVORITE': 'juegos_favoritos',
                'INTERESTED': 'juegos_interesados',
                'NO_GUSTADOS': 'juegos_no_gustados',
                'PLAYED': 'juegos_jugados'
            }
            list_name = preference_map.get(preference_type)
            if not list_name:
                print(f"Invalid preference type: {preference_type}")
                return False

            # Avoid duplicates and remove from other lists
            if game_name not in user[list_name]:
                user[list_name].append(game_name)
                # Remove the game from other lists to avoid conflicts
                for other_list in preference_map.values():
                    if other_list != list_name and game_name in user[other_list]:
                        user[other_list].remove(game_name)
            else:
                print(f"Game {game_name} already in {list_name} for {correo}")
                return True

    if not user_found:
        print(f"User {correo} not found in users.json.")
        return False

    try:
        with open('users.json', 'w', encoding='utf-8') as file:
            json.dump(users, file, indent=2, ensure_ascii=False)
        print(f"users.json updated for {correo} with {game_name} in {preference_type}.")
        return True
    except Exception as e:
        print(f"Error writing to users.json: {str(e)}")
        return False

@preferences_bp.route('/users/<correo>/suggest_games', methods=['POST'])
def suggest_games(correo):
    correo = unquote(correo)
    data = request.get_json()
    print(f"Received suggest_games data: {data}, correo: {correo}")

    # Validate input
    if not data or not isinstance(data.get("generos_favoritos", []), list) or \
       not isinstance(data.get("plataformas_favoritas", []), list) or \
       "prefiere_multijugador" not in data:
        return jsonify({"error": "Invalid preferences data"}), 400

    generos = data.get("generos_favoritos", [])
    plataformas = data.get("plataformas_favoritas", [])
    prefiere_multijugador = data.get("prefiere_multijugador", False)

    # Query to find games matching preferences
    query = """
    MATCH (g:Game)
    WHERE 
        (size($generos) = 0 OR ANY(genre IN g.genres WHERE genre IN $generos))
        AND (size($plataformas) = 0 OR ANY(platform IN g.platforms WHERE platform IN $plataformas))
        AND ($prefiere_multijugador IS NULL OR g.multiplayer = $prefiere_multijugador)
        AND NOT EXISTS((:User {correo: $correo})-[:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g))
    RETURN g.name AS name, g.genres AS genres, g.platforms AS platforms, g.multiplayer AS multiplayer, g.score AS score
    ORDER BY g.score DESC
    LIMIT 10
    """
    with get_driver().session() as session:
        result = session.run(query, {
            "correo": correo,
            "generos": generos,
            "plataformas": plataformas,
            "prefiere_multijugador": prefiere_multijugador
        })
        games = [
            {
                "name": record["name"],
                "genres": record["genres"],
                "platforms": record["platforms"],
                "multiplayer": record["multiplayer"],
                "score": record["score"]
            } for record in result
        ]

        if not games:
            return jsonify({"message": "No games found matching the preferences"}), 200

        return jsonify(games), 200

@preferences_bp.route('/users/<correo>/game_preference', methods=['POST'])
def set_game_preference(correo):
    correo = unquote(correo)
    data = request.get_json()
    print(f"Received game_preference data: {data}, correo: {correo}")

    # Validate input
    if not data or not data.get("game_name") or not data.get("preference_type"):
        return jsonify({"error": "game_name and preference_type are required"}), 400

    game_name = data["game_name"]
    preference_type = data["preference_type"].upper()
    if preference_type not in ['FAVORITE', 'INTERESTED', 'NO_GUSTADOS', 'PLAYED']:
        return jsonify({"error": "preference_type must be FAVORITE, INTERESTED, NO_GUSTADOS, or PLAYED"}), 400

    # Map preference type to weight
    weight_map = {
        'FAVORITE': 5,
        'INTERESTED': 2,
        'NO_GUSTADOS': -5,
        'PLAYED': 0
    }
    weight = weight_map[preference_type]

    with get_driver().session() as session:
        # Check if the game exists
        result = session.run("MATCH (g:Game {name: $name}) RETURN g", {"name": game_name})
        if not result.single():
            return jsonify({"error": f"Game {game_name} not found"}), 404

        # Check if the user exists
        result = session.run("MATCH (u:User {correo: $correo}) RETURN u", {"correo": correo})
        if not result.single():
            return jsonify({"error": f"User {correo} not found"}), 404

        # Remove any existing relationship with this game
        session.run("""
            MATCH (u:User {correo: $correo})-[r:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g:Game {name: $game_name})
            DELETE r
        """, {"correo": correo, "game_name": game_name})

        # Create the new relationship
        session.run("""
            MATCH (u:User {correo: $correo}), (g:Game {name: $game_name})
            MERGE (u)-[r:%s]->(g)
            ON CREATE SET r.weight = $weight
        """ % preference_type, {
            "correo": correo,
            "game_name": game_name,
            "weight": weight
        })

        # Update users.json
        if update_users_json(correo, game_name, preference_type):
            return jsonify({"message": f"Preference {preference_type} for {game_name} updated"}), 200
        else:
            return jsonify({"message": f"Preference {preference_type} for {game_name} updated in database, but failed to update users.json"}), 200