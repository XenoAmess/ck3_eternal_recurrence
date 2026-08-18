# -*- coding: utf-8 -*-
"""Machine-authoritative contracts and Glassfire Gaze progression."""

CONTRACTS = (
    {
        "id": 1, "key": "conqueror", "name_zh": "征服者", "name_en": "Conqueror",
        "goal_zh": "赢得战争", "goal_en": "win wars",
        "milestones_zh": ("第一面败旗已经落进火里。", "疆界开始记得你的名字。", "十场胜利，足够让王冠也学会低头。"),
        "milestones_en": ("The first fallen banner enters the flame.", "Borders are beginning to remember your name.", "Ten victories are enough to teach crowns to bow."),
    },
    {
        "id": 2, "key": "weaver", "name_zh": "织网者", "name_en": "Webweaver",
        "goal_zh": "使用牵制", "goal_en": "spend hooks",
        "milestones_zh": ("第一根暗线已经绷紧。", "宫廷里的呼吸开始随你的指尖起伏。", "十根线结成一张网，而网心总是温暖的。"),
        "milestones_en": ("The first hidden thread is taut.", "A court now breathes with your fingertips.", "Ten threads make a web, and its center is always warm."),
    },
    {
        "id": 3, "key": "saint", "name_zh": "圣徒", "name_en": "Saint",
        "goal_zh": "见证直辖伯爵领改宗", "goal_en": "see held counties change faith",
        "milestones_zh": ("第一簇祷声有了新的回音。", "六座祭坛已经替你保存余温。", "十片土地同诵一名，信仰也有了分量。"),
        "milestones_en": ("The first prayer returns with a new echo.", "Six altars now preserve your warmth.", "Ten lands speak one name; even faith has acquired weight."),
    },
    {
        "id": 4, "key": "patriarch", "name_zh": "家主", "name_en": "Patriarch",
        "goal_zh": "迎来子嗣", "goal_en": "welcome children",
        "milestones_zh": ("第一声啼哭替契约添了一行小字。", "血脉已经长出六条温热的枝。", "十枚新名字，足够把一生写成族谱。"),
        "milestones_en": ("A first cry adds fine print to the pact.", "Six warm branches now grow from your bloodline.", "Ten new names are enough to turn one life into a lineage."),
    },
    {
        "id": 5, "key": "steward", "name_zh": "贤王", "name_en": "Wise Ruler",
        "goal_zh": "完成建设", "goal_en": "complete buildings",
        "milestones_zh": ("第一块新石已经压住旧日的尘。", "六处梁柱替你托起了国度。", "十座新建之物，会比赞歌更久地记住你。"),
        "milestones_en": ("The first new stone has pinned down yesterday's dust.", "Six sets of pillars now shoulder your realm.", "Ten works will remember you longer than any hymn."),
    },
    {
        "id": 6, "key": "reveler", "name_zh": "享乐者", "name_en": "Hedonist",
        "goal_zh": "在低压力下度过生辰", "goal_en": "reach birthdays below high stress",
        "milestones_zh": ("第三支生日蜡烛没有被忧愁吹灭。", "六度岁月从容落杯。", "十个轻盈的年头，情感的滋味恰到好处。"),
        "milestones_en": ("A third birthday candle survives sorrow's breath.", "Six years have settled calmly into the cup.", "Ten light years: emotion seasoned to perfection."),
    },
)

MILESTONES = (3, 6, 10)


