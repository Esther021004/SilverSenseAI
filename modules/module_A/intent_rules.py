INTENT_PATTERNS = [
    ("traffic_accident", [
        "교통사고", "차에치", "차가치", "버스사고", "오토바이사고",
        "접촉사고", "추돌사고",
    ]),

    ("fire", [
        "불이났", "불났", "화재", "연기가", "타는냄새", "불붙었",
    ]),

    ("cardiac_arrest", [
        "심정지", "심장이안뛰", "맥이안뛰", "호흡이없", 
        "숨을안쉬", "숨이멎",
    ]),

    ("breathing_difficulty", [
        "숨이안쉬", "숨막혀", "숨쉬기힘들", "숨을못쉬",
        "호흡곤란", "숨이가빠",
    ]),

    ("chest_pain", [
        "가슴이아파", "가슴아파", "흉통", "가슴답답",
    ]),

    ("unconscious", [
        "의식이없", "기절했", "반응이없", "안깨", "눈을안떠",
    ]),

    ("seizure", [
        "경련", "발작", "간질", "몸이떨", "거품",
    ]),

    ("falling", [
        "넘어졌", "미끄러졌", "떨어졌", "낙상", "계단에서굴",
    ]),

    ("bleeding", [
        "피가나", "출혈", "피가많이", "피가안멈춰",
    ]),

    ("dizziness", [
        "어지러", "현기증", "빙빙돈", "머리가핑",
    ]),

    ("assault", [
        "맞았", "폭행", "싸우다가", "칼에", "흉기에",
    ]),
]


def map_intent(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)

    t = text.replace(" ", "")
    for intent, keywords in INTENT_PATTERNS:
        for kw in keywords:
            if kw.replace(" ", "") in t:
                return intent

    return "unknown"
