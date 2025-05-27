from flask import Flask
from flask_cors import CORS
from routes.videogames import videogames_bp
from routes.recommendations import recommendations_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(videogames_bp, url_prefix='/api/v1')
app.register_blueprint(recommendations_bp, url_prefix='/api/v1')

if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5050)
