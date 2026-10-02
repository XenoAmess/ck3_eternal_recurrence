"""Read-only mechanism investigation plus a new, evidence-bound full script.

Authoring only: no CK3, desktop, TTS, rendering, upload or human signoff.
Old runs and the a08 story are immutable inputs. Every output is new.
"""
from __future__ import annotations
import argparse
import copy
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
import copy_revision_a09 as revision
import review_story_a04 as media

P = Path(__file__).resolve().parent
E = P / 'evidence-a09-copy-audit-20261002'
GAME = Path('C:/SteamLibrary/steamapps/common/Crusader Kings III')
HISTORY = Path('C:/w/ep2a03')
RESEARCH = Path('C:/w/e2research1001')
CASE = Path('D:/workspace/ck3_native_war_ai_promo_work/episode01-day05-wound-growth-attempt-039')
R148 = Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-12-identifier-append-safe/R0148-six-gap-finite-case-semantic-closure-a01.json')
GROWTH = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0148-actual-finite-growth-accolade-audit-other-a01/actual-finite-normal-a04/current-finite-growth-accolade-projection.json')
R149 = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0149-actual-join-control-audit-reinforcement-a01/R0149-finite-reinforcement-facts-a01.json')
DATA = HISTORY / 'ck3_autonomous_player/src/xar_autoplayer/simulation/data'
NEXT = DATA / 'ck3_1_19_0_6_episode01_messina_knight_maim_next_input.json'
WEIGHTS = DATA / 'ck3_1_19_0_6_episode01_day26_runtime_weights_v1.json'
SCREEN = RESEARCH / 'docs/ck3-native-ai/pursuit-screen-nonzero-branch-contract-2026-09-27.md'
INV = RESEARCH / 'docs/ck3-native-ai/pursuit-screen-frozen-candidate-audit-2026-09-27.md'

def require(value, message):
    if not value: raise ValueError(message)

def fact(path, locator, claim, confidence='verified'):
    return {'source_path':str(path), 'source_field_or_line':locator,
            'claim':claim, 'confidence':confidence}

def pin_expected(path, checksum):
    pin = media.ref(path)
    require(pin['sha256']==checksum.upper(), 'Frozen original bytes changed: '+str(path))
    return pin

def excerpt(path, start, end):
    lines=path.read_text(encoding='utf-8-sig').splitlines()
    return {'source':media.ref(path), 'first_line':start, 'last_line':end,
            'numbered_text':'\n'.join(f'{n}: {lines[n-1]}' for n in range(start,end+1))}

