import json
import os
from neo4j_driver import get_driver

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

            # Create relationships between games
            session.run("""
                MATCH (g1:Game), (g2:Game)
                WHERE g1 <> g2 AND ANY(genre IN g1.genres WHERE genre IN g2.genres)
                MERGE (g1)-[:SIMILAR_GENRE {weight: 5}]->(g2)
            """)

            session.run("""
                MATCH (g1:Game), (g2:Game)
                WHERE g1 <> g2 AND ANY(platform IN g1.platforms WHERE platform IN g2.platforms)
                MERGE (g1)-[:SIMILAR_PLATFORM]->(g2)
            """)

            print("Games and relationships loaded successfully.")

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
            # Create user node
            session.run("""
                MERGE (u:User {correo: $correo})
                SET u.nombre = $nombre,
                    u.apellido = $apellido,
                    u.contraseña = $contraseña
            """, {
                "correo": user["correo"],
                "nombre": user["nombre"],
                "apellido": user["apellido"],
                "contraseña": user["contraseña"]
            })

            # Create FAVORITE relationships
            for game in user.get("juegos_favoritos", []):
                result = session.run("MATCH (g:Game {name: $game}) RETURN g", {"game": game})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $game})
                        MERGE (u)-[r:FAVORITE]->(g)
                        ON CREATE SET r.weight = 5
                    """, {"correo": user["correo"], "game": game})
                else:
                    print(f"Game {game} not found for user {user['correo']}")

            # Create INTERESTED relationships
            for game in user.get("juegos_interesados", []):
                result = session.run("MATCH (g:Game {name: $game}) RETURN g", {"game": game})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $game})
                        MERGE (u)-[r:INTERESTED]->(g)
                        ON CREATE SET r.weight = 2
                    """, {"correo": user["correo"], "game": game})
                else:
                    print(f"Game {game} not found for user {user['correo']}")

            # Create NO_GUSTADOS relationships
            for game in user.get("juegos_no_gustados", []):
                result = session.run("MATCH (g:Game {name: $game}) RETURN g", {"game": game})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $game})
                        MERGE (u)-[r:NO_GUSTADOS]->(g)
                        ON CREATE SET r.weight = -5
                    """, {"correo": user["correo"], "game": game})
                else:
                    print(f"Game {game} not found for user {user['correo']}")

            # Create PLAYED relationships
            for game in user.get("juegos_jugados", []):
                result = session.run("MATCH (g:Game {name: $game}) RETURN g", {"game": game})
                if result.single():
                    session.run("""
                        MATCH (u:User {correo: $correo}), (g:Game {name: $game})
                        MERGE (u)-[r:PLAYED]->(g)
                        ON CREATE SET r.weight = 0
                    """, {"correo": user["correo"], "game": game})
                else:
                    print(f"Game {game} not found for user {user['correo']}")

            # Create FRIEND relationships
            for amigo in user.get("amigos", []):
                result = session.run("MATCH (u2:User {correo: $amigo}) RETURN u2", {"amigo": amigo})
                if result.single():
                    session.run("""
                        MATCH (u1:User {correo: $correo}), (u2:User {correo: $amigo})
                        MERGE (u1)-[r:FRIEND]->(u2)
                        ON CREATE SET r.weight = 5
                    """, {"correo": user["correo"], "amigo": amigo})
                else:
                    print(f"Friend {amigo} not found for user {user['correo']}")

        print("Users and relationships loaded successfully.")

if __name__ == "__main__":
    initialize_database()