# Proyecto_2_Algoritmos_y_Estructuras_de_Datos

# Sistema de Recomendación de Videojuegos:

Este sistema utiliza una base de datos en grafo y una API REST desarrollada en Flask para gestionar usuarios y videojuegos, y construir relaciones inteligentes entre ellos. Permite representar preferencias, similitudes y vínculos entre usuarios y títulos, sentando las bases para recomendaciones personalizadas.


# Características:

- API RESTful desarrollada con Flask.
- Base de datos Neo4j para representar relaciones en grafo.
- Carga automática de datos desde games.json y users.json.
- Algoritmo de relacionamiento que considera:
- Géneros en común entre juegos.
- Plataformas compartidas.
- Puntuación, duración y estilo (multijugador o no)
- Preferencias de usuario (favoritos, interesados, jugados, no gustados).
- Relaciones sociales entre usuarios (amistades).

# Requisitos:

- Python 3.10+
- Neo4j (instancia local)
- Pip (para gestión de dependencias)
- Dependencias listadas a continuación
- Dependencias (requirements.txt)
  - Flask
  - Flask-Cors
  - neo4j

# Instalación rápida:
  - pip install flask flask-cors neo4j


# Instalaión y ejecución
1. Colonar el repositorio.
 - git clone https://github.com/Luis-Angel-G/Frontend-P2-Algoritmos.git
 - cd sistema-recomendacion-videojuegos/backend

2. Crear entorno virtual
 - python -m venv venv
   venv\\Scripts\\activate 

3. Instalar dependencias
 -  pip install -r requirements.txt

4. Condigurar conexión a Neo4J
 - Editar el archivo neo4j_driver.py con los datos de acceso:
    - uri = "bolt://localhost:7687"
    - user = "neo4j"
    - password = "tu_contraseña"

5. Ejecutar la API
 - python main.py

# Documentación de la API

1. Juegos (/api/v1/videogames)
 - GET /videogames → Listar todos los juegos
 - POST /videogames → Crear un nuevo juego y relacionarlo con otros automáticamente
 - GET /videogames/<name> → Ver detalles de un juego
 - PUT /videogames/<name> → Actualizar un juego
 - DELETE /videogames/<name> → Eliminar un juego

2. Usuarios (/api/v1/users)
 - POST /users → Crear un nuevo usuario con relaciones
 - GET /users → Listar todos los usuarios
 - GET /users/<correo> → Ver detalles de un usuario
 - PUT /users/<correo> → Actualizar nombre, apellido, contraseña
 - DELETE /users/<correo> → Eliminar usuario

3. Relaciones adicionales
 - PUT /users/<correo>/actualizar_juegos → Actualizar favoritos, jugados, interesados y no gustados
 - PUT /users/<correo>/actualizar_amigos → Agregar amigos
 - DELETE /users/<correo>/eliminar_amigo/<amigo> → Quitar amigos
 - DELETE /users/<correo>/eliminar_juego/<juego> → Quitar juegos de cualquier categoría
 - PUT /users/<correo>/actualizar_contraseña → Cambiar contraseña
 - PUT /users/<correo>/actualizar_correo → Cambiar correo

4. Preferencias
 - POST /users/<correo>/preferences → Establecer géneros y plataformas favoritas

5. Login
 - POST /login → Validación de usuario (correo + contraseña)


# Datos de prueba
- games.json: incluye videojuegos con atributos como:

- name, genres, platforms, score, multiplayer, company, hours_duration

- users.json: usuarios con relaciones hacia videojuegos (favoritos, jugados, etc.) y otros usuarios (amigos)

# Estructura del backend
backend/
├── api/
│   ├── main.py                     # Punto de entrada del backend
│   ├── init_db.py                  # Inicializa juegos y usuarios desde JSON
│   ├── neo4j_driver.py             # Configura conexión a Neo4j
│   └── routes/
│       ├── videogames.py           # Rutas de juegos y usuarios
│       ├── preferences.py          # Preferencias del usuario
│       └── recommendations.py      # (Opcional) lógica de recomendación
├── games.json
├── users.json
└── requirements.txt

# Modelo de Datos
1.  Usuario (User)
- Nombre, Apellido, Correo, Contraseña
    - Relaciones:
        - :FAVORITE, :INTERESTED, :NO_GUSTADOS, :PLAYED → con juegos
        - :FRIEND → con otros usuarios
        - generos_favoritos, plataformas_favoritas, prefiere_multijugador

2. Videojuego (Game)
 - Nombre, Compañía, Géneros, Plataformas, Score,  Multiplayer, Horas de duración
    - Relaciones:
    - :SIMILAR_GENRE, :SIMILAR_PLATFORM, :SAME_COMPANY, :SAME_SCORE, :SAME_DURATION


# Lógica de recomendación (Estructura base)

# Videos sobre feedback
- Link: https://www.canva.com/design/DAGo49ksld8/wEtRlSPN5Sv4ekSj3aRd0Q/watch?utm_content=DAGo49ksld8&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h9f30b246a7
