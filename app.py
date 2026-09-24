"""
手相解析アプリ - 鮮明で正確な手相分析
Flask + Pillow による画像処理（Vercel互換）
"""

import os
import base64
from flask import Flask, request, jsonify, send_from_directory

from analysis_service import analyze_image_bytes

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


@app.route('/manifest.json')
def manifest():
    return send_from_directory('public', 'manifest.json')


@app.route('/sw.js')
def service_worker():
    return send_from_directory('public', 'sw.js'), 200, {
        'Content-Type': 'application/javascript',
        'Service-Worker-Allowed': '/'
    }


@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files and 'image_data' not in request.form:
        return jsonify({'error': '画像が送信されていません'}), 400
    
    try:
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'ファイルが選択されていません'}), 400
            if not allowed_file(file.filename):
                return jsonify({'error': '許可されていないファイル形式です（png, jpg, jpeg, webp）'}), 400
            
            img_bytes = file.read()
        else:
            image_data = request.form['image_data']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            img_bytes = base64.b64decode(image_data)
        
        result, err = analyze_image_bytes(img_bytes)
        if err:
            return jsonify({'error': err}), 400
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
