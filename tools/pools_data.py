# -*- coding: utf-8 -*-
# 奖池数据表（100 祝福 + 100 诅咒）。生成器：tools/gen_pools.py。
# 权威文档 docs/blessing-curse-pools.md 由 gen_pools.py 从本表导出，勿手改。
#
# 条目格式：
#   数值家族: (rarity, family, magnitude, {lang: name})
#     code 与效果摘要由 family 模板生成（见 SUM_T）。
#   特质/修正/传说: (rarity, "custom", code, {lang: name}, {lang: summary})
#     code = 完整 effect 片段；summary = loc 括号内文本（9 语言各写）。
# rarity: "c" 普通(权重10) / "r" 稀有(权重3) / "l" 传说(权重1)

LANGS = ["simp_chinese", "english", "french", "german", "japanese", "korean", "polish", "russian", "spanish"]


def N(zh, en, fr, de, ja, ko, pl, ru, es):
    return dict(zip(LANGS, (zh, en, fr, de, ja, ko, pl, ru, es)))


# ---------- 效果摘要模板：SUM_T[family][lang] = 函数或带 {v} 的格式串 ----------
def _t(d):
    return {fam: {lang: (tpl if callable(tpl) else (lambda v, _t=tpl: _t.format(v=v))) for lang, tpl in langs.items()} for fam, langs in d.items()}


SUM_T = _t({
    "gold": {
        "simp_chinese": "{v} 金币", "english": "{v} gold", "french": "{v} or", "german": "{v} Gold",
        "japanese": "{v} ゴールド", "korean": "{v} 골드", "polish": "{v} złota", "russian": "{v} золота", "spanish": "{v} oro",
    },
    "prestige": {
        "simp_chinese": "{v} 威望", "english": "{v} prestige", "french": "{v} prestige", "german": "{v} Prestige",
        "japanese": "{v} 威望", "korean": "{v} 위상", "polish": "{v} prestiżu", "russian": "{v} престижа", "spanish": "{v} prestigio",
    },
    "piety": {
        "simp_chinese": "{v} 虔诚", "english": "{v} piety", "french": "{v} piété", "german": "{v} Frömmigkeit",
        "japanese": "{v} 信心", "korean": "{v} 경건", "polish": "{v} pobożności", "russian": "{v} благочестия", "spanish": "{v} piedad",
    },
    "influence": {
        "simp_chinese": "{v} 影响力", "english": "{v} influence", "french": "{v} influence", "german": "{v} Einfluss",
        "japanese": "{v} 影響力", "korean": "{v} 영향력", "polish": "{v} wpływów", "russian": "{v} влияния", "spanish": "{v} influencia",
    },
    "skill": {
        "simp_chinese": "{v} 属性", "english": "{v} skill", "french": "{v} compétence", "german": "{v} Fähigkeit",
        "japanese": "{v} 能力値", "korean": "{v} 능력치", "polish": "{v} atrybutu", "russian": "{v} к навыку", "spanish": "{v} atributo",
    },
    "xp": {
        "simp_chinese": "{v} 生活方式经验", "english": "{v} lifestyle XP", "french": "{v} XP de style de vie", "german": "{v} Lebensstil-EP",
        "japanese": "{v} ライフスタイル経験値", "korean": "{v} 생활 방식 경험치", "polish": "{v} PD stylu życia", "russian": "{v} ед. опыта образа жизни", "spanish": "{v} EXP de estilo de vida",
    },
    "dynasty": {
        "simp_chinese": "{v} 宗族威望", "english": "{v} renown", "french": "{v} renom", "german": "{v} Renommee",
        "japanese": "{v} 一族の名声", "korean": "{v} 왕조 명성", "polish": "{v} renomy", "russian": "{v} известности", "spanish": "{v} renombre",
    },
    "stress_b": {
        "simp_chinese": "{v} 压力", "english": "{v} stress", "french": "{v} stress", "german": "{v} Stress",
        "japanese": "{v} ストレス", "korean": "{v} 스트레스", "polish": "{v} stresu", "russian": "{v} стресса", "spanish": "{v} estrés",
    },
    # ---- 诅咒数值家族 ----
    "golddrain": {
        "simp_chinese": "月收入 {v}，持续 10 年", "english": "{v} monthly income, 10 years", "french": "{v} revenu mensuel, 10 ans", "german": "{v} monatliches Einkommen, 10 Jahre",
        "japanese": "月収 {v}、10 年間", "korean": "월 수입 {v}, 10년", "polish": "{v} dochodu miesięcznie, 10 lat", "russian": "{v} к месячному доходу, на 10 лет", "spanish": "{v} de ingreso mensual, 10 años",
    },
})

# 负数摘要格式化辅助：v 传入时带符号
def S(v):
    return f"+{v}" if v >= 0 else str(v)


# ========================================================================
# 祝福池（100 项）：家族布局 gold7 prestige8 piety8 influence7 skill18 xp15
# trait12 mod11 dynasty4 stress4 life1 legendary5
# ========================================================================
B = []

# ---- 遗金系 add_gold（7）----
for rarity, v, names in [
    ("c", 50, N("遗金碎屑", "Ember Motes", "Miettes de braise", "Glutflocken", "残火の粒々", "잔불 조각", "Drobiny żaru", "Искры золы", "Pavesas de brasa")),
    ("c", 100, N("余烬遗金", "Ember Legacy", "Héritage de braise", "Glutvermächtnis", "残火の遺金", "잔화의 유금", "Złoto żaru", "Золото тлеющих углей", "Oro de las brasas")),
    ("c", 200, N("沉匣之金", "Sunken Coffer", "Coffre englouti", "Versunkene Kiste", "沈んだ金庫", "가라앉은 금고", "Zatopiona skrzynia", "Затонувший ларец", "Cofre hundido")),
    ("c", 350, N("焰纹钱囊", "Flame-Marked Purse", "Bourse marquée de flamme", "Flammenbeutel", "炎紋の金袋", "화염 문장 돈주머니", "Płomienny mieszek", "Огненный кошель", "Bolsa marcada por el fuego")),
    ("c", 500, N("仲魔的打赏", "The Broker's Tip", "Pourboire du Courtier", "Trinkgeld des Mittlers", "仲魔の心付け", "중마의 뇌물", "Napiwek Pośrednika", "Чаевые Посредника", "Propina del Intermediario")),
    ("r", 750, N("琉璃金流", "Glassfire Stream", "Flux de verre-feu", "Glutstrom", "琉璃の金流", "유리불 금류", "Strumień szklanego ognia", "Стеклянный поток", "Corriente de fuego vítreo")),
    ("r", 1000, N("咒间金脉", "Curse-Vein Lode", "Veine d'or du Sort", "Fluchgoldader", "呪間の金脈", "주술 금맥", "Żyła złota klątwy", "Золотая жила проклятия", "Veta de oro maldito")),
]:
    B.append((rarity, "gold", v, names))

# ---- 颂歌系 add_prestige（8）----
for rarity, v, names in [
    ("c", 75, N("颂歌残章", "Hymn Fragment", "Fragment d'hymne", "Hymnenfragment", "賛歌の断章", "찬가의 단편", "Fragment hymnu", "Фрагмент гимна", "Fragmento de himno")),
    ("c", 150, N("街角的颂词", "Streetcorner Praise", "Louange au coin des rues", "Lob an jeder Ecke", "街角の頌詞", "길모퉁이 찬사", "Pochwały na ulicach", "Хвала на углах", "Elogio callejero")),
    ("c", 300, N("众口的颂歌", "Song of Many Mouths", "Chant de mille bouches", "Lied vieler Münder", "万口の頌歌", "만인의 찬가", "Pieśń tysiąca ust", "Песнь тысячи уст", "Canción de mil bocas")),
    ("c", 450, N("传唱四方", "Sung Abroad", "Chanté aux quatre vents", "In alle Lande gesungen", "四方に歌われて", "사방에 전해지는 노래", "Śpiewany wszędzie", "Поют повсюду", "Cantado a los cuatro vientos")),
    ("c", 600, N("桂冠的余音", "Laurel Echo", "Écho du laurier", "Echo des Lorbeers", "桂冠の余韻", "월계의 여운", "Echo laurowe", "Эхо лавров", "Eco del laurel")),
    ("r", 900, N("万邦传唱", "Sung in Ten Thousand Realms", "Chanté dans dix mille royaumes", "In zehntausend Reichen besungen", "万邦に歌われる", "만방에 울려 퍼지는 찬가", "Pieśń dziesięciu tysięcy królestw", "Песнь десяти тысяч королевств", "Cantado en diez mil reinos")),
    ("r", 1200, N("焰名的加冕", "Crowning of the Flame-Name", "Couronnement du nom de feu", "Krönung des Flammennamens", "炎名の戴冠", "불꽃 이름의 대관", "Koronacja płomiennego imienia", "Коронация огненного имени", "Coronación del nombre llameante")),
    ("r", 1800, N("不朽声名", "Undying Renown", "Renom immortel", "Unsterblicher Ruhm", "不滅の名声", "불멸의 명성", "Nieśmiertelna sława", "Бессмертная слава", "Fama inmortal")),
]:
    B.append((rarity, "prestige", v, names))

# ---- 祷声系 add_piety（8）----
for rarity, v, names in [
    ("c", 75, N("烛芯微光", "Wicklight", "Lueur de mèche", "Dochtglimmen", "灯芯の微光", "심지의 빛", "Błysk knotu", "Огонёк фитиля", "Luz de la mecha")),
    ("c", 150, N("静焰的祷声", "Prayer of the Still Flame", "Prière de la flamme tranquille", "Gebet der stillen Flamme", "静炎の祷り", "잔불의 기도", "Modlitwa cichego płomienia", "Молитва тихого пламени", "Plegaria de la llama serena")),
    ("c", 300, N("龛前的炽愿", "Vow at the Shrine", "Vœu ardent au sanctuaire", "Schwur am Schrein", "龕前の願い", "감실 앞의 서원", "Ślubowanie przed kapliczką", "Обет у святыни", "Voto ante el altar")),
    ("c", 450, N("圣焰垂听", "The Holy Flame Hears", "La sainte flamme écoute", "Die heilige Flamme hört", "聖炎は聞き届ける", "성화가 귀 기울이다", "Święty ogień słucha", "Святое пламя внемлет", "La llama sagrada escucha")),
    ("c", 600, N("琉璃圣痕", "Glassfire Stigma", "Stigmate de verre-feu", "Glasfeuer-Mal", "琉璃の聖痕", "유리불 성흔", "Sygmat szklanego ognia", "Стеклянное стигматание", "Estigma de fuego vítreo")),
    ("r", 900, N("神座侧耳", "The Throne Inclines", "Le trône prête l'oreille", "Der Thron neigt das Ohr", "神座が耳を傾ける", "신좌가 귀를 기울이다", "Tron się pochyla", "Престол склоняет слух", "El trono inclina el oído")),
    ("r", 1200, N("天国的账页", "Ledger of Heaven", "Page du registre céleste", "Seite im Himmelsbuch", "天国の帳ページ", "천국의 장부", "Stronica niebiańskiej księgi", "Страница небесной книги", "Página del libro celestial")),
    ("r", 1800, N("圣徒的余烬", "Ember of Saints", "Braise des saints", "Heiligenfunke", "聖徒の残火", "성인의 잔화", "Żar świętych", "Уголёк святых", "Brasa de los santos")),
]:
    B.append((rarity, "piety", v, names))

