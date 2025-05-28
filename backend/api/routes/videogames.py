from flask import Blueprint, request, jsonify
from neo4j_driver import get_driver
from urllib.parse import unquote

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

        // Relación de géneros (A->B)
        WITH new, other,
            [x IN new.genres WHERE x IN other.genres] AS shared_genres,
            size(new.genres) AS new_genres_count,
            size(other.genres) AS other_genres_count
        FOREACH (_ IN CASE WHEN size(shared_genres) > 0 THEN [1] ELSE [] END |
            MERGE (new)-[r:SIMILAR_GENRE]->(other)
            ON CREATE SET r.weight = 
                CASE
                    WHEN toFloat(size(shared_genres))/toFloat(new_genres_count) >= 1 THEN 5
                    WHEN 1 > toFloat(size(shared_genres))/toFloat(new_genres_count) >= 0.75 THEN 4
                    WHEN 0.75 > toFloat(size(shared_genres))/toFloat(new_genres_count) >= 0.5 THEN 3
                    WHEN 0.5 > toFloat(size(shared_genres))/toFloat(new_genres_count) >= 0.25 THEN 2
                    WHEN 0.25 > toFloat(size(shared_genres))/toFloat(new_genres_count) > 0 THEN 1
                    ELSE 0
                END
        )

        // Relación de géneros (B->A)
        FOREACH (_ IN CASE WHEN size(shared_genres) > 0 THEN [1] ELSE [] END |
            MERGE (other)-[r2:SIMILAR_GENRE]->(new)
            ON CREATE SET r2.weight = 
                CASE
                    WHEN toFloat(size(shared_genres))/toFloat(other_genres_count) >= 1 THEN 5
                    WHEN 1 > toFloat(size(shared_genres))/toFloat(other_genres_count) >= 0.75 THEN 4
                    WHEN 0.75 > toFloat(size(shared_genres))/toFloat(other_genres_count) >= 0.5 THEN 3
                    WHEN 0.5 > toFloat(size(shared_genres))/toFloat(other_genres_count) >= 0.25 THEN 2
                    WHEN 0.25 > toFloat(size(shared_genres))/toFloat(other_genres_count) > 0 THEN 1
                    ELSE 0
                END
        )

        // Relación de plataformas (A->B)
        WITH new, other,
            [x IN new.platforms WHERE x IN other.platforms] AS shared_platforms,
            size(new.platforms) AS new_platforms_count,
            size(other.platforms) AS other_platforms_count
        FOREACH (_ IN CASE WHEN size(shared_platforms) > 0 THEN [1] ELSE [] END |
            MERGE (new)-[r:SIMILAR_PLATFORM]->(other)
            ON CREATE SET r.weight = 
                CASE
                    WHEN toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 1 THEN 5
                    WHEN 1 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 0.75 THEN 4
                    WHEN 0.75 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 0.5 THEN 3
                    WHEN 0.5 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 0.25 THEN 2
                    WHEN 0.25 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) > 0 THEN 1
                    ELSE 0
                END
        )

        // Relación de plataformas (B->A)
        FOREACH (_ IN CASE WHEN size(shared_platforms) > 0 THEN [1] ELSE [] END |
            MERGE (other)-[r2:SIMILAR_PLATFORM]->(new)
            ON CREATE SET r2.weight = 
                CASE
                    WHEN toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 1 THEN 5
                    WHEN 1 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 0.75 THEN 4
                    WHEN 0.75 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 0.5 THEN 3
                    WHEN 0.5 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 0.25 THEN 2
                    WHEN 0.25 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) > 0 THEN 1
                    ELSE 0
                END
        )

        // Las demás relaciones igual...
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
                    WHEN abs(new.hours_duration - other.hours_duration) <= 5 THEN 5
                    WHEN abs(new.hours_duration - other.hours_duration) <= 10 THEN 4
                    WHEN abs(new.hours_duration - other.hours_duration) <= 15 THEN 3
                    WHEN abs(new.hours_duration - other.hours_duration) <= 20 THEN 2
                    WHEN abs(new.hours_duration - other.hours_duration) <= 25 THEN 1
                    ELSE 0
                END
            MERGE (other)-[r2:SAME_DURATION]->(new)
            ON CREATE SET r2.weight =
                CASE
                    WHEN abs(new.hours_duration - other.hours_duration) <= 5 THEN 5
                    WHEN abs(new.hours_duration - other.hours_duration) <= 10 THEN 4
                    WHEN abs(new.hours_duration - other.hours_duration) <= 15 THEN 3
                    WHEN abs(new.hours_duration - other.hours_duration) <= 20 THEN 2
                    WHEN abs(new.hours_duration - other.hours_duration) <= 25 THEN 1
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

        for juego in data["juegos_no_gustados"]:
            session.run("""
            MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
            MERGE (u)-[r:NO_GUSTADOS]->(g)
            ON CREATE SET r.weight = -5
            """, {"correo": data["correo"], "juego": juego})

        for juego in data["juegos_jugados"]:
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

