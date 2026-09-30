"""Preserve the root's 87 sentence reviews of the original a04 narration.

Notes were reviewed against frozen native cards, their original responses,
the existing UI maps and exact-build static research. References and machine
conditions remain distinct from direct UI readings and human video signoff.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EP2 = ROOT.parent.parent
A04 = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04')
VER = Path('C:/Users/1/ck3-video-vanilla-verification-20260930/attempt-a03/pursuit/pursuit-verification-a03.json')
CARDS = Path('C:/w/ep2a03/promo/ck3_native_war_ai/episode-02-battle-second-half/cards')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

cache = {}
def ref(path):
    path = Path(path)
    token = str(path.resolve())
    if token not in cache:
        if not path.is_file():
            cache[token] = {'path': token, 'exists': False}
        else:
            data = path.read_bytes()
            cache[token] = {'path': token, 'exists': True, 'bytes': len(data),
                            'sha256': hashlib.sha256(data).hexdigest().upper()}
    return cache[token]

NOTES = {
'opening-o001': '原案 UI 1288/330，比例3.903；问句不声称胜率或结果。',
'opening-o002': 'Robert29829、Ali31549、目标Title2111/省2638与战场省2633分开。第二事实定位已修；实际原生字段 war_objective_province_ids、primary_opponent_character_id，不使用旧别名作原始键。',
'opening-o003': '接战 UI 只证明当时入场人数。新军、骑士与追击由各自轨迹证据解释，不宣称已预测未来变化。',
'opening-o004': 'A05 d28/d31实际UI824→761；内部软转硬另看原生账，不将显示整数差直接称死亡。',
'opening-o005': 'a08当前勇武7与a02新增通告分轨；该句未断言33437当前次日死亡，名单变化不能作人物生命查询。',
'opening-o006': '海上UI2570与join incoming current2560是不同字段。已有原生名单/缓存/宽度；没有tooltip或hook同帧图像。',
'opening-o007': 'A05玩家是battle side1/war attacker，本场signed row -5000000；同次战争窗-50。战争尚在进行。',
'opening-o008': '同案例冷载不是同轨迹；原案与004已存在数值分叉。来源卡不能把独立回放剪成连续。',
'opening-o009': '软伤是溃散账，不是人物医学受伤；原生内部值与实际UI分源。未取得治疗/归队机制。',
'opening-o010': 'A05从004日27冷载，d28是追击起始状态；四边界、三tick，败方是玩家侧。',
'pursuit-p001': 'A05 source_relation和起点SHA证明另行冷载；004标签仅标源。',
'pursuit-p002': 'd28原图实际战败、玩家撤退中/敌追击中，双方战斗身份与军队ID对齐。',
'pursuit-p003': '三种账分列：current、soft、hard。原生跨日soft等量转hard；不是当前人数再扣同量。',
'pursuit-p004': '原图只可见撤退中；没有溃散tooltip，不补治疗或归队提示。语义来自原生链和已声明边界。',
'pursuit-p005': 'A05 d28败方24团、两软伤池62528090+19904137=82432227，除Q得到824.32227。',
'pursuit-p006': 'Q=100000用于人数定点值；effective属性及追击量即使同缩放也不是人数。',
'pursuit-p007': '连算保留模型自己的败方后态；逐日原生败方状态只作对拍，未重喂当答案。',
'pursuit-p008': '75203000是同版模型据胜方有效追击/current及系数复算；没有单独原生P scalar，旁白已标模型。',
'pursuit-p009': '本案败方有效screen=0，extra=max(0,P-screen)=P；仅覆盖零掩护输入。',
'pursuit-p010': 'T为逐团有效toughness乘当天soft后汇总，首日1489459979；是复算中间量。',
'pursuit-p011': '本案base/floor=74472998、5%T；额外与保底两预算各自保留整数截断，不泛化全部分支。',
'pursuit-p012': '本次native efficiency0和retreat_losses-25000合为75000；预算依div/mul/mul/div3逐步截断。',
'pursuit-p013': 'levy/MAA分组冻结S0；两类各算extra/floor后分配到团，不用统一等额。',
'pursuit-p014': '同组当天soft占比，先mul再div并限于soft；保留native团顺序。',
'pursuit-p015': '模型475–520及exact-build静态0x23CD660两遍顺序相符；第二遍按存储顺序分余数。永久writer先于entry.soft写回，句子不宣称中途原子更新。',
'pursuit-p016': '50团首日soft减少107720、可读hard增加107720=1.0772人当量；hard ledger不是额外人物死亡观测。',
'pursuit-p017': 'd29实际UI803；首tick原生soft→hard2070677=20.70677，整数与精度分层。',
'pursuit-p018': '首tick24soft/23readablehard逐行零差；没有称24hard全部可读。',
'pursuit-p019': '每tick一项hard unavailable，三tick共3空值；null保留，不补0。',
'pursuit-p020': '第二tick接模型前一日后态；native d29只能作比较。',
'pursuit-p021': 'd30实际UI782；第二tick2097473=20.97473，24soft/23readablehard匹配。',
'pursuit-p022': 'd31实际UI761；第三tick2126119=21.26119，24soft/23readablehard匹配。',
'pursuit-p023': 'd28/29/30/31四暂停边界，中间三跨日；原版PURSUIT_PHASE_DAYS=3。',
'pursuit-p024': '2070677+2097473+2126119=6294269=62.94269；累计72soft/69readablehard。',
'pursuit-p025': 'P三日75203000；T1489459979→1452047877→1414150820，软伤构成不同。不是首日总量乘三。',
'pursuit-p026': '预算用d28冻结S0，逐团分摊用已经变化的当天soft；连算保留两种口径。',
'pursuit-p027': '72项current保持，原生败方current合计一直0；UI下降不等于current额外扣63。',
'pursuit-p028': '四UI整数824/803/782/761与soft去小数吻合；内部UI getter仍未证。旧图卡箭头缺字仅在a06修复。',
'pursuit-p029': '给定A05 d28初态的三tick局部对拍成立；不等于战前或整场概率预测。',
'pursuit-p030': '非零screen静态/模型会进入预算及条件分支；本次screen0不验收非零自然战例。',
'terminal-t001': 'A05同轨迹d32/raw53146992 normal_result，接在三次追击之后。',
'terminal-t002': '原始terminal body.prior为normal_result/winner0，玩家battle side1；不是玩家胜利。',
'terminal-t003': '玩家battle defender、war attacker分读；实际UI war_before也可见战争进攻方。旧引用根定位错误已修。',
'terminal-t004': 'Army18 in_combat=false/retreating=true、successor subject_retreating；画面左下败退可读，中央事件遮挡保留。不能证明AI主动撤退。',
'terminal-t005': '同A05两段战争窗0→-50；分段来源明确。旧引用定位已修。',
'terminal-t006': '真实战争窗底部总分与剑形分项-50，中央遮挡并未隐瞒；成片有实际原图crop。',
'terminal-t007': 'UI两个-50是可见读数；分子/桶/系数等右侧解释来自native，不能称UI显示。',
'terminal-t008': '从writer输入顺算、经过cap；仅已封顶-50不能逆推完整公式。',
'terminal-t009': 'count原始值Q100000；人当量小数是账的精度，不是独立实体数量。',
'terminal-t010': 'terminal baseline129800000=1298，与接战当前1288分栏；不改成同口径。',
'terminal-t011': 'stored_current0是terminal输入；不证明全部军队或人物全灭。',
'terminal-t012': 'levy_soft57753614、MAA_soft18384344=577.53614/183.84344，由sameA05 writer输入。',
'terminal-t013': '129800000-0-57753614-18384344=53662042=536.62042，为战分损失分子。',
'terminal-t014': '同A05分子53662042与participant_hard52662042差1000000=10人当量；原因未闭合，不增加一笔死亡。',
'terminal-t015': '明确拒绝把分子称536名实际战死；没有完整逐人死亡证明。旧引用定位已修。',
'terminal-t016': 'original0x25BBE70按败方所属战争侧participants，调用0x292FC40(mode2)八数量桶；不是本场参战人数。',
'terminal-t017': 'sameA05 body.prior.battle_warscore.denominator_inputs.participants唯一29829，原始顺序保留，不用024替身。',
'terminal-t018': '原始八桶[0,675,310,0,0,0,11,0]合996，与native sum_int32/after_minimum_int32一致。',
'terminal-t019': '675 levy、310MAA、11knights的命名来自exact-build指令与原版loc标签；动态回执只给八槽数量，命名证据另列。',
'terminal-t020': 'levy/MAA槽是MAX不是CURRENT；knights是数量不是power。MAX也有原生过滤，不能称全国全军满员。',
'terminal-t021': '1298取battle baseline，996取war participants八桶；两独立链不互换。',
'terminal-t022': '真实UI当前士兵897与996不是同字段；用battle起始人数代分母会改原版输入。',
'terminal-t023': '53662042//996=53877，整数截断，未四舍五入。',
'terminal-t024': '53877/Q=0.53877=53.877%；先截断再scale，不能调换乘除。',
'terminal-t025': '比例上限Q=100000，本次未触发；继续使用动态读取的已加载CB系数。',
'terminal-t026': 'sameA05 selected_cb_battle_scale_raw_q100000=15000000=150；不是假定static默认。',
'terminal-t027': '53877*15000000//100000=8081550，按整数次序复算。',
'terminal-t028': '80.8155是复算uncapped中间值；writer未单独暴露该scalar，UI也没有它。',
'terminal-t029': '该战争侧路径stock WAR_DEFENDER_COMBAT_MAX_SCORE50；sameA05 row magnitude5000000验证结果，未动态暴露独立cap字段。',
'terminal-t030': 'native winner_is_war_attacker=false，获胜方+50幅度；war attacker relative=-5000000。',
'terminal-t031': 'd32 paused snapshot War4=-50及实际战争窗总分/剑=-50同源；旧a04最终CB14及a06均有实际crop。',
'terminal-t032': '本场signed row与当前total同为-50是本例巧合；占领/目标等总账分项另有来源。',
'terminal-t033': 'UI只证可见结果；分子、分母、截断、系数靠sameA05原始回执/静态链与复算。',
'terminal-t034': 'A05独立coldload004日27，024历史对照不拼轨迹；输入SHA同也不证明同run。',
'terminal-t035': '闭合normal terminal→signed row→samepausedWar4这段局部链；没有全战预测。',
'terminal-t036': '其他CB、特殊部队容器边界及败后策略未覆盖；原八桶命名不能充当所有制度动态验收。',
'terminal-t037': 'UI-50和逐步复算支持本例，战争继续；没有下一场或整场胜率。旧引用定位已修。',
'closing-c001': '继承sameA05三tick62.94269/72soft/69readablehard；约63只是口播取整，不是63名已核实死亡。',
'closing-c002': '明确两历史独立链039→040致残34333属性11→7仍在阵；036→038移除33437/65，不替代当前a02次日UNKNOWN。',
'closing-c003': '继承A01九字段旧行不变、cache残差归零及2220首次出伤；UI2570/4106不能证明hook同帧。',
'closing-c004': 'sameA05 normal_result后自动败退、signed row=-50、pausedWar4=-50；未声称主动退军。',
'closing-c005': '是观察步骤建议；原案当前人数与a08当前tooltip7仅为所示例，不提供他人唯一ID或前态。',
'closing-c006': '是下场观察建议；A01已有前后人数图，但精确入场hook同帧仍未绑定。未来到达/路径不在本片证明范围。',
'closing-c007': 'UI824→761与精确软硬账分开，不通过两个整数差报告阵亡。',
'closing-c008': '先分battle/war身份、single row/total，再按war participant汇总996；不把战斗人数作分母。',
'closing-c009': '明确尚缺非零screen自然实机、未来join、其他人物effect、普通AI主动撤退与整场概率，不以局部成功代全部能力。',
'closing-c010': '是下一问与观察原则，没有新增机制或概率完成声明。',
}

GAPS = {
'opening-o005': ('当前a02的33437 d27生命/selector读数缺；本句只介绍独立通告与属性，不宣告次日死亡。', '当前骑士次日原图与targetID绑定未补。', '优先新d26→d27run和严格保存态检查。'),
'opening-o006': ('join值已证，但暂停画面与hook瞬间未精确绑定。', '缺同帧人数/战宽tooltip。', '优先新run推进前后两暂停图＋snapshot/control。'),
'pursuit-p004': ('治疗与归队机制未验证，旁白明确排除。', '当前帧没有溃散tooltip。', '如扩展语义，另取原版tooltip/恢复分支，不给旧图补字。'),
'pursuit-p019': ('三tick各一项hard字段unavailable。', '', '原版reader补该RegimentID字段后另run对拍；旧null保留。'),
'pursuit-p028': ('UI内部取数公式未证；本句只声称本案对应。', '旧a04四箭头缺字；a06已修。', '若要宣称getter公式，另核originalGUI/native取数链。'),
'pursuit-p030': ('非零败方screen自然战例及下一日逐团账缺。', '缺该条件下对应原版画面。', '新自然样本绑定paused输入/nextday24项soft及可读hard，保留分支条件。'),
'terminal-t004': ('未取得普通战争AI主动撤退决策。', '现有败退画面不证明主动下令。', '如扩展策略，另采实际请求/接受/后态；不将自动败退重命名。'),
'terminal-t014': ('分子与硬账差10的成因未闭合；两数本身有同run来源。', '', '若解释差值成因，另追producer口径和同帧写入，不编额外死亡。'),
'terminal-t015': ('没有536名实际逐人战死证明；旁白明确拒绝该说法。', '', '保持战分分子标签；不从计分输入制造死亡人数。'),
'terminal-t036': ('其他CB、特殊部队、容器资格/枚举生命周期及败后策略缺动态验证。', '缺这些新条件的实机画面。', '另新案例保存逐桶源容器/当前数量/CB输入、writer及UI，不用本例外推。'),
'closing-c002': ('当前a02骑士33437次日仍UNKNOWN，历史两链不替代。', '历史链没有本次新次日画面。', '采用knights/capture-nextday-plan.json。'),
'closing-c003': ('A01已证join内部值；缺原生到画面hook精确绑定。', '缺战宽tooltip及前后原生同帧图。', '采用reinforcement/minimum-supplement.json。'),
'closing-c006': ('未来到达未验证；现有前后图不等于hook时刻。', '同帧增援画面仍缺。', '先完成两暂停帧最小配方；未来路径另案。'),
'closing-c009': ('非零screen、未来增援、其他事件写集、普通AI主动撤退、完整概率均未覆盖。', '对应新条件实机画面未取得。', '按具体条件分开新run，不将本片复算称通用验收。'),
}

def main():
    timeline = read(A04 / 'timeline.json')
    catalog = read(EP2 / 'project/review-story-a04-v2.json')
    active = {chapter['id'] + '-' + row['id']: row for chapter in catalog['chapters']
              for row in chapter['utterances']}
    rows = [row for chapter in timeline['chapters'] if chapter['id'] in ('opening', 'pursuit', 'terminal', 'closing')
            for row in chapter['utterances']]
    assert len(rows) == 87 and set(NOTES) == {row['key'] for row in rows}
    verification = read(VER)
    pursuit_card = read(CARDS / 'e2-02-03-a05-pursuit-facts-20260928.json')
    writer_card = read(CARDS / 'e2-09-a05-writer-facts-20260928-v3.json')
    primary = {}
    for card in (pursuit_card, writer_card):
        for name, source in card['sources'].items():
            path = Path(source['path'])
            if path.suffix.lower() == '.mkv':
                assert path.stat().st_size == source['bytes']
                primary[name] = {**source, 'verification_scope': 'existing recorder SHA plus actual size, no repeated full video hash'}
                continue
            item = ref(path)
            if not item['exists'] or item['sha256'] != source['sha256'].upper():
                raise ValueError('Primary input missing or differs from frozen card: ' + str(path))
            primary[name] = {**item, 'matches_frozen_card': True}
    writer = read(writer_card['sources']['writer_response']['path'])['body']['prior']['battle_warscore']
    assert writer['denominator_inputs']['participants'] == [{'character_id': 29829, 'buckets_native_add_order_int32': [0,675,310,0,0,0,11,0]}]
    assert writer['denominator_inputs']['sum_int32'] == 996
    assert writer['selected_cb_battle_scale_raw_q100000'] == 15000000
    assert writer['value_raw_q100000'] == 5000000 and writer['attacker_relative_delta_raw_q100000'] == -5000000
    assert writer['winner_is_war_attacker'] is False
    assert 129800000 - 57753614 - 18384344 == 53662042
    assert 53662042 // 996 == 53877 and 53877 * 15000000 // 100000 == 8081550
    assert sum(verification['pursuit']['daily_soft_to_hard_raw']) == 6294269
    assert verification['pursuit']['soft_exact_rows'] == 72 and verification['pursuit']['readable_hard_exact_rows'] == 69
    static = [ref(Path('C:/w/ep2a03/docs/ck3-native-ai') / name) for name in (
        'combat-pursuit-write-order-and-final-side-attribution-static-2026-09-27.md',
        'war-film-battle-score-denominator-2026-09-23.md',
        'battle-terminal-and-reentry.md')]
    assert all(item['exists'] for item in static)
    anchors = []
    for anchor in verification['ui_anchors']:
        item = ref(anchor['path'])
        assert item['sha256'] == anchor['sha256']
        anchors.append({**anchor, 'actual_ref': item,
                        'review_scope': 'existing direct still-frame review; no new full human video review'})
    result = []
    for row in rows:
        key = row['key']
        assert active[key]['zh'] == row['zh']
        gap = GAPS.get(key, ('', '', 'No new capture required for the wording as scoped; broader mechanisms remain unverified.'))
        claims = []
        for index, fact in enumerate(row.get('facts', [])):
            effective = active[key]['facts'][index]
            source = ref(effective['source_path'])
            claims.append({'claim': fact['claim'], 'original_a04_locator': fact,
                           'effective_locator': effective, 'source': source,
                           'assessment': 'SUPPORTED_WITH_DECLARED_SCOPE' if source['exists'] else 'MISSING_SOURCE',
                           'source_level': 'static/model or documented historical scope' if Path(effective['source_path']).suffix in ('.py', '.md')
                           else 'native/visual evidence index; primary binding listed separately'})
        missing = [claim for claim in claims if not claim['source']['exists']]
        conclusion = 'MISSING_SOURCE' if missing else 'SUPPORTED_WITH_DECLARED_SCOPE'
        if key == 'pursuit-p028':
            conclusion = 'FACT_SUPPORTED_A04_GLYPH_DISPLAY_DEFECT'
        result.append({'key': key, 'chapter': row['chapter'], 'chinese_sentence': row['zh'],
                       'claims': claims, 'finding': NOTES[key], 'conclusion': conclusion,
                       'evidence_levels': ['actual native response or scoped existing evidence', 'model/static corroboration where named',
                                           'actual UI only for separately visible fields'],
                       'render_binding': {'a04_start': row['global_start'], 'duration': row['duration'],
                                          'visual': row['visual'], 'human_full_1x_review': False},
                       'missing_original_reading': gap[0], 'missing_original_picture': gap[1],
                       'minimum_supplement': gap[2],
                       'same_frame_relation': 'A01 same-run/date UI does not prove the join hook instant' if key in ('opening-o006','closing-c003','closing-c006')
                       else 'Use each named trajectory itself; summaries/crops/model fields do not create a new same-frame observation'})
    doc = {'schema': 'ck3.a04.other.utterance-audit.v1',
           'created_at': datetime.now(timezone.utc).isoformat(),
           'author_scope': 'Root reviewed and wrote the 87 rows after taking over the delayed table; prior peer source findings reused explicitly.',
           'target': ref(A04 / 'timeline.json'), 'corrected_catalog': ref(EP2 / 'project/review-story-a04-v2.json'),
           'scope': 'Original a04: opening10/pursuit30/terminal37/closing10. No game launch, new frame, master intake or human approval.',
           'summary': {'utterances': len(result), 'chapters': dict(Counter(row['chapter'] for row in result)),
                       'conclusions': dict(Counter(row['conclusion'] for row in result)),
                       'all_primary_card_source_pins_match': True, 'new_live_evidence': False},
           'primary_native_sources': primary, 'existing_verification': ref(VER),
           'native_writer_exact_payload_pointer': '/body/prior/battle_warscore',
           'static_corroboration': static, 'actual_ui_anchors': anchors,
           'utterances': result}
    output = ROOT / 'utterance-audit.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(doc, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'output': ref(output), 'summary': doc['summary']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
