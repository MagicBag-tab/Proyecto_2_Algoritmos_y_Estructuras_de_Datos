import json
from neo4j_driver import get_driver

def initialize_database():
    with get_driver().session() as session:
        # Verificar si la base de datos ya tiene juegos
        result = session.run("MATCH (g:Game) RETURN count(g) AS count")
        if result.single()["count"] > 0:
            print("Base de datos ya contiene juegos, omitiendo carga.")
            return

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

if __name__ == "__main__":
    initialize_database()