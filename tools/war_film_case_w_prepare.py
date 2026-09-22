"""Freeze an offline CASE-W plan from existing R0004 receipts; never access CK3."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
EXE_SHA='2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86'
DEFAULT_WORK=Path('D:/workspace/ck3_war_film_research_20260923')

def binding(path):
    data=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def save(path,value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir',type=Path,default=DEFAULT_WORK)
    parser.add_argument('--game',type=Path,default=Path('C:/SteamLibrary/steamapps/common/CRUSAD~1/game'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    responses=args.workdir/'capture-live-live-r4c/interactive-requests-responses'
    paths={key:responses/name for key,name in [('capabilities','002-capabilities.json'),('checkpoint','003-checkpoint.json'),('campaign','005-campaign-root.json'),('assessment_one','009-assessment-one.json'),('assessment_two','010-assessment-two.json'),('last_snapshot','011-case-end-snapshot.json')]}
    raw={key:json.loads(path.read_bytes()) for key,path in paths.items()}
    snapshot=raw['last_snapshot']['body']
    assessment=raw['assessment_two']['body']
    checkpoint=raw['checkpoint']['body']['checkpoint']
    archived_save=args.workdir/'robert-input-case-r1/day-zero.ck3'
    save_binding=binding(archived_save)
    if save_binding['sha256']!=checkpoint['sha256'].lower() or save_binding['bytes']!=checkpoint['size']:
        raise ValueError('day-zero archive is not the checkpoint receipt bytes')
    assert snapshot['played_character']['character_id']==29829
    assert snapshot['revision']==6 and snapshot['native_revision']==5 and snapshot['date_raw']==53144328
    declaration=next(row for row in snapshot['declarable_wars'] if row['declaration_id']=='31549-40--1')
    assert declaration['target_character_id']==31549 and declaration['casus_belli_key']=='minor_religious_war'
    power=assessment['war_entry_assessments']['assessments'][0]
    assert power['target_character_id']==31549 and power['effective_target_character_id']==31549
    assert power['actor_power_total_raw']==3786000000 and power['target_power_total_raw']==1334000000
    assert assessment['war_entry_assessments']['readiness']['ready'] is True
    assert assessment['queried_revision']==snapshot['revision'] and assessment['queried_native_revision']==snapshot['native_revision']
    campaign=raw['campaign']['body']
    candidates=[row for row in campaign['campaign_root_context']['related_character_contexts'] if row.get('character_id')==31549 and row.get('capital_province_id')==2638]
    if len(candidates)!=1:
        raise ValueError('current-run target role binding not unique')
    target=candidates[0]
    projected=[row for row in campaign['related_character_contexts'] if row.get('character_id')==31549]
    if projected != [target]:
        raise ValueError('campaign target projection disagrees with canonical context')
    assert target['primary_title']['title_id']==2111 and target['independent'] is True
    current_steps=raw['capabilities']['body']['action_steps']
    required_steps=['pause-map','resume-map','set-speed-1','set-speed-2']
    assert all(step in current_steps for step in required_steps)
    identity_path=args.workdir/'capture-live-live-r4c/live-run-identity.json'
    run_id=json.loads(identity_path.read_bytes())['identities'][0]['run_id']
    sources=[]
    for rel,start,end in [('common/landed_titles/00_landed_titles.txt',14197,14220),('history/provinces/k_sicily.txt',75,95),('history/titles/k_sicily.txt',500,515),('history/characters/maghrebi.txt',627,652)]:
        path=args.game/rel
        sources.append({'game_relative_path':rel,**binding(path),'lines':[{'line':i,'text':line} for i,line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(),1) if start<=i<=end]})
    localizations=[]
    keys=['b_syracusa','c_siracusa','cn_sarqusa']
    for language in ['english','simp_chinese']:
        for filename in [f'titles_l_{language}.yml',f'titles_cultural_names_l_{language}.yml']:
            path=args.game/'localization'/language/filename
            matches=[{'line':i,'text':line} for i,line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(),1) if any(line.lstrip().startswith(key+':') for key in keys)]
            localizations.append({**binding(path),'lines':matches})
    baseline={'schema':'xar.war-film-case-w.baseline.v1','authority':'existing R0004 saved receipts and archived checkpoint, not a new live read','run_id':run_id,'pid':raw['last_snapshot']['driver_state']['bridge_pid'],'connection_generation':raw['last_snapshot']['driver_state']['connection_generation'],'episode_run_id':snapshot['episode_run_id'],'snapshot':{key:snapshot[key] for key in ['snapshot_id','revision','native_revision','date_raw','paused','episode_character_id']},'actor_character_id':29829,'target_character_id':31549,'declaration':declaration,'strategic_power':power,'target_current_run_role':target,'checkpoint':checkpoint,'archived_save':save_binding,'read_receipts':{key:binding(path) for key,path in paths.items()},'run_identity':binding(identity_path),'current_advertised_time_steps':required_steps,'name_binding':{'confirmed_capital_province':2638,'confirmed_official_capital_key':'b_syracusa','confirmed_capital_base_zh':'叙拉古','source_county_key':'c_siracusa','source_county_base_zh':'锡拉库萨','source_cultural_key':'cn_sarqusa','source_cultural_zh':'塞尔古塞','current_character_display_name':None,'history_candidate':{'history_character_key':'20829','name':'Ali','nickname_key':'nick_benavert','title':'c_siracusa','holder_period_start':'1062.1.1'},'boundary':'The current runtime character is bound to capital province 2638 and title ID 2111. The historical 20829 record is not equated with runtime CharacterID 31549 without this save or a fresh official name readback. No old-run ID/name mapping is used.','save_parser_boundary':'Archive is raw binary SAV0101. Existing local character-scope parser requires Rakaly-melted text; open_kaishek syntax parser does not establish a runtime character ID mapping from this binary.'},'official_history_and_location_sources':sources,'official_localizations':localizations}
    source_contract={'schema':'xar.war-film-case-w.tool-contract.v1','exe_sha256':EXE_SHA,'files':[binding(ROOT/'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'),binding(ROOT/'docs/ck3-native-ai/war-film-robert-mcp-shot-runbook-2026-09-23.md')],'tools':{'binding':['ck3_get_capabilities','ck3_get_bridge_diagnostics','ck3_take_snapshot','ck3_query_campaign_root_context_v1','ck3_save_checkpoint','ck3_inspect_save_artifacts_v1'],'operator_intervention':['ck3_query_declarable_wars','ck3_declare_war','ck3_raise_troops_default','ck3_move_army','ck3_execute_step'],'native_observation':['ck3_get_war_state','ck3_query_army_strengths','ck3_query_battle_reinforcement_assignment_v1','ck3_query_actual_contact_scope','ck3_query_battle_control_snapshot_v1','ck3_query_battle_transition_v1']},'argument_rule':'expected_revision is always the latest public revision. Public CUnit IDs come from current player/war army rows; native CArmy ID is not interchangeable. CombatID comes from actual contact/control/transition. No blind write retry.','scope':'Public bindings and available narrow readbacks only; no full scoring, autonomous declaration or retreat policy observer.'}
    window={'schema':'xar.war-film-case-w.window.v1','state':'prepared-not-executed','owner':'existing root R0004 owner only','run_identity':baseline['run_identity'],'intervention_label':'operator-declared legal minor_religious_war; subsequent NPC behavior is native; not natural AI declaration','fresh_precondition':'Same live PID, connection generation, episode, actor and target; after checkpoint obtain a fresh paused snapshot, current final-legal declaration row and fresh revision. Historical token is a candidate, not replay authority.','primary_stop':'Stop after one same-war enemy public CUnit has an observed post-declaration appearance/raising state and a committed route plus a later position/progress read, or after 30 observed game-calendar days / 12 paused sampling rounds / 12 wall minutes, whichever occurs first.','optional_contact_extension':'Only if needed for the film and existing bound armies/routes make one contact feasible within remaining budget: capture at most one actual CombatID. Total hard limits including primary window: 45 game-calendar days, 16 paused sampling rounds, 15 wall minutes. No repeated chases or second battle.','failure_stop':['war creation is not proved after one declaration submission and one reconciliation','identity/owner/episode changes','lost connection or typed unavailable prevents required binding','target war disappears or main opponent changes','unexpected action/event requiring an unrelated intervention','hard window limit'], 'sampling':'First pause after a newly observed game day, then at most three calendar days per slice. Use advertised set-speed-1/2, resume-map, pause-map; use fresh snapshots to observe dates. Prefer speed 1 near actual contact. No guessed raw-date arithmetic and no life-advance macro.','operator_actions':'At most one declaration. Player raise once and one player movement may be used only as explicit recorded interventions by the owner, with current native legality and scope; never submit orders to the NPC. Every ACK needs postcondition readback.','zero_result':'No enemy army or route inside the bounded window means not observed in this window; already present troops are not proof of a new raise decision. No combat means contact not observed, not that the AI refuses combat.','runtime_record_required':['pre_declaration_checkpoint bytes/hash and materialization','UTC and monotonic mark for every action/query/snapshot','snapshot_id, public/native revision, date and paused state','full generation-bearing WarID and actor/defender sides','public CUnit IDs, owners, controllable flag, native membership if available','route snapshot plus later same-unit progress; label split/merge successors explicitly','actual CombatID and both sides, if contact exists','raw video hash and timeline mark correspondence']}
    # R0004 has ended. Its rows are immutable historical baseline, never a live guard.
    baseline['historical_session_state']='ended; parent reported normal service budget expiry at 2026-09-22T21:33:03Z'
    baseline['role_for_case_w']='archived independent-count baseline; new run must revalidate identity and legal declaration'
    window['owner']='root only; a new officially allocated run is required, with no R0004 continuation endpoint'
    window['run_identity_role']='historical baseline only; future run identity is unbound'
    window['fresh_precondition']='New official run after validated day-zero restore (or separately labelled new start); bind fresh PID, connection generation, episode, actor/target, paused snapshot and current final-legal declaration row. Stop if intended actor/target/CB no longer match. Historical token and public/native revisions are not replay authority.'
    window['runtime_record_required'][:0]=['fresh official run_ID, PID, connection generation and episode; actual ready/HUD postcondition','restored seed bytes/hash plus formal restore/readback receipt, or explicit new-start label']
    args.output_dir.mkdir(parents=True,exist_ok=False)
    for name,value in [('baseline.json',baseline),('source-contract.json',source_contract),('sampling-window.json',window)]:save(args.output_dir/name,value)
    evidence=[]
    for ident,name,layer,supports in [('baseline','baseline.json','live-observation','Existing R0004 baseline only; no CASE-W action or NPC behavior has been observed.'),('source','source-contract.json','source-contract','Existing official tool signatures and their observation limits.'),('window','sampling-window.json','source-contract','Explicit bounded proposed sampling procedure, not permission or successful execution.')]:
        row={'id':ident,'path':name,'layer':layer,'sha256':binding(args.output_dir/name)['sha256'],'exe_sha256':EXE_SHA,'supports':supports}
        if layer=='live-observation':row.update({'session':run_id+' / PID31108 / connection-generation1','frame':'native:5 / public6 / native5 / date53144328','identity':'actor CharacterID29829; target/effective CharacterID31549; existing CASE-R receipts only'})
        evidence.append(row)
    nodes=[('baseline','Existing R0004 player/legal target baseline'),('operator','Explicit operator declaration intervention'),('war','New same-scope active WarID'),('enemy','NPC-owned enemy public CUnit appears/raises'),('route','Same-unit committed route and observed progress'),('combat','Optional first actual same-war CombatID'),('stop','Bounded stop; retain all outcomes')]
    edges=[('baseline-frame','baseline','operator','Existing baseline is bound; current pre-action refresh remains required','live-confirmed',['baseline'],None),('operator-declaration','operator','war','Operator submits one current legal token; prove resulting WarID','unknown',[],'No declaration has been submitted by this preparation package.'),('npc-raise','war','enemy','Observe enemy unit appearance or explicit raising transition within that WarID','unknown',[],'Require before/after ownership and war membership; pre-existing troops do not prove raising.'),('npc-route','enemy','route','Observe native enemy committed route and later progress','unknown',[],'Require same full CUnit or explicit split/merge successor binding, not flag animation.'),('first-contact','route','combat','Optional actual same-war contact with exact CombatID','unknown',[],'No projected encounter or simulator input is an actual battle.'),('bounded-record','route','stop','Stop on primary evidence or the first applicable budget/failure condition','counter-policy',[],None)]
    plan={'schema':'xar.native-research-plan.v1','topic':'war-film-case-w-native-npc-response-20260923','question':'After one explicitly operator-declared legal war in R0004, which same-war NPC raising, committed movement and optional first-contact transitions can the current public native tools actually observe?','purpose':'npc-choice','build':{'version':'1.19.0.6','exe_sha256':EXE_SHA},'observation':{'mode':'passive-runtime','actor_kind':'ai','owner_scope':'NPC31549 and its published same-war army scope only; human29829 initiates war as an explicit intervention, never as evidence of autonomous AI declaration.','identity_kind':'generation-id','identity_lifetime':'One current R0004 PID/connection/episode and new exact WarID; each full CUnit/CombatID is taken from current formal rows and retired on disappearance/split/merge unless a successor is explicit.','producer_trigger':'daily-tick','producer':'Normal NPC daily wartime military/coordinator processing after the separately recorded operator declaration; samples observe published raising/route/contact state, not unexposed score intermediates.','caller':'The existing unique owner uses advertised resume-map/pause-map time slices; paused official query readbacks never force an NPC order.','consumer':'Current snapshot/war-army rows and narrow army/reinforcement/contact/battle queries, hash-bound to checkpoint, frame/time and raw footage.','cache_lifetime':'Refresh snapshot after every action/publication/time slice; every paused query uses that public revision and retains returned native revision/date. Historical public6/native5 is baseline only.','expected_signal':'New exact WarID, NPC-owned full public CUnit appearance/raising, committed route and later progress; optionally one actual CombatID shared with the same war and sides.','zero_sample_meaning':window['zero_result'],'stop_condition':window['primary_stop']+' '+window['optional_contact_extension']+' Stop also on any failure_stop in the window.','runtime_window_ref':'sampling-window.json (prepared CASE-W continuation of '+run_id+'; owner alone executes after fresh preconditions)'},'pre_observation':{'checkpoint':'Preserve a fresh pre-declaration checkpoint to a new external path and validate bytes/materialization; retained day-zero archive is immutable rollback evidence, not current state by assumption.','current_token':'Refresh legal declarations after checkpoint/snapshot. Continue only if target31549/effective31549 and exact intended CB row remain legal. Do not replay historical public revision6.','video':'New CASE-W raw recording and timeline; every operator action is explicitly marked.'},'bindings_to_fill_from_live':{key:None for key in ['case_w_checkpoint','case_w_start_utc','snapshot_id','public_revision','native_revision','date_raw','declaration_response','war_id','npc_public_cunit_id','npc_army_owner','route_start_frame','route_progress_frame','combat_id','end_reason']},'evidence':evidence,'nodes':[{'id':ident,'label':label} for ident,label in nodes],'edges':[{'id':ident,'from':start,'to':end,'label':label,'status':status,'evidence':refs,'open_question':question} for ident,start,end,label,status,refs,question in edges],'cases':[{'id':'same-war-npc-response','question':'One bounded raise/route sequence in the new operator-triggered war.','status':'pending','evidence':[]},{'id':'optional-first-contact','question':'At most one same-war actual combat if it occurs within the unchanged hard budget.','status':'pending','evidence':[]}],'explicit_nonclaims':['natural NPC declaration','complete target scoring or reason for target selection','complete combat-power scoring or win probability','ordinary/desperate mode decision','retreat strategy or caller','reinforcement requesting-to-assigned closure','complete war outcome or peace strategy']}
    plan['question']='After a new official run restores the frozen day-zero save (or records a separate new start), which same-war NPC raising, committed movement and optional first-contact transitions can public native tools observe after one explicitly operator-declared legal war?'
    plan['observation']['identity_lifetime']='One newly bound official run/PID/connection/episode and exact WarID; R0004 is historical only. Full CUnit/CombatID are read from fresh formal rows and retired on disappearance/split/merge unless a successor is explicit.'
    plan['observation']['caller']='The unique owner of the new official run uses advertised resume-map/pause-map time slices; paused official query readbacks never force an NPC order.'
    plan['observation']['runtime_window_ref']='sampling-window.json (prepared future official run; R0004 has ended and supplies historical baseline only)'
    plan['pre_observation']['new_run']='Root must allocate and complete formal save restore/readback in a new run, or label a new start; preparation neither launches nor restores a game. Bind actual ready/HUD state, identity and current capabilities before any CASE-W action.'
    plan['bindings_to_fill_from_live'].update({key:None for key in ['official_run_id','pid','connection_generation','episode_run_id','restore_or_new_start_receipt','seed_save_binding','raw_video_binding']})
    save(args.output_dir/'plan.json',plan)
    print(json.dumps({'output':str(args.output_dir),'state':'prepared-not-executed','target_character_id':31549,'checkpoint_sha256':save_binding['sha256'],'live_case_w_edges':0}))

if __name__=='__main__':main()
