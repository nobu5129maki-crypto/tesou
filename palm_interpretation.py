"""手相解釈ロジック（app.pyとapi/analyze.pyで共有）"""


def get_palm_reading_interpretation(analysis):
    """伝統的手相学に基づく解釈（カテゴリ付き）"""
    interpretations = []
    
    def add_interpretation(line, category, high_reading, mid_reading, low_reading, score):
        if score > 70:
            interpretations.append({'line': line, 'category': category, 'reading': high_reading, 'score': score})
        elif score > 40:
            interpretations.append({'line': line, 'category': category, 'reading': mid_reading, 'score': score})
        else:
            interpretations.append({'line': line, 'category': category, 'reading': low_reading, 'score': score})
    
    add_interpretation('感情線', 'love_marriage',
        '感情が豊かで、恋愛運に恵まれています。愛情表現が上手く、相手に尽くすタイプ。情熱的でロマンチックな恋愛を好み、周囲からも慕われやすいでしょう。',
        'バランスの取れた恋愛観の持ち主。理性的でありながら、適度な情熱も兼ね備えています。相手を大切にし、安定した関係を築く傾向があります。',
        '控えめで慎重な性格。感情を表に出すより、内に秘める傾向があります。一度心を許した相手には深い愛情を注ぎ、長く続く絆を大切にします。',
        analysis.get('heart_zone', 50))
    
    add_interpretation('結婚線', 'love_marriage',
        '結婚運が強い方です。良縁に恵まれ、パートナーとの絆が深まりやすい傾向があります。家庭を大切にし、長く続く関係を築けるでしょう。',
        '結婚に対して真摯な気持ちを持っています。相手を選ぶ目があり、慎重に考えた末に良いパートナーと結ばれる傾向があります。',
        '自由な恋愛観の持ち主。結婚は人生の選択肢の一つとして、焦らず自分らしいタイミングで考える傾向があります。',
        analysis.get('marriage_zone', 50))
    
    add_interpretation('知能線', 'intelligence',
        '知的好奇心が旺盛で、学習意欲が高い方です。論理的思考に優れ、問題解決能力に長けています。',
        'バランスの取れた思考力を持っています。直感と論理の両方を活用できる柔軟な頭脳の持ち主です。',
        '実践的で行動派。考えるより先に動くタイプ。経験から学ぶことが得意です。',
        analysis.get('head_zone', 50))
    
    add_interpretation('生命線', 'health',
        '生命力が強く、健康運に恵まれています。活力に満ち、困難にも立ち向かう力があります。',
        '安定した生命力。規則正しい生活を心がけることで、長く健康を維持できるでしょう。',
        '繊細な体質。休息とリフレッシュを大切にすることで、持てる力を最大限発揮できます。',
        analysis.get('life_zone', 50))
    
    add_interpretation('運命線', 'work_success',
        'キャリア運が強い方。運命に導かれる力があり、チャンスを掴む才能があります。努力が実を結びやすいでしょう。',
        '自分で道を切り開く力があります。努力次第でキャリアを好転させられるタイプです。',
        '自由な精神の持ち主。型にはまらない生き方を好み、独自の道を歩む傾向があります。',
        analysis.get('fate_zone', 50))
    
    add_interpretation('太陽線', 'work_success',
        '成功運・名声運に恵まれています。才能が開花しやすく、人から認められやすい傾向。芸術や創造の分野でも花開く可能性があります。',
        '努力が報われやすいタイプ。地道な積み重ねが評価につながり、着実に成功に近づいていけるでしょう。',
        '内なる才能を秘めています。自分を表現する機会を大切にすると、隠れた能力が発揮されるでしょう。',
        analysis.get('sun_zone', 50))
    
    add_interpretation('金運線', 'money',
        '金運に恵まれる傾向があります。お金が入るチャンスに恵まれ、貯蓄や投資のセンスもあるでしょう。',
        '堅実な金銭感覚の持ち主。計画的に貯めることが得意で、安定した財産形成が期待できます。',
        'お金より心の豊かさを大切にする傾向。必要な時に必要な分が入ってくる、流れに任せるタイプです。',
        analysis.get('money_zone', 50))
    
    add_interpretation('健康線', 'health',
        '体のバランスが良く、自己治癒力が高い傾向。健康管理への意識が高く、長く元気でいられるでしょう。',
        '体調の波はありますが、休息を取れば回復するタイプ。無理をしすぎないことが長く健康でいる秘訣です。',
        '繊細な体質。睡眠や食事を大切にし、ストレスを溜め込まない生活がおすすめです。',
        analysis.get('health_zone', 50))
    
    add_interpretation('直感線', 'intuition',
        '直感力・第六感が鋭い方。ひらめきに恵まれ、スピリチュアルな感覚にも敏感。芸術やヒーリングの才能があるかもしれません。',
        '時々「なんとなく」で正解を導くことがあります。自分の感覚を信じることで、より良い選択ができるでしょう。',
        '論理や経験を大切にするタイプ。直感を磨くには、静かに自分と向き合う時間を持つと良いでしょう。',
        analysis.get('intuition_zone', 50))
    
    return interpretations
