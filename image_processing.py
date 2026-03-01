"""
手相解析 - 画像処理（Pillow版・numpyなし）
"""

import io
import base64
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageStat


def load_image(img_bytes):
    try:
        return Image.open(io.BytesIO(img_bytes)).convert('RGB')
    except Exception:
        return None


def resize_if_needed(img, max_size=1000):
    w, h = img.size
    if max(h, w) <= max_size:
        return img
    scale = max_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def assess_lighting(img):
    """
    画像の照明度を評価する（補正前の元画像で判定）
    戻り値: { status, message, brightness }
    """
    gray = img.convert('L')
    stat = ImageStat.Stat(gray)
    mean_brightness = stat.mean[0]

    if mean_brightness < 60:
        return {
            'status': 'too_dark',
            'message': '照明が不足しています。明るい場所でもう一度撮影することをおすすめします。',
            'brightness': round(mean_brightness, 1),
        }
    if mean_brightness < 90:
        return {
            'status': 'dark',
            'message': 'やや暗めです。もう少し明るい場所で撮影すると、より正確に解析できます。',
            'brightness': round(mean_brightness, 1),
        }
    if mean_brightness > 220:
        return {
            'status': 'too_bright',
            'message': '明るすぎます。直射日光や強い光を避け、柔らかい光で撮影してみてください。',
            'brightness': round(mean_brightness, 1),
        }
    if mean_brightness > 180:
        return {
            'status': 'bright',
            'message': 'やや明るめです。解析は可能ですが、少し暗めの環境だとより良い結果が出る場合があります。',
            'brightness': round(mean_brightness, 1),
        }
    if 100 <= mean_brightness <= 160:
        return {
            'status': 'good',
            'message': '照明は適切です。手相の線がはっきり検出しやすい条件です。',
            'brightness': round(mean_brightness, 1),
        }
    return {
        'status': 'ok',
        'message': '照明は問題ありません。解析できます。',
        'brightness': round(mean_brightness, 1),
    }


def preprocess_for_lighting(img):
    """照明条件に合わせて画像を補正（暗い・コントラスト不足に対応）"""
    img = img.convert('RGB')
    gray = img.convert('L')
    stat = ImageStat.Stat(gray)
    mean_brightness = stat.mean[0]
    # 暗い画像は明るさを上げる
    if mean_brightness < 80:
        factor = 100 / max(mean_brightness, 20)
        img = ImageEnhance.Brightness(img).enhance(min(factor, 2.5))
    elif mean_brightness > 180:
        factor = 140 / mean_brightness
        img = ImageEnhance.Brightness(img).enhance(max(factor, 0.6))
    # コントラストを自動補正
    r, g, b = img.split()
    r = ImageOps.autocontrast(r, cutoff=2)
    g = ImageOps.autocontrast(g, cutoff=2)
    b = ImageOps.autocontrast(b, cutoff=2)
    return Image.merge('RGB', (r, g, b))


def detect_palm_lines(img):
    img = preprocess_for_lighting(img)
    gray = img.convert('L')
    # ヒストグラム均等化でしわ・線のコントラストを強調
    gray = ImageOps.equalize(gray)
    enhanced = ImageEnhance.Contrast(gray).enhance(3.0)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(3.0)
    # エッジ強調フィルタで線をはっきりさせる
    enhanced = enhanced.filter(ImageFilter.EDGE_ENHANCE_MORE)
    results = []
    for blur_radius in [1, 2, 3]:
        blurred = enhanced.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        edges = blurred.filter(ImageFilter.FIND_EDGES)
        edges = ImageEnhance.Contrast(edges).enhance(6.0)
        # 閾値でノイズを抑えつつ線を検出（低すぎると塊になる）
        edges_binary = edges.point(lambda x: 255 if x > 12 else 0, mode='L')
        # 線を適度に太く（強くしすぎると塊になって見えなくなる）
        edges_binary = edges_binary.filter(ImageFilter.MaxFilter(5))
        line_count = sum(1 for p in edges_binary.getdata() if p > 0)
        results.append((edges_binary, line_count))
    results.sort(key=lambda x: abs(x[1] - 6000))
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


def create_visualization(img, edges):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    # 明るいシアンで線をはっきり表示（肌色との対比が強い）
    line_color = (0, 255, 220)
    black = Image.new('RGB', img.size, (0, 0, 0))
    mask = edges.point(lambda x: 255 if x > 0 else 0, mode='1')
    overlay = Image.composite(
        Image.new('RGB', img.size, line_color), black, mask
    )
    return Image.blend(img, overlay, 0.78)


def edges_to_visible_display(edges):
    """検出された線をはっきり見える色で表示用に変換"""
    dark_bg = Image.new('RGB', edges.size, (15, 15, 18))
    bright_line = Image.new('RGB', edges.size, (0, 255, 220))
    mask = edges.point(lambda x: 255 if x > 0 else 0, mode='1')
    return Image.composite(bright_line, dark_bg, mask)


def encode_image_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
