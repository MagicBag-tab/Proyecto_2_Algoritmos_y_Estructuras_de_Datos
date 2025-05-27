from flask import Blueprint, request, jsonify
from neo4j_driver import get_driver

videogames_bp = Blueprint('videogames', __name__)

@videogames_bp.route('/videogames', methods=['POST'])
def create_videogame():
    data = request.get_json()
    query = """
    CREATE (g:Game {
        name: $name,
        multiplayer: $multiplayer,
        genres: $genres,
        platforms: $platforms,
        score: $score,
        company: $company,
        hours_duration: $hours_duration
    })
    """
    with get_driver().session() as session:
        session.run(query, **data)

        # Relacionar con juegos similares
        relation_query = """
        MATCH (new:Game {name: $name}), (other:Game)
        WHERE new.name <> other.name

        FOREACH (_ IN CASE WHEN any(x IN new.genres WHERE x IN other.genres) THEN [1] ELSE [] END |
            MERGE (new)-[r:SIMILAR_GENRE]->(other)
            ON CREATE SET r.weight = 5
            MERGE (other)-[r2:SIMILAR_GENRE]->(new)
            ON CREATE SET r2.weight = 5
        )
        FOREACH (_ IN CASE WHEN any(x IN new.platforms WHERE x IN other.platforms) THEN [1] ELSE [] END |
            MERGE (new)-[r:SIMILAR_PLATFORM]->(other)
            ON CREATE SET r.weight = 5
            MERGE (other)-[r2:SIMILAR_PLATFORM]->(new)
            ON CREATE SET r2.weight = 5
        )
        FOREACH (_ IN CASE WHEN new.company = other.company THEN [1] ELSE [] END |
            MERGE (new)-[r:SAME_COMPANY]->(other)
            ON CREATE SET r.weight = 5
            MERGE (other)-[r2:SAME_COMPANY]->(new)
            ON CREATE SET r2.weight = 5
        )
        FOREACH (_ IN CASE WHEN new.multiplayer = other.multiplayer THEN [1] ELSE [] END |
            MERGE (new)-[r:SAME_MULTIPLAYER]->(other)
            ON CREATE SET r.weight = 5
            MERGE (other)-[r2:SAME_MULTIPLAYER]->(new)
            ON CREATE SET r2.weight = 5
        )
        FOREACH (_ IN CASE WHEN new.hours_duration = other.hours_duration THEN [1] ELSE [] END |
            MERGE (new)-[r:SAME_DURATION]->(other)
            ON CREATE SET r.weight =
                CASE
                    WHEN abs(new.hours_duration - other.hours_duration) <= 10 THEN 5
                    WHEN abs(new.hours_duration - other.hours_duration) <= 20 THEN 4
                    WHEN abs(new.hours_duration - other.hours_duration) <= 30 THEN 3
                    WHEN abs(new.hours_duration - other.hours_duration) <= 40 THEN 2
                    WHEN abs(new.hours_duration - other.hours_duration) <= 50 THEN 1
                    ELSE 0
                END
            MERGE (other)-[r2:SAME_DURATION]->(new)
            ON CREATE SET r2.weight =
                CASE
                    WHEN abs(new.hours_duration - other.hours_duration) <= 10 THEN 5
                    WHEN abs(new.hours_duration - other.hours_duration) <= 20 THEN 4
                    WHEN abs(new.hours_duration - other.hours_duration) <= 30 THEN 3
                    WHEN abs(new.hours_duration - other.hours_duration) <= 40 THEN 2
                    WHEN abs(new.hours_duration - other.hours_duration) <= 50 THEN 1
                    ELSE 0
                END
        )
        FOREACH (_ IN CASE WHEN new.score = other.score THEN [1] ELSE [] END |
            MERGE (new)-[r:SAME_SCORE]->(other)
            ON CREATE SET r.weight =
                CASE
                    WHEN abs(new.score - other.score) <= 0.1 THEN 5
                    WHEN abs(new.score - other.score) <= 0.2 THEN 4
                    WHEN abs(new.score - other.score) <= 0.3 THEN 3
                    WHEN abs(new.score - other.score) <= 0.4 THEN 2
                    WHEN abs(new.score - other.score) <= 0.5 THEN 1
                    ELSE 0
                END
            MERGE (other)-[r2:SAME_SCORE]->(new)
            ON CREATE SET r2.weight =
                CASE
                    WHEN abs(new.score - other.score) <= 0.1 THEN 5
                    WHEN abs(new.score - other.score) <= 0.2 THEN 4
                    WHEN abs(new.score - other.score) <= 0.3 THEN 3
                    WHEN abs(new.score - other.score) <= 0.4 THEN 2
                    WHEN abs(new.score - other.score) <= 0.5 THEN 1
                    ELSE 0
                END
        )
        """
        session.run(relation_query, {"name": data["name"]})

    return jsonify({"message": "Videojuego creado y relacionado con otros"}), 201