def collect_investigation(run):
    pins=[]
    commander=GAME/'game/common/scripted_effects/00_commander_effects.txt'
    phase=GAME/'game/common/combat_phase_events/00_knight_phase_events.txt'
    defs=GAME/'game/common/defines/00_defines.txt'
    pins.append(pin_expected(commander,'7999F7731F56A63A5E6E615EF1805F6382101D958A5AD4967F9C68CF3E8EE6F6'))
    pins.append(pin_expected(phase,'E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1'))
    pins.append(pin_expected(defs,'C1ECA141C71EC1E741CA5336E01BB538EEFAEC05B0684EDEC477CFC9053C3807'))
    pins.append(pin_expected(GAME/'binaries/ck3.exe','2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'))
    maim=media.read(DATA/'ck3_1_19_0_6_episode01_messina_knight_maim_replay_v3.json')
    for day, name in [(5,'d05-replay-source-melted.ck3'),(6,'d06-melted.ck3')]:
        pins.append(pin_expected(CASE/name,maim['melted_save_sha256_by_day'][str(day)]))
    pins.append(pin_expected(NEXT,'961DA3BC152903316214CEC3CA820669F83161A3A04C6EC3D6235C239E164100'))
    pins.append(pin_expected(WEIGHTS,'8BC27BC8420B31474DEDABDF00E004E5C2C910C4906406A15CE0D46144E809A8'))
    names=GAME/'game/localization/simp_chinese/names/character_names_l_simp_chinese.yml'
    name_text=names.read_text(encoding='utf-8-sig'); identities=[]
    for day,name in [(5,'d05-replay-source-melted.ck3'),(6,'d06-melted.ck3')]:
        text=(CASE/name).read_text(encoding='utf-8-sig')
        for cid,key,zh in [(34333,'Geoffroy','若弗鲁瓦'),(47032,'Muhammad','穆罕默德')]:
            blocks=re.findall(rf'^\t{cid}=\{{\n(.*?)^\t\}}',text,re.M|re.S)
            require(len(blocks)==1,'Character block must be unique')
            key_matches=re.findall(r'^\t\tfirst_name="([^"]+)"$',blocks[0],re.M)
            require(key_matches==[key],'Saved first name mismatch')
            matches=re.findall(r'^\s*'+key+r':\s*"([^"]+)"$',name_text,re.M)
            require(matches==[zh],'Stock Chinese localization mismatch')
            identities.append({'day':day,'character_id':cid,'first_name_key':key,'stock_zh':zh,
                               'save':media.ref(CASE/name),'localization':media.ref(names),
                               'source_scope':'given-name key; no unobserved title/dynasty UI concatenation claimed'})
    next_input=media.read(NEXT);math=[]
    for tag in ('before','after'):
        row=next_input['maimed_next_input_'+tag]
        for kind,base in [('damage',50),('toughness',10)]:
            expected=Decimal(row['prowess'])*Decimal(row['knight_effectiveness_raw'])/100000*base
            observed=Decimal(row['effective_'+kind+'_raw'])/100000
            require(expected==observed,'Native knight stat parity mismatch')
            math.append({'state':tag,'stat':kind,'effective_prowess':row['prowess'],
                         'E':str(Decimal(row['knight_effectiveness_raw'])/100000),
                         'base_per_prowess':base,'computed':str(expected),'native_reading':str(observed),
                         'source':media.ref(NEXT)})
    w=media.read(WEIGHTS)['native_choice']
    require(w['weights_native_int32']==[40,30,15] and w['positive_weight_total']==85
            and w['selected_source_order_index']==0, 'Historical growth receipt mismatch')
    root=media.read(R148);g=media.read(GROWTH)
    require(root['closed_count']==6 and root['finite_13_domain_case_chain_closed'] is True,
            'Current finite closure required')
    require(g['actual_named_growth_role']['finite_no_write_closed'] is True,
            'Current selected growth branch must be closed')
    observations={
      'schema':'ck3.episode02.four-question-investigation/v1','created_at_utc':media.stamp(),
      'scope':'Original 1.19.0.6 local bytes and retained receipts; zero new game/desktop actions',
      'question_1':{'formula_and_static_vectors_researched':True,'nonzero_loser_live_parity_complete':False,
        'zero_loser_screen_case_is_not_nonzero_screen_validation':True,
        'existing_inventory':'252 receipts / 32 pursuit snapshots / 0 losing-side nonzero screen candidates; inventory is scoped and historical',
        'required_next_case':['same-frame losing soft>0 AND effective screen>0',
          'winner and loser effective attributes, modifiers, frozen levy/MAA pools, original storage order',
          'original budget and per-entry writes; next-day soft/readable hard; participant hard ledger',
          'separate screen>pursuit and 0<screen<pursuit cases'],
        'sources':[media.ref(SCREEN),media.ref(INV)],'new_live_capture':False},
      'question_2':{'formula':'damage=P_effective*50*E; toughness=P_effective*10*E; E=displayed_percentage/100',
        'E_example':'175%=1.75; 100%=1; 200%=2','live_case_math':math,
        'scope':'stock base per-prowess rule and the exact 039→040 case; damage is a stat, not daily deaths'},
      'question_3':{'identities':identities,'names_verified_both_saves':True,
        'same_name_different_characters_must_keep_IDs':True},
      'question_4':{'source_order':['select opposing knight','award prestige','growth random list and guarded followup','battle event','death request and deferred commit'],
        'three_growth_results':['no-op','add_prowess_skill=1','blademaster_lifestyle_rank_up_effect'],
        'base_weights':[60,30,10],
        'no_op_weight_rule':'60-2*effective Learning, then factor0.5 if warfare_legacy_3; only positive evaluated weights enter selection',
        'prowess_plus_one_weight':30,
        'blademaster_weight_rules':{'base':10,'martial_education_add':5,
          'education_martial_prowess_add_by_rank':[4,8,12,16],
          'existing_blademaster_add':15,'shrewd_add':10,'physique_good_add':10,
          'intellect_good_add_by_rank':[5,15,30],
          'culture_blademaster_traits_more_common_factor':3,'existing_blademaster_XP_at_least_100_factor':0},
        'blademaster_effect':'absent: add trait; present and XP<100: add10 XP; stock trait thresholds50/100; not prowess+10',
        'historical_observed_weights':w,'historical_conditional_prowess_gain_share':str(Decimal(30)/85*100),
        'historical_weights_not_backfilled_into_R0148':True,
        'current_case_selected_empty_entry':g['actual_named_growth_role'],
        'player_liege_followup':'if player liege and not flagged was_the_target_of_event_court_5060: increment/init number_of_impressive_knight_things; guarded four-year maintenance and liege impressive_knights list; current finite followup dispatches no child',
        'proof_limit':'Other nonempty growth branches are explained from exact stock scripts; no new nonempty live branch is asserted'},
      'exact_original_pins_verified':pins,'master_intake':False,'rendered_new_video':False,
      'human_full_video_review_or_signoff':False}
    media.write(run/'four-question-investigation.json',observations)
    excerpts=[excerpt(commander,20,147),excerpt(phase,1243,1322),excerpt(defs,610,611),
              excerpt(GAME/'game/common/scripted_effects/00_lifestyle_focus_effects.txt',574,594),
              excerpt(GAME/'game/common/traits/00_traits.txt',1177,1235),
              excerpt(GAME/'game/common/script_values/00_trait_values.txt',1,12)]
    media.write(run/'original-script-excerpts.json',excerpts)
    return observations

