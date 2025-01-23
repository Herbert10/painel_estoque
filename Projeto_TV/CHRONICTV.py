from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# Diretórios das mídias
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, 'static', 'videos')
IMAGES_DIR = os.path.join(BASE_DIR, 'static', 'images')

@app.route('/')
def index():
    return render_template('index.html')

# Rota para servir os vídeos
@app.route('/videos/<path:filename>')
def videos(filename):
    return send_from_directory(VIDEOS_DIR, filename)

# Rota para servir as imagens
@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory(IMAGES_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
