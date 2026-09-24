"""
手相解析 - 画像処理（Pillow版・numpyなし）
"""

import io
import base64
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageStat


def load_image(img_bytes):
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img = ImageOps.exif_transpose(img)
        return img.convert('RGB')
    except Exception:
        return None


def count_lit_pixels(gray_img):
    hist = gray_img.histogram()
    return sum(hist[1:]) if hist else 0


def assess_palm_presence(img):
    """肌色の割合から、手のひらが写っていそうかを見る。"""
    sample = img.resize((96, 96), Image.Resampling.BILINEAR)
    pixels = list(sample.getdata())
    skin = 0
    for r, g, b in pixels:
        if r < 70 or g < 35 or b > 210:
            continue
        if r > g >= b * 0.65 and (r - b) > 12 and (r - g) < 90:
            skin += 1
    ratio = skin / max(len(pixels), 1)
    likely = ratio >= 0.16
    return {
        'likely_palm': likely,
        'skin_ratio': round(ratio * 100, 1),
        'message': (
            '手のひらとして解析しました。'
            if likely else
            '手のひらがはっきり写っていない可能性があります。明るい場所で、手のひら全体を近づけて撮り直すと精度が上がります。'
        ),
    }


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
    gray = ImageOps.equalize(gray)
    enhanced = ImageEnhance.Contrast(gray).enhance(2.2)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)
    enhanced = enhanced.filter(ImageFilter.EDGE_ENHANCE)
    w, h = enhanced.size
    target = max(4000, int(w * h * 0.045))
    results = []
    for blur_radius, threshold in ((1.2, 28), (1.8, 22), (2.4, 18)):
        blurred = enhanced.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        edges = blurred.filter(ImageFilter.FIND_EDGES)
        edges = ImageEnhance.Contrast(edges).enhance(3.4)
        edges_binary = edges.point(lambda x, t=threshold: 255 if x > t else 0, mode='L')
        edges_binary = edges_binary.filter(ImageFilter.MaxFilter(3))
        line_count = count_lit_pixels(edges_binary)
        results.append((edges_binary, line_count))
    results.sort(key=lambda x: abs(x[1] - target))
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
        count = count_lit_pixels(crop)
        density = count / total * 100
        # エッジ密度が低くても飽和しないよう、緩やかに 12〜92 へ写す
        score = 100 * (1 - pow(2.718281828, -density / 7.5))
        analysis[name] = round(min(92, max(12, score)), 1)
    return analysis


def create_visualization(img, edges):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    # 元写真の上に検出線を重ねる（元写真はそのまま見えるように）
    line_color = (0, 255, 220)
    line_layer = Image.new('RGB', img.size, line_color)
    mask = edges.point(lambda x: 255 if x > 0 else 0, mode='1')
    # 線の部分だけシアンを重ね、それ以外は元画像を表示
    return Image.composite(line_layer, img, mask)


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
