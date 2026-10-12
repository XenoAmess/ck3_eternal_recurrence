"""Authored active practices; permanent tenet modifiers live in content_data.

These are deliberate game mechanics, not claims of supernatural historical
abilities. Costs are charged only by a freshly qualified event option. Temporary
training survives changing one's tenets, but each practice retains its cooldown.
"""
from __future__ import annotations

from dataclasses import dataclass
from content_data import TENETS_BY_CODE


@dataclass(frozen=True)
class PracticeOption:
    zh: str
    en: str
    gold: int = 0
    piety: int = 0
    prestige: int = 0
    rewards: tuple[str, ...] = ()
    character: tuple[tuple[str, str], ...] = ()
    county: tuple[tuple[str, str], ...] = ()
    conditions: tuple[str, ...] = ()
    control: int = 0
    development: int = 0
    duration: int = 1095
    # T33 alternates genuine stored phases; neither branch grants both rewards.
    phase: str = ""
    tutor: bool = False


@dataclass(frozen=True)
class Practice:
    code: str
    zh: str
    en: str
    purpose_zh: str
    purpose_en: str
    options: tuple[PracticeOption, ...]
    cooldown: int = 1095

    @property
    def slug(self) -> str:
        return TENETS_BY_CODE[self.code].slug

    @property
    def key(self) -> str:
        return "lyd_play_" + self.slug


def option(zh: str, en: str, *, character=(), county=(), rewards=(), conditions=(), **kw) -> PracticeOption:
    return PracticeOption(zh, en, rewards=tuple(rewards), character=tuple(character), county=tuple(county), conditions=tuple(conditions), **kw)


