"""
Vercel Serverless Function - 手相解析API
BaseHTTPRequestHandler形式（Vercel互換）
Pillowのみ使用（numpyなし・250MB制限対策）
cgi非使用（Python 3.13互換）
"""

import io
import base64
import json
import re
from http.server import BaseHTTPRequestHandler
from PIL import Image, ImageFilter, ImageEnhance


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
        content = part[header_end + 4:].rstrip(b'\r\n')
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


def load_image(img_bytes):
    try:
        return Image.open(io.BytesIO(img_bytes)).convert('RGB')
    except Exception:
        return None


def resize_if_needed(img, max_size=800):
    w, h = img.size
    if max(h, w) <= max_size:
        return img
    scale = max_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def detect_palm_lines(img):
    gray = img.convert('L')
    enhanced = ImageEnhance.Contrast(gray).enhance(1.8)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.5)

    results = []
    for blur_radius in [1, 2]:
        blurred = enhanced.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        edges = blurred.filter(ImageFilter.FIND_EDGES)
        edges = ImageEnhance.Contrast(edges).enhance(2.0)
        edges_binary = edges.point(lambda x: 255 if x > 80 else 0, mode='L')
        line_count = sum(1 for p in edges_binary.getdata() if p > 0)
        results.append((edges_binary, line_count))

    results.sort(key=lambda x: abs(x[1] - 5000))
    return results[0][0], enhanced


def analyze_line_characteristics(edges_img):
    w, h = edges_img.size
    regions = [
        ('heart_zone', 0, 0, w, int(h*0.35)),
        ('marriage_zone', int(w*0.65), 0, w, int(h*0.25)),
        ('head_zone', 0, int(h*0.35), w, int(h*0.55)),
        ('life_zone', 0, 0, int(w*0.35), h),
        ('fate_zone', int(w*0.35), 0, int(w*0.65), h),
        ('sun_zone', int(w*0.5), int(h*0.2), int(w*0.8), int(h*0.6)),
        ('money_zone', int(w*0.25), int(h*0.4), int(w*0.6), int(h*0.8)),
        ('health_zone', int(w*0.3), int(h*0.5), int(w*0.55), h),
        ('intuition_zone', int(w*0.55), int(h*0.55), w, h),
    ]
    analysis = {}
    for name, left, upper, right, lower in regions:
        if right <= left or lower <= upper:
            analysis[name] = 50
            continue
        crop = edges_img.crop((left, upper, right, lower))
        cw, ch = crop.size
        total = cw * ch
        if total == 0:
            analysis[name] = 50
            continue
        count = sum(1 for p in crop.getdata() if p > 0)
        density = count / total * 100
        analysis[name] = min(100, density * 10)
    return analysis


