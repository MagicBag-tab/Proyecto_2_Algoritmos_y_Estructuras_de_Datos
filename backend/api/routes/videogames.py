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
        company: $company
    })
    """
    with get_driver().session() as session:
        session.run(query, **data)

        # Relacionar con juegos similares
        relation_query = """
        MATCH (new:Game {name: $name}), (other:Game)
        WHERE new.name <> other.name

        FOREACH (_ IN CASE WHEN any(x IN new.genres WHERE x IN other.genres) THEN [1] ELSE [] END |
            MERGE (new)-[:SIMILAR_GENRE]->(other)
        )
        FOREACH (_ IN CASE WHEN any(x IN new.platforms WHERE x IN other.platforms) THEN [1] ELSE [] END |
            MERGE (new)-[:SIMILAR_PLATFORM]->(other)
        )
        FOREACH (_ IN CASE WHEN new.company = other.company THEN [1] ELSE [] END |
            MERGE (new)-[:SAME_COMPANY]->(other)
        )
        """
        session.run(relation_query, {"name": data["name"]})

    return jsonify({"message": "Videogame creado y relacionado con otros"}), 201

@videogames_bp.route('/videogames', methods=['GET'])
def get_all_videogames():
    query = "MATCH (g:Game) RETURN g"
    results = []
    with get_driver().session() as session:
        for record in session.run(query):
            g = record["g"]
            results.append(g._properties)
    return jsonify(results), 200

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
            MERGE (u)-[:FAVORITE]->(g)
            """, {"correo": data["correo"], "juego": juego})

    return jsonify({"message": "Usuario creado y conectado a sus juegos favoritos"}), 201

@videogames_bp.route('/recommendations/<correo>', methods=['GET'])
def recommend_games(correo):
    query = """
    MATCH (u:User {correo: $correo})-[:FAVORITE]->(f:Game)
    MATCH (f)-[:SIMILAR_GENRE|SIMILAR_PLATFORM|SAME_COMPANY]->(rec:Game)
    WHERE NOT (u)-[:FAVORITE]->(rec)
    RETURN DISTINCT rec LIMIT 10
    """
    with get_driver().session() as session:
        result = session.run(query, {"correo": correo})
        games = [record["rec"]._properties for record in result]
    return jsonify(games), 200