# ---- 耳语系 change_influence（7）----
for rarity, v, names in [
    ("c", 25, N("蛛丝低语", "Webstrand Whisper", "Murmure du fil", "Flüstern des Fadens", "蜘蛛糸の囁き", "거미줄의 속삭임", "Szept pajęczej nici", "Шёпот паутины", "Susurro de la hebra")),
    ("c", 35, N("帘后的耳语", "Whisper Behind the Curtain", "Murmure derrière le rideau", "Hinter dem Vorhang", "帘の奥の声", "휘장 뒤의 속삭임", "Szept zza kotary", "Шёпот за занавесом", "Voz tras el cortinaje")),
    ("c", 50, N("暗线轻扯", "A Tug on the Hidden Thread", "Un tiraillement du fil caché", "Zug am verborgenen Faden", "暗線を引く", "숨은 실 당기기", "Pociągnięcie ukrytej nici", "Рывок скрытой нити", "Tirón del hilo oculto")),
    ("c", 75, N("耳语之网", "Web of Whispers", "Toile de murmures", "Netz des Flüsterns", "囁きの網", "속삭임의 그물", "Sieć szeptów", "Сеть шёпотов", "Red de susurros")),
    ("c", 100, N("影子议会", "Council of Shadows", "Conseil des ombres", "Rat der Schatten", "影の議会", "그림자 의회", "Rada cieni", "Совет теней", "Concilio de sombras")),
    ("r", 125, N("幕后的执笔", "The Hand Behind the Pen", "La main qui tient la plume", "Die Hand hinter der Feder", "背後の執筆者", "장막 뒤의 필자", "Ręka za piórem", "Рука за пером", "La mano tras la pluma")),
    ("r", 150, N("垂帘之手", "Hand Behind the Veil", "Main derrière le voile", "Hand hinter dem Schleier", "垂帘の手", "발 뒤의 손", "Dłoń za zasłoną", "Рука за пологом", "Mano tras el velo")),
]:
    B.append((rarity, "influence", v, names))

# ---- 六维馈赠 add_X_skill（18）：+1/+2/+3 ----
SKILL_FAM = {
    "dip": N("巧言", "Silver Tongue", "Langue d'argent", "Silberzunge", "巧言", "교언", "Srebrny język", "Серебряный язык", "Lengua de plata"),
    "mar": N("戎光", "Warlight", "Lumière de guerre", "Kriegsglut", "戦火", "전광", "Wojenny blask", "Воинский свет", "Luz de guerra"),
    "ste": N("权衡", "Balanced Scales", "Poids mesuré", "Abwägung", "権衡", "형량", "Wyważenie", "Взвешивание", "Ponderación"),
    "int": N("夜眸", "Night Eyes", "Yeux de nuit", "Nachtaugen", "夜の眸", "밤의 눈", "Nocne oczy", "Ночные глаза", "Ojos nocturnos"),
    "lea": N("烛照", "Candlelit Study", "Étude à la chandelle", "Kerzenlicht", "灯明かり", "촛불", "Blask świecy", "Свеча", "Luz de vela"),
    "pro": N("锋刃", "Blade Edge", "Tranchant", "Klinge", "刃先", "칼날", "Ostrze", "Лезвие", "Filo"),
}
SKILL_NAME2 = {
    "dip": N("蜜语的唇枪", "Honeyed Barb", "Trait de miel", "Honigzunge", "蜜語の舌", "달콤한 설득", "Miodowe słowa", "Медовые речи", "Palabras de miel"),
    "mar": N("战焰的臂膀", "Arm of Warfire", "Bras de feu de guerre", "Arm des Kriegsfeuers", "戦炎の腕", "전염의 팔", "Ramię ognia wojny", "Мышца воинского пламени", "Brazo de fuego guerrero"),
    "ste": N("铁算盘的清响", "Iron Abacus Ring", "Cliquetis du boulier", "Klang des Rechenbretts", "鉄そろばんの音", "쇠주판 소리", "Brzęk żelaznego liczydła", "Звон железных счётов", "Sonido del ábaco de hierro"),
    "int": N("影织的指尖", "Shadowweave Fingers", "Doigts tisse-ombre", "Schattenfinger", "影織の指先", "그림자 짜는 손", "Palce tkacza cieni", "Пальцы тенеткача", "Dedos tejesombras"),
    "lea": N("烛下千卷", "A Thousand Scrolls by Candlelight", "Mille rouleaux à la chandelle", "Tausend Rollen im Kerzenlicht", "灯下千巻", "촛불 아래 천 권", "Tysiąc zwojów przy świecy", "Тысяча свитков при свече", "Mil rollos a la luz de la vela"),
    "pro": N("血焰的淬火", "Bloodflame Tempering", "Trempe de sang-feu", "Blutfeuer-Härtung", "血炎の焼入れ", "피의 불꽃 담금질", "Hartowanie w krwi i ogniu", "Закалка в кровавом пламени", "Temple en llama de sangre"),
}
SKILL_NAME3 = {
    "dip": N("琉璃舌", "Glass Tongue", "Langue de verre", "Glaszunge", "琉璃の舌", "유리 혀", "Szklany język", "Стеклянный язык", "Lengua de vidrio"),
    "mar": N("不坠的战旗", "The Unfallen Banner", "La bannière qui ne tombe pas", "Das unerschütterliche Banner", "倒れぬ戦旗", "쓰러지지 않는 전기", "Niezachwiana chorągiew", "Непоколебимое знамя", "El estandarte que no cae"),
    "ste": N("金库的守火", "Keeper of the Vault Flame", "Gardien du feu du coffre", "Wächter der Kassenflamme", "金庫の守り火", "금고의 불지기", "Strażnik ognia skarbca", "Хранитель огня казны", "Guardián del fuego del tesoro"),
    "int": N("无面之契", "Faceless Pact", "Pacte sans visage", "Pakt ohne Gesicht", "無貌の契り", "무얼굴의 계약", "Pakt bez twarzy", "Безликий договор", "Pacto sin rostro"),
    "lea": N("智焰长明", "Wisdom Everburning", "Flamme de sagesse éternelle", "Ewiges Feuer der Weisheit", "智炎長明", "영원히 타는 지혜", "Wieczny ogień mądrości", "Вечный огонь мудрости", "Llama eterna de sabiduría"),
    "pro": N("琉璃战骨", "Glassfire Warbones", "Os de verre-feu", "Glutknochen", "琉璃の戦骨", "유리불 전골", "Kości szklanego ognia", "Кости стеклянного пламени", "Huesos de fuego vítreo"),
}
for attr, effect in [("dip", "add_diplomacy_skill"), ("mar", "add_martial_skill"), ("ste", "add_stewardship_skill"),
                     ("int", "add_intrigue_skill"), ("lea", "add_learning_skill"), ("pro", "add_prowess_skill")]:
    for tier, v in ((1, 1), (2, 2), (3, 3)):
        fam_name = SKILL_FAM[attr] if tier == 1 else (SKILL_NAME2[attr] if tier == 2 else SKILL_NAME3[attr])
        B.append(("c", "skill", (effect, v), fam_name))


# ---- 属性/生活方式树的语种词（摘要里用） ----
ATTR_WORD = {
    "dip": N("外交", "Diplomacy", "Diplomatie", "Diplomatie", "外交", "외교", "Dyplomacja", "Дипломатия", "Diplomacia"),
    "mar": N("军事", "Martial", "Art martial", "Kriegsführung", "軍事", "군사", "Wojenność", "Военное дело", "Marcial"),
    "ste": N("管理", "Stewardship", "Intendance", "Verwaltung", "管理", "관리", "Zarząd", "Управление", "Administración"),
    "int": N("谋略", "Intrigue", "Intrigue", "Intrige", "謀略", "음모", "Intrygi", "Интриги", "Intriga"),
    "lea": N("学识", "Learning", "Érudition", "Gelehrsamkeit", "学識", "학식", "Uczenie", "Учёность", "Erudición"),
    "pro": N("勇武", "Prowess", "Prouesse", "Tapferkeit", "勇武", "용맹", "Sprawność", "Доблесть", "Proeza"),
}

# ---- 残页系 add_X_lifestyle_xp（15）：250/500/750 ----
XP_NAMES = {
    ("dip", 250): N("席间的残局", "Endgame of the Feast", "Fin de partie du banquet", "Nachspiel des Festes", "宴席の残局", "연회의残局", "Końcówka uczty", "Эндшпиль пира", "Final del banquete"),
    ("dip", 500): N("唇舌的年轮", "Growth Rings of Tongues", "Anneaux des langues", "Jahresringe der Zungen", "舌の年輪", "혀의 나이테", "Słoje języków", "Кольца языков", "Anillos de las lenguas"),
    ("dip", 750): N("万言的余温", "Warmth of Ten Thousand Words", "Tiédeur de mille mots", "Wärme zehntausend Worte", "万言の余温", "만언의 여운", "Ciepło dziesięciu tysięcy słów", "Тепло десяти тысяч слов", "Calor de diez mil palabras"),
    ("mar", 250): N("沙盘的灰烬", "Ashes of the Sand Table", "Cendres du sand-box", "Asche des Sandtisches", "砂盤の灰", "모래판의 재", "Popiół planszy", "Пепел песочного стола", "Cenizas del mapa de arena"),
    ("mar", 500): N("兵棋的余局", "Endgame of the Wargame", "Fin de la partie de guerre", "Endspiel des Kriegsspiels", "兵棋の残局", "병기의 잔국", "Końcówka gry wojennej", "Остаток военной игры", "Final del juego de guerra"),
    ("mar", 750): N("烽火的编年", "Chronicle of Beacon Fires", "Chronique des feux d'alarme", "Chronik der Leuchtfeuer", "烽火の編年", "봉화의 편년", "Kronika ognisk sygnałowych", "Хроника сигнальных огней", "Crónica de las almenaras"),
    ("ste", 250): N("账册的灰页", "Grey Ledger Pages", "Pages grises du registre", "Graue Buchseiten", "帳簿の灰ページ", "장부의 잿빛 페이지", "Szare strony księgi", "Серые страницы книги", "Páginas grises del libro"),
    ("ste", 500): N("仓廪的余策", "Granary Afterthoughts", "Arrière-pensées du grenier", "Nachgedanken des Speichers", "倉廩の余策", "곡창의 여책", "Spichlerzowe przemyślenia", "Запасы амбара", "Reflexiones del granero"),
    ("ste", 750): N("国帑的长算", "Long Reckoning of the Treasury", "Long calcul du trésor", "Lange Rechnung des Schatzes", "国帑の長算", "국고의 긴 계산", "Długi rachunek skarbca", "Долгий подсчёт казны", "Larga cuenta del tesoro"),
    ("int", 250): N("暗巷的足音", "Footsteps in Dark Alleys", "Pas dans les ruelles", "Schritte in dunklen Gassen", "暗巷の足音", "어두운 골목의 발소리", "Kroki w ciemnych alejach", "Шаги в тёмных переулках", "Pasos en callejones oscuros"),
    ("int", 500): N("罗网的余丝", "Loose Threads of the Net", "Fils restants du filet", "Restfäden des Netzes", "羅網の余糸", "라망의 여실", "Luźne nici sieci", "Остатки сети", "Hilos sueltos de la red"),
    ("int", 750): N("千面的戏文", "Play of a Thousand Faces", "Pièce aux mille visages", "Stück der tausend Gesichter", "千面の戯文", "천면의 희곡", "Sztuka tysiąca twarzy", "Пьеса тысячи лиц", "Obra de mil rostros"),
    ("lea", 250): N("书库的残页", "Loose Pages of the Library", "Pages arrachées de la bibliothèque", "Lose Seiten der Bibliothek", "書庫の残頁", "서고의残頁", "Wyrwane strony biblioteki", "Вырванные страницы библиотеки", "Páginas sueltas de la biblioteca"),
    ("lea", 500): N("青灯的余卷", "Remaining Scrolls of the Green Lamp", "Rouleaux restants de la lampe verte", "Restrollen der grünen Lampe", "青灯の余巻", "청등의 여권", "Pozostałe zwoje zielonej lampy", "Остатки свитков зелёной лампы", "Rollos restantes de la lámpara verde"),
    ("lea", 750): N("智海的拾贝", "Shell-Gathering in the Sea of Wisdom", "Cueillette dans la mer de sagesse", "Muscheln am Meer der Weisheit", "智海の貝拾い", "지혜의 바다 조개 줍기", "Zbieranie muszli w morzu mądrości", "Сбор ракушек в море мудрости", "Recogiendo conchas en el mar de la sabiduría"),
}
ATTR_FULL = {"dip": "diplomacy", "mar": "martial", "ste": "stewardship", "int": "intrigue", "lea": "learning", "pro": "prowess"}

