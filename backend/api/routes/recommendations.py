from flask import Blueprint, request, jsonify
from neo4j_driver import get_driver

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    correo = request.args.get('correo')
    if not correo:
        return jsonify({"error": "Correo requerido"}), 400

    with get_driver().session() as session:
        # 1. Juegos relacionados al usuario y sus pesos
        user_games_query = """
        MATCH (u:User {correo: $correo})-[rel:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g:Game)
        RETURN g.name AS name, type(rel) AS rel_type, rel.weight AS weight
        """
        user_games = []
        for record in session.run(user_games_query, {"correo": correo}):
            user_games.append({
                "name": record["name"],
                "rel_type": record["rel_type"],
                "weight": record["weight"]
            })

        # 2. Amigos del usuario
        friends_query = """
        MATCH (u:User {correo: $correo})-[:FRIEND]->(f:User)
        RETURN f.correo AS correo
        """
        friends = []
        for record in session.run(friends_query, {"correo": correo}):
            friends.append(record["correo"])
        num_friends = len(friends)

        # 3. Juegos relacionados a los amigos y sus pesos
        friends_games = []
        for friend in friends:
            friend_games_query = """
            MATCH (u:User {correo: $correo})-[rel:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g:Game)
            RETURN g.name AS name, type(rel) AS rel_type, rel.weight AS weight
            """
            for record in session.run(friend_games_query, {"correo": friend}):
                friends_games.append({
                    "friend": friend,
                    "name": record["name"],
                    "rel_type": record["rel_type"],
                    "weight": record["weight"]
                })

        # 4. Calcular el peso máximo posible
        num_user_games = len(user_games)
        max_user_game_weight = 5  # FAVORITE
        max_game_relation_weight = 5  # Por característica
        num_characteristics = 6
        max_total_user = (num_user_games * max_user_game_weight) + (num_user_games * num_characteristics * max_game_relation_weight)
        max_total_friends = num_friends + sum([
            5 * len([g for g in friends_games if g["friend"] == friend])
            for friend in friends
        ])
        max_total = max_total_user + max_total_friends

        # 5. Obtener juegos no relacionados con el usuario
        unrelated_games_query = """
        MATCH (g:Game)
        WHERE NOT EXISTS( ( :User {correo: $correo} )-[:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g) )
        RETURN g.name AS name, g.score AS score, g.genres AS genres, g.platforms AS platforms
        """
        unrelated_games = []
        for record in session.run(unrelated_games_query, {"correo": correo}):
            unrelated_games.append({
                "name": record["name"],
                "score": record["score"],
                "genres": record["genres"],
                "platforms": record["platforms"]
            })

        # 6. Calcular el score para cada juego no relacionado
        recommendations = []
        for game in unrelated_games:
            total_weight = 0

            # a) Sumar pesos de relaciones entre juegos del usuario y el juego candidato
            for user_game in user_games:
                rel_query = """
                MATCH (g1:Game {name: $user_game}), (g2:Game {name: $candidate})
                OPTIONAL MATCH (g1)-[r]-(g2)
                RETURN sum(COALESCE(r.weight,0)) AS rel_weight
                """
                rel_result = session.run(rel_query, {"user_game": user_game["name"], "candidate": game["name"]})
                rel_weight = rel_result.single()["rel_weight"] or 0
                total_weight += rel_weight

                # b) Sumar el peso de la relación del usuario con el juego relacionado (si hay relación entre user_game y candidate)
                if rel_weight > 0:
                    total_weight += user_game["weight"]

            # c) Sumar pesos de los amigos y sus juegos
            for friend in friends:
                # Peso por ser amigo
                friend_weight = 1
                # ¿El amigo tiene relación directa con el juego candidato?
                friend_game_query = """
                MATCH (u:User {correo: $correo})-[rel:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g:Game {name: $game})
                RETURN rel.weight AS weight
                """
                rel_result = session.run(friend_game_query, {"correo": friend, "game": game["name"]})
                record = rel_result.single()
                if record and record["weight"]:
                    total_weight += record["weight"] + friend_weight

            recommendations.append({
                "name": game["name"],
                "score": game["score"],
                "genres": game["genres"],
                "platforms": game["platforms"],
                "normalized_score": total_weight / max_total if max_total > 0 else 0
            })

        # 7. Ordenar y devolver los 3 mejores
        recommendations.sort(key=lambda x: x["normalized_score"], reverse=True)
        return jsonify(recommendations[:3]), 200