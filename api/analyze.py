"""
Vercel Serverless Function - 手相解析API
BaseHTTPRequestHandler形式（Vercel互換）
Pillowのみ使用（numpyなし・250MB制限対策）
cgi非使用（Python 3.13互換）
"""

import base64
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler

# プロジェクトルートをパスに追加（image_processing をインポートするため）
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from analysis_service import analyze_image_bytes


def parse_multipart(body: bytes, content_type: str):
    """multipart/form-data を手動パース（cgi非依存）"""
    match = re.search(r'boundary=([^;\s]+)', content_type)
    if not match:
        return {}
    boundary = match.group(1).strip().encode()
    if boundary.startswith(b'"') and boundary.endswith(b'"'):
        boundary = boundary[1:-1]
    parts = body.split(b'--' + boundary)
    result = {}
    for part in parts:
        if not part or part.strip() in (b'', b'--'):
            continue
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            header_end = part.find(b'\n\n')
        if header_end == -1:
            continue
        headers = part[:header_end].decode('utf-8', errors='ignore')
        sep_len = 4 if part[header_end:header_end + 4] == b'\r\n\r\n' else 2
        content = part[header_end + sep_len:]
        if content.endswith(b'\r\n'):
            content = content[:-2]
        elif content.endswith(b'\n'):
            content = content[:-1]
        disp_match = re.search(r'name="([^"]+)"', headers)
        if not disp_match:
            continue
        name = disp_match.group(1)
        filename_match = re.search(r'filename="([^"]*)"', headers)
        if filename_match:
            result[name] = ('file', content)
        else:
            result[name] = ('field', content.decode('utf-8', errors='ignore'))
    return result

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def send_json(handler, data, status=200):
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        send_json(self, {'status': 'ok', 'message': '手相解析API'}, 200)

    def do_POST(self):
        try:
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0) or 0)

            if content_length <= 0:
                send_json(self, {'error': '画像が送信されていません'}, 400)
                return

            body = self.rfile.read(content_length)
            img_bytes = None

            if 'multipart/form-data' in content_type:
                form = parse_multipart(body, content_type)
                if 'image' in form:
                    kind, data = form['image']
                    if kind == 'file' and data:
                        img_bytes = data
                elif 'image_data' in form:
                    kind, image_data = form['image_data']
                    if image_data and ',' in image_data:
                        image_data = image_data.split(',')[1]
                    if image_data:
                        img_bytes = base64.b64decode(image_data)

            if img_bytes is None:
                send_json(self, {'error': '画像が送信されていません'}, 400)
                return

            result, err = analyze_image_bytes(img_bytes)
            if err:
                send_json(self, {'error': err}, 400)
                return

            send_json(self, result, 200)

        except Exception as e:
            send_json(self, {'error': str(e)}, 500)