for (attr, v), names in XP_NAMES.items():
    B.append(("c", "xp", (f"add_{ATTR_FULL[attr]}_lifestyle_xp", v), names))


# ---- 特质系 add_trait（12）：6 普通 + 6 稀有 ----
# (rarity, trait_key, names, trait_word_per_lang)
TRAIT_B = [
    ("c", "physique_good_1", N("不败之躯", "Unconquered Flesh", "Chair invaincue", "Unbesiegtes Fleisch", "不敗の躯", "불패의 몸", "Niezwyciężone ciało", "Непобедимая плоть", "Carne invicta"),
        N("健壮", "Hale", "Vigoureux", "Wacker", "丈夫", "건장", "Krzepki", "Крепкий", "Fornido")),
    ("r", "physique_good_2", N("琉璃体魄", "Glassfire Physique", "Corps de verre-feu", "Glutleib", "琉璃の体躯", "유리불 체격", "Postać szklanego ognia", "Телосложение стеклянного пламени", "Físico de fuego vítreo"),
        N("强健", "Robust", "Robuste", "Robust", "頑健", "강건", "Tęgi", "Дюжий", "Robusto")),
    ("r", "physique_good_3", N("焰铸圣躯", "Flame-Forged Body", "Corps forgé dans la flamme", "Flammengeschmiedeter Leib", "炎鋳の聖躯", "불꽃으로 벼린 몸", "Ciało kuté w płomieniu", "Тело, выкованное пламенем", "Cuerpo forjado en llamas"),
        N("赫拉克勒斯", "Herculean", "Herculéen", "Herkulisch", "ヘラクレス", "헤라클레스", "Herkulesowy", "Геркулес", "Hercúleo")),
    ("c", "beauty_good_1", N("烛下的容颜", "Candlelit Visage", "Visage à la chandelle", "Antlitz im Kerzenlicht", "灯下の顔立ち", "촛불 아래 용모", "Oblicze w blasku świecy", "Лицо при свече", "Rostro a la luz de la vela"),
        N("清秀", "Comely", "Avenant", "Hübsch", "端正", "곱상", "Ładny", "Миловидный", "Agraciado")),
    ("r", "beauty_good_2", N("琉璃面庞", "Glassfire Countenance", "Visage de verre-feu", "Glasfeuer-Antlitz", "琉璃の面立ち", "유리불 얼굴", "Twarz szklanego ognia", "Стеклянное лицо", "Rostro de fuego vítreo"),
        N("姣好", "Beautiful", "Beau", "Schön", "美麗", "아름다움", "Piękny", "Красивый", "Hermoso")),
    ("c", "intellect_good_1", N("灵犀一点", "A Spark of Wit", "Une étincelle d'esprit", "Ein Funke Geist", "霊犀一点", "영리한 불꽃", "Iskra dowcipu", "Искра остроумия", "Chispa de ingenio"),
        N("聪敏", "Quick", "Vif", "Gewitzt", "俊敏", "영민", "Bystry", "Сообразительный", "Despierto")),
    ("r", "intellect_good_2", N("慧焰入颅", "Wisdom-Flame Enthroned", "Flamme de sagesse au crâne", "Weisheitsflamme im Schädel", "慧炎入腦", "지혜의 불꽃 입두", "Płomień mądrości w czaszce", "Пламя мудрости в черепе", "Llama de sabiduría en el cráneo"),
        N("颖慧", "Intelligent", "Intelligent", "Intelligent", "賢明", "총명", "Inteligentny", "Умный", "Inteligente")),
    ("r", "shrewd", N("狐焰的狡黠", "Foxfire Cunning", "Ruse du feu de renard", "Fuchsfeuer-List", "狐火の狡黠", "여우불의 교활", "Przebiegłość lisi ognik", "Хитрость лисьего огня", "Astucia del fuego fatuo"),
        N("精明", "Shrewd", "Astucieux", "Gerissen", "狡猾", "교활", "Przebiegły", "Проницательный", "Astuto")),
    ("r", "strong", N("焰筋铁骨", "Sinews of Flame and Iron", "Tendons de flamme et de fer", "Sehnen aus Flamme und Eisen", "炎筋鉄骨", "불꽃 힘줄 무쇠뼈", "Ścięgna płomienia i żelaza", "Жилы пламени и железа", "Tendones de llama y hierro"),
        N("强壮", "Strong", "Fort", "Stark", "強壮", "강인", "Silny", "Сильный", "Fuerte")),
    ("c", "brave", N("壮行的火种", "Ember of Bold Venture", "Tison de bravoure", "Funke der Tapferkeit", "壮行の火種", "장행의 불씨", "Żar odwagi", "Искра отваги", "Brasa de valentía"),
        N("勇敢", "Brave", "Courageux", "Tapfer", "勇敢", "용감", "Odważny", "Храбрый", "Valiente")),
    ("c", "diligent", N("不息的炭火", "The Unresting Coal", "Le charbon qui ne s'éteint pas", "Die ruhelose Kohle", "絶えぬ炭火", "쉬지 않는 숯불", "Węgiel bez wytchnienia", "Неугасающий уголёк", "El carbón incansable"),
        N("勤勉", "Diligent", "Assidu", "Fleißig", "勤勉", "근면", "Pracowity", "Усердный", "Diligente")),
    ("c", "patient", N("长明的定力", "Steadiness of the Everlit Lamp", "Constance de la lampe éternelle", "Geduld der ewigen Lampe", "長明の定力", "장명의 정력", "Stałość wiecznej lampy", "Стойкость вечного светильника", "Constancia de la lámpara eterna"),
        N("耐心", "Patient", "Patient", "Geduldig", "辛抱強い", "인내심", "Cierpliwy", "Терпеливый", "Paciente")),
]
for rarity, key, names, tword in TRAIT_B:
    B.append((rarity, "trait", f"add_trait = {key}", names, tword))


