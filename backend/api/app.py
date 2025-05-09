from flask import Flask
from routes.videogames import videogames_bp

app = Flask(__name__)
app.register_blueprint(videogames_bp, url_prefix='/api/v1')

if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5050)