def sources_for(key):
    commander=GAME/'game/common/scripted_effects/00_commander_effects.txt'
    if key.startswith('pursuit-p030'):
        return [fact(SCREEN,'lines7-9;38-43','Formula/static vectors are researched; losing-side nonzero live parity is still missing'),
                fact(INV,'lines3-22','Scoped inventory has no active losing-side nonzero-screen pursuit candidate')]
    if key in ('knights-k004','knights-k004a'):
        return [fact(NEXT,'/maimed_next_input_before; /maimed_next_input_after; /scale','Exact prowess × E ×50/10 agrees with the two retained native states'),
                fact(GAME/'game/common/defines/00_defines.txt','lines610-611','Stock per-prowess damage50 and toughness10')]
    if key in ('knights-k006','knights-k009'):
        return [fact(E/'four-question-investigation.json','/question_3/identities','Both same-source saves bind34333 to Geoffroy/若弗鲁瓦 and47032 to Muhammad/穆罕默德')]
    if key in ('knights-k026','knights-k026a','knights-k026b','knights-k026c'):
        return [fact(commander,'lines20-103','Stock three-way growth list and complete conditional weight modifiers'),
                fact(GAME/'game/common/combat_phase_events/00_knight_phase_events.txt','lines1252-1258;1278-1320','Prestige and growth precede battle-event and death request'),
                fact(R148,'/six_gap_items/5','Current finite case13-domain boundary and no-write growth closure')]
    if key=='knights-k026d':
        return [fact(GAME/'game/common/scripted_effects/00_lifestyle_focus_effects.txt','lines575-593','Absent trait is added; existing XP below100 receives10 XP'),
                fact(GAME/'game/common/traits/00_traits.txt','lines1177-1235','Blademaster XP track thresholds50 and100'),
                fact(GAME/'game/common/script_values/00_trait_values.txt','line10','trait_third_level=100')]
    if key in ('knights-k026e','knights-k026f'):
        return [fact(WEIGHTS,'/native_choice','Separate historical original capture: weights40/30/15, total85, selected entry0'),
                fact(GROWTH,'/actual_named_growth_role','Current R0148 selected empty entry and finite no-write closure; no old weights attributed to this run')]
    if key=='knights-k026g':
        return [fact(commander,'lines105-147','Guarded player-liege impressive deeds bookkeeping follows the growth draw'),
                fact(GROWTH,'/actual_named_growth_role/followup_body','Current original followup has no actual child invocation')]
    if key=='closing-c002':
        return [fact(NEXT,'/maimed_next_input_before; /maimed_next_input_after; /knights_before_after','039→040 retained maiming chain'),
                fact(R148,'/six_gap_items/0; /six_gap_items/1','Current same-run death pages and complete rosters')]
    if key in ('closing-c003','reinforcement-r002','reinforcement-r003','reinforcement-r040'):
        return [fact(R149,'/actual_join_enter_return; /original_join_width_boundaries; /original_frame_native_bindings_and_save_time_layers; /pixel_direct_inspection','Current R0149 join and separately bound original paused full-frame pair')]
    return []