# ---- 修正系（10 年 modifier，11 项）----
# (rarity, modifier_id, modifier_fields, names, summaries)
MOD_B = [
    ("c", "xar_pb_income_s", "monthly_income = 0.5",
        N("余烬钱脉", "Ember Coin-Vein", "Veine de monnaie de braise", "Glut-Geldader", "残火の銭脈", "잔화의 돈줄", "Żyła monet żaru", "Денежная жила золы", "Veta de monedas de brasa"),
        N("月收入 +0.5，持续 10 年", "+0.5 monthly income, 10 years", "+0,5 revenu mensuel, 10 ans", "+0,5 monatliches Einkommen, 10 Jahre", "月収 +0.5、10 年間", "월 수입 +0.5, 10년", "+0,5 dochodu miesięcznie, 10 lat", "+0,5 к месячному доходу, на 10 лет", "+0,5 de ingreso mensual, 10 años")),
    ("r", "xar_pb_income_m", "monthly_income = 1",
        N("琉焰银根", "Glassfire Silver Root", "Racine d'argent du verre-feu", "Glasfeuer-Silberwurzel", "琉璃の銀根", "유리불 은뿌리", "Srebrny korzeń szklanego ognia", "Серебряный корень стеклянного пламени", "Raíz de plata del fuego vítreo"),
        N("月收入 +1，持续 10 年", "+1 monthly income, 10 years", "+1 revenu mensuel, 10 ans", "+1 monatliches Einkommen, 10 Jahre", "月収 +1、10 年間", "월 수입 +1, 10년", "+1 dochodu miesięcznie, 10 lat", "+1 к месячному доходу, на 10 лет", "+1 de ingreso mensual, 10 años")),
    ("r", "xar_pb_income_l", "monthly_income = 2",
        N("咒间金泉", "Curse-Vein Goldspring", "Source d'or du sort", "Fluch-Goldquelle", "呪間の金泉", "주술 금샘", "Złote źródło klątwy", "Золотой ключ проклятия", "Manantial de oro maldito"),
        N("月收入 +2，持续 10 年", "+2 monthly income, 10 years", "+2 revenu mensuel, 10 ans", "+2 monatliches Einkommen, 10 Jahre", "月収 +2、10 年間", "월 수입 +2, 10년", "+2 dochodu miesięcznie, 10 lat", "+2 к месячному доходу, на 10 лет", "+2 de ingreso mensual, 10 años")),
    ("c", "xar_pb_health_s", "health = 0.3",
        N("温焰护体", "Warm Ember Ward", "Garde de braise tiède", "Warme Glut-Hülle", "温炎の護り", "따뜻한 불꽃 보호", "Ciepła ochrona żaru", "Тёплая защита углей", "Protección de brasa tibia"),
        N("健康 +0.3，持续 10 年", "+0.3 health, 10 years", "+0,3 santé, 10 ans", "+0,3 Gesundheit, 10 Jahre", "健康 +0.3、10 年間", "건강 +0.3, 10년", "+0,3 zdrowia, 10 lat", "+0,3 здоровья, на 10 лет", "+0,3 de salud, 10 años")),
    ("r", "xar_pb_health_m", "health = 0.6",
        N("琉璃色的体温", "Glassfire Warmth", "Chaleur du verre-feu", "Glasfeuer-Wärme", "琉璃色の体温", "유리빛 체온", "Ciepło szklanego ognia", "Стеклянное тепло", "Calor vítreo"),
        N("健康 +0.6，持续 10 年", "+0.6 health, 10 years", "+0,6 santé, 10 ans", "+0,6 Gesundheit, 10 Jahre", "健康 +0.6、10 年間", "건강 +0.6, 10년", "+0,6 zdrowia, 10 lat", "+0,6 здоровья, на 10 лет", "+0,6 de salud, 10 años")),
    ("r", "xar_pb_health_l", "health = 1.0",
        N("圣焰织体", "Body Woven of Holy Flame", "Corps tissé de flamme sainte", "Leib aus heiliger Flamme", "聖炎の織体", "성염으로 짠 몸", "Ciało tkane ze świętego ognia", "Тело, сотканное святым пламенем", "Cuerpo tejido de llama santa"),
        N("健康 +1.0，持续 10 年", "+1.0 health, 10 years", "+1,0 santé, 10 ans", "+1,0 Gesundheit, 10 Jahre", "健康 +1.0、10 年間", "건강 +1.0, 10년", "+1,0 zdrowia, 10 lat", "+1,0 здоровья, на 10 лет", "+1,0 de salud, 10 años")),
    ("c", "xar_pb_fert_s", "fertility = 0.15",
        N("薪火相传", "The Flame Passes On", "La flamme se transmet", "Das Feuer wird weitergegeben", "薪火相伝", "신화전승", "Przekazanie ognia", "Передача пламени", "El fuego se transmite"),
        N("生育 +15%，持续 10 年", "+15% fertility, 10 years", "+15 % fertilité, 10 ans", "+15 % Fruchtbarkeit, 10 Jahre", "出産率 +15%、10 年間", "출산율 +15%, 10년", "+15% płodności, 10 lat", "+15% к плодовитости, на 10 лет", "+15 % de fertilidad, 10 años")),
    ("r", "xar_pb_fert_m", "fertility = 0.30",
        N("焰嗣绵延", "Heirs of the Flame", "Lignée de la flamme", "Erben der Flamme", "炎嗣綿延", "화손연면", "Potomstwo płomienia", "Потомки пламени", "Descendencia de la llama"),
        N("生育 +30%，持续 10 年", "+30% fertility, 10 years", "+30 % fertilité, 10 ans", "+30 % Fruchtbarkeit, 10 Jahre", "出産率 +30%、10 年間", "출산율 +30%, 10년", "+30% płodności, 10 lat", "+30% к плодовитости, на 10 лет", "+30 % de fertilidad, 10 años")),
    ("c", "xar_pb_vassal", "vassal_opinion = 10",
        N("俯首的敬意", "Bowed Reverence", "Révérence baissée", "Verneigte Ehrfurcht", "俯首の敬意", "고개 숙인 경의", "Pokorna cześć", "Склонённое почтение", "Reverencia inclinada"),
        N("封臣好感 +10，持续 10 年", "+10 vassal opinion, 10 years", "+10 opinion des vassaux, 10 ans", "+10 Vasallenmeinung, 10 Jahre", "陪臣の評価 +10、10 年間", "봉신 호감 +10, 10년", "+10 opinii wasali, 10 lat", "+10 к мнению вассалов, на 10 лет", "+10 opinión de vasallos, 10 años")),
    ("c", "xar_pb_stress", "stress_gain_mult = -0.15",
        N("心静琉璃", "Heart of Still Glass", "Cœur de verre tranquille", "Herz aus stillem Glas", "心静なる琉璃", "잔잔한 유리 심장", "Serce ze spokojnego szkła", "Сердце из тихого стекла", "Corazón de vidrio sereno"),
        N("压力获取 -15%，持续 10 年", "-15% stress gain, 10 years", "-15 % gain de stress, 10 ans", "-15 % Stresszuwachs, 10 Jahre", "ストレス獲得 -15%、10 年間", "스트레스 획득 -15%, 10년", "-15% przyrostu stresu, 10 lat", "-15% к получению стресса, на 10 лет", "-15 % de ganancia de estrés, 10 años")),
    ("c", "xar_pb_prestige", "monthly_prestige = 0.5",
        N("名望余温", "Lingering Warmth of Fame", "Tiédeur de la renommée", "Nachwärme des Ruhms", "名望の余温", "명망의 여운", "Pozostałość sławy", "Тепло славы", "Calor de la fama"),
        N("月威望 +0.5，持续 10 年", "+0.5 monthly prestige, 10 years", "+0,5 prestige mensuel, 10 ans", "+0,5 monatliches Prestige, 10 Jahre", "月威望 +0.5、10 年間", "월 위상 +0.5, 10년", "+0,5 prestiżu miesięcznie, 10 lat", "+0,5 престижа в месяц, на 10 лет", "+0,5 de prestigio mensual, 10 años")),
]
for rarity, mid, fields, names, sums in MOD_B:
    B.append((rarity, "mod", (mid, fields), names, sums))


# ---- 宗门系 add_dynasty_prestige（4）----
for rarity, v, names in [
    ("c", 50, N("族徽的擦亮", "Polishing the Crest", "Polissage du blason", "Wappenpolitur", "家紋を磨く", "가문 문장 닦기", "Polerowanie herbu", "Полировка герба", "Pulido del blasón")),
    ("c", 150, N("宗门的余晖", "Afterglow of the Lineage", "Lueur du lignage", "Nachglut der Sippe", "宗門の余輝", "종문의 여휘", "Poświata rodowita", "Отблеск рода", "Resplandor del linaje")),
    ("r", 300, N("族焰的加冠", "Crowning of the House Flame", "Couronnement de la flamme du sang", "Krönung des Hausfeuers", "族炎の加冠", "족염의 가관", "Koronacja płomienia rodu", "Коронация пламени рода", "Coronación de la llama de la casa")),
    ("r", 500, N("万世谱的烫金", "Gilding the Eternal Pedigree", "Dorure du pedigree éternel", "Vergoldung des ewigen Stammbaums", "万世譜の箔押し", "만세보의 도금", "Złocenie wiecznego rodowodu", "Позолота вечного родословия", "Dorado del pedigrí eterno")),
]:
    B.append((rarity, "dynasty", v, names))

# ---- 抚平系 add_stress（4，负值=减压）----
for rarity, v, names in [
    ("c", -50, N("静焰抚平", "The Still Flame Soothes", "La flamme tranquille apaise", "Die stille Flamme beruhigt", "静炎が撫でる", "잔불이 어루만지다", "Cichy płomień koi", "Тихое пламя успокаивает", "La llama serena alivia")),
    ("c", -75, N("灰烬浴", "Ashen Bath", "Bain de cendres", "Aschebad", "灰の浴", "재 목욕", "Kąpiel w popiele", "Пепельная купель", "Baño de ceniza")),
    ("c", -100, N("长夜的灰烬浴", "Ashen Bath of the Long Night", "Bain de cendres de la longue nuit", "Aschebad der langen Nacht", "長夜の灰浴", "긴 밤의 재 목욕", "Kąpiel popiołowa długiej nocy", "Пепельная купель долгой ночи", "Baño de ceniza de la larga noche")),
    ("r", -150, N("忘川的洗礼", "Baptism in the River Lethe", "Baptême du Léthé", "Taufe im Lethe", "忘川の洗礼", "망천의 세례", "Chrzest w Lete", "Крещение в Лете", "Bautismo en el Lete")),
]:
    B.append((rarity, "stress_b", v, names))

# ---- 余火系（1）：永久健康修正 ----
B.append(("r", "custom", "add_character_modifier = { modifier = xar_pb_life_2 }",
    N("不灭的灯芯", "The Unquenchable Wick", "La mèche inextinguible", "Der unlöschbare Docht", "不滅の灯芯", "꺼지지 않는 심지", "Niewygasły knot", "Негасимый фитиль", "La mecha inextinguible"),
    N("余命 +2（健康 +2，永久）", "+2 lifespan (permanent)", "+2 durée de vie (permanent)", "+2 Lebenserwartung (permanent)", "余命 +2（永続）", "여명 +2 (영구)", "+2 lat życia (na stałe)", "+2 года жизни (навсегда)", "+2 años de vida (permanente)")))

# ---- 传说祝福（5）----
B.append(("l", "custom", "add_diplomacy_skill = 1\n\tadd_martial_skill = 1\n\tadd_stewardship_skill = 1\n\tadd_intrigue_skill = 1\n\tadd_learning_skill = 1\n\tadd_prowess_skill = 1",
    N("琉焰之拥", "Embrace of the Glassfire", "Étreinte du verre-feu", "Umarmung des Glasfeuers", "琉璃炎の抱擁", "유리염의 포옹", "Obejrzenie szklanego ognia", "Объятия стеклянного пламени", "Abrazo del fuego vítreo"),
    N("六维各 +1", "+1 to all six skills", "+1 aux six compétences", "+1 auf alle sechs Fähigkeiten", "六能力各 +1", "여섯 능력 각 +1", "+1 do sześciu atrybutów", "+1 ко всем шести навыкам", "+1 a los seis atributos")))
B.append(("l", "custom", "add_character_modifier = { modifier = xar_leg_life }",
    N("不灭的灯芯·真", "The True Unquenchable Wick", "La mèche inextinguible véritable", "Der wahre unlöschbare Docht", "不滅の灯芯・真", "진정한 불멸의 심지", "Prawdziwie niewygasły knot", "Истинный негасимый фитиль", "La mecha verdaderamente inextinguible"),
    N("余命 +10（健康 +10，永久）", "+10 lifespan (permanent)", "+10 durée de vie (permanent)", "+10 Lebenserwartung (permanent)", "余命 +10（永続）", "여명 +10 (영구)", "+10 lat życia (na stałe)", "+10 лет жизни (навсегда)", "+10 años de vida (permanente)")))
B.append(("l", "custom", "add_gold = 1000\n\tadd_character_modifier = { modifier = xar_leg_wealth days = 3650 }",
    N("万邦的账簿", "Ledger of Ten Thousand Realms", "Registre de dix mille royaumes", "Buch der zehntausend Reiche", "万邦の帳簿", "만방의 장부", "Księga dziesięciu tysięcy królestw", "Книга десяти тысяч королевств", "Libro de diez mil reinos"),
    N("+1000 金币，月收入 +1 持续 10 年", "+1000 gold, +1 monthly income for 10 years", "+1000 or, +1 revenu mensuel pendant 10 ans", "+1000 Gold, +1 monatliches Einkommen für 10 Jahre", "+1000 ゴールド、月収 +1 が 10 年間", "+1000 골드, 월 수입 +1 (10년)", "+1000 złota, +1 dochodu miesięcznie przez 10 lat", "+1000 золота, +1 к доходу в месяц на 10 лет", "+1000 oro, +1 de ingreso mensual durante 10 años")))
B.append(("l", "custom", "add_prestige = 300\n\tadd_piety = 300\n\tchange_influence = 100",
    N("垂青的印记", "Mark of Favor", "Marque de faveur", "Mal der Gunst", "垂青の印", "총애의 인장", "Znak łaski", "Знак благосклонности", "Marca de favor"),
    N("威望/虔诚/影响力 +300/+300/+100", "+300 prestige, +300 piety, +100 influence", "+300 prestige, +300 piété, +100 influence", "+300 Prestige, +300 Frömmigkeit, +100 Einfluss", "威望/信心/影響力 +300/+300/+100", "위상/경건/영향력 +300/+300/+100", "+300 prestiżu, +300 pobożności, +100 wpływów", "+300 престижа, +300 благочестия, +100 влияния", "+300 prestigio, +300 piedad, +100 influencia")))