@videogames_bp.route('/videogames', methods=['GET'])
def get_all_videogames():
    query = "MATCH (g:Game) RETURN g"
    results = []
    with get_driver().session() as session:
        for record in session.run(query):
            g = record["g"]
            results.append(g._properties)
    return jsonify(results), 200

@videogames_bp.route('/videogames/<name>', methods=['GET'])
def get_videogame(name):
    query = "MATCH (g:Game {name: $name}) RETURN g"
    with get_driver().session() as session:
        result = session.run(query, {"name": name})
        record = result.single()
        if record:
            g = record["g"]
            return jsonify(g._properties), 200
        else:
            return jsonify({"error": "Videojuego no encontrado"}), 404
        
@videogames_bp.route('/videogames/<name>', methods=['DELETE'])
def delete_videogame(name):
    query = "MATCH (g:Game {name: $name}) DETACH DELETE g"
    with get_driver().session() as session:
        result = session.run(query, {"name": name})
        if result.summary().counters.nodes_deleted > 0:
            return jsonify({"message": "Videojuego eliminado"}), 200
        else:
            return jsonify({"error": "Videojuego no encontrado"}), 404
        
@videogames_bp.route('/videogames/<name>', methods=['PUT'])
def update_videogame(name):
    data = request.get_json()
    query = """
    MATCH (g:Game {name: $name})
    SET g.multiplayer = $multiplayer,
        g.genres = $genres,
        g.platforms = $platforms,
        g.score = $score,
        g.company = $company,
        g.hours_duration = $hours_duration
    """
    with get_driver().session() as session:
        result = session.run(query, {"name": name, **data})
        if result.summary().counters.properties_set > 0:
            return jsonify({"message": "Videojuego actualizado"}), 200
        else:
            return jsonify({"error": "Videojuego no encontrado"}), 404

@videogames_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    query = """
    CREATE (u:User {
        nombre: $nombre,
        apellido: $apellido,
        correo: $correo,
        contraseña: $contraseña
    })
    """
    with get_driver().session() as session:
        session.run(query, {
            "nombre": data["nombre"],
            "apellido": data["apellido"],
            "correo": data["correo"],
            "contraseña": data["contraseña"]
        })

        for juego in data["juegos_favoritos"]:
            session.run("""
            MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
            MERGE (u)-[r:FAVORITE]->(g)
            ON CREATE SET r.weight = 5
            """, {"correo": data["correo"], "juego": juego})

        for juego in data["juegos_interesados"]:
            session.run("""
            MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
            MERGE (u)-[r:INTERESTED]->(g)
            ON CREATE SET r.weight = 2
            """, {"correo": data["correo"], "juego": juego})

        for juego in data.get("juegos_no_gustados", []):  # Usa get() con valor por defecto []
            session.run("""
            MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
            MERGE (u)-[r:NO_GUSTADOS]->(g)
            ON CREATE SET r.weight = -5
            """, {"correo": data["correo"], "juego": juego})

        for juego in data.get("juegos_jugados", []):  # Usa get() con valor por defecto []
            session.run("""
            MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
            MERGE (u)-[r:PLAYED]->(g)
            ON CREATE SET r.weight = 0
             """, {"correo": data["correo"], "juego": juego})

        for amigo in data["amigos"]:
            session.run("""
            MATCH (u1:User {correo: $correo}), (u2:User {correo: $amigo})
            MERGE (u1)-[r:FRIEND]->(u2)
            ON CREATE SET r.weight = 5
            MERGE (u2)-[r2:FRIEND]->(u1)
            ON CREATE SET r2.weight = 5
            """, {"correo": data["correo"], "amigo": amigo})

    return jsonify({"message": "Usuario creado"}), 201

