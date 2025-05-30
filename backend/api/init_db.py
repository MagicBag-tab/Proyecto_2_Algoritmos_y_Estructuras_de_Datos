import json
import os
from neo4j_driver import get_driver
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def initialize_database():
    with get_driver().session() as session:
        # Clear the database
        session.run("MATCH (n) DETACH DELETE n")
        
        # Check if games already exist
        result = session.run("MATCH (g:Game) RETURN count(g) AS count")
        if result.single()["count"] > 0:
            print("Database already contains games, skipping game loading.")
        else:
            # Resolve absolute path for games.json
            SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
            GAMES_JSON_PATH = os.path.join(SCRIPT_DIR, 'games.json')
            try:
                with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as file:
                    games = json.load(file)
            except FileNotFoundError:
                print(f"Error: games.json not found at {GAMES_JSON_PATH}.")
                return
            except json.JSONDecodeError:
                print("Error: games.json has invalid format.")
                return

            # Load games into Neo4j
            for game in games:
                session.run("""
                    MERGE (g:Game {name: $name})
                    SET g.multiplayer = $multiplayer,
                        g.genres = $genres,
                        g.platforms = $platforms,
                        g.score = $score,
                        g.company = $company,
                        g.hours_duration = $hours_duration,
                        g.image_url = $image_url
                """, game)

                # Crear relaciones idénticas a videogames.py
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
                            WHEN toFloat(size(shared_genres))/toFloat(new_genres_count) >= 1 THEN 10
                            WHEN 1 > toFloat(size(shared_genres))/toFloat(new_genres_count) >= 0.75 THEN 7
                            WHEN 0.75 > toFloat(size(shared_genres))/toFloat(new_genres_count) >= 0.5 THEN 5
                            WHEN 0.5 > toFloat(size(shared_genres))/toFloat(new_genres_count) >= 0.25 THEN 3
                            WHEN 0.25 > toFloat(size(shared_genres))/toFloat(new_genres_count) > 0 THEN 1
                            ELSE 0
                        END
                )

                // Relación de géneros (B->A)
                FOREACH (_ IN CASE WHEN size(shared_genres) > 0 THEN [1] ELSE [] END |
                    MERGE (other)-[r2:SIMILAR_GENRE]->(new)
                    ON CREATE SET r2.weight = 
                        CASE
                            WHEN toFloat(size(shared_genres))/toFloat(other_genres_count) >= 1 THEN 10
                            WHEN 1 > toFloat(size(shared_genres))/toFloat(other_genres_count) >= 0.75 THEN 7
                            WHEN 0.75 > toFloat(size(shared_genres))/toFloat(other_genres_count) >= 0.5 THEN 5
                            WHEN 0.5 > toFloat(size(shared_genres))/toFloat(other_genres_count) >= 0.25 THEN 3
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
                            WHEN toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 1 THEN 10
                            WHEN 1 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 0.75 THEN 7
                            WHEN 0.75 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 0.5 THEN 5
                            WHEN 0.5 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) >= 0.25 THEN 3
                            WHEN 0.25 > toFloat(size(shared_platforms))/toFloat(new_platforms_count) > 0 THEN 1
                            ELSE 0
                        END
                )

                // Relación de plataformas (B->A)
                FOREACH (_ IN CASE WHEN size(shared_platforms) > 0 THEN [1] ELSE [] END |
                    MERGE (other)-[r2:SIMILAR_PLATFORM]->(new)
                    ON CREATE SET r2.weight = 
                        CASE
                            WHEN toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 1 THEN 10
                            WHEN 1 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 0.75 THEN 7
                            WHEN 0.75 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 0.5 THEN 5
                            WHEN 0.5 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) >= 0.25 THEN 3
                            WHEN 0.25 > toFloat(size(shared_platforms))/toFloat(other_platforms_count) > 0 THEN 1
                            ELSE 0
                        END
                )

                // SAME_COMPANY
                FOREACH (_ IN CASE WHEN new.company = other.company THEN [1] ELSE [] END |
                    MERGE (new)-[r:SAME_COMPANY]->(other)
                    ON CREATE SET r.weight = 5
                    MERGE (other)-[r2:SAME_COMPANY]->(new)
                    ON CREATE SET r2.weight = 5
                )
                // SAME_MULTIPLAYER
                FOREACH (_ IN CASE WHEN new.multiplayer = other.multiplayer THEN [1] ELSE [] END |
                    MERGE (new)-[r:SAME_MULTIPLAYER]->(other)
                    ON CREATE SET r.weight = 5
                    MERGE (other)-[r2:SAME_MULTIPLAYER]->(new)
                    ON CREATE SET r2.weight = 5
                )
                // SAME_DURATION
                FOREACH (_ IN CASE WHEN abs(new.hours_duration - other.hours_duration) <= 25 THEN [1] ELSE [] END |
                    MERGE (new)-[r:SAME_DURATION]->(other)
                    ON CREATE SET r.weight =
                        CASE
                            WHEN abs(new.hours_duration - other.hours_duration) <= 5.1 THEN 5
                            WHEN 5.1 < abs(new.hours_duration - other.hours_duration) <= 10.1 THEN 4
                            WHEN 10.1 < abs(new.hours_duration - other.hours_duration) <= 15.1 THEN 3
                            WHEN 15.1 < abs(new.hours_duration - other.hours_duration) <= 20.1 THEN 2
                            WHEN 20.1 < abs(new.hours_duration - other.hours_duration) <= 25.1 THEN 1
                            ELSE 0
                        END
                    MERGE (other)-[r2:SAME_DURATION]->(new)
                    ON CREATE SET r2.weight =
                        CASE
                            WHEN abs(new.hours_duration - other.hours_duration) <= 5.1 THEN 5
                            WHEN 5.1 < abs(new.hours_duration - other.hours_duration) <= 10.1 THEN 4
                            WHEN 10.1 < abs(new.hours_duration - other.hours_duration) <= 15.1 THEN 3
                            WHEN 15.1 < abs(new.hours_duration - other.hours_duration) <= 20.1 THEN 2
                            WHEN 20.1 < abs(new.hours_duration - other.hours_duration) <= 25.1 THEN 1
                            ELSE 0
                        END
                )
                // SAME_SCORE
                FOREACH (_ IN CASE WHEN abs(new.score - other.score) <= 0.5 THEN [1] ELSE [] END |
                    MERGE (new)-[r:SAME_SCORE]->(other)
                    ON CREATE SET r.weight =
                        CASE
                            WHEN abs(new.score - other.score) <= 0.11 THEN 5
                            WHEN 0.11 < abs(new.score - other.score) <= 0.21 THEN 4
                            WHEN 0.21 < abs(new.score - other.score) <= 0.31 THEN 3
                            WHEN 0.31 < abs(new.score - other.score) <= 0.41 THEN 2
                            WHEN 0.41 < abs(new.score - other.score) <= 0.51 THEN 1
                            ELSE 0
                        END
                    MERGE (other)-[r2:SAME_SCORE]->(new)
                    ON CREATE SET r2.weight =
                        CASE
                            WHEN abs(new.score - other.score) <= 0.11 THEN 5
                            WHEN 0.11 < abs(new.score - other.score) <= 0.21 THEN 4
                            WHEN 0.21 < abs(new.score - other.score) <= 0.31 THEN 3
                            WHEN 0.31 < abs(new.score - other.score) <= 0.41 THEN 2
                            WHEN 0.41 < abs(new.score - other.score) <= 0.51 THEN 1
                            ELSE 0
                        END
                )
                """
                session.run(relation_query, {"name": game["name"]})

        # Check if users already exist
        result = session.run("MATCH (u:User) RETURN count(u) AS count")
        if result.single()["count"] > 0:
            print("Database already contains users, skipping users loading.")
            return

        # Resolve absolute path for users.json
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        USERS_JSON_PATH = os.path.join(SCRIPT_DIR, 'users.json')
        try:
            with open(USERS_JSON_PATH, 'r', encoding='utf-8') as file:
                users = json.load(file)
        except FileNotFoundError:
            print(f"Error: users.json not found at {USERS_JSON_PATH}.")
            return
        except json.JSONDecodeError:
            print("Error: users.json has invalid format.")
            return

        # Load users and relationships
        for user in users:
            # Cifrar la contraseña antes de guardar
            hashed_password = bcrypt.generate_password_hash(user["contraseña"]).decode('utf-8')
            session.run("""
                MERGE (u:User {correo: $correo})
                SET u.nombre = $nombre,
                    u.apellido = $apellido,
                    u.contraseña = $contraseña
            """, {
                "correo": user["correo"],
                "nombre": user["nombre"],
                "apellido": user["apellido"],
                "contraseña": hashed_password
            })

            # FAVORITE
            for juego in user.get("juegos_favoritos", []):
                result = session.run("MATCH (g:Game {name: $juego}) RETURN g", {"juego": juego})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                        MERGE (u)-[r:FAVORITE]->(g)
                        ON CREATE SET r.weight = 10
                    """, {"correo": user["correo"], "juego": juego})
                else:
                    print(f"Game {juego} not found for user {user['correo']}")

            # INTERESTED
            for juego in user.get("juegos_interesados", []):
                result = session.run("MATCH (g:Game {name: $juego}) RETURN g", {"juego": juego})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                        MERGE (u)-[r:INTERESTED]->(g)
                        ON CREATE SET r.weight = 5
                    """, {"correo": user["correo"], "juego": juego})
                else:
                    print(f"Game {juego} not found for user {user['correo']}")

            # NO_GUSTADOS
            for juego in user.get("juegos_no_gustados", []):
                result = session.run("MATCH (g:Game {name: $juego}) RETURN g", {"juego": juego})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                        MERGE (u)-[r:NO_GUSTADOS]->(g)
                        ON CREATE SET r.weight = -10
                    """, {"correo": user["correo"], "juego": juego})
                else:
                    print(f"Game {juego} not found for user {user['correo']}")

            # PLAYED
            for juego in user.get("juegos_jugados", []):
                result = session.run("MATCH (g:Game {name: $juego}) RETURN g", {"juego": juego})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                        MERGE (u)-[r:PLAYED]->(g)
                        ON CREATE SET r.weight = 0
                    """, {"correo": user["correo"], "juego": juego})
                else:
                    print(f"Game {juego} not found for user {user['correo']}")

            # FRIEND (bidireccional)
            for amigo in user.get("amigos", []):
                result = session.run("MATCH (u2:User {correo: $amigo}) RETURN u2", {"amigo": amigo})
                if result.single():
                    session.run("""
                        MATCH (u1:User {correo: $correo}), (u2:User {correo: $amigo})
                        MERGE (u1)-[r:FRIEND]->(u2)
                        ON CREATE SET r.weight = 1
                        MERGE (u2)-[r2:FRIEND]->(u1)
                        ON CREATE SET r2.weight = 1
                    """, {"correo": user["correo"], "amigo": amigo})
                else:
                    print(f"Friend {amigo} not found for user {user['correo']}")

        print("Users and relationships loaded successfully.")

if __name__ == "__main__":
    initialize_database()