B.append(("l", "custom", "dynasty ?= { add_dynasty_prestige = 1000 }",
    N("预支的来世", "The Afterlife, Prepaid", "L'au-delà, prépayé", "Das Jenseits, vorausbezahlt", "来世の前払い", "내세의 선불", "Zaświaty, opłacone z góry", "Загробная жизнь, оплаченная вперёд", "El más allá, prepagado"),
    N("宗族威望 +1000", "+1000 renown", "+1000 renom", "+1000 Renommee", "一族の名声 +1000", "왕조 명성 +1000", "+1000 renomy", "+1000 известности", "+1000 renombre")))


# ========================================================================
# 诅咒池（100 项）：与祝福同布局。量级 = 祝福 ÷ 0.75（取整）。
# 金币只走月收入 drain（1.19 无合规一次性扣金，见 docs/grammar/pitfalls.md）。
# ========================================================================
C = []

# ---- 漏金系 monthly_income 修正 10 年（7）----
DRAIN = [
    ("c", "xar_pc_drain_a", "-0.3", N("钱袋的细沙", "Fine Sand in the Purse", "Sable fin dans la bourse", "Feiner Sand im Beutel", "金袋の細砂", "돈주머니의 가는 모래", "Drobny piasek w mieszku", "Мелкий песок в кошеле", "Arena fina en la bolsa")),
    ("c", "xar_pc_drain_b", "-0.5", N("渗漏的钱袋", "The Seeping Purse", "Bourse qui fuit", "Der undichte Beutel", "漏れる金袋", "새는 돈주머니", "Przeciekający mieszek", "Протекающий кошель", "La bolsa que gotea")),
    ("c", "xar_pc_drain_c", "-0.75", N("漏底的荷包", "The Bottomless Purse", "Bourse sans fond", "Der bodenlose Beutel", "底なしの金袋", "밑 빠진 돈주머니", "Bezdenny mieszek", "Бездонный кошель", "La bolsa sin fondo")),
    ("c", "xar_pc_drain_d", "-1.0", N("暗账的虫蛀", "Moth-Eaten Ledger", "Registre rongé par les mites", "Mottenfraß im Buch", "帳簿の虫食い", "장부의 좀", "Mole w księgach", "Моль в книгах", "Polillas en el libro")),
    ("c", "xar_pc_drain_e", "-1.25", N("无声的分流", "The Silent Diversion", "Détournement silencieux", "Stille Umleitung", "无声の分流", "무성의 분류", "Ciche odprowadzenie", "Тихий отвод", "Desviación silenciosa")),
    ("r", "xar_pc_drain_f", "-1.5", N("咒痕的利息", "Interest of the Curse-Mark", "Intérêts de la marque", "Zinsen des Fluchmals", "呪痕の利息", "주흔의 이자", "Odsetki znaku klątwy", "Проценты по метке", "Intereses de la marca")),
    ("r", "xar_pc_drain_g", "-2.0", N("琉焰的月贡", "Monthly Tithe to the Glassfire", "Dîme mensuelle du verre-feu", "Monatlicher Zehnt ans Glasfeuer", "琉璃への月貢", "유리염의 월공", "Miesięczny dziesięcina szklanemu ogniowi", "Месячная десятина стеклянному пламени", "Diezmo mensual al fuego vítreo")),
]
for rarity, mid, v, names in DRAIN:
    C.append((rarity, "custom", f"add_character_modifier = {{ modifier = {mid} days = 3650 }}", names,
        {lang: SUM_T["golddrain"][lang](v) for lang in LANGS}))

# ---- 嗤笑系 add_prestige 负值（8）----
for rarity, v, names in [
    ("c", -100, N("背后的低笑", "Snickers Behind Your Back", "Ricanements dans le dos", "Gekicher hinter dem Rücken", "背後の失笑", "등 뒤의 비웃음", "Chichoty za plecami", "Смешки за спиной", "Risas a tus espaldas")),
    ("c", -200, N("暗处的嗤笑", "Sneers from the Shadows", "Ricanements de l'ombre", "Höhnen aus dem Schatten", "暗がりの嘲笑", "어둠 속의 조소", "Szyderstwa z cienia", "Насмешки из тени", "Burlas desde las sombras")),
    ("c", -400, N("宴会的冷场", "The Feast Falls Silent", "Le banquet se tait", "Das Fest verstummt", "宴会の冷場", "연회의 냉담", "Uczta zamiera", "Пир замолкает", "El banquete enmudece")),
    ("c", -600, N("名望的剥落", "Flaking Renown", "Renom qui s'écaille", "Abblätternder Ruhm", "名声の剥落", "명망의 박리", "Łuszcząca się sława", "Отслаивающаяся слава", "Fama que se deshoja")),
    ("c", -800, N("众口的毒刺", "Poisoned Tongues of the Crowd", "Langues empoisonnées", "Vergiftete Zungen", "万口の毒刺", "만인의 독설", "Zatrute języki tłumu", "Отравленные языки толпы", "Lenguas envenenadas")),
    ("r", -1200, N("桂冠的蒙尘", "Dust on the Laurel", "Poussière sur le laurier", "Staub auf dem Lorbeer", "桂冠の蒙塵", "월계의 먼지", "Kurz na laurze", "Пыль на лаврах", "Polvo en el laurel")),
    ("r", -1600, N("耻辱的烙印", "Brand of Shame", "Marque de la honte", "Brandmal der Schande", "恥辱の烙印", "치욕의 낙인", "Piętno wstydu", "Клеймо позора", "Marca de la vergüenza")),
    ("r", -2400, N("遗臭的批注", "Infamous Annotation", "Annotation infamante", "Berüchtigte Anmerkung", "遺臭の注釈", "악명의 주석", "Niesławna adnotacja", "Позорная пометка", "Anotación infame")),
]:
    C.append((rarity, "prestige", v, names))

# ---- 沉默系 add_piety 负值（8）----
for rarity, v, names in [
    ("c", -100, N("龛火的摇曳", "Flickering Shrine Light", "Vacillement du sanctuaire", "Flackern des Schreins", "龕火の揺らぎ", "감실 불의 흔들림", "Migotanie kapliczki", "Мерцание святыни", "Parpadeo del altar")),
    ("c", -200, N("圣像的沉默", "The Icons' Silence", "Le silence des icônes", "Das Schweigen der Ikonen", "聖像の沈黙", "성상의 침묵", "Cisza ikon", "Молчание икон", "El silencio de los íconos")),
    ("c", -400, N("祷词的哽塞", "The Prayer Sticks in the Throat", "La prière s'étrangle", "Das Gebet stockt", "祷りの哽塞", "기도의 막힘", "Modlitwa w gardle", "Молитва в горле", "La plegaria se atasca")),
    ("c", -600, N("香灰的迷眼", "Incense Ash in the Eyes", "Cendre d'encens aux yeux", "Weihrauchasche in den Augen", "香灰の迷眼", "향재의 미안", "Popiół kadzidła w oczach", "Пепел ладана в глазах", "Ceniza de incienso en los ojos")),
    ("c", -800, N("神坛的冷寂", "The Altar Grown Cold", "L'autel refroidi", "Der kalte Altar", "祭壇の冷寂", "제단의 냉랭", "Wychłodzony ołtarz", "Остывший алтарь", "El altar enfriado")),
    ("r", -1200, N("圣痕的逆灼", "The Stigma Burns Inverse", "Le stigmate brûle à rebours", "Das Mal brennt verkehrt", "聖痕の逆灼", "성흔의 역화", "Sygmat płonący odwrotnie", "Стигма жжёт вспять", "El estigma arde al revés")),
    ("r", -1600, N("天听的掩耳", "Heaven Covers Its Ears", "Le ciel se bouche les oreilles", "Der Himmel hält sich die Ohren zu", "天聴の掩耳", "천청의 이이", "Niebo zatyka uszy", "Небо затыкает уши", "El cielo se tapa los oídos")),
    ("r", -2400, N("神眷的断约", "The Covenant Severed", "L'alliance rompue", "Der gebrochene Bund", "神眷の断約", "신권의 단약", "Zerwane przymierze", "Разорванный завет", "El pacto roto")),
]:
    C.append((rarity, "piety", v, names))

# ---- 断线系 change_influence 负值（7）----
for rarity, v, names in [
    ("c", -35, N("线的松脱", "The Thread Slackens", "Le fil se relâche", "Der Faden lockert sich", "糸の緩み", "실의 느슨함", "Luzująca się nić", "Нить слабеет", "El hilo se afloja")),
    ("c", -50, N("暗桩的倒戈", "The Mole Turns", "La taupe se retourne", "Der Maulwurf wechselt", "暗桩の倒戈", "암말의 배신", "Kret się odwraca", "Крот предаёт", "El topo deserta")),
    ("c", -65, N("耳语的退潮", "Ebb of Whispers", "Reflux des murmures", "Ebbede des Flüsterns", "囁きの退潮", "속삭임의 썰물", "Odpływ szeptów", "Отлив шёпотов", "Marea de susurros")),
    ("c", -100, N("断线的傀儡", "The Severed Puppet", "La marionnette coupée", "Die abgetrennte Marionette", "断線の傀儡", "끊어진 꼭두각시", "Marionetka z przeciętą nić", "Марионетка с обрезанными нитями", "La marioneta cortada")),
    ("c", -135, N("罗网的破眼", "A Hole in the Net", "Un trou dans le filet", "Ein Loch im Netz", "羅網の破目", "라망의 파목", "Dziura w sieci", "Дыра в сети", "Agujero en la red")),
    ("r", -165, N("帷幕的坠落", "The Curtain Falls", "Le rideau tombe", "Der Vorhang fällt", "帷幕の落下", "휘막의 낙하", "Kurtyna opada", "Занавес падает", "El telón cae")),
    ("r", -200, N("垂帘的断手", "The Hand Behind the Veil, Severed", "La main derrière le voile, coupée", "Die Hand hinter dem Schleier, abgetrennt", "垂帘の断手", "발 뒤의断手", "Dłoń za zasłoną, odcięta", "Рука за пологом, отсечённая", "La mano tras el velo, cercenada")),
]:
    C.append((rarity, "influence", v, names))