@videogames_bp.route('/users/<correo>/actualizar_juegos', methods=['PUT'])
def update_user_games(correo):
    data = request.get_json()
    mensajes = []

    with get_driver().session() as session:
        # Actualizar juegos favoritos
        for juego in data.get("juegos_favoritos", []):
            result = session.run("""
                MATCH (u:User {correo: $correo})-[r:FAVORITE]->(g:Game {name: $juego})
                RETURN r
            """, {"correo": correo, "juego": juego})
            if result.single():
                mensajes.append(f"{juego} ya es favorito.")
            else:
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:FAVORITE]->(g)
                    ON CREATE SET r.weight = 5
                """, {"correo": correo, "juego": juego})
                mensajes.append(f"{juego} agregado como favorito.")

        # Actualizar juegos interesados
        for juego in data.get("juegos_interesados", []):
            result = session.run("""
                MATCH (u:User {correo: $correo})-[r:INTERESTED]->(g:Game {name: $juego})
                RETURN r
            """, {"correo": correo, "juego": juego})
            if result.single():
                mensajes.append(f"{juego} ya está como interesado.")
            else:
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:INTERESTED]->(g)
                    ON CREATE SET r.weight = 2
                """, {"correo": correo, "juego": juego})
                mensajes.append(f"{juego} agregado como interesado.")

        # Actualizar juegos no gustados
        for juego in data.get("juegos_no_gustados", []):
            result = session.run("""
                MATCH (u:User {correo: $correo})-[r:NO_GUSTADOS]->(g:Game {name: $juego})
                RETURN r
            """, {"correo": correo, "juego": juego})
            if result.single():
                mensajes.append(f"{juego} ya está como no gustado.")
            else:
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:NO_GUSTADOS]->(g)
                    ON CREATE SET r.weight = -5
                """, {"correo": correo, "juego": juego})
                mensajes.append(f"{juego} agregado como no gustado.")

        # Actualizar juegos jugados
        for juego in data.get("juegos_jugados", []):
            result = session.run("""
                MATCH (u:User {correo: $correo})-[r:PLAYED]->(g:Game {name: $juego})
                RETURN r
            """, {"correo": correo, "juego": juego})
            if result.single():
                mensajes.append(f"{juego} ya está como jugado.")
            else:
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:PLAYED]->(g)
                    ON CREATE SET r.weight = 0
                """, {"correo": correo, "juego": juego})
                mensajes.append(f"{juego} agregado como jugado.")

    return jsonify({"mensajes": mensajes}), 200

