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

        # 2. Obtener amigos y sus juegos
        friends_query = """
        MATCH (u:User {correo: $correo})-[:FRIEND]->(f:User)
        RETURN f.correo AS correo
        """
        friends = [record["correo"] for record in session.run(friends_query, {"correo": correo})]
        num_friends = len(friends)

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

        # 3. Calcular el peso máximo posible (usuario + amigos)
        num_user_games = len(user_games)
        max_user_game_weight = 10  # FAVORITE
        max_game_relation_weight = 10  # Por característica
        num_characteristics = 6  # SIMILAR_GENRE, SIMILAR_PLATFORM, SAME_COMPANY, SAME_MULTIPLAYER, SAME_DURATION, SAME_SCORE
        max_total = (num_user_games * max_user_game_weight * num_characteristics * max_game_relation_weight)

        # 4. Obtener juegos no relacionados con el usuario
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

        # 5. Calcular el score para cada juego no relacionado
        recommendations = []

        for game in unrelated_games:
            total_weight = 0
            debug_info = {"game": game["name"], "rel_weights": [], "friend_weights": []}

            # a) Sumar pesos de relaciones entre juegos del usuario y el juego candidato, multiplicados por el peso usuario-juego
            for user_game in user_games:
                rel_query = """
                MATCH (g1:Game {name: $user_game}), (g2:Game {name: $candidate})
                OPTIONAL MATCH (g1)-[r1:SIMILAR_GENRE]->(g2)
                WITH g1, g2, COALESCE(max(r1.weight), 0) AS genre_weight
                OPTIONAL MATCH (g1)-[r2:SIMILAR_PLATFORM]->(g2)
                WITH g1, g2, genre_weight, COALESCE(max(r2.weight), 0) AS platform_weight
                OPTIONAL MATCH (g1)-[r3:SAME_COMPANY]->(g2)
                WITH g1, g2, genre_weight, platform_weight, COALESCE(max(r3.weight), 0) AS company_weight
                OPTIONAL MATCH (g1)-[r4:SAME_MULTIPLAYER]->(g2)
                WITH g1, g2, genre_weight, platform_weight, company_weight, COALESCE(max(r4.weight), 0) AS multiplayer_weight
                OPTIONAL MATCH (g1)-[r5:SAME_DURATION]->(g2)
                WITH g1, g2, genre_weight, platform_weight, company_weight, multiplayer_weight, COALESCE(max(r5.weight), 0) AS duration_weight
                OPTIONAL MATCH (g1)-[r6:SAME_SCORE]->(g2)
                RETURN genre_weight, platform_weight, company_weight, multiplayer_weight, duration_weight, COALESCE(max(r6.weight), 0) AS score_weight
                """
                rel_result = session.run(rel_query, {"user_game": user_game["name"], "candidate": game["name"]})
                rel_record = rel_result.single()
                rel_weights = [
                    ("SIMILAR_GENRE", rel_record["genre_weight"]),
                    ("SIMILAR_PLATFORM", rel_record["platform_weight"]),
                    ("SAME_COMPANY", rel_record["company_weight"]),
                    ("SAME_MULTIPLAYER", rel_record["multiplayer_weight"]),
                    ("SAME_DURATION", rel_record["duration_weight"]),
                    ("SAME_SCORE", rel_record["score_weight"])
                ]
                rel_sum = sum(w for _, w in rel_weights)
                rel_weight_total = rel_sum * user_game["weight"]  # Multiplicación aquí
                total_weight += rel_weight_total
                debug_info["rel_weights"].append({
                    "user_game": user_game["name"],
                    "user_game_weight": user_game["weight"],
                    "relations": [
                        {"type": rel_type, "weight": float(weight)} for rel_type, weight in rel_weights
                    ],
                    "sum_relations": float(rel_sum),
                    "total_for_this_game": float(rel_weight_total)
                })

            # b) Sumar pesos de los amigos y sus juegos (solo relación directa)
            for friend in friends:
                friend_weight = 1
                friend_game_query = """
                MATCH (u:User {correo: $correo})-[rel:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g:Game {name: $game})
                RETURN rel.weight AS weight
                """
                rel_result = session.run(friend_game_query, {"correo": friend, "game": game["name"]})
                record = rel_result.single()
                if record and record["weight"]:
                    total_weight += record["weight"] + friend_weight
                    debug_info["friend_weights"].append((friend, record["weight"], friend_weight))

            normalized_score = total_weight / max_total if max_total > 0 else 0

            debug_info["total_weight"] = total_weight
            debug_info["max_total"] = max_total
            debug_info["normalized_score"] = normalized_score

            recommendations.append({
                "name": game["name"],
                "score": game["score"],
                "genres": game["genres"],
                "platforms": game["platforms"],
                "normalized_score": normalized_score
            })

        # 6. Ordenar y devolver los 3 mejores, y crear relación RECOMMENDED para esos 3
        recommendations.sort(key=lambda x: x["normalized_score"], reverse=True)
        top3 = recommendations[:3]

        for rec in top3:
            session.run("""
                MATCH (u:User {correo: $correo}), (g:Game {name: $name})
                MERGE (u)-[r:RECOMMENDED]->(g)
                ON CREATE SET r.weight = $peso
                ON MATCH SET r.weight = $peso
            """, {"correo": correo, "name": rec["name"], "peso": rec["normalized_score"]})

        # Devuelve solo el top3 y su debug
        return jsonify({"top3": top3}), 200