# ---- 褪色系 add_X_skill 负值（18）：-1/-3/-4 ----
SKILL_C_NAMES = {
    "dip": {1: N("锈死的门环", "The Rusted Door-Knocker", "Le heurtoir rouillé", "Der verrostete Türklopfer", "錆死の門環", "녹슨 문고리", "Zardzewiały kołatnik", "Заржавевшее кольцо", "El llamador oxidado"),
            2: N("结舌的毒涎", "Venom on the Tongue", "Venin sur la langue", "Gift auf der Zunge", "結舌の毒涎", "설근의 독침", "Jad na języku", "Яд на языке", "Veneno en la lengua"),
            3: N("失声的琉璃", "The Voiceless Glass", "Le verre sans voix", "Das stumme Glas", "失声の琉璃", "실성의 유리", "Nieme szkło", "Немое стекло", "El vidrio mudo")},
    "mar": {1: N("钝刃的锈斑", "Rust on the Blunted Blade", "Rouille sur la lame émoussée", "Rost auf der stumpfen Klinge", "鈍刃の錆斑", "둔인의 녹반", "Rdza na stępionym ostrzu", "Ржавчина на тупом клинке", "Óxido en la hoja roma"),
            2: N("战阵的迷途", "Lost in the Battle Line", "Perdu dans la ligne", "Verloren in der Schlachtlinie", "戦陣の迷途", "전진의 미로", "Zgubiony w szyku", "Заблудившийся в строю", "Perdido en la línea"),
            3: N("折戟的残旗", "The Broken Halberd's Tattered Banner", "L'étendard en lambeaux de la hallebarde brisée", "Das zerfetzte Banner der gebrochenen Hellebarde", "折戟の残旗", "절극의残旗", "Podarty sztandar złamanej halabardy", "Рваное знамя сломанной алебарды", "El estandarte harapiento del alabarda rota")},
    "ste": {1: N("蒙尘的算珠", "Dusty Abacus Beads", "Boules poussiéreuses du boulier", "Staubige Rechenkugeln", "蒙塵の算珠", "몽진의 산주", "Zakurzone koraliki liczydła", "Запыленные костяшки", "Cuentas polvorientas del ábaco"),
            2: N("烂账的霉斑", "Mildew on the Rotten Books", "Moisissure des livres pourris", "Schimmel auf den verfaulten Büchern", "爛帳の黴斑", "난장의 곰팡이", "Pleśń na zgniłych księgach", "Плесень на гнилых книгах", "Moho en los libros podridos"),
            3: N("金库的漏底", "The Vault's Broken Bottom", "Le fond percé du coffre", "Der durchbrochene Boden des Tresors", "金庫の漏底", "금고의 누저", "Przebity spód skarbca", "Дно казны пробито", "El fondo roto de la bóveda")},
    "int": {1: N("褪色的心眼", "The Faded Mind's Eye", "L'œil de l'esprit fané", "Das verblasste geistige Auge", "褪色の心眼", "퇴색의 심안", "Wyblakłe oko umysłu", "Вырожденный ум", "El ojo de la mente desvaído"),
            2: N("影子的叛逃", "The Shadow Defects", "L'ombre déserte", "Der Schatten läuft über", "影の叛逃", "그림자의 반도", "Cień dezerteruje", "Тень дезертирует", "La sombra deserta"),
            3: N("无面的弃契", "The Faceless Pact, Broken", "Le pacte sans visage, rompu", "Der Pakt ohne Gesicht, gebrochen", "無面の棄契", "무얼굴의 파기된 계약", "Pakt bez twarzy, zerwany", "Безликий договор, разорванный", "El pacto sin rostro, roto")},
    "lea": {1: N("蒙尘的经卷", "Dusty Scriptures", "Écritures poussiéreuses", "Staubige Schriften", "蒙塵の経巻", "몽진의 경권", "Zakurzone pisma", "Запыленные свитки", "Escrituras polvorientas"),
            2: N("青灯的油耗", "The Green Lamp Drinks Its Oil", "La lampe verte boit son huile", "Die grüne Lampe trinkt ihr Öl", "青灯の油耗", "청등의 기름 소모", "Zielona lampa pije olej", "Зелёная лампа пьёт масло", "La lámpara verde bebe su aceite"),
            3: N("智海的沉船", "Shipwreck in the Sea of Wisdom", "Naufrage dans la mer de sagesse", "Schiffbruch im Meer der Weisheit", "智海の沈船", "지해의 침선", "Wrak w morzu mądrości", "Кораблекрушение в море мудрости", "Naufragio en el mar de la sabiduría")},
    "pro": {1: N("锈甲的呻吟", "The Groaning of Rusted Mail", "Le gémissement de la cotte rouillée", "Das Ächzen der verrosteten Rüstung", "錆甲の呻吟", "녹갑의 신음", "Jęk zardzewiałej zbroi", "Стон ржавой брони", "El gemido de la malla oxidada"),
            2: N("战骨的酥蚀", "The War-Bones Erode", "Les os de guerre s'érodent", "Die Kriegsknochen zerbröseln", "戦骨の酥蝕", "전골의 부식", "Kości wojenne się kruszą", "Воинские кости крошатся", "Los huesos de guerra se erosionan"),
            3: N("断刃的迟暮", "Twilight of the Broken Blade", "Crépuscule de la lame brisée", "Dämmerung der gebrochenen Klinge", "断刃の遅暮", "단인의 지목", "Zmierzch złamanego ostrza", "Закат сломанного клинка", "Ocaso de la hoja rota")},
}
for attr, effect in [("dip", "add_diplomacy_skill"), ("mar", "add_martial_skill"), ("ste", "add_stewardship_skill"),
                     ("int", "add_intrigue_skill"), ("lea", "add_learning_skill"), ("pro", "add_prowess_skill")]:
    for tier, v in ((1, -1), (2, -3), (3, -4)):
        C.append(("c", "skill", (effect, v), SKILL_C_NAMES[attr][tier]))

# ---- 蚀卷系 add_X_lifestyle_xp 负值（15）：-350/-650/-1000 ----
XP_C_NAMES = {
    ("dip", -350): N("席间的冷羹", "Cold Broth at the Feast", "Soupe froide au banquet", "Kalte Brühe beim Fest", "宴席の冷羹", "연회의 차가운 국", "Zimna zupa na uczcie", "Холодный суп на пиру", "Caldo frío en el banquete"),
    ("dip", -650): N("唇舌的石蜡", "Paraffin on Tongues", "Paraffine sur les langues", "Paraffin auf den Zungen", "唇舌の石蝋", "순설의 석유", "Parafina na językach", "Парафин на языках", "Parafina en las lenguas"),
    ("dip", -1000): N("万言的失声", "Ten Thousand Words, Silenced", "Mille mots, réduits au silence", "Zehntausend Worte, verstummt", "万言の失声", "만언의 실성", "Dziesięć tysięcy słów, uciszone", "Десять тысяч слов, безмолвные", "Diez mil palabras, enmudecidas"),
    ("mar", -350): N("沙盘的塌角", "The Sand Table Collapses", "Le coin du sand-box s'effondre", "Die Ecke des Sandtisches bricht ein", "砂盤の塌角", "모래판의 붕괴", "Narożnik planszy się sypie", "Угол песочного стола рушится", "La esquina del mapa de arena se derrumba"),
    ("mar", -650): N("兵棋的乱局", "The Wargame in Disarray", "La partie de guerre en désordre", "Das Kriegsspiel im Chaos", "兵棋の乱局", "병기의 난국", "Gra wojenna w nieładzie", "Военная игра в беспорядке", "El juego de guerra en desorden"),
    ("mar", -1000): N("烽火的湿薪", "Wet Fuel for the Beacon", "Bois mouillé pour le feu d'alarme", "Nasses Holz für das Leuchtfeuer", "烽火の湿薪", "봉화의 젖은 장작", "Mokre drwa na ognisko sygnałowe", "Мокрые дрова для сигнального огня", "Leña húmeda para la almenara"),
    ("ste", -350): N("账册的墨渍", "Ink Stains on the Ledger", "Taches d'encre sur le registre", "Tintenflecke im Buch", "帳簿の墨渍", "장부의 먹자국", "Atramentowe plamy w księdze", "Чернильные пятна в книге", "Manchas de tinta en el libro"),
    ("ste", -650): N("仓廪的鼠患", "Rats in the Granary", "Rats dans le grenier", "Ratten im Speicher", "倉廩の鼠患", "곡창의 서리", "Szczury w spichlerzu", "Крысы в амбаре", "Ratas en el granero"),
    ("ste", -1000): N("国帑的空算", "The Treasury's Empty Reckoning", "Le calcul vide du trésor", "Die leere Rechnung des Schatzes", "国帑の空算", "국고의 공산", "Pusty rachunek skarbca", "Пустой подсчёт казны", "La cuenta vacía del tesoro"),
    ("int", -350): N("暗巷的迷灯", "The Stray Lamp in Dark Alleys", "La lampe égarée des ruelles", "Die verirrte Lampe der Gassen", "暗巷の迷灯", "암항의 미등", "Błądząca lampa w alejach", "Заблудший фонарь в переулках", "La lámpara perdida en los callejones"),
    ("int", -650): N("罗网的断丝", "Broken Threads of the Net", "Fils brisés du filet", "Gesprengte Fäden des Netzes", "羅網の断糸", "라망의 단사", "Przerwane nici sieci", "Обрывки сети", "Hilos rotos de la red"),
    ("int", -1000): N("千面的哑剧", "The Dumb Show of a Thousand Faces", "La pantomime aux mille visages", "Das stumme Spiel der tausend Gesichter", "千面の唖劇", "천면의 아극", "Pantomima tysiąca twarzy", "Пантомима тысячи лиц", "La pantomima de mil rostros"),
    ("lea", -350): N("书库的蠹痕", "Bookworm Trails in the Library", "Pistes de ver dans la bibliothèque", "Bücherwurm-Spuren in der Bibliothek", "書庫の蠹痕", "서고의 충흔", "Ślady mola w bibliotece", "Следы книжного червя", "Rastros de polilla en la biblioteca"),
    ("lea", -650): N("青灯的泪尽", "The Green Lamp's Tears Run Dry", "Les larmes de la lampe verte s'épuisent", "Die Tränen der grünen Lampe versiegen", "青灯の涙尽", "청등의 눈물 마름", "Łzy zielonej lampy wysychają", "Слёзы зелёной лампы иссякают", "Las lágrimas de la lámpara verde se agotan"),
    ("lea", -1000): N("智海的搁滩", "Beached on the Shore of Wisdom", "Échoué sur la rive de la sagesse", "Gestrandet am Ufer der Weisheit", "智海の擱灘", "지해의 좌초", "Uwięziony na brzegu mądrości", "На мели у моря мудрости", "Varado en la orilla de la sabiduría"),
}
for (attr, v), names in XP_C_NAMES.items():
    C.append(("c", "xp", (f"add_{ATTR_FULL[attr]}_lifestyle_xp", v), names))


