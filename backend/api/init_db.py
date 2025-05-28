import json
from neo4j_driver import get_driver

def initialize_database():
    with get_driver().session() as session:
        # Verificar si la base de datos ya tiene juegos
        result = session.run("MATCH (g:Game) RETURN count(g) AS count")
        if result.single()["count"] > 0:
            print("Base de datos ya contiene juegos, omitiendo carga de juegos.")
        else:
            # Cargar juegos desde JSON
            try:
                with open('games.json', 'r', encoding='utf-8') as file:
                    games = json.load(file)
            except FileNotFoundError:
                print("Error: games.json no encontrado.")
                return
            except json.JSONDecodeError:
                print("Error: games.json tiene un formato inválido.")
                return

            for game in games:
                session.run("""
                    MERGE (g:Game {name: $name})
                    SET g.multiplayer = $multiplayer,
                        g.genres = $genres,
                        g.platforms = $platforms,
                        g.score = $score,
                        g.company = $company,
                        g.hours_duration = $hours_duration
                """, game)

            # Crear relaciones entre juegos
            session.run("""
                MATCH (g1:Game), (g2:Game)
                WHERE g1 <> g2 AND ANY(genre IN g1.genres WHERE genre IN g2.genres)
                MERGE (g1)-[:SIMILAR_GENRE {weight: 5}]->(g2)
            """)

            session.run("""
                MATCH (g1:Game), (g2:Game)
                WHERE g1 <> g2 AND ANY(platform IN g1.platforms WHERE platform IN g2.platforms)
                MERGE (g1)-[:SIMILAR_PLATFORM {weight: 5}]->(g2)
            """)

            print("Juegos y relaciones cargados exitosamente.")

        # Verificar si la base de datos ya tiene usuarios
        result = session.run("MATCH (u:User) RETURN count(u) AS count")
        if result.single()["count"] > 0:
            print("Base de datos ya contiene usuarios, omitiendo carga de usuarios.")
            return

        # Cargar usuarios desde JSON
        try:
            with open('users.json', 'r', encoding='utf-8') as file:
                users = json.load(file)
        except FileNotFoundError:
            print("Error: users.json no encontrado.")
            return
        except json.JSONDecodeError:
            print("Error: users.json tiene un formato inválido.")
            return

        for user in users:
            # Crear el nodo User
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

            # Crear relaciones FAVORITE
            for juego in user.get("juegos_favoritos", []):
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:FAVORITE]->(g)
                    ON CREATE SET r.weight = 5
                """, {"correo": user["correo"], "juego": juego})

            # Crear relaciones INTERESTED
            for juego in user.get("juegos_interesados", []):
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:INTERESTED]->(g)
                    ON CREATE SET r.weight = 2
                """, {"correo": user["correo"], "juego": juego})

            # Crear relaciones NO_GUSTADOS
            for juego in user.get("juegos_no_gustados", []):
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:NO_GUSTADOS]->(g)
                    ON CREATE SET r.weight = -5
                """, {"correo": user["correo"], "juego": juego})

            # Crear relaciones PLAYED
            for juego in user.get("juegos_jugados", []):
                session.run("""
                    MATCH (u:User {correo: $correo}), (g:Game {name: $juego})
                    MERGE (u)-[r:PLAYED]->(g)
                    ON CREATE SET r.weight = 0
                """, {"correo": user["correo"], "juego": juego})

            # Crear relaciones FRIEND
            for amigo in user.get("amigos", []):
                session.run("""
                    MATCH (u1:User {correo: $correo}), (u2:User {correo: $amigo})
                    MERGE (u1)-[r:FRIEND]->(u2)
                    ON CREATE SET r.weight = 5
                """, {"correo": user["correo"], "amigo": amigo})

        print("Usuarios y relaciones cargados exitosamente.")

if __name__ == "__main__":
    initialize_database()