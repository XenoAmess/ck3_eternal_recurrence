"""Generate player-only active practices from the authored 36-tenet catalogue.

Standalone generation writes only this producer's new paths. gen_runtime may
include build_outputs() as an extension; this module never invokes gen_runtime.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from content_data import TENETS_BY_CODE
from tenet_playstyle_data import PRACTICES, Practice, PracticeOption, validate_practices

SOURCE = Path(__file__).resolve().parents[1]
HEADER = '# GENERATED FILE: edit tools/tenet_playstyle_data.py and tools/gen_tenet_playstyles.py\n'
PHASE_FLAG = 'lyd_play_knowing_acting_inquiry_completed'


def design_document() -> bytes:
    """One catalogue page for players; exact choices remain in the native menu."""
    lines=['# 三十六信条：主动实践', '<!-- GENERATED FILE: edit tools/tenet_playstyle_data.py and tools/gen_tenet_playstyles.py -->', '',
        '当前礼仪的核心信条，或角色已选择的个人信条，均可解锁对应决议；仅仅学会或获准选择不会解锁。AI 不会自动使用这些决议。', '',
        '打开菜单和取消均不收费。确认时重新检查成年、自由、能力、信条资格、资源、冷却和所选路径的情境。所有分支共享本项冷却；临时修习成果不会因换信条立即消失。京畿行动只影响自己的首都县，不扫描世界角色。', '',
        '下表成本按确认时一次扣除。持续修正通常三年，部分战时/静修两年、长期营建四年；实际选项会显示全部即时所得、代价与持续时间。经验与修正使用游戏原生效果，未凭脚本生成军队、头衔或继承人。', '',
        '| 信条 | 专属行动与主要特色 | 选择成本 | 冷却 |', '|---|---|---|---|']
    features={
        'T01':'虔诚换正统性100、威望250与京畿控制25；行政能力提高。',
        'T02':'压力−80、谋略经验400；谋略+4且敌方阴谋成功率−20点。',
        'T03':'压力−60、外交经验400；封臣与京畿民意同时改善。',
        'T04':'威望400、虔诚200；宗族好感+25与生育率+20点。',
        'T05':'直辖上限+1、管理+4、管理经验500；京畿控制+20，压力+30。',
        'T06':'虔诚400、正统性75；京畿控制+35、民意+35与抗疫+20。',
        'T07':'牺牲威望换正统性150、封臣好感+25，承受压力25。',
        'T08':'本人学识经验550，一位真实成年廷臣学识经验500。',
        'T09':'恻隐赈济、羞恶防谋、辞让和众、是非明辨四择，各有不同所得。',
        'T10':'军事与管理经验各400、两项能力各+3，压力+35。',
        'T11':'必须在战争中：勇武+6、骑士效率+35%、军事经验400。',
        'T12':'京畿控制低于80才能用：控制+40、发展进度+50与发展增长+35%。',
        'T13':'健康+1、宗族好感+20、生育率+15点，压力−60。',
        'T14':'学识经验600、京畿发展进度+75与发展增长+40%。',
        'T15':'压力−100、学识经验500、学识+5；暂时生育率−15点。',
        'T16':'捐财换虔诚650、威望300、同信仰好感+20。',
        'T17':'学识经验350、外交经验450；京畿民意+25、控制+20。',
        'T18':'治理路线改善赋税与控制；战时路线提高勇武并降低军费。',
        'T19':'四年宗教地产建造成本−30%、耗时−35%；学识经验300。',
        'T20':'学识经验450，再择管理、外交或军事经验450及对应能力+3。',
        'T21':'正统性125、威望500、学识+4；压力+40与封臣好感−5。',
        'T22':'京畿发展进度+50；赋税、补员与发展增长各+30%。',
        'T23':'必须和平：压力−120、健康+0.75与压力获取−30%。',
        'T24':'京畿控制+40、民意+30与控制增长+50%；外交经验400。',
        'T25':'六艺六择：礼的声望、乐的减压、射的勇武、御的统军、书的学识、数的财计。',
        'T26':'学识经验900、学识+6与文化领袖革新速度+25%，压力+30。',
        'T27':'四年收入+30%、京畿赋税+30%、建设耗时−35%；发展进度+50。',
        'T28':'必须在战争中：军费−30%、军事+4，兼顾虔诚与京畿控制。',
        'T29':'恐怖值−30，换正统性100、压力−60与敌方阴谋成功率−25点。',
        'T30':'四年京畿建设耗时−40%、发展增长+50%，民意−10。',
        'T31':'财计、备御、研学三策：分别偏收入、军事防务、学习，不预言事件。',
        'T32':'学识经验650、虔诚300、同信仰好感+25；收入−10%。',
        'T33':'先问学得经验600；一年后才能践行，得管理经验600、金钱200与威望200，再回到问学。',
        'T34':'四年健康+0.75、生育率+35点、宗族好感+30；虔诚300。',
        'T35':'学识经验750、学识+6与压力−100；暂时外交−2。',
        'T36':'政事、人伦、军旅三择，分别侧重财政控制、关系减压、真实战时能力。',
    }
    for p in PRACTICES:
        costs=[]
        for o in p.options:
            values=[f'{v}{label}' for v,label in ((o.gold,'金'),(o.piety,'虔诚'),(o.prestige,'威望')) if v]
            costs.append((o.zh+'：' if len(p.options)>1 else '')+'+'.join(values))
        tenet=TENETS_BY_CODE[p.code]
        years=p.cooldown//365
        lines.append(f'| {tenet.name_zh} | {p.zh}：{features[p.code]} | '+ '<br>'.join(costs)+f' | {years}年 |')
    lines.extend(['', '本页是设计与生成源码说明。静态测试证明生成合同；游戏内实际按钮、效果和数值仍须按产品验收合同验证，不能把源码检查当成实机结果。', ''])
    return '\n'.join(lines).encode('utf-8')


def encoded(text: str) -> bytes:
    return (text.rstrip() + '\n').encode('utf-8-sig')


def option_key(p: Practice, index: int) -> str:
    return f'{p.key}_option_{index}'


def requirements(p: Practice, o: PracticeOption) -> str:
    rows=[f'{p.key}_ready_trigger = yes']
    for resource,value in (('gold',o.gold),('piety',o.piety),('prestige',o.prestige)):
        if value:
            rows.append(f'{resource} >= {value}')
    if o.county or o.control or o.development:
        rows.extend(('is_landed = yes','exists = capital_county'))
    rows.extend(o.conditions)
    if o.tutor:
        rows.append('any_courtier = { is_alive = yes is_adult = yes }')
    if o.phase == 'inquiry':
        rows.append(f'custom_description = {{ text = lyd_play_inquiry_not_done_tt NOT = {{ has_character_flag = {PHASE_FLAG} }} }}')
    elif o.phase == 'practice':
        rows.append(f'custom_description = {{ text = lyd_play_inquiry_done_tt has_character_flag = {PHASE_FLAG} }}')
    return '\n'.join(rows)


def option_effect(p: Practice, o: PracticeOption, index: int) -> str:
    key=option_key(p,index)
    rows=[]
    if o.gold:
        rows.append(f'remove_short_term_gold = {o.gold}')
    if o.piety:
        rows.append(f'add_piety = -{o.piety}')
    if o.prestige:
        rows.append(f'add_prestige = -{o.prestige}')
    rows.extend(o.rewards)
    if o.character:
        rows.append(f'add_character_modifier = {{ modifier = {key}_character days = {o.duration} }}')
    if o.county or o.control or o.development:
        county=[]
        if o.control:
            county.append(f'change_county_control = {o.control}')
        if o.development:
            county.append(f'change_development_progress = {o.development}')
        if o.county:
            county.append(f'add_county_modifier = {{ modifier = {key}_county days = {o.duration} }}')
        rows.append('capital_county = {\n' + '\n'.join(county) + '\n}')
    if o.tutor:
        rows.append('random_courtier = { limit = { is_alive = yes is_adult = yes } add_learning_lifestyle_xp = 500 }')
    if o.phase == 'inquiry':
        rows.append(f'add_character_flag = {PHASE_FLAG}')
    elif o.phase == 'practice':
        rows.append(f'remove_character_flag = {PHASE_FLAG}')
    rows.append(f'add_character_flag = {{ flag = {p.key}_cooldown days = {p.cooldown} }}')
    # Recheck the same closed trigger immediately before any cost or mutation.
    return f'{key}_effect = {{\nif = {{\nlimit = {{ {key}_trigger = yes }}\n'+'\n'.join(rows)+'\n}\n}\n'


def build_outputs() -> dict[str, bytes]:
    validate_practices()
    triggers=[]
    decisions=[]
    events=['namespace = lyd']
    modifiers=[]
    effects=[]
    loc={
        'lyd_play_cancel':('暂且搁置，不付费用','Set this aside without paying'),
        'lyd_play_confirm':('筹划此项实践','Plan this practice'),
        'lyd_play_available_tt':('至少有一条实践路径满足资源和具体条件。打开菜单不付费；确认选项时再次检查。','At least one path meets its resource and situational requirements. Opening the menu is free; each choice is checked again when confirmed.'),
        'lyd_play_inquiry_not_done_tt':('尚未完成本轮问学，可先积累可行之知。','This cycle of inquiry has not yet been completed.'),
        'lyd_play_inquiry_done_tt':('已完成本轮问学，且一年实践等待期已结束。','This cycle of inquiry is complete and the one-year practice cooldown has ended.'),
    }
    for number,p in enumerate(PRACTICES,1000):
        tenet=TENETS_BY_CODE[p.code]
        triggers.append(f'''{p.key}_eligible_trigger = {{
is_ai = no
is_alive = yes
OR = {{
    AND = {{ exists = rite rite = {{ rite_has_tenet = {tenet.script_id} }} }}
    has_personal_tenet = {tenet.script_id}
}}
}}
{p.key}_ready_trigger = {{
{p.key}_eligible_trigger = yes
is_adult = yes
is_imprisoned = no
NOT = {{ has_trait = incapable }}
custom_description = {{ text = {p.key}_cooldown_tt NOT = {{ has_character_flag = {p.key}_cooldown }} }}
}}
''')
        gates=[]
        choices=[]
        for i,o in enumerate(p.options):
            key=option_key(p,i)
            triggers.append(f'{key}_trigger = {{\n{requirements(p,o)}\n}}\n')
            gates.append(f'{key}_trigger = yes')
            effects.append(option_effect(p,o,i))
            choices.append(f'option = {{ name = {key} trigger = {{ {key}_trigger = yes }} {key}_effect = yes }}')
            loc[key]=(o.zh,o.en)
            for suffix,values in (('character',o.character),('county',o.county)):
                if values:
                    identifier=f'{key}_{suffix}'
                    modifiers.append(identifier+' = {\n'+'\n'.join(f'{k} = {v}' for k,v in values)+'\n}')
                    loc[identifier]=(p.zh+'：'+o.zh,p.en+': '+o.en)
                    loc[identifier+'_desc']=(p.purpose_zh,p.purpose_en)
        triggers.append(f'{p.key}_available_trigger = {{ {p.key}_ready_trigger = yes OR = {{ '+ ' '.join(gates)+' } }\n')
        decisions.append(f'''{p.key}_decision = {{
picture = {{ reference = "gfx/interface/illustrations/decisions/decision_personal_religious.dds" }}
decision_group_type = religious
selection_tooltip = {p.key}_decision_tooltip
confirm_text = {p.key}_decision_confirm
ai_check_interval = 0
is_shown = {{ {p.key}_eligible_trigger = yes }}
is_valid = {{
    {p.key}_ready_trigger = yes
    custom_description = {{ text = {p.key}_available_tt {p.key}_available_trigger = yes }}
}}
effect = {{ if = {{ limit = {{ {p.key}_available_trigger = yes }} trigger_event = lyd.{number} }} }}
ai_will_do = {{ base = 0 }}
}}''')
        events.append(f'''lyd.{number} = {{
type = character_event
title = {p.key}_title
desc = {p.key}_desc
theme = learning
trigger = {{ {p.key}_available_trigger = yes }}
{chr(10).join(choices)}
option = {{ name = lyd_play_cancel }}
}}''')
        years=p.cooldown/365
        years_text=str(int(years)) if years.is_integer() else str(years)
        desc_zh=(p.purpose_zh+f' 核心信条信奉者与已选择此个人信条者均可使用。确认一条路径后，本项实践冷却 {years_text} 年；取消不收费。临时修习成果不会因改换信条立刻消失。')
        desc_en=(p.purpose_en+f' Available through your rite core tenet or your selected personal tenet. Confirming one path starts a {years_text}-year practice cooldown; cancellation is free. Temporary training does not vanish immediately when changing tenets.')
        loc[p.key+'_decision']=(p.zh,p.en)
        loc[p.key+'_decision_desc']=(desc_zh,desc_en)
        loc[p.key+'_decision_tooltip']=(p.purpose_zh,p.purpose_en)
        loc[p.key+'_decision_confirm']=loc['lyd_play_confirm']
        loc[p.key+'_title']=(p.zh,p.en)
        loc[p.key+'_desc']=(desc_zh,desc_en)
        loc[p.key+'_cooldown_tt']=(f'本项实践的 {years_text} 年冷却已结束。',f'The {years_text}-year cooldown for this practice has ended.')
        path_text=[[],[]]
        for o in p.options:
            costs_zh=[];costs_en=[]
            for value,zh,en in ((o.gold,'金钱','gold'),(o.piety,'虔诚','piety'),(o.prestige,'威望','prestige')):
                if value:
                    costs_zh.append(f'{value} {zh}');costs_en.append(f'{value} {en}')
            need_county=bool(o.county or o.control or o.development)
            context_zh=[];context_en=[]
            if need_county:
                context_zh.append('拥有京畿');context_en.append('a capital county')
            if 'is_landed = yes' in o.conditions and not need_county:
                context_zh.append('拥有地产');context_en.append('landed')
            if 'is_at_war = yes' in o.conditions:
                context_zh.append('处于战争');context_en.append('at war')
            if 'is_at_war = no' in o.conditions:
                context_zh.append('处于和平');context_en.append('at peace')
            if 'capital_county = { county_control < 80 }' in o.conditions:
                context_zh.append('京畿控制力低于 80');context_en.append('capital control below 80')
            if o.tutor:
                context_zh.append('至少一位成年在廷角色');context_en.append('at least one adult courtier')
            if o.phase:
                context_zh.append('先问学再践行，二者交替');context_en.append('inquiry and practice alternate')
            path_text[0].append(o.zh+'：'+'、'.join(costs_zh+context_zh))
            path_text[1].append(o.en+': '+', '.join(costs_en+context_en))
        loc[p.key+'_available_tt']=('至少满足一条路径：'+'；'.join(path_text[0])+'。打开菜单不收费，确认时再次核验。','Meet at least one path: '+'; '.join(path_text[1])+'. Opening the menu is free; requirements are checked again on confirmation.')
    outputs={
        'common/decisions/lyd_tenet_playstyle_decisions.txt':encoded(HEADER+'\n'.join(decisions)+'\n'),
        'common/scripted_triggers/lyd_tenet_playstyle_triggers.txt':encoded(HEADER+'\n'.join(triggers)+'\n'),
        'common/modifiers/lyd_tenet_playstyle_modifiers.txt':encoded(HEADER+'\n'.join(modifiers)+'\n'),
        'events/lyd_tenet_playstyle_events.txt':encoded(HEADER+'\n'.join(events)+'\n'),
    }
    # Existing production validator caps helper files at ten top-level effects.
    for start in range(0,len(effects),8):
        outputs[f'common/scripted_effects/lyd_tenet_playstyle_{start//8+1:02}_effects.txt']=encoded(HEADER+'\n'.join(effects[start:start+8])+'\n')
    for language,column in (('simp_chinese',0),('english',1)):
        lines=[f'l_{language}:', ' # GENERATED FILE: edit tools/tenet_playstyle_data.py and tools/gen_tenet_playstyles.py']
        for key,texts in loc.items():
            value=texts[column].replace('\\','\\\\').replace('"','\\"')
            lines.append(f' {key}:0 "{value}"')
        outputs[f'localization/{language}/lyd_tenet_playstyle_l_{language}.yml']=encoded('\n'.join(lines)+'\n')
    outputs['docs/tenet-active-practices.md']=design_document()
    return outputs


def generate(output: Path, *, check: bool = False) -> list[str]:
    mismatches=[]
    for relative,payload in build_outputs().items():
        path=output/relative
        if check:
            if not path.is_file() or path.read_bytes()!=payload:
                mismatches.append(relative)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(payload)
    return mismatches


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=SOURCE)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    mismatches=generate(args.output,check=args.check)
    if mismatches:
        raise SystemExit('Generated practice files differ: '+', '.join(mismatches))
    print(f'{len(build_outputs())} active-practice files {"checked" if args.check else "generated"}; no CK3 run')


if __name__=='__main__':
    main()
