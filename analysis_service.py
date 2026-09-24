"""手相解析の共通処理（Flask / Vercel の両方から利用）"""

from image_processing import (
    load_image,
    resize_if_needed,
    assess_lighting,
    assess_palm_presence,
    detect_palm_lines,
    analyze_line_characteristics,
    create_visualization,
    edges_to_visible_display,
    encode_image_to_base64,
)
from palm_interpretation import get_palm_reading_interpretation

CATEGORIES = [
    {'id': 'love_marriage', 'name': '恋愛・結婚', 'icon': '💕'},
    {'id': 'work_success', 'name': '仕事・成功', 'icon': '💼'},
    {'id': 'money', 'name': '金運・財産', 'icon': '💰'},
    {'id': 'health', 'name': '健康・生命力', 'icon': '💪'},
    {'id': 'intelligence', 'name': '知性・才能', 'icon': '📚'},
    {'id': 'intuition', 'name': '直感・スピリチュアル', 'icon': '✨'},
]


def analyze_image_bytes(img_bytes):
    img = load_image(img_bytes)
    if img is None or 0 in img.size:
        return None, '画像の読み込みに失敗しました'

    img = resize_if_needed(img)
    lighting = assess_lighting(img)
    palm = assess_palm_presence(img)
    edges, _ = detect_palm_lines(img)
    analysis = analyze_line_characteristics(edges)
    interpretations = get_palm_reading_interpretation(analysis)
    visualization = create_visualization(img, edges)
    viz_base64 = encode_image_to_base64(visualization)
    edges_display = edges_to_visible_display(edges)
    edges_base64 = encode_image_to_base64(edges_display)

    return {
        'success': True,
        'interpretations': interpretations,
        'categories': CATEGORIES,
        'analysis': analysis,
        'lighting': lighting,
        'palm': palm,
        'visualization': f'data:image/png;base64,{viz_base64}',
        'edges_image': f'data:image/png;base64,{edges_base64}',
    }, None