# ---- 蚀体系 add_trait（12）：6 普通 + 6 稀有 ----
TRAIT_C = [
    ("c", "weak", N("抽骨的酸软", "The Bone-Drawn Ache", "La douleur qui vide les os", "Der knochenleere Schmerz", "骨抜きの酸软", "뼈 빠진 쇠약", "Ból wyjmujący kości", "Слабость, вынимающая кости", "El dolor que vacía los huesos"),
        N("虚弱", "Weak", "Faible", "Schwach", "虚弱", "허약", "Słaby", "Слабый", "Débil")),
    ("c", "clubfooted", N("盘根的绊足", "The Root-Tangled Foot", "Le pied pris dans les racines", "Der wurzelverfängte Fuß", "盤根の绊足", "반근의 족", "Stopa w korzeniach", "Нога в корнях", "El pie enredado en raíces"),
        N("畸形足", "Clubfooted", "Pied-bot", "Klumpfuß", "内反足", "기형족", "Krzywa stopa", "Косолапый", "Patizambo")),
    ("c", "physique_bad_1", N("琉璃的脆纹", "The Brittle Vein in the Glass", "La veine fragile du verre", "Die spröde Ader im Glas", "琉璃の脆紋", "유리의 취약 문", "Krucha żyła w szkle", "Хрупкая жилка в стекле", "La veta quebradiza en el vidrio"),
        N("柔弱", "Delicate", "Délicat", "Zart", "繊細", "연약", "Delikatny", "Хрупкий", "Delicado")),
    ("c", "beauty_bad_1", N("蒙灰的铜镜", "The Dust-Dimmed Bronze Mirror", "Le miroir de bronze terni", "Der verstaubte Bronzespiegel", "蒙灰の銅鏡", "몽회의 동경", "Zakurzone lustro", "Запыленное медное зеркало", "El espejo de bronce empañado"),
        N("其貌不扬", "Homely", "Disgracieux", "Unansehnlich", "見劣り", "못생김", "Niepoczęty", "Невзрачный", "Poco agraciado")),
    ("c", "craven", N("膝软的阴影", "The Knee-Bending Shadow", "L'ombre qui plie les genoux", "Der kniebeugende Schatten", "膝軟の陰影", "무릎 꺾는 그림자", "Cień uginający kolana", "Тень, сгибающая колени", "La sombra que dobla las rodillas"),
        N("怯懦", "Craven", "Lâche", "Feige", "臆病", "비겁", "Tchórzliwy", "Трусливый", "Cobarde")),
    ("c", "lazy", N("席地的沉疴", "The Ground-Binding Lethargy", "La léthargie qui cloue au sol", "Die bodenbindende Lethargie", "席地の沉疴", "석지의 침고", "Letarg przykuwający do ziemi", "Летаргия, сковывающая землю", "La letargia que ata al suelo"),
        N("怠惰", "Lazy", "Paresseux", "Faul", "怠惰", "게으름", "Leniwy", "Ленивый", "Perezoso")),
    ("r", "sickly", N("缠身的病影", "The Clinging Shade of Illness", "L'ombre collante de la maladie", "Der klebende Schatten der Krankheit", "纏身の病影", "침신의 병영", "Lepki cień choroby", "Прилипчивая тень болезни", "La sombra pegajosa de la enfermedad"),
        N("体弱多病", "Sickly", "Maladif", "Kränklich", "病弱", "병약", "Chory", "Болезненный", "Enfermizo")),
    ("r", "hunchbacked", N("负山的佝偻", "The Mountain-Bearing Stoop", "La bosse qui porte la montagne", "Der bergtragende Buckel", "負山の僂儔", "부산의 구부", "Garba niosąca górę", "Горб, несущий гору", "La joroba que carga la montaña"),
        N("驼背", "Hunchbacked", "Bossu", "Buckelig", "せむし", "꼽추", "Garbaty", "Горбатый", "Jorobado")),
    ("r", "intellect_bad_1", N("雾锁的灵台", "The Fog-Locked Mind", "L'esprit enfermé dans la brume", "Der nebelverschlossene Geist", "霧鎖の霊台", "무쇠의 영대", "Umysł w mgle", "Ум в тумане", "La mente en la niebla"),
        N("迟钝", "Slow", "Lent", "Langsam", "鈍い", "둔함", "Tępy", "Тупой", "Lerdo")),
    ("r", "intellect_bad_2", N("熄焰的空颅", "The Skull of Quenched Flame", "Le crâne de flamme éteinte", "Der Schädel der erloschenen Flamme", "熄炎の空頭", "식염의 공두", "Czaszka ugaszonego płomienia", "Череп погасшего пламени", "El cráneo de la llama apagada"),
        N("痴愚", "Imbecile", "Imbécile", "Schwachsinnig", "白痴", "백치", "Głupi", "Глупый", "Imbécil")),
    ("r", "beauty_bad_2", N("碎面的铜镜", "The Bronze Mirror, Cracked", "Le miroir de bronze, fêlé", "Der Bronzespiegel, gesprungen", "砕面の銅鏡", "쇄면의 동경", "Pęknięte lustro", "Треснувшее медное зеркало", "El espejo de bronce, agrietado"),
        N("丑陋", "Ugly", "Laid", "Hässlich", "醜悪", "추함", "Brzydki", "Безобразный", "Feo")),
    ("r", "paranoid", N("窥隙的疑目", "The Suspicious Eye at Every Crack", "L'œil soupçonneux à chaque fente", "Das misstrauische Auge an jeder Ritze", "窺隙の疑目", "규극의 의목", "Podejrzliwe oko w każdej szczelinie", "Подозрительный глаз в каждой щели", "El ojo suspicaz en cada rendija"),
        N("多疑", "Paranoid", "Paranoïaque", "Paranoid", "疑心暗鬼", "편집증", "Paranoidalny", "Параноидальный", "Paranoico")),
]
for rarity, key, names, tword in TRAIT_C:
    C.append((rarity, "trait", f"add_trait = {key}", names, tword))


# ---- 修正系（10 年 modifier，11 项）----
MOD_C = [
    ("c", "xar_pc_health_s", "health = -0.4",
        N("蚀骨的寒痕", "The Bone-Gnawing Frost-Mark", "La marque de gel qui ronge les os", "Das knochenfressende Frostmale", "蝕骨の寒痕", "식골의 한흔", "Znak mrozu gryzącym kości", "Морозная метка, грызущая кости", "La marca de escarcha que roe los huesos"),
        N("健康 -0.4，持续 10 年", "-0.4 health, 10 years", "-0,4 santé, 10 ans", "-0,4 Gesundheit, 10 Jahre", "健康 -0.4、10 年間", "건강 -0.4, 10년", "-0,4 zdrowia, 10 lat", "-0,4 здоровья, на 10 лет", "-0,4 de salud, 10 años")),
    ("r", "xar_pc_health_m", "health = -0.8",
        N("寒焰的蚀体", "The Cold Flame Consumes", "La flamme froide consume", "Die kalte Flamme zehrt", "寒炎の蝕体", "한염의 식체", "Zimny płomień pożera", "Холодное пламя пожирает", "La llama fría consume"),
        N("健康 -0.8，持续 10 年", "-0.8 health, 10 years", "-0,8 santé, 10 ans", "-0,8 Gesundheit, 10 Jahre", "健康 -0.8、10 年間", "건강 -0.8, 10년", "-0,8 zdrowia, 10 lat", "-0,8 здоровья, на 10 лет", "-0,8 de salud, 10 años")),
    ("r", "xar_pc_health_l", "health = -1.2",
        N("余命的漏刻", "The Lifespan's Leaking Hourglass", "Le sablier percé de la vie", "Die undichte Sanduhr des Lebens", "余命の漏刻", "여명의 누각", "Przeciekająca klepsydra życia", "Дырявые часы жизни", "El reloj de arena roto de la vida"),
        N("健康 -1.2，持续 10 年", "-1.2 health, 10 years", "-1,2 santé, 10 ans", "-1,2 Gesundheit, 10 Jahre", "健康 -1.2、10 年間", "건강 -1.2, 10년", "-1,2 zdrowia, 10 lat", "-1,2 здоровья, на 10 лет", "-1,2 de salud, 10 años")),
    ("c", "xar_pc_fert_s", "fertility = -0.2",
        N("薪火的湿薪", "Damp Fuel on the Hearthfire", "Bois humide sur le feu", "Nasses Holz auf dem Herdfeuer", "薪火の湿薪", "신화의 습신", "Mokre drwa na ognisku", "Мокрые дрова на очаге", "Leña húmeda en el hogar"),
        N("生育 -20%，持续 10 年", "-20% fertility, 10 years", "-20 % fertilité, 10 ans", "-20 % Fruchtbarkeit, 10 Jahre", "出産率 -20%、10 年間", "출산율 -20%, 10년", "-20% płodności, 10 lat", "-20% к плодовитости, на 10 лет", "-20 % de fertilidad, 10 años")),
    ("r", "xar_pc_fert_m", "fertility = -0.35",
        N("嗣线的霜结", "Frost on the Line of Heirs", "Gel sur la lignée", "Frost auf der Erbenlinie", "嗣線の霜結", "사선의 상결", "Szron na linii dziedziców", "Иней на линии наследников", "Escarcha en la línea de herederos"),
        N("生育 -35%，持续 10 年", "-35% fertility, 10 years", "-35 % fertilité, 10 ans", "-35 % Fruchtbarkeit, 10 Jahre", "出産率 -35%、10 年間", "출산율 -35%, 10년", "-35% płodności, 10 lat", "-35% к плодовитости, на 10 лет", "-35 % de fertilidad, 10 años")),
    ("c", "xar_pc_vassal_s", "vassal_opinion = -10",
        N("阶下的窃议", "Whispers Below the Throne", "Murmures sous le trône", "Geflüster unter dem Thron", "階下の窃議", "계하의 절의", "Szepty pod tronem", "Шёпот под троном", "Susurros bajo el trono"),
        N("封臣好感 -10，持续 10 年", "-10 vassal opinion, 10 years", "-10 opinion des vassaux, 10 ans", "-10 Vasallenmeinung, 10 Jahre", "陪臣の評価 -10、10 年間", "봉신 호감 -10, 10년", "-10 opinii wasali, 10 lat", "-10 к мнению вассалов, на 10 лет", "-10 opinión de vasallos, 10 años")),
    ("r", "xar_pc_vassal_m", "vassal_opinion = -15",
        N("俯首的假面", "The Bowed Mask", "Le masque baissé", "Die gesenkte Maske", "俯首の仮面", "복수의 가면", "Pokorna maska", "Склонённая маска", "La máscara inclinada"),
        N("封臣好感 -15，持续 10 年", "-15 vassal opinion, 10 years", "-15 opinion des vassaux, 10 ans", "-15 Vasallenmeinung, 10 Jahre", "陪臣の評価 -15、10 年間", "봉신 호감 -15, 10년", "-15 opinii wasali, 10 lat", "-15 к мнению вассалов, на 10 лет", "-15 opinión de vasallos, 10 años")),
    ("c", "xar_pc_stress_s", "stress_gain_mult = 0.15",
        N("心弦的绷响", "The Heartstring Twangs Taut", "La corde du cœur se tend", "Die Herzensaite spannt sich", "心弦の繃響", "심현의 팽팽함", "Struna serca naciąga się", "Струна сердца натягивается", "La cuerda del corazón se tensa"),
        N("压力获取 +15%，持续 10 年", "+15% stress gain, 10 years", "+15 % gain de stress, 10 ans", "+15 % Stresszuwachs, 10 Jahre", "ストレス獲得 +15%、10 年間", "스트레스 획득 +15%, 10년", "+15% przyrostu stresu, 10 lat", "+15% к получению стресса, на 10 лет", "+15 % de ganancia de estrés, 10 años")),
    ("r", "xar_pc_stress_m", "stress_gain_mult = 0.25",
        N("梦魇的常客", "The Nightmare's Regular", "L'habitué du cauchemar", "Der Stammgast des Albtraums", "夢魘の常客", "몽염의 상객", "Stały gość koszmaru", "Постоянный гость кошмара", "El cliente habitual de la pesadilla"),
        N("压力获取 +25%，持续 10 年", "+25% stress gain, 10 years", "+25 % gain de stress, 10 ans", "+25 % Stresszuwachs, 10 Jahre", "ストレス獲得 +25%、10 年間", "스트레스 획득 +25%, 10년", "+25% przyrostu stresu, 10 lat", "+25% к получению стресса, на 10 лет", "+25 % de ganancia de estrés, 10 años")),
    ("c", "xar_pc_mprestige", "monthly_prestige = -0.5",
        N("名望的漏勺", "The Fame-Skimmer's Leak", "L'écumoire à renommée fuit", "Der Ruhmlöffel leckt", "名望の漏杓", "명망의 누국", "Durszlak sławy", "Дуршлаг славы", "El colador de la fama"),
        N("月威望 -0.5，持续 10 年", "-0.5 monthly prestige, 10 years", "-0,5 prestige mensuel, 10 ans", "-0,5 monatliches Prestige, 10 Jahre", "月威望 -0.5、10 年間", "월 위상 -0.5, 10년", "-0,5 prestiżu miesięcznie, 10 lat", "-0,5 престижа в месяц, на 10 лет", "-0,5 de prestigio mensual, 10 años")),
    ("c", "xar_pc_mpiety", "monthly_piety = -0.5",
        N("龛火的断供", "The Shrine Flame Unfed", "Le feu du sanctuaire sans offrande", "Das Schreinfeuer ohne Nachschub", "龕火の断供", "감화의 단공", "Ogień kapliczki bez dostawy", "Святыня без подношений", "La llama del altar sin ofrendas"),
        N("月虔诚 -0.5，持续 10 年", "-0.5 monthly piety, 10 years", "-0,5 piété mensuelle, 10 ans", "-0,5 monatliche Frömmigkeit, 10 Jahre", "月信心 -0.5、10 年間", "월 경건 -0.5, 10년", "-0,5 pobożności miesięcznie, 10 lat", "-0,5 благочестия в месяц, на 10 лет", "-0,5 de piedad mensual, 10 años")),
]
for rarity, mid, fields, names, sums in MOD_C:
    C.append((rarity, "mod", (mid, fields), names, sums))


