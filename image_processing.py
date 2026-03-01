"""
手相解析 - 画像処理（Pillow版・numpyなし）
"""

import io
import base64
from PIL import Image, ImageFilter, ImageEnhance


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
    enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.5)
    results = []
    for blur_radius in [1, 2]:
        blurred = enhanced.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        edges = blurred.filter(ImageFilter.FIND_EDGES)
        edges = ImageEnhance.Contrast(edges).enhance(5.0)
        edges_binary = edges.point(lambda x: 255 if x > 15 else 0, mode='L')
        edges_binary = edges_binary.filter(ImageFilter.MaxFilter(5))
        edges_binary = edges_binary.filter(ImageFilter.MaxFilter(5))
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


def create_visualization(img, edges):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    green = Image.new('RGB', img.size, (0, 255, 80))
    black = Image.new('RGB', img.size, (0, 0, 0))
    mask = edges.point(lambda x: 255 if x > 0 else 0, mode='1')
    overlay = Image.composite(green, black, mask)
    return Image.blend(img, overlay, 0.65)


def edges_to_visible_display(edges):
    """検出された線を明るい緑で表示用に変換"""
    rgb = Image.new('RGB', edges.size, (20, 18, 16))
    green = Image.new('RGB', edges.size, (0, 255, 100))
    mask = edges.point(lambda x: 255 if x > 0 else 0, mode='1')
    return Image.composite(green, rgb, mask)


def encode_image_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
