EMOTION_KEYWORDS = {
    "笑": ["笑", "微笑", "轻笑", "莞尔", "嘴角上扬"],
    "悲": ["悲", "流泪", "落泪", "哭", "抽泣", "哽咽", "泪"],
    "怒": ["怒", "生气", "恼怒", "皱眉", "火大", "发火", "气"],
}


def detect_emotion(text):
    if not text:
        return None
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return emotion
    return None