GAZE_MILESTONES = (
    {
        "xp": 10, "rerolls": 1, "seals": 0,
        "modifiers": (("diplomacy", 1),),
        "growth_zh": "外交 +1", "growth_en": "Diplomacy +1",
        "desc_zh": "第一重火纹睁开。言辞会更容易找到门缝；我也赠你一次重抽，好让垂青显得更合心意。",
        "desc_en": "The first ring of glassfire opens. Words find narrower doors, and I grant one reroll so favor may better suit your taste.",
    },
    {
        "xp": 20, "rerolls": 0, "seals": 1,
        "modifiers": (("martial", 1),),
        "growth_zh": "军事 +1", "growth_en": "Martial +1",
        "desc_zh": "第二重火纹学会衡量锋刃。你获得一枚封印；偶尔免去一道咒痕，会让下一笔典当更香甜。",
        "desc_en": "The second ring learns the measure of a blade. You gain one seal; waiving a curse-mark now and then sweetens the next pawn.",
    },
    {
        "xp": 30, "rerolls": 2, "seals": 0,
        "modifiers": (("stewardship", 1),),
        "growth_zh": "管理 +1", "growth_en": "Stewardship +1",
        "desc_zh": "第三重火纹开始替你数清每一粒余烬。两次重抽归你，旅人——选择越多，签下的欲望便越像出自本心。",
        "desc_en": "The third ring counts every ember for you. Two rerolls are yours, traveler; the more choices offered, the more desire resembles consent.",
    },
    {
        "xp": 40, "rerolls": 0, "seals": 2,
        "modifiers": (("intrigue", 1),),
        "growth_zh": "谋略 +1", "growth_en": "Intrigue +1",
        "desc_zh": "第四重火纹懂得把秘密藏在眨眼之间。两枚封印已经冷却，足够你从容挑选愿意留下的咒痕。",
        "desc_en": "The fourth ring hides secrets between blinks. Two seals have cooled, enough to choose which curse-marks you are willing to keep.",
    },
    {
        "xp": 50, "rerolls": 2, "seals": 1,
        "modifiers": (("learning", 1),),
        "growth_zh": "学识 +1", "growth_en": "Learning +1",
        "desc_zh": "第五重火纹照见契约背面的字。两次重抽与一枚封印，请收好；知识从不使代价消失，只让你看清它。",
        "desc_en": "The fifth ring illuminates the pact's reverse. Keep two rerolls and one seal; knowledge never removes a price, only reveals it.",
    },
    {
        "xp": 60, "rerolls": 1, "seals": 2,
        "modifiers": (("prowess", 2),),
        "growth_zh": "勇武 +2", "growth_en": "Prowess +2",
        "desc_zh": "第六重火纹沿骨骼燃烧，却仍温柔得像拥抱。一次重抽、两枚封印，以及更锋利的躯壳，都是我的垂青。",
        "desc_en": "The sixth ring burns along the bone, gentle as an embrace. One reroll, two seals, and a sharper vessel are all my favor.",
    },
    {
        "xp": 70, "rerolls": 3, "seals": 1,
        "modifiers": (("diplomacy", 1), ("intrigue", 1)),
        "growth_zh": "外交 +1、谋略 +1", "growth_en": "Diplomacy +1, Intrigue +1",
        "desc_zh": "第七重火纹让真话与谎言共享同一种温度。三次重抽和一枚封印，足够把偶然雕成你偏爱的命运。",
        "desc_en": "The seventh ring gives truth and lies the same warmth. Three rerolls and one seal can carve chance into your preferred fate.",
    },
    {
        "xp": 80, "rerolls": 1, "seals": 3,
        "modifiers": (("martial", 1), ("stewardship", 1)),
        "growth_zh": "军事 +1、管理 +1", "growth_en": "Martial +1, Stewardship +1",
        "desc_zh": "第八重火纹已经能替王冠称重。一次重抽、三枚封印；你可以更大胆地伸手，而我会耐心记账。",
        "desc_en": "The eighth ring can weigh a crown. One reroll and three seals let you reach more boldly while I keep patient account.",
    },
    {
        "xp": 90, "rerolls": 4, "seals": 2,
        "modifiers": (("learning", 1), ("prowess", 2)),
        "growth_zh": "学识 +1、勇武 +2", "growth_en": "Learning +1, Prowess +2",
        "desc_zh": "第九重火纹几乎与灵魂重合。四次重抽、两枚封印——终末尚远，你却已学会如何向它索价。",
        "desc_en": "The ninth ring nearly overlaps the soul. Four rerolls and two seals; the end is distant, yet you have learned to name its price.",
    },
    {
        "xp": 100, "rerolls": 3, "seals": 4,
        "modifiers": (("diplomacy", 1), ("martial", 1), ("stewardship", 1),
                      ("intrigue", 1), ("learning", 1), ("prowess", 2)),
        "growth_zh": "五维各 +1、勇武 +2", "growth_en": "All five skills +1, Prowess +2",
        "desc_zh": "第十重火纹闭合为完整的琉焰之视。三次重抽、四枚封印，以及最后一轮成长——旅人，你终于像一件值得珍藏的契物。",
        "desc_en": "The tenth ring closes into the full Glassfire Gaze. Three rerolls, four seals, and one final growth: traveler, you have become a keepsake worth preserving.",
    },
)
