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

# Instalación rápida:
```sh
pip install flask flask-cors neo4j
```

# Instalación y ejecución
1. Clonar el repositorio.
   ```sh
   git clone https://github.com/Luis-Angel-G/Frontend-P2-Algoritmos.git
   cd sistema-recomendacion-videojuegos/backend
   ```

2. Crear entorno virtual
   ```sh
   python -m venv venv
   venv\Scripts\activate   # En Windows
   # o
   source venv/bin/activate  # En Linux/Mac
   ```

3. Instalar dependencias
   ```sh
   pip install -r requirements.txt
   ```
   O directamente:
   ```sh
   pip install flask flask-cors neo4j
   ```

4. Configurar conexión a Neo4J
   - Editar el archivo neo4j_driver.py con los datos de acceso:
     - uri = "bolt://localhost:7687"
     - user = "neo4j"
     - password = "tu_contraseña"

5. Ejecutar la API
   ```sh
   python main.py
   ```

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

# Lógica de recomendación

El sistema de recomendación utiliza la información de los juegos y usuarios almacenados en la base de datos Neo4j para sugerir videojuegos personalizados a cada usuario. El algoritmo funciona de la siguiente manera:

1. **Obtiene los juegos relacionados al usuario** (favoritos, jugados, interesados, no gustados) y asigna un peso a cada tipo de relación.
2. **Obtiene los amigos del usuario** y los juegos relacionados de cada amigo.
3. **Busca juegos no relacionados con el usuario** (candidatos a recomendar).
4. **Para cada juego candidato:**
   - Suma los pesos de las relaciones entre los juegos del usuario y el juego candidato, considerando características como género, plataforma, compañía, multijugador, duración y score.
   - Multiplica cada relación por el peso de la relación usuario-juego.
   - Suma los pesos de los juegos de los amigos si tienen relación directa con el juego candidato.
5. **Normaliza el score** dividiendo el peso total entre el peso máximo posible.
6. **Ordena los juegos candidatos** por score y selecciona el top 3.
7. **Crea una relación RECOMMENDED** entre el usuario y cada uno de los 3 juegos recomendados.

Esto permite recomendar juegos personalizados considerando tanto las preferencias directas del usuario como la influencia de sus amigos y las similitudes entre juegos.

Puedes consultar la implementación en el archivo `api/routes/recommendations.py`.

# ¿Cómo integrar este sistema como motor de recomendaciones en otras aplicaciones?

Este sistema puede ser utilizado como un motor de recomendaciones independiente para cualquier otra aplicación (web, móvil, escritorio) que requiera sugerencias personalizadas de videojuegos. Para integrarlo:

1. **Despliega la API** siguiendo los pasos de instalación y ejecución descritos arriba.
2. **Consume los endpoints REST** desde tu aplicación externa usando HTTP (por ejemplo, con `fetch` en JavaScript, `requests` en Python, o librerías similares en otros lenguajes).
3. **Endpoint principal para recomendaciones:**
   ```
   GET /api/v1/recommendations/top3/<correo>
   ```
   Donde `<correo>` es el correo del usuario para el que deseas obtener recomendaciones.

4. **Puedes crear, actualizar y consultar usuarios, juegos y relaciones** usando los demás endpoints documentados en este README.

De esta forma, puedes conectar tu frontend, app móvil o cualquier otro sistema a este backend y aprovechar su lógica de recomendación sin necesidad de modificar el código interno.