PRACTICES = (
    Practice('T01', '告天审政', 'Review the Mandate', '斋戒告天，以可见的治绩重建统治威望。', 'Fast and review public government to renew the authority of your rule.', (
        option('整肃政令，安定京畿', 'Set government in order', piety=200, rewards=('add_legitimacy = 100', 'add_prestige = 250'), character=(('stewardship','3'),), control=25),), 1460),
    Practice('T02', '慎独立誓', 'Keep a Private Vigil', '独处检点念头，建立不为外物所动的防备。', 'Examine your intentions in solitude and become harder to manipulate.', (
        option('闭门省察，不欺暗室', 'Examine myself in solitude', prestige=150, rewards=('add_stress = -80', 'add_intrigue_lifestyle_xp = 400'), character=(('intrigue','4'),('enemy_hostile_scheme_success_chance_add','-20'))),)),
    Practice('T03', '礼乐合奏', 'Convene Ritual and Music', '以礼乐协调人心，使朝廷与乡里共享安宁。', 'Use ritual and music to reconcile court and county.', (
        option('延请乐工，合奏雅乐', 'Invite the musicians', gold=150, rewards=('add_stress = -60', 'add_diplomacy_lifestyle_xp = 400'), character=(('diplomacy','4'),('vassal_opinion','15')), county=(('county_opinion_add','20'),)),)),
    Practice('T04', '修谱祭祖', 'Renew the Ancestral Register', '追述先人，修明族谱，使宗族记得彼此责任。', 'Renew the genealogy and the responsibilities of kinship.', (
        option('祭祖合族，续修家乘', 'Gather the dynasty at the ancestral rite', gold=125, rewards=('add_prestige = 400', 'add_piety = 200'), character=(('dynasty_opinion','25'),('fertility','0.20'))),), 1825),
    Practice('T05', '清查名分', 'Audit Names and Duties', '清查官责与账册，扩充亲自治理的能力。', 'Audit offices and accounts to improve direct administration.', (
        option('循名责实，重整职司', 'Make every office answer for its duties', prestige=200, rewards=('add_stewardship_lifestyle_xp = 500', 'add_stress = 30'), character=(('domain_limit','1'),('stewardship','4')), control=20),), 1460),
    Practice('T06', '开仓赈恤', 'Open the Relief Granaries', '让财用救济乡里，以实际仁政换取民心。', 'Turn wealth into tangible relief and public trust.', (
        option('赈粮济困，不取偿还', 'Distribute relief without demanding repayment', gold=200, rewards=('add_piety = 400', 'add_legitimacy = 75'), county=(('county_opinion_add','35'),('epidemic_resistance','20')), control=35),), 1460),
    Practice('T07', '冒颜匡谏', 'Invite Unwelcome Remonstrance', '让臣下公开指出过失，以眼前颜面换取长远信任。', 'Sacrifice immediate prestige so your vassals can speak honestly.', (
        option('纳逆耳之言，改正政失', 'Accept the criticism and correct my government', prestige=300, rewards=('add_legitimacy = 150', 'add_stress = 25'), character=(('vassal_opinion','25'),('diplomacy','3'))),), 1460),
    Practice('T08', '授业传经', 'Teach the Classics', '亲授经义，既精进己学，也培养一位真实在廷成人。', 'Teach the classics, advancing yourself and an adult at your court.', (
        option('开讲传道，奖掖后学', 'Open the lecture hall', gold=100, rewards=('add_learning_lifestyle_xp = 550', 'add_piety = 200'), character=(('learning','4'),), conditions=('is_landed = yes',), tutor=True),), 1460),
    Practice('T09', '扩充四端', 'Cultivate the Four Sprouts', '择一善端加以践履；四条道路给予不同的实际所得。', 'Choose one moral beginning and put it into practice.', (
        option('恻隐：恤民', 'Compassion: relieve the people', gold=150, rewards=('add_piety = 350',), county=(('county_opinion_add','30'),), control=25),
        option('羞恶：正己', 'Shame: put myself in order', piety=150, rewards=('add_stress = -75',), character=(('enemy_hostile_scheme_success_chance_add','-20'),('intrigue','3'))),
        option('辞让：和众', 'Deference: reconcile the court', prestige=150, rewards=('add_diplomacy_lifestyle_xp = 600',), character=(('vassal_opinion','20'),)),
        option('是非：明辨', 'Discernment: distinguish right from wrong', gold=100, rewards=('add_learning_lifestyle_xp = 650',), character=(('learning','4'),)),)),
    Practice('T10', '师法习律', 'Train through Rules and Teachers', '以反复训练矫正习性；勤勉也会带来压力。', 'Repeated training disciplines your habits, at a cost in stress.', (
        option('习法度与军政', 'Practice disciplined administration', gold=125, rewards=('add_stress = 35', 'add_martial_lifestyle_xp = 400', 'add_stewardship_lifestyle_xp = 400'), character=(('martial','3'),('stewardship','3'))),)),
    Practice('T11', '集义誓师', 'Rally the Righteous Host', '在真实战争中振奋军心，不凭誓言凭空生成军队。', 'Rally an army during a real war; vows do not conjure troops.', (
        option('正其师出，亲励将士', 'Lead the host by righteous example', piety=250, rewards=('add_martial_lifestyle_xp = 400',), character=(('prowess','6'),('knight_effectiveness_mult','0.35')), conditions=('is_at_war = yes',), duration=730),), 1460),
    Practice('T12', '灾后省政', 'Rebuild after Disorder', '京畿控制力不足时，以反省与投入恢复秩序。', 'When your capital lacks control, turn reflection into reconstruction.', (
        option('修缮灾后政务', 'Rebuild local government', gold=175, rewards=('add_legitimacy = 75',), county=(('development_growth_factor','0.35'),), conditions=('capital_county = { county_control < 80 }',), control=40, development=50),), 1460),
    Practice('T13', '养生恤亲', 'Care for Life and Kin', '同体之仁先及自身与家族的生养。', 'Care for the life and continuity of yourself and your dynasty.', (
        option('节劳养生，亲睦宗族', 'Rest and attend to my kin', gold=125, rewards=('add_stress = -60',), character=(('health','1'),('dynasty_opinion','20'),('fertility','0.15'))),), 1460),
    Practice('T14', '亲察工物', 'Investigate Works and Things', '亲自观察田亩与工艺，把知识变为京畿发展。', 'Study farming and craft directly, turning knowledge into development.', (
        option('测量田亩，考察工艺', 'Survey fields and workshops', gold=150, rewards=('add_learning_lifestyle_xp = 600',), county=(('development_growth_factor','0.40'),), development=75),), 1460),
    Practice('T15', '持敬专修', 'Undertake Reverent Study', '一段专注修养换取清明，暂且疏远世俗欢娱。', 'Dedicated study brings clarity while worldly pleasures are set aside.', (
        option('屏除杂念，持敬专修', 'Set distractions aside', piety=175, rewards=('add_stress = -100', 'add_learning_lifestyle_xp = 500'), character=(('learning','5'),('stress_gain_mult','-0.25'),('fertility','-0.15'))),), 1460),
    Practice('T16', '舍利明心', 'Give Wealth to Clarify the Heart', '舍弃一笔可观财物，以行动证明所守。', 'Give up substantial wealth to demonstrate what you truly value.', (
        option('散财助学，返求本心', 'Endow learning and examine the heart', gold=250, rewards=('add_piety = 650', 'add_prestige = 300'), character=(('learning','3'),('same_faith_opinion','20'))),), 1825),
    Practice('T17', '问道庶人', 'Learn from Ordinary People', '走出书斋，听取乡人的实际经验。', 'Leave the study and listen to the experience of ordinary people.', (
        option('访民问俗，取善于人', 'Listen to the county', prestige=150, rewards=('add_learning_lifestyle_xp = 350', 'add_diplomacy_lifestyle_xp = 450'), county=(('county_opinion_add','25'),), control=20),)),
    Practice('T18', '践履承诺', 'Make Good on a Commitment', '所知必须落实为一项实际职责。', 'What you know must become a concrete duty.', (
        option('履行治民之责', 'Fulfil my duty of government', gold=175, rewards=('add_stewardship_lifestyle_xp = 650', 'add_legitimacy = 75'), county=(('tax_mult','0.25'),), control=30),
        option('履行临阵之责', 'Fulfil my duty in the field', prestige=200, rewards=('add_martial_lifestyle_xp = 650',), character=(('prowess','5'),('army_maintenance_mult','-0.25')), conditions=('is_at_war = yes',), duration=730),)),
    Practice('T19', '营建礼祠', 'Commission Ritual Architecture', '以经礼校定营建法式，集中资源修筑宗教地产。', 'Use ritual scholarship to organize the construction of temples.', (
        option('校定祠式，招集工匠', 'Prepare plans and gather the builders', piety=250, gold=100, rewards=('add_learning_lifestyle_xp = 300',), character=(('church_holding_build_gold_cost','-0.30'),('church_holding_build_speed','-0.35')), conditions=('is_landed = yes',), duration=1460),), 1825),
    Practice('T20', '跨经会讲', 'Bring the Classics into Dialogue', '以经学融通另一门实践之学，所选路径确实不同。', 'Connect classical learning with one practical discipline.', (
        option('经义与政事', 'Classics and government', gold=125, rewards=('add_learning_lifestyle_xp = 450', 'add_stewardship_lifestyle_xp = 450'), character=(('stewardship','3'),)),
        option('经义与邦交', 'Classics and diplomacy', prestige=150, rewards=('add_learning_lifestyle_xp = 450', 'add_diplomacy_lifestyle_xp = 450'), character=(('diplomacy','3'),)),
        option('经义与军旅', 'Classics and command', piety=175, rewards=('add_learning_lifestyle_xp = 450', 'add_martial_lifestyle_xp = 450'), character=(('martial','3'),)),), 1460),
    Practice('T21', '修春秋实录', 'Commission a Candid Chronicle', '以笔削明是非，也接受记述过失的压力。', 'Make moral judgments in a candid chronicle, including your own failings.', (
        option('秉笔直书，不隐己过', 'Record the truth, including my mistakes', gold=150, rewards=('add_legitimacy = 125', 'add_prestige = 500', 'add_stress = 40'), character=(('learning','4'),('vassal_opinion','-5'))),), 1825),
    Practice('T22', '勘农备荒', 'Survey Farms and Prepare for Scarcity', '不待天意赐福，主动修整农业与储备。', 'Do not wait for heavenly favor: improve farming and preparations.', (
        option('劝农储粟，修整水利', 'Repair irrigation and store grain', gold=200, rewards=('add_stewardship_lifestyle_xp = 500',), county=(('tax_mult','0.30'),('levy_reinforcement_rate','0.30'),('development_growth_factor','0.30')), development=50),), 1825),
    Practice('T23', '澄心复性', 'Retreat to Restore Clarity', '在和平中暂离纷扰，以休养恢复本性。', 'Withdraw from distractions during peace and recover your clarity.', (
        option('暂息机务，澄心静养', 'Take a peaceful retreat', gold=100, rewards=('add_stress = -120', 'add_learning_lifestyle_xp = 350'), character=(('health','0.75'),('stress_gain_mult','-0.30')), conditions=('is_at_war = no',), duration=730),), 1460),
    Practice('T24', '缔结乡约', 'Establish a Local Compact', '把日用伦理落实为京畿互助与自治。', 'Make everyday ethics into mutual aid and local order.', (
        option('公议乡约，互助守望', 'Agree on a compact of mutual aid', gold=125, prestige=100, rewards=('add_diplomacy_lifestyle_xp = 400',), county=(('county_opinion_add','30'),('monthly_county_control_growth_factor','0.50')), control=40),), 1460),
    Practice('T25', '六艺习行', 'Practice the Six Arts', '六种训练分别通往礼、乐、射、御、书、数的实际能力。', 'Six distinct disciplines develop different practical abilities.', (
        option('礼：习仪', 'Rites: practice ceremony', piety=125, rewards=('add_diplomacy_lifestyle_xp = 600', 'add_prestige = 150'), character=(('vassal_opinion','15'),)),
        option('乐：习和', 'Music: cultivate harmony', gold=100, rewards=('add_stress = -90',), character=(('diplomacy','5'),('stress_loss_mult','0.30'))),
        option('射：习武', 'Archery: train in arms', gold=125, rewards=('add_martial_lifestyle_xp = 600',), character=(('prowess','6'),)),
        option('御：习军', 'Charioteering: train in command', prestige=150, rewards=('add_martial_lifestyle_xp = 500',), character=(('martial','5'),('knight_effectiveness_mult','0.20'))),
        option('书：习文', 'Writing: study the written word', gold=100, rewards=('add_learning_lifestyle_xp = 650',), character=(('learning','4'),)),
        option('数：习算', 'Mathematics: study calculation', gold=125, rewards=('add_stewardship_lifestyle_xp = 650',), character=(('stewardship','4'),('monthly_income_mult','0.15'))),)),
    Practice('T26', '校勘辨伪', 'Collate and Authenticate Texts', '投入长期考据，分辨版本与伪说。', 'Invest in textual scholarship and the authentication of sources.', (
        option('搜集异本，校勘群经', 'Collect and collate the manuscripts', gold=200, rewards=('add_learning_lifestyle_xp = 900', 'add_stress = 30'), character=(('learning','6'),('cultural_head_fascination_mult','0.25')), duration=1460),), 1825),
    Practice('T27', '兴办实业', 'Invest in Practical Achievement', '集中财政经营工事，使道义体现为可见的事业。', 'Concentrate resources on works that turn principle into achievement.', (
        option('筹资兴业，整备工料', 'Fund the works and organize supplies', gold=300, rewards=('add_stewardship_lifestyle_xp = 650',), character=(('monthly_income_mult','0.30'),), county=(('build_speed','-0.35'),('tax_mult','0.30')), development=50, duration=1460),), 1825),
    Practice('T28', '约束军纪', 'Discipline the Army', '战时抑制暴掠，以纪律降低损耗、恢复京畿秩序。', 'Restrain plunder during war, lowering costs and restoring order.', (
        option('申明军令，禁绝暴掠', 'Proclaim and enforce military discipline', prestige=250, rewards=('add_martial_lifestyle_xp = 450', 'add_piety = 200'), character=(('army_maintenance_mult','-0.30'),('martial','4')), conditions=('is_at_war = yes',), control=25, duration=730),), 1460),
    Practice('T29', '私下补过', 'Make Quiet Amends', '放弃威吓的便利，以改过重建正当性。', 'Give up intimidation and rebuild legitimacy by making amends.', (
        option('减损威势，诚实补过', 'Make amends without demanding praise', gold=125, rewards=('add_dread = -30', 'add_legitimacy = 100', 'add_stress = -60'), character=(('enemy_hostile_scheme_success_chance_add','-25'),('diplomacy','3'))),)),
    Practice('T30', '经义变法', 'Reform through Interpretation', '以新解经义推动政务改革，也承担短期民怨。', 'Use fresh interpretation to reform administration, accepting disruption.', (
        option('变通制度，集中营建', 'Reform the institutions and organize construction', gold=200, prestige=200, rewards=('add_stewardship_lifestyle_xp = 700',), county=(('build_speed','-0.40'),('development_growth_factor','0.50'),('county_opinion_add','-10')), duration=1460),), 1825),
    Practice('T31', '观象定策', 'Use Patterns to Form a Strategy', '象数是筹划的方法；选择财计、备御或研学，不预言事件。', 'Use patterns for planning: finance, defense, or study, not prophecy.', (
        option('财计之策', 'Plan the finances', gold=150, rewards=('add_stewardship_lifestyle_xp = 500',), character=(('monthly_income_mult','0.25'),('stewardship','3'))),
        option('备御之策', 'Plan the defenses', prestige=175, rewards=('add_martial_lifestyle_xp = 500',), character=(('martial','4'),('siege_phase_time','-0.15')), county=(('levy_size','0.25'),)),
        option('研学之策', 'Plan a course of study', piety=175, rewards=('add_learning_lifestyle_xp = 650',), character=(('learning','4'),('monthly_lifestyle_xp_gain_mult','0.20'))),)),
    Practice('T32', '论玄释纷', 'Debate the Profound', '以会通之论疏解纷争，减少一时逐利。', 'Use philosophical debate to resolve disputes, setting profit aside.', (
        option('开席论玄，求同存异', 'Host a searching philosophical debate', gold=125, rewards=('add_learning_lifestyle_xp = 650', 'add_piety = 300'), character=(('learning','4'),('same_faith_opinion','25'),('monthly_income_mult','-0.10'))),), 1460),
    Practice('T33', '问学与践行', 'Alternate Inquiry and Practice', '先问学、后践行，两步不能以一次点击兼得。', 'Inquire first, then act: the two stages cannot be completed with one choice.', (
        option('问学：积累可行之知', 'Inquiry: prepare actionable knowledge', gold=100, rewards=('add_learning_lifestyle_xp = 600',), character=(('learning','3'),), phase='inquiry', duration=365),
        option('践行：完成所学之事', 'Practice: carry out what I learned', piety=200, rewards=('add_stewardship_lifestyle_xp = 600', 'add_gold = 200', 'add_prestige = 200'), character=(('stewardship','3'),), phase='practice', duration=365),), 365),
    Practice('T34', '育养生生', 'Nurture Continuing Life', '支持族人生养，使生命的延续成为共同责任。', 'Support the growth of your dynasty as a shared responsibility.', (
        option('扶幼恤长，厚养宗族', 'Care for the young and the old', gold=200, rewards=('add_piety = 300', 'add_stress = -40'), character=(('health','0.75'),('fertility','0.35'),('dynasty_opinion','30')), duration=1460),), 1825),
    Practice('T35', '静坐求得', 'Sit Quietly and Find Understanding', '静养中求得自明，暂时减少应酬。', 'Seek understanding through quiet cultivation and fewer social duties.', (
        option('静坐涵泳，反求自得', 'Sit in quiet contemplation', prestige=150, rewards=('add_learning_lifestyle_xp = 750', 'add_stress = -100'), character=(('learning','6'),('diplomacy','-2')), duration=730),), 1460),
    Practice('T36', '随处体认', 'Find Principle in the Present', '在眼前的行政、人伦或军旅中择一体认。', 'Find principle in the government, relationships, or conflict before you.', (
        option('在政事中体认', 'Recognize principle in administration', gold=150, rewards=('add_stewardship_lifestyle_xp = 550', 'add_legitimacy = 75'), county=(('tax_mult','0.20'),), control=25),
        option('在人伦中体认', 'Recognize principle in relationships', prestige=150, rewards=('add_diplomacy_lifestyle_xp = 550', 'add_stress = -50'), character=(('diplomacy','4'),('dynasty_opinion','20'))),
        option('在军旅中体认', 'Recognize principle in the field', piety=200, rewards=('add_martial_lifestyle_xp = 550',), character=(('martial','4'),('prowess','4'),('knight_effectiveness_mult','0.25')), conditions=('is_at_war = yes',), duration=730),)),
)