@videogames_bp.route('users/<correo>/actualizar_contraseña', methods=['PUT'])
def update_user_password(correo):
    data = request.get_json()
    new_password = data.get("contraseña")
    if not new_password:
        return jsonify({"error": "Nueva contraseña requerida"}), 400

    query = """
    MATCH (u:User {correo: $correo})
    SET u.contraseña = $contraseña
    """
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo, "contraseña": new_password})
        if result.summary().counters.properties_set > 0:
            return jsonify({"message": "Contraseña actualizada"}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
@videogames_bp.route('/users/<correo>/actualizar_amigos', methods=['PUT'])
def update_user_friends(correo):
    data = request.get_json()
    amigos = data.get("amigos", [])

    with get_driver().session() as session:
        mensajes = []
        for amigo in amigos:
            # Verifica si la relación ya existe
            result = session.run("""
                MATCH (u1:User {correo: $correo})-[r:FRIEND]->(u2:User {correo: $amigo})
                RETURN r
            """, {"correo": correo, "amigo": amigo})
            if result.single():
                mensajes.append(f"{amigo} ya es amigo.")
            else:
                # Crea la relación en ambos sentidos
                session.run("""
                    MATCH (u1:User {correo: $correo}), (u2:User {correo: $amigo})
                    MERGE (u1)-[r:FRIEND]->(u2)
                    ON CREATE SET r.weight = 5
                    MERGE (u2)-[r2:FRIEND]->(u1)
                    ON CREATE SET r2.weight = 5
                """, {"correo": correo, "amigo": amigo})
                mensajes.append(f"{amigo} agregado como amigo.")

    return jsonify({"mensajes": mensajes}), 200

@videogames_bp.route('/users/<correo>/actualizar_correo', methods=['PUT'])
def update_user_email(correo):
    data = request.get_json()
    new_email = data.get("correo")
    if not new_email:
        return jsonify({"error": "Nuevo correo requerido"}), 400

    query = """
    MATCH (u:User {correo: $correo})
    SET u.correo = $nuevo_correo
    """
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo, "nuevo_correo": new_email})
        if result.summary().counters.properties_set > 0:
            return jsonify({"message": "Correo actualizado"}), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
@videogames_bp.route('/users/<correo>/eliminar_amigo/<amigo>', methods=['DELETE'])
def delete_user_friend(correo, amigo):
    query = """
    MATCH (u1:User {correo: $correo})-[r:FRIEND]->(u2:User {correo: $amigo})
    DELETE r
    """
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo, "amigo": amigo})
        if result.summary().counters.relationships_deleted > 0:
            return jsonify({"message": "Amigo eliminado"}), 200
        else:
            return jsonify({"error": "Amigo no encontrado"}), 404
        
@videogames_bp.route('/users/<correo>/eliminar_juego/<juego>', methods=['DELETE'])
def delete_user_game(correo, juego):
    query = """
    MATCH (u:User {correo: $correo})-[r:FAVORITE|INTERESTED|NO_GUSTADOS|PLAYED]->(g:Game {name: $juego})
    DELETE r
    """
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo, "juego": juego})
        if result.summary().counters.relationships_deleted > 0:
            return jsonify({"message": "Juego eliminado de las relaciones del usuario"}), 200
        else:
            return jsonify({"error": "Juego no encontrado en las relaciones del usuario"}), 404
        
from urllib.parse import unquote


#Extra para ver las preferencias del usuario

@videogames_bp.route('/users/<correo>/preferences', methods=['POST'])
def set_user_preferences(correo):
    correo = unquote(correo)  # Decodifica la URL
    data = request.get_json()
    print(f"Received data: {data}, correo: {correo}")  # Depuración
    query = """
    MATCH (u:User {correo: $correo})
    SET u.generos_favoritos = $generos_favoritos,
        u.plataformas_favoritas = $plataformas_favoritas,
        u.prefiere_multijugador = $prefiere_multijugador
    RETURN u
    """
    with get_driver().session() as session:
        result = session.run(query, {
            "correo": correo,
            "generos_favoritos": data.get("generos_favoritos", []),
            "plataformas_favoritas": data.get("plataformas_favoritas", []),
            "prefiere_multijugador": data.get("prefiere_multijugador", False)
        })
        record = result.single()
        if record:
            print(f"Updated user: {record['u']._properties}")  # Depuración
            return jsonify({"message": "Preferencias actualizadas"}), 200
        else:
            print(f"User not found: {correo}")  # Depuración
            return jsonify({"error": "Usuario no encontrado"}), 404