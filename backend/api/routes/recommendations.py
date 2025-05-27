from flask import Blueprint, jsonify
from neo4j_driver import get_driver

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommendations/top3/<correo>', methods=['GET'])
def get_recommendations(correo):
    with get_driver().session() as session:
        # 1. Obtener juegos relacionados al usuario y sus pesos
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

        if not user_games:
            return jsonify({"error": "Usuario no tiene juegos relacionados"}), 404

        # 2. Calcular el peso máximo posible
        num_user_games = len(user_games)
        max_user_game_weight = 5  # FAVORITE
        max_game_relation_weight = 5  # Por característica
        num_characteristics = 6  # SIMILAR_GENRE, SIMILAR_PLATFORM, SAME_COMPANY, SAME_MULTIPLAYER, SAME_DURATION, SAME_SCORE
        max_total = (num_user_games * max_user_game_weight) + (num_user_games * num_characteristics * max_game_relation_weight)

        # 3. Obtener juegos no relacionados con el usuario
        unrelated_games_query = """
        MATCH (g:Game)
        WHERE NOT EXISTS((:User {correo: $correo})-[:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g))
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

        # 4. Calcular el puntaje para cada juego no relacionado
        recommendations = []
        for game in unrelated_games:
            total_weight = 0

            # a) Sumar pesos de relaciones entre juegos del usuario y el juego candidato
            for user_game in user_games:
                rel_query = """
                MATCH (g1:Game {name: $user_game}), (g2:Game {name: $candidate})
                OPTIONAL MATCH (g1)-[r:SIMILAR_GENRE|SIMILAR_PLATFORM|SAME_COMPANY|SAME_MULTIPLAYER|SAME_DURATION|SAME_SCORE]-(g2)
                RETURN COALESCE(sum(r.weight), 0) AS rel_weight
                """
                rel_result = session.run(rel_query, {"user_game": user_game["name"], "candidate": game["name"]})
                rel_weight = rel_result.single()["rel_weight"]
                total_weight += rel_weight

                # b) Sumar el peso de la relación usuario-juego si hay conexión
                if rel_weight > 0:
                    total_weight += user_game["weight"]

            normalized_score = total_weight / max_total if max_total > 0 else 0

            # Crear relación RECOMMENDED si el puntaje es mayor a un umbral (0.05)
            if normalized_score > 0.05:
                session.run("""
                MATCH (u:User {correo: $correo}), (g:Game {name: $name})
                MERGE (u)-[r:RECOMMENDED]->(g)
                ON CREATE SET r.weight = $peso
                ON MATCH SET r.weight = $peso
                """, {"correo": correo, "name": game["name"], "peso": normalized_score})

            recommendations.append({
                "name": game["name"],
                "score": game["score"],
                "genres": game["genres"],
                "platforms": game["platforms"],
                "normalized_score": normalized_score
            })

        # 5. Ordenar y devolver los 3 mejores
        recommendations.sort(key=lambda x: x["normalized_score"], reverse=True)
        return jsonify(recommendations[:3]), 200