CHARACTER_KEYS = frozenset('learning stewardship diplomacy martial intrigue prowess health fertility domain_limit vassal_opinion dynasty_opinion same_faith_opinion monthly_income_mult army_maintenance_mult knight_effectiveness_mult siege_phase_time stress_loss_mult stress_gain_mult enemy_hostile_scheme_success_chance_add church_holding_build_gold_cost church_holding_build_speed cultural_head_fascination_mult monthly_lifestyle_xp_gain_mult'.split())
COUNTY_KEYS = frozenset('county_opinion_add tax_mult development_growth_factor build_speed monthly_county_control_growth_factor levy_size levy_reinforcement_rate epidemic_resistance'.split())


def validate_practices(practices=PRACTICES) -> None:
    import re
    from decimal import Decimal
    if {p.code for p in practices} != set(TENETS_BY_CODE) or len(practices) != 36:
        raise ValueError('exact 36-tenet coverage required')
    signatures = set()
    for p in practices:
        if not 365 <= p.cooldown <= 1825 or not p.options:
            raise ValueError('missing bounded cooldown or choices')
        signature = tuple((o.rewards,o.character,o.county,o.conditions,o.control,o.development,o.phase,o.tutor) for o in p.options)
        if signature in signatures:
            raise ValueError('renamed identical practice package')
        signatures.add(signature)
        for o in p.options:
            if any(type(v) is not int or v < 0 for v in (o.gold,o.piety,o.prestige)) or not any((o.gold,o.piety,o.prestige)):
                raise ValueError('each choice requires a real positive resource cost')
            if not (o.rewards or o.character or o.county or o.control or o.development or o.tutor):
                raise ValueError('choice has no gameplay effect')
            if o.duration <= 0 or o.duration > p.cooldown or o.phase not in ('','inquiry','practice'):
                raise ValueError('invalid duration or stored phase')
            for entries,allowed in ((o.character,CHARACTER_KEYS),(o.county,COUNTY_KEYS)):
                if len(dict(entries)) != len(entries):
                    raise ValueError('duplicate modifier')
                for k,v in entries:
                    if k not in allowed or not re.fullmatch(r'-?\d+(?:\.\d+)?',v) or not Decimal(v).is_finite() or Decimal(v)==0:
                        raise ValueError('unsupported same-scope modifier')
            for reward in o.rewards:
                if not re.fullmatch(r'add_(?:gold|piety|prestige|stress|legitimacy|dread|(?:learning|martial|diplomacy|stewardship|intrigue)_lifestyle_xp) = -?\d+', reward):
                    raise ValueError('unsupported immediate effect')
                if reward.startswith('add_gold = -'):
                    raise ValueError('negative gold uses remove_short_term_gold')
    phases=[o.phase for p in practices for o in p.options if o.phase]
    if phases != ['inquiry','practice']:
        raise ValueError('inquiry/practice must form one explicit two-step cycle')
