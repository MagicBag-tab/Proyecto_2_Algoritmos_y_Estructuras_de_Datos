from neo4j_driver import get_driver

def test_connection():
    with get_driver().session() as session:
        result = session.run("RETURN 'Conexión exitosa' AS message")
        for record in result:
            print(record["message"])

if __name__ == "__main__":
    test_connection()