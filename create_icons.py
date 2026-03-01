"""
手相解析アプリ用アイコン生成
✋ 手のひらをモチーフ（index.htmlのロゴと統一）
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size):
    bg = (26, 22, 20)           # #1a1614 ダークブラウン
    hand = (232, 212, 138)      # #e8d48a 明るいゴールド（手）
    gold = (201, 162, 39)       # #c9a227 ゴールド（枠・アクセント）
    outline = (139, 115, 85)    # #8b7355 縁取り
    
    img = Image.new('RGB', (size, size), bg)
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    
    # ✋ を絵文字フォントで描画
    font_size = int(size * 0.7)
    emoji_rendered = False
    
    for font_path in [
        "C:/Windows/Fonts/seguiemj.ttf",
        "C:/Windows/Fonts/SegoeUIEmoji.ttf",
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                bbox = draw.textbbox((0, 0), "✋", font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                x = (size - tw) // 2 - bbox[0]
                y = (size - th) // 2 - bbox[1] - int(size * 0.03)
                try:
                    draw.text((x, y), "✋", font=font, fill=hand, embedded_color=True)
                except TypeError:
                    draw.text((x, y), "✋", font=font, fill=hand)
                emoji_rendered = True
                break
            except Exception:
                continue
    
    if not emoji_rendered:
        # フォントがない場合：✋の形を楕円で表現（手のひら+5本の指）
        # 手のひら（下側・横長の楕円）
        palm_w, palm_h = int(size * 0.5), int(size * 0.25)
        palm_y = cy + int(size * 0.1)
        draw.ellipse([cx - palm_w, palm_y - palm_h, cx + palm_w, palm_y + palm_h],
                     fill=hand, outline=outline)
        # 5本の指（上向き、弧状に配置）
        finger_centers = [
            (cx - int(size * 0.32), cy - int(size * 0.15)),
            (cx - int(size * 0.16), cy - int(size * 0.22)),
            (cx, cy - int(size * 0.25)),  # 中指
            (cx + int(size * 0.16), cy - int(size * 0.22)),
            (cx + int(size * 0.32), cy - int(size * 0.15)),
        ]
        fw, fh = int(size * 0.14), int(size * 0.22)
        for fx, fy in finger_centers:
            draw.ellipse([fx - fw//2, fy, fx + fw//2, fy + fh], fill=hand, outline=outline)
        # 指の付け根をつなぐ
        draw.ellipse([cx - int(size * 0.2), cy - int(size * 0.08), 
                      cx + int(size * 0.2), cy + int(size * 0.08)], fill=hand, outline=outline)
    
    # 外枠
    margin = size // 12
    draw.ellipse([margin, margin, size - margin, size - margin], 
                 fill=None, outline=gold, width=max(2, size // 48))
    
    return img

if __name__ == '__main__':
    for sz, name in [(192, 'icon-192.png'), (512, 'icon-512.png')]:
        icon = create_icon(sz)
        icon.save(f'public/{name}')
        print(f'Created public/{name}')