def get_palm_reading_interpretation(analysis):
    interpretations = []
    def add(line, cat, high, mid, low, score):
        if score > 70:
            interpretations.append({'line': line, 'category': cat, 'reading': high, 'score': score})
        elif score > 40:
            interpretations.append({'line': line, 'category': cat, 'reading': mid, 'score': score})
        else:
            interpretations.append({'line': line, 'category': cat, 'reading': low, 'score': score})

    add('感情線', 'love_marriage',
        '感情が豊かで、恋愛運に恵まれています。愛情表現が上手く、相手に尽くすタイプ。情熱的でロマンチックな恋愛を好み、周囲からも慕われやすいでしょう。',
        'バランスの取れた恋愛観の持ち主。理性的でありながら、適度な情熱も兼ね備えています。相手を大切にし、安定した関係を築く傾向があります。',
        '控えめで慎重な性格。感情を表に出すより、内に秘める傾向があります。一度心を許した相手には深い愛情を注ぎ、長く続く絆を大切にします。',
        analysis.get('heart_zone', 50))
    add('結婚線', 'love_marriage',
        '結婚運が強い方です。良縁に恵まれ、パートナーとの絆が深まりやすい傾向があります。家庭を大切にし、長く続く関係を築けるでしょう。',
        '結婚に対して真摯な気持ちを持っています。相手を選ぶ目があり、慎重に考えた末に良いパートナーと結ばれる傾向があります。',
        '自由な恋愛観の持ち主。結婚は人生の選択肢の一つとして、焦らず自分らしいタイミングで考える傾向があります。',
        analysis.get('marriage_zone', 50))
    add('知能線', 'intelligence',
        '知的好奇心が旺盛で、学習意欲が高い方です。論理的思考に優れ、問題解決能力に長けています。',
        'バランスの取れた思考力を持っています。直感と論理の両方を活用できる柔軟な頭脳の持ち主です。',
        '実践的で行動派。考えるより先に動くタイプ。経験から学ぶことが得意です。',
        analysis.get('head_zone', 50))
    add('生命線', 'health',
        '生命力が強く、健康運に恵まれています。活力に満ち、困難にも立ち向かう力があります。',
        '安定した生命力。規則正しい生活を心がけることで、長く健康を維持できるでしょう。',
        '繊細な体質。休息とリフレッシュを大切にすることで、持てる力を最大限発揮できます。',
        analysis.get('life_zone', 50))
    add('運命線', 'work_success',
        'キャリア運が強い方。運命に導かれる力があり、チャンスを掴む才能があります。努力が実を結びやすいでしょう。',
        '自分で道を切り開く力があります。努力次第でキャリアを好転させられるタイプです。',
        '自由な精神の持ち主。型にはまらない生き方を好み、独自の道を歩む傾向があります。',
        analysis.get('fate_zone', 50))
    add('太陽線', 'work_success',
        '成功運・名声運に恵まれています。才能が開花しやすく、人から認められやすい傾向。芸術や創造の分野でも花開く可能性があります。',
        '努力が報われやすいタイプ。地道な積み重ねが評価につながり、着実に成功に近づいていけるでしょう。',
        '内なる才能を秘めています。自分を表現する機会を大切にすると、隠れた能力が発揮されるでしょう。',
        analysis.get('sun_zone', 50))
    add('金運線', 'money',
        '金運に恵まれる傾向があります。お金が入るチャンスに恵まれ、貯蓄や投資のセンスもあるでしょう。',
        '堅実な金銭感覚の持ち主。計画的に貯めることが得意で、安定した財産形成が期待できます。',
        'お金より心の豊かさを大切にする傾向。必要な時に必要な分が入ってくる、流れに任せるタイプです。',
        analysis.get('money_zone', 50))
    add('健康線', 'health',
        '体のバランスが良く、自己治癒力が高い傾向。健康管理への意識が高く、長く元気でいられるでしょう。',
        '体調の波はありますが、休息を取れば回復するタイプ。無理をしすぎないことが長く健康でいる秘訣です。',
        '繊細な体質。睡眠や食事を大切にし、ストレスを溜め込まない生活がおすすめです。',
        analysis.get('health_zone', 50))
    add('直感線', 'intuition',
        '直感力・第六感が鋭い方。ひらめきに恵まれ、スピリチュアルな感覚にも敏感。芸術やヒーリングの才能があるかもしれません。',
        '時々「なんとなく」で正解を導くことがあります。自分の感覚を信じることで、より良い選択ができるでしょう。',
        '論理や経験を大切にするタイプ。直感を磨くには、静かに自分と向き合う時間を持つと良いでしょう。',
        analysis.get('intuition_zone', 50))
    return interpretations


def create_visualization(img, edges):
    green = Image.new('RGB', img.size, (0, 200, 100))
    black = Image.new('RGB', img.size, (0, 0, 0))
    mask = edges.point(lambda x: 255 if x > 0 else 0, mode='1')
    overlay = Image.composite(green, black, mask)
    return Image.blend(img, overlay, 0.3)


def encode_image_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def send_json(handler, data, status=200):
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))


def process_analyze(img_bytes):
    img = load_image(img_bytes)
    if img is None or 0 in img.size:
        return None, '画像の読み込みに失敗しました'
    img = resize_if_needed(img)
    edges, _ = detect_palm_lines(img)
    analysis = analyze_line_characteristics(edges)
    interpretations = get_palm_reading_interpretation(analysis)
    visualization = create_visualization(img, edges)
    viz_base64 = encode_image_to_base64(visualization)
    edges_base64 = encode_image_to_base64(edges)
    categories = [
        {'id': 'love_marriage', 'name': '恋愛・結婚', 'icon': '💕'},
        {'id': 'work_success', 'name': '仕事・成功', 'icon': '💼'},
        {'id': 'money', 'name': '金運・財産', 'icon': '💰'},
        {'id': 'health', 'name': '健康・生命力', 'icon': '💪'},
        {'id': 'intelligence', 'name': '知性・才能', 'icon': '📚'},
        {'id': 'intuition', 'name': '直感・スピリチュアル', 'icon': '✨'},
    ]
    return {
        'success': True,
        'interpretations': interpretations,
        'categories': categories,
        'analysis': analysis,
        'visualization': f'data:image/png;base64,{viz_base64}',
        'edges_image': f'data:image/png;base64,{edges_base64}',
    }, None


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

            result, err = process_analyze(img_bytes)
            if err:
                send_json(self, {'error': err}, 400)
                return

            send_json(self, result, 200)

        except Exception as e:
            send_json(self, {'error': str(e)}, 500)
