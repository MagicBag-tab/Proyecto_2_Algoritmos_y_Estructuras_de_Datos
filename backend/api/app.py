from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.videogames import videogames_bp
from routes.recommendations import recommendations_bp
from init_db import initialize_database

app = Flask(__name__)
CORS(app)
app.register_blueprint(videogames_bp, url_prefix='/api/v1')
app.register_blueprint(recommendations_bp, url_prefix='/api/v1')

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True, host="127.0.0.1", port=5050)