@videogames_bp.route('/users', methods=['GET'])
def get_all_users():
    query = "MATCH (u:User) RETURN u"
    results = []
    with get_driver().session() as session:
        for record in session.run(query):
            u = record["u"]
            results.append(u._properties)
    return jsonify(results), 200

@videogames_bp.route('/users/<correo>', methods=['GET'])
def get_user(correo):
    query = "MATCH (u:User {correo: $correo}) RETURN u"
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo})
        record = result.single()
        if record:
            u = record["u"]
            return jsonify(u._properties), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
@videogames_bp.route('/users/<correo>', methods=['DELETE'])
def delete_user(correo):
    query = "MATCH (u:User {correo: $correo}) DETACH DELETE u"
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo})
        if result.summary().counters.nodes_deleted > 0:
            return jsonify({"message": "Usuario eliminado"}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
@videogames_bp.route('/users/<correo>', methods=['PUT'])
def update_user(correo):
    data = request.get_json()
    query = """
    MATCH (u:User {correo: $correo})
    SET u.nombre = $nombre,
        u.apellido = $apellido,
        u.contraseña = $contraseña
    """
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo, **data})
        if result.summary().counters.properties_set > 0:
            return jsonify({"message": "Usuario actualizado"}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404

@videogames_bp.route('/users/<correo>/preferences', methods=['POST'])
def set_user_preferences(correo):
    data = request.get_json()
    query = """
    MATCH (u:User {correo: $correo})
    SET u.generos_favoritos = $generos_favoritos,
        u.plataformas_favoritas = $plataformas_favoritas,
        u.prefiere_multijugador = $prefiere_multijugador
    """
    with get_driver().session() as session:
        result = session.run(query, {
            "correo": correo,
            "generos_favoritos": data.get("generos_favoritos", []),
            "plataformas_favoritas": data.get("plataformas_favoritas", []),
            "prefiere_multijugador": data.get("prefiere_multijugador", False)
        })
        if result.summary().counters.properties_set > 0:
            # Crear relaciones RECOMMENDED basadas en preferencias
            games_query = """
            MATCH (g:Game)
            WHERE ANY(x IN $generos_favoritos WHERE x IN g.genres)
               OR ANY(x IN $plataformas_favoritas WHERE x IN g.platforms)
               OR g.multiplayer = $prefiere_multijugador
            MERGE (u:User {correo: $correo})-[r:RECOMMENDED]->(g)
            ON CREATE SET r.weight = 
                (SIZE([x IN $generos_favoritos WHERE x IN g.genres]) * 0.4 +
                 SIZE([x IN $plataformas_favoritas WHERE x IN g.platforms]) * 0.3 +
                 (CASE WHEN g.multiplayer = $prefiere_multijugador THEN 0.2 ELSE 0 END))
            ON MATCH SET r.weight = 
                (SIZE([x IN $generos_favoritos WHERE x IN g.genres]) * 0.4 +
                 SIZE([x IN $plataformas_favoritas WHERE x IN g.platforms]) * 0.3 +
                 (CASE WHEN g.multiplayer = $prefiere_multijugador THEN 0.2 ELSE 0 END))
            """
            session.run(games_query, {
                "correo": correo,
                "generos_favoritos": data.get("generos_favoritos", []),
                "plataformas_favoritas": data.get("plataformas_favoritas", []),
                "prefiere_multijugador": data.get("prefiere_multijugador", False)
            })
            return jsonify({"message": "Preferencias actualizadas y recomendaciones creadas"}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404