# ---- 族黯系 add_dynasty_prestige 负值（4）----
for rarity, v, names in [
    ("c", -65, N("族徽的蒙尘", "Dust on the Crest", "Poussière sur le blason", "Staub auf dem Wappen", "家紋の蒙塵", "가문 문장의 먼지", "Kurz na herbie", "Пыль на гербе", "Polvo en el blasón")),
    ("c", -200, N("黯淡的族徽", "The Dimmed Crest", "Le blason terni", "Das verdunkelte Wappen", "暗淡の家紋", "암담한 가문 문장", "Przyciemniony herb", "Потускневший герб", "El blasón oscurecido")),
    ("r", -400, N("族焰的萎灭", "The House Flame Dwindles", "La flamme du sang s'éteint", "Das Hausfeuer schwindet", "族炎の萎滅", "족염의 위멸", "Płomień rodu przygasa", "Пламя рода угасает", "La llama de la casa mengua")),
    ("r", -650, N("谱系的断页", "The Pedigree's Torn Page", "La page arrachée du pedigree", "Die herausgerissene Seite des Stammbaums", "譜系の断頁", "보계의 단엽", "Wyrwana strona rodowodu", "Вырванная страница родословной", "La página arrancada del pedigrí")),
]:
    C.append((rarity, "dynasty", v, names))

# ---- 压契系 add_stress 正值（4）----
for rarity, v, names in [
    ("c", 65, N("压舱的石契", "The Stone Deed as Ballast", "L'acte de pierre en lest", "Die steinerne Urkunde als Ballast", "圧舱の石契", "압창의 석계", "Kamienna umowa jako balast", "Каменная купчая как балласт", "La escritura de piedra como lastre")),
    ("c", 100, N("账契的枷锁", "The Shackles of the Deed", "Les chaînes de l'acte", "Die Fesseln der Urkunde", "帳契の枷鎖", "장계의 가련", "Kajdany umowy", "Оковы договора", "Los grilletes de la escritura")),
    ("c", 135, N("梦魇的加演", "The Nightmare's Encore", "La reprise du cauchemar", "Die Zugabe des Albtraums", "夢魘の加演", "몽염의 앙코르", "Bis koszmaru", "Кошмар на бис", "El bis de la pesadilla")),
    ("r", 200, N("心渊的坠石", "The Stone Sinking into the Heart's Abyss", "La pierre qui coule dans l'abîme du cœur", "Der Stein, der in den Abgrund des Herzens sinkt", "心淵の墜石", "심연의 추석", "Kamień tonący w otchłani serca", "Камень, тонущий в бездне сердца", "La piedra que se hunde en el abismo del corazón")),
]:
    C.append((rarity, "stress_c", v, names))

# ---- 折寿系（1）：永久健康负修正 ----
C.append(("r", "custom", "add_character_modifier = { modifier = xar_pc_life }",
    N("灯芯的焦痕", "The Wick's Charred Scar", "La cicatrice de la mèche", "Die verbrannte Narbe des Dochts", "灯芯の焦痕", "심지의 초흔", "Zwęglona blizna knota", "Обожжённый след фитиля", "La cicatriz chamuscada de la mecha"),
    N("余命 -1（健康 -0.8，永久）", "-1 lifespan (permanent)", "-1 durée de vie (permanent)", "-1 Lebenserwartung (permanent)", "余命 -1（永続）", "여명 -1 (영구)", "-1 rok życia (na stałe)", "-1 год жизни (навсегда)", "-1 año de vida (permanente)")))

# ---- 传说诅咒（5，痛而不毁档）----
C.append(("l", "custom", "add_character_modifier = { modifier = xar_leg_cold days = 3650 }",
    N("蚀魂的寒斑", "The Soul-Gnawing Frostblight", "La gelure qui ronge l'âme", "Das seelenfressende Frostmal", "蝕魂の寒斑", "식혼의 한반", "Mrozowisko gryzące duszę", "Морозная язва, грызущая душу", "La helada que roe el alma"),
    N("健康 -2，持续 10 年", "-2 health, 10 years", "-2 santé, 10 ans", "-2 Gesundheit, 10 Jahre", "健康 -2、10 年間", "건강 -2, 10년", "-2 zdrowia, 10 lat", "-2 здоровья, на 10 лет", "-2 de salud, 10 años")))
C.append(("l", "custom", "add_character_modifier = { modifier = xar_leg_tax days = 3650 }",
    N("琉焰的抽成", "The Glassfire's Cut", "La part du verre-feu", "Der Anteil des Glasfeuers", "琉璃の取り分", "유리염의 몫", "Udział szklanego ognia", "Доля стеклянного пламени", "La tajada del fuego vítreo"),
    N("月收入 -40%，持续 10 年", "-40% monthly income, 10 years", "-40 % revenu mensuel, 10 ans", "-40 % monatliches Einkommen, 10 Jahre", "月収 -40%、10 年間", "월 수입 -40%, 10년", "-40% dochodu miesięcznie, 10 lat", "-40% к месячному доходу, на 10 лет", "-40 % de ingreso mensual, 10 años")))
C.append(("l", "custom", "add_character_modifier = { modifier = xar_leg_vassal days = 3650 }",
    N("众叛的耳语", "Whispers of Betrayal", "Murmures de trahison", "Geflüster des Verrats", "衆叛の囁き", "중반의 속삭임", "Szepty zdrady", "Шёпоты предательства", "Susurros de traición"),
    N("封臣好感 -20，持续 10 年", "-20 vassal opinion, 10 years", "-20 opinion des vassaux, 10 ans", "-20 Vasallenmeinung, 10 Jahre", "陪臣の評価 -20、10 年間", "봉신 호감 -20, 10년", "-20 opinii wasali, 10 lat", "-20 к мнению вассалов, на 10 лет", "-20 opinión de vasallos, 10 años")))
C.append(("l", "custom", "add_diplomacy_skill = -1\n\tadd_martial_skill = -1\n\tadd_stewardship_skill = -1\n\tadd_intrigue_skill = -1\n\tadd_learning_skill = -1\n\tadd_prowess_skill = -1",
    N("褪色的馈赠", "The Faded Gift", "Le don fané", "Das verblasste Geschenk", "褪色の贈り物", "퇴색의 선물", "Wyblakły dar", "Вырожденный дар", "El regalo desvaído"),
    N("六维各 -1", "-1 to all six skills", "-1 aux six compétences", "-1 auf alle sechs Fähigkeiten", "六能力各 -1", "여섯 능력 각 -1", "-1 do sześciu atrybutów", "-1 ко всем шести навыкам", "-1 a los seis atributos")))
C.append(("l", "custom", "add_stress = 150\n\tadd_character_modifier = { modifier = xar_leg_stress days = 3650 }",
    N("重压的账契", "The Crushing Deed", "L'acte écrasant", "Die erdrückende Urkunde", "重圧の帳契", "중압의 장계", "Przytłaczająca umowa", "Давящая купчая", "La escritura aplastante"),
    N("压力 +150，压力获取 +30% 持续 10 年", "+150 stress, +30% stress gain for 10 years", "+150 stress, +30 % gain de stress pendant 10 ans", "+150 Stress, +30 % Stresszuwachs für 10 Jahre", "ストレス +150、獲得 +30% が 10 年間", "스트레스 +150, 획득 +30% (10년)", "+150 stresu, +30% przyrostu przez 10 lat", "+150 стресса, +30% к получению на 10 лет", "+150 estrés, +30 % de ganancia durante 10 años")))


# ---- 传说/余火条目引用的修正定义（生成进 xar_generated_pool_modifiers.txt）----
EXTRA_MODIFIERS = {
    # 漏金系（月收入 drain，10 年；custom 条目的 code 直接引用这些 id）
    "xar_pc_drain_a": "monthly_income = -0.3",
    "xar_pc_drain_b": "monthly_income = -0.5",
    "xar_pc_drain_c": "monthly_income = -0.75",
    "xar_pc_drain_d": "monthly_income = -1.0",
    "xar_pc_drain_e": "monthly_income = -1.25",
    "xar_pc_drain_f": "monthly_income = -1.5",
    "xar_pc_drain_g": "monthly_income = -2.0",
    # ----
    "xar_pb_life_2": "health = 2",            # 不灭的灯芯（永久）
    "xar_leg_life": "health = 10",            # 不灭的灯芯·真（永久）
    "xar_leg_wealth": "monthly_income = 1",   # 万邦的账簿（10 年）
    "xar_pc_life": "health = -0.8",           # 灯芯的焦痕（永久）
    "xar_leg_cold": "health = -2",            # 蚀魂的寒斑（10 年）
    "xar_leg_tax": "monthly_income_mult = -0.4",  # 琉焰的抽成（10 年）
    "xar_leg_vassal": "vassal_opinion = -20",     # 众叛的耳语（10 年）
    "xar_leg_stress": "stress_gain_mult = 0.3",   # 重压的账契（10 年）
}

WEIGHTS = {"c": 10, "r": 3, "l": 1}
