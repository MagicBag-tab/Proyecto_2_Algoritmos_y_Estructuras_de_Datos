from neo4j import GraphDatabase

uri = "neo4j+s://021bb73e.databases.neo4j.io"
user = "neo4j"
password = "051waQUeNSwpGfJRpoIojjA5L6eQRzSHRaxIdseNMsc"

# Luego las usas correctamente aquí
driver = GraphDatabase.driver(uri, auth=(user, password))

def get_driver():
    return driver