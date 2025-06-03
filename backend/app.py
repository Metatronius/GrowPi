from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='../frontend/dist')
CORS(app)

@app.route('/api/status')
def status():
    return jsonify({"temperature": 68, "humidity": 55})

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), path)

@app.route('/favicon.ico')
def serve_favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

@app.route('/meters')

@app.route('/controls')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
