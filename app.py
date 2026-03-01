"""
手相解析アプリ - 鮮明で正確な手相分析
Flask + Pillow による画像処理（Vercel互換）
"""

import os
import base64
from flask import Flask, request, jsonify, send_from_directory

from image_processing import (
    load_image,
    resize_if_needed,
    detect_palm_lines,
    analyze_line_characteristics,
    create_visualization,
    encode_image_to_base64,
)
from palm_interpretation import get_palm_reading_interpretation

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
        
        img = load_image(img_bytes)
        if img is None or 0 in img.size:
            return jsonify({'error': '画像の読み込みに失敗しました'}), 400
        
        img = resize_if_needed(img)
        
        # 手相解析
        edges, enhanced = detect_palm_lines(img)
        analysis = analyze_line_characteristics(edges)
        interpretations = get_palm_reading_interpretation(analysis)
        
        # ビジュアル画像生成
        visualization = create_visualization(img, edges)
        viz_base64 = encode_image_to_base64(visualization)
        edges_base64 = encode_image_to_base64(edges)
        
        # カテゴリ一覧（見たい分野を選べるように）
        categories = [
            {'id': 'love_marriage', 'name': '恋愛・結婚', 'icon': '💕'},
            {'id': 'work_success', 'name': '仕事・成功', 'icon': '💼'},
            {'id': 'money', 'name': '金運・財産', 'icon': '💰'},
            {'id': 'health', 'name': '健康・生命力', 'icon': '💪'},
            {'id': 'intelligence', 'name': '知性・才能', 'icon': '📚'},
            {'id': 'intuition', 'name': '直感・スピリチュアル', 'icon': '✨'},
        ]
        
        return jsonify({
            'success': True,
            'interpretations': interpretations,
            'categories': categories,
            'analysis': analysis,
            'visualization': f'data:image/png;base64,{viz_base64}',
            'edges_image': f'data:image/png;base64,{edges_base64}',
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
