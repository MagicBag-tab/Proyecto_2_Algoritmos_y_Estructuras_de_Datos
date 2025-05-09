from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "12345678"

# Luego las usas correctamente aquí
driver = GraphDatabase.driver(uri, auth=(user, password))

def get_driver():
    return driver