def main(run):
    require(not run.exists(),'Fresh audit attempt required')
    run.mkdir(parents=True); (run/'logs').mkdir(); (run/'sources').mkdir()
    original_path=P/'project/review-story-a08-story.json';original_pin=media.ref(original_path)
    original=media.read(original_path); old={c['id']+'-'+u['id']:u for c in original['chapters'] for u in c['utterances']}
    require(len(old)==167,'Audit must cover all167 original cues')
    branch=media.command(run,'private-branch',['git','-C',str(P),'branch','--show-current']).read_text(encoding='utf-8').strip()
    require(branch=='codex/war-series-brown-gold-20261001','Independent private branch required')
    for p,n in [(original_path,'a08-original-story.json'),(Path(__file__),'auditor-source.py'),(Path(revision.__file__),'editorial-source.py')]:
        shutil.copyfile(p,run/'sources'/n)
    findings=collect_investigation(run)
    require(not E.exists(),'New checked-in evidence destination required')
    E.mkdir()
    for n in ('four-question-investigation.json','original-script-excerpts.json'):
        shutil.copyfile(run/n,E/n)
    story=copy.deepcopy(original);edits={k:(zh,en,reason) for k,zh,en,reason in revision.REVISIONS}
    require(len(edits)==len(revision.REVISIONS) and set(edits)<=set(old),'Unique existing cue revisions required')
    ledger=[]
    for chapter in story['chapters']:
        cues=[]
        for u in chapter['utterances']:
            key=chapter['id']+'-'+u['id'];reason='逐句核对主语、数字、日期、单位、来源与可证明范围后保留。'
            if key in edits:
                u['zh'],u['en'],reason=edits[key]
            extras=sources_for(key)
            if extras:
                # Keep original locators as provenance; point this revision at the exact supporting sources.
                u['inherited_facts_a08']=copy.deepcopy(u['facts'])
                u['facts']=extras+copy.deepcopy(u['facts'])
            if key.startswith('knights-') and key in edits:
                u.setdefault('visual',{})['copy_revision_note']='Update on-screen title/labels to match this narration before rendering; retain original UI pixels and run labels.'
            u['copy_audit_status']='reviewed-with-explicit-evidence-scope'
            cues.append(u)
            ledger.append({'key':key,'origin':'a08-existing-cue','decision':'revised' if key in edits else 'retained',
              'reason':reason,'before_zh':old[key]['zh'],'after_zh':u['zh'],
              'before_en':old[key]['en'],'after_en':u['en'],'facts':u['facts'],
              'semantic_review':'root reviewed Chinese narration, English equivalence, entity identity, numerical scale, chronology, source scope and repeated wording; no human video approval inferred'})
            for uid,zh,en,reason in revision.ADDITIONS.get(key,[]):
                new_key=chapter['id']+'-'+uid
                require(new_key not in old and new_key not in {r['key'] for r in ledger},'Duplicate added cue')
                fs=sources_for(new_key);require(fs,'Every new mechanism cue needs concrete sources')
                v={'id':uid,'zh':zh,'en':en,'facts':fs,'copy_audit_status':'reviewed-with-explicit-evidence-scope',
                   'visual':{'kind':'pending-evidence-bound-board','focus':reason,
                     'source_hint':'Use labelled static formula / historical or current native records. New board and TTS pending; do not treat this draft as media.'}}
                cues.append(v);ledger.append({'key':new_key,'origin':'a09-new-cue','decision':'added','reason':reason,
                     'after_zh':zh,'after_en':en,'facts':fs,'semantic_review':'Root-authored evidence-bound addition; static/historical/current scopes kept separate'})
        chapter['utterances']=cues
        chapter['inherited_coverage_a08']=chapter.pop('coverage',{})
        chapter['coverage']={'copy_audit':'all original cues reviewed; edited and added cues independently source-bound',
          'media_status':'new authoring only; TTS, boards, render, full1x review pending',
          'preserved_mechanism_scope':'same chapter, same original cases and integer derivation; additions explicitly label static or historical sources'}
        chapter['char_count_zh']=sum(len(u['zh']) for u in cues)
    # Cross-case summaries must bind the newly referenced runs rather than stale earlier metadata.
    closing=next(c for c in story['chapters'] if c['id']=='closing')
    closing['coverage']['remaining_mechanism_gaps']=[
      'nonzero losing-side screen: same-frame inputs / next-day regiment parity',
      'future arrival timing and earlier route/assistance inputs',
      'other character event and nonempty growth branches across conditions',
      'voluntary retreat decision and whole-battle probability calibration']
    story['revision']='a09-four-question-investigation-and-full-copy-audit'
    story['authoring_status']='audited-bilingual-draft; no new render or signoff'
    story['human_signoff']='not-provided';story['production_clean_admission']=False
    story['research_prerequisite']={'finite_R0148_six_case_gaps_closed':True,
      'R0149_complete_same_frame_capture_closed':True,'nonzero_losing_screen_live_parity_closed':False,
      'nonempty_growth_branches_new_live_validation':False,'all_video_mechanism_boundaries_complete':False}
    story['original_a08']=original_pin
    story['new_cue_count']=sum(len(c['utterances']) for c in story['chapters'])
    checks=[]
    for c in story['chapters']:
        for u in c['utterances']:
            key=c['id']+'-'+u['id']
            for lang,limit in [('zh',40),('en',100)]:
                lines=media.ass_text(u[lang],limit).count(r'\N')+1
                checks.append({'key':key,'language':lang,'subtitle_lines':lines,'limit':2,'passed':lines<=2})
    media.write(run/'subtitle-layout-preflight.json',checks)
    require(all(x['passed'] for x in checks),'Draft subtitle line overflow; inspect retained preflight')
    source_paths=sorted({Path(f['source_path']) for c in story['chapters'] for u in c['utterances'] for f in u['facts']},key=str)
    source_pins=[media.ref(p) for p in source_paths]
    require(media.ref(original_path)==original_pin,'Old a08 changed during audit')
    # Pin all currently cited source bytes twice. This proves integrity, not semantic completeness.
    for pin in source_pins:
        require(media.ref(pin['path'])==pin,'Source changed during audit')
    report={'schema':'ck3.episode02.complete-copy-audit/v1','created_at_utc':media.stamp(),
      'reviewer':'/root; agent textual/evidence review, not human1x movie signoff',
      'original_story':original_pin,'scope':'All167 original Chinese utterances and English counterparts; existing visuals evaluated through their source policies, not a fresh film review',
      'original_cues_reviewed':167,'original_cues_revised':len(edits),'original_cues_retained':167-len(edits),
      'new_cues':story['new_cue_count']-167,'total_optimized_cues':story['new_cue_count'],
      'chapters':[{'id':c['id'],'cues':len(c['utterances']),'characters_zh':c['char_count_zh']} for c in story['chapters']],
      'all_fact_source_files_pinned_twice':source_pins,
      'per_cue_review':ledger,'subtitle_preflight_all_passed':True,
      'boundary_claims_preserved_not_marked_closed':['nonzero losing-side screen parity','unreadable per-regiment hard field',
        'pursuit UI getter formula','10-person-equivalent score numerator discrepancy attribution',
        'R0148 house guard failing child','nonempty-growth live outputs across conditions','future arrival and full-battle probability'],
      'old_a08_story_unchanged':True,'new_TTS':False,'new_boards':False,'new_render':False,
      'human_full1x_review':False,'signoff':'not-provided','master_intake':False}
    out=P/'project/review-story-a09-story.json';media.write(out,story)
    config=media.read(P/'project/review-story-a08-project.json')
    config['project']['id']='ck3-war-ai-episode02-copy-audit-a09'
    config['project']['title']='战斗后半笔账：完整文案审计与骑士成长详解'
    media.write(P/'project/review-story-a09-project.json',config)
    media.write(run/'full-copy-audit.json',report);shutil.copyfile(run/'full-copy-audit.json',E/'full-copy-audit.json')
    lines=['战争系列第二期｜a09 全量审计后中文旁白',
      '状态：文案稿；未生成新配音或新成片。姓名、机制公式与来源定位见逐句JSON审计。',
      '原167句全部审阅；保留完整六章推导。非零败方掩护实机对拍仍未完成。','']
    bilingual=[]
    for c in story['chapters']:
        lines.extend(['',c['title'],''])
        bilingual.extend(['',c['id']+' | '+c['title'],''])
        for u in c['utterances']:
            lines.extend(['['+u['id']+'] '+u['zh'],''])
            bilingual.extend(['['+u['id']+'] '+u['zh'],u['en'],''])
    media.text_once(P/'project/full-narration-zh-a09.txt','\n'.join(lines).rstrip()+'\n')
    media.text_once(P/'project/full-narration-zh-en-a09.txt','\n'.join(bilingual).rstrip()+'\n')
    media.write(run/'deliverable-index.json',{'story':media.ref(out),'audit':media.ref(E/'full-copy-audit.json'),
      'findings':media.ref(E/'four-question-investigation.json'),
      'full_narration_zh':media.ref(P/'project/full-narration-zh-a09.txt'),
      'status':'AUTHORING_COMPLETE_MEDIA_PENDING','human_signoff':'not-provided'})
    print(json.dumps({'original_reviewed':167,'revised':len(edits),'new_cues':story['new_cue_count']-167,
       'optimized_total':story['new_cue_count'],'source_files_pinned':len(source_pins),'new_render':False},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    main(parser.parse_args().run)
