"""One bounded C2 item chain through shared public tools; attribution stays unknown."""
from __future__ import annotations
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import faith_e02_first_four_integrated_queue as Q
from ck3_mod_acceptance_client import write_once
from ck3_mod_acceptance_cases.faith_e02_pilgrimage_adapter import (
    require_root_visual_review, visual_observation_sha256)

CASE = 'faith-engine-e02-first-four-integrated-v1'
PRODUCT = 'faith-engine'
ORIGIN = Path('C:/workspace/ck3-faith-and-power-20261017/episode02/production-b3-a01/native/qualifications/first-four-public-scout-a01/candidate/tools')
sys.path.insert(0,str(ORIGIN))
try:
    spec = importlib.util.spec_from_file_location('_faith_firstfour_original_scout', ORIGIN / 'ck3_mod_acceptance_cases/faith_e02_first_four_scout_adapter.py')
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
finally:
    sys.path.remove(str(ORIGIN))
require = Q.require
MAX_CALLS = 96
LIFECYCLE = S.LIFECYCLE | {'ck3_query_pending_character_interaction_context_v1',
    'ck3_reply_pending_character_interaction','ck3_select_event_option'}
# Public Selection requires the full original relic action bundle. The product
# dispatch policy still forbids remove and explicit slot manipulation.
RELIC_BUNDLE = {'ck3_set_holy_site_relic_slot_selection_v1','ck3_select_holy_site_relic_artifact_v1',
    'ck3_remove_holy_site_relic_v1',Q.ENSHRINE}
REQUIRED = Q.TOOLS | LIFECYCLE | RELIC_BUNDLE
SCOPE = {'equip_once':True,'unequip_once':True,'enshrine_once':True,'replace_allowed':False,
    'create_allowed':False,'promote_allowed':False,'day_advance_allowed':False,
    'new_save_allowed':False,'ordinary_campaign_credit':False,'site_attribution_inferred':False}

def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def validate_contract(context):
    c = context['case_contract']; spec = context['case_spec']
    require(c.get('schema') == 'faith-e02-first-four-integrated-case-v1' and c.get('case') == context.get('case') == CASE
        and c.get('product') == context.get('product') == PRODUCT,'Integrated case identity differs')
    saved = c.get('saved_input',{})
    require(set(saved) == {'save',*S.SAVE} and all(type(saved.get(k)) is type(v) and saved[k] == v for k,v in S.SAVE.items()),
        'Original independent C2 identity differs')
    require(c.get('profile') == {'enabled_mods':[],'product_files':[]} and c.get('scope') == SCOPE
        and c.get('max_public_calls') == MAX_CALLS,'Narrow vanilla scope differs')
    require(c.get('machine_id') == '4-8e1c2f1861','Explicit target machine required')
    for flag in ('opt_in_holy_site_creation_ui','opt_in_holy_site_relic_actions',
                 'opt_in_player_artifact_personal_use_actions','opt_in_player_inventory_window_open'):
        require(spec.get(flag) is True,'Independent public flag missing: '+flag)
    for flag in ('opt_in_holy_site_creation_create_once','opt_in_player_rite_creation_actions','opt_in_player_pilgrimage_execution'):
        require(spec.get(flag) is False,'Unrelated world operation must stay closed')
    require(set(spec.get('required_mcp_tools',[])) == REQUIRED and set(spec.get('opt_in_read_only_mcp_tools',[])) == Q.READONLY,
        'Actual explicit required/read-only tool bundle differs')
    require(type(c.get('dependencies')) is list and len(c['dependencies']) == 6,
        'Exact case/scout/binding/visual-review source pins are required')
    for row in c['dependencies']: require(S.pin(row['path']) == row,'Pinned case/provider source changed')
    require(type(c.get('provider_source_evidence')) is list and len(c['provider_source_evidence']) == 3,
        'Frozen faith, actor and inventory SDK evidence is required')
    for row in c['provider_source_evidence']:require(S.pin(row['path']) == row,'Provider source evidence changed')
    return c

def prepare_case(context):
    from ck3_mod_acceptance_prepare import materialize_product_profile, finish_product_profile
    from ck3_live_run_id import current_machine_id
    c = validate_contract(context);require(current_machine_id() == c['machine_id'],'Executing machine differs')
    admission = context['case_inputs']['storage_admission']
    require(S.pin(admission['path']) == admission,'Fresh admission pin changed')
    grant = read(admission['path'])
    require(grant.get('active') is True and grant.get('machine_id') == c['machine_id']
        and datetime.now(timezone.utc) < datetime.fromisoformat(grant['expires_at_utc'].replace('Z','+00:00')),
        'Fresh scene capacity admission required')
    saved = dict(context['saved_campaign']);require(saved == c['saved_input'],'Original saved input differs')
    actual = S.pin(saved['save']);require(all(actual[k] == saved[k] for k in ('bytes','sha256')),'Original C2 bytes changed')
    profile = materialize_product_profile(context,None,context['case_inputs']['configuration'])
    profile = finish_product_profile(context,profile,provenance={'machine_id':c['machine_id'],
        'kind':'first-four-integrated-original-C2','saved_input':saved,'storage_admission':admission,
        'preparation_mod_mounted':False,'actual_restore_observed':False,'world_actions_performed':False})
    return {'startup':{'mode':'saved_campaign','state_dir':profile['state_dir'],
        'saved_campaign':{**saved,'product_inventory':profile['product_inventory']['path']}},
        'profile':profile,'initial_plan':context['case_spec']['initial_plan'],
        'runtime_status':'NOT_RUN','business_pass':False,'product_release_pass':False}

class Integrated(S.Scout):
    def __init__(self,context,client,binding,reader):
        super().__init__(context,client,binding,reader)
        self.world = {'equip':0,'unequip':0,'enshrine':0,'inventory_open':0}
        self.unknown = False
    def guard(self,n=1):
        require(self.calls+n <= MAX_CALLS,'Finite integrated public-control budget exhausted')
        self.client.guard(120+30*n+10)
    def scene(self,frame):
        if frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None:
            self.guard();self.calls += 1
            frame = self.client.snapshot(require_event_free=False)
        if frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None:
            request = {'machine_id':self.context['case_contract']['machine_id'],'run_id':self.context['run_id'],
                'frame':frame,'actual_native_options_required':True,'native_selection_only':True,
                'policy':'Known dedicated policy first; unknown event saves actual IDs/options and selects first displayed native option; interaction uses original left semantics. No OCR/mouse. Offline analysis runs concurrently.',
                'remaining_public_controls':MAX_CALLS-self.calls}
            self.sequence += 1
            response = S._review(self.context,self.client,'firstfour-integrated-interruption-'+str(self.sequence),request,160)
            require(response.get('native_selection_only') is True and response.get('ack_and_disappearance_separate') is True
                and response.get('offline_analysis_input_written') is True,'Root must preserve actual interruption inputs and independent outcome')
            require(type(response.get('evidence')) is list and bool(response['evidence']),
                'Actual native event/option/ACK/post/offline-input evidence is required')
            external = response.get('actual_public_controls_used')
            require(type(external) is int and 1 <= external <= 12 and self.calls+external+1 <= MAX_CALLS,
                'Bound the actual Root native interruption controls in this case budget')
            for row in response.get('evidence',[]):require(S.pin(row['path']) == row,'Actual interruption evidence changed')
            self.calls += external+1
            frame = self.client.snapshot(require_event_free=False)
        S.same_scene(frame,self.binding,self.reader)
        require(frame.get('pending_character_interaction') is None,'Original interaction remains visible')
        return frame
    def submit(self,steps,name):
        self.guard(len(steps));Q.validate({'steps':steps});self.calls += len(steps)
        rows = self.client.execute_plan(steps,name,timeout=30*len(steps))
        require(type(rows) is list and len(rows) == len(steps),'Original public result rows missing')
        for step,row in zip(steps,rows):
            self.rows.append({'step':step,'row':row})
            for key in ('before_snapshot','after_snapshot'):
                require(type(row.get(key)) is dict,'Independent original public frame missing')
                self.scene(row[key])
        return rows
    def domain(self,tool,args=None):
        value = self.value(self.call(tool,args))
        if value is not None and tool in Q.READONLY:
            require(value.get('read_only') is True,'Original observer lost read-only role')
            for key in ('holy_site_id','artifact_id'):
                if args and key in args:require(value.get('requested_'+key) == args[key],'Native observer crossed requested full ID: '+key)
        return value
    def review(self,name,observation,approval):
        request = {'machine_id':self.context['case_contract']['machine_id'],'run_id':self.context['run_id'],
            'native_observation':observation,'native_observation_sha256':visual_observation_sha256(observation),
            'approval_key':approval,'prepare_original_image':True,'scope':SCOPE,
            'note':'Review actual full IDs, legality, current native slot/quote and original pixels; no total-to-site attribution.'}
        answer = S._review(self.context,self.client,'firstfour-integrated-review-'+name,request,160)
        require_root_visual_review(answer,observation,approval)
        return answer
    def once(self,key,tool,args):
        require(not self.unknown and self.world[key] == 0,'Unknown/consumed original mutation cannot be replayed')
        self.world[key] += 1
        self.client.checkpoint('firstfour-integrated-'+key+'-once-intent',{'run_id':self.context['run_id'],
            'machine_id':self.context['case_contract']['machine_id'],'tool':tool,'args':args,'automatic_retry':False})
        try:
            row = self.call(tool,args)
        except Exception:
            self.unknown = True
            raise
        value = self.value(row)
        if value is None or ((value.get('once_intent_consumed') is True or value.get('invoked') is True)
                and value.get('needs_recovery') is not False): self.unknown = True
        return value

def recipient_ids(evidence,player):
    ids = [player]
    for row in evidence.get('site_observations',[]):
        context = (row.get('relic') or {}).get('county_context',{})
        target = context.get('county_holder_id')
        if context.get('available') is True and Q.ref(target) and target not in ids: ids.append(target)
        if len(ids) == 2: break
    return ids

def actor_read(case,ids):
    result = {}
    for target in ids:
        value = case.domain(Q.ACTOR,{'character_id':target,'skill':'diplomacy'})
        if value is not None:
            require(value.get('character_id') == target and value.get('played_character_id') == case.binding['played_character_id']
                and value.get('date_raw') == case.binding['date_raw'],'Actor target/current source differs')
            require(value.get('site_attribution_observed') is False and value.get('selected_site_contribution_raw') is None,
                'Current provider cannot grant selected-site numeric attribution')
        result[str(target)] = value
    return result

def paired_actors(before,after,ids):
    pairs = []
    for target in ids:
        a,b = before.get(str(target)),after.get(str(target))
        observed = bool(a and b and a.get('available') is True and b.get('available') is True
            and a.get('character_id') == b.get('character_id') == target
            and a.get('requested_skill') == b.get('requested_skill') == 'diplomacy'
            and a.get('played_character_id') == b.get('played_character_id')
            and a.get('date_raw') == b.get('date_raw')
            and a.get('faith_id') == b.get('faith_id') and a.get('rite_id') == b.get('rite_id'))
        pairs.append({'character_id':target,'independent_pair_observed':observed,
            'before':a,'after':b,'site_attribution_observed':False,'selected_site_contribution_raw':None,
            'phase_scope':'Whole equip -> unequip -> enshrine chain; any intervening native event is a separate possible cause',
            'unattributed_diplomacy_difference':b['current_skill_points']['diplomacy']-a['current_skill_points']['diplomacy'] if observed else None,
            'cache_generation_time_known':False,'personal_or_site_net_gain_proven':False})
    return pairs

def inventory_visible(value):
    current = (value or {}).get('current',{})
    return bool(value and value.get('available') is True and current.get('available') is True
        and all(current.get(key) is True for key in ('window_present','root_present','native_visible','effective_visible','current_player_selected')))

def ensure_inventory(case):
    require(case.unknown is False,'Existing unknown intent cannot be cleared by an inventory query')
    original = case.domain('ck3_query_ingame_ui_window_v1',{'window_kind':'inventory'})
    require(not original or original.get('client_replay_blocked') is not True,'Existing inventory replay lock requires original recovery')
    if inventory_visible(original): return {'already_visible':True,'current':original,'new_open_observed':False}
    require(original and original.get('available') is True,'Actual inventory/HUD owner/source unavailable')
    answer = case.once('inventory_open',Q.OPEN_INVENTORY,{})
    sequence = (answer or {}).get('intent_sequence')
    no_claim = bool(answer and sequence == 0 and type(sequence) is int and all(
        answer.get(key) is False for key in ('once_intent_consumed','invoked','needs_recovery')))
    if no_claim:
        require(answer.get('status') == 'inventory_current_player_already_visible_no_call',
            'Known inventory preinvoke rejection cannot recover a historical intent')
        current = case.domain('ck3_query_ingame_ui_window_v1',{'window_kind':'inventory'})
        require(current and current.get('client_replay_blocked') is not True and inventory_visible(current),
            'No-call inventory must be independently visible for the current player')
        return {'already_visible':True,'submit':answer,'current':current,'new_open_observed':False}
    if not (type(sequence) is int and sequence > 0):
        # A retained query sequence alone is not proof of this call. Keep unknown
        # until a caller-bound current sequence contract is actually available.
        case.unknown = True
        raise ValueError('Unknown inventory Open has no call-bound native sequence; never retry or post historical intent')
    for _ in range(3):
        post = case.value(case.call(Q.INVENTORY_POST,{'expected_intent_sequence':sequence}))
        if post and post.get('desired_window_observed') is True and inventory_visible(post):
            case.unknown = False
            return {'already_visible':False,'submit':answer,'post':post,'new_open_observed':True}
    case.unknown = True
    raise ValueError('Original inventory opening lacks a current independent post; never retry')

def item_query(case,artifact):
    value = case.domain(Q.ARTIFACT,{'artifact_id':artifact})
    require(value and value.get('requested_artifact_id') == artifact and value.get('played_character_id') == case.binding['played_character_id'],
        'Actual personal item identity unavailable')
    require(value.get('personal_net_effect_attributed') is False,'Item modifier text cannot become actor net effect')
    return value

def equip_unequip(case,artifact,result):
    before = item_query(case,artifact)
    require(before.get('available') is True and before.get('personally_owned') is True
        and before.get('inventory_artifact') is True and before.get('equipped') is False
        and before.get('inventory_view_visible') is True and before.get('native_equipped_observed') is True
        and before.get('can_equip_in_effective_slot') is True and before.get('replacing_artifact_id') is None
        and type(before.get('effective_slot_index')) is int,'A real unequipped owned artifact and empty legal personal slot are required')
    result['personal_before'] = before
    for key,desired in (('equip',True),('unequip',False)):
        current = item_query(case,artifact)
        slot = current.get('effective_slot_index') if desired else current.get('equipped_slot_index')
        legal = (current.get('available') is True and current.get('equipped') is not desired
            and (current.get('can_equip_in_effective_slot') is True if desired else current.get('can_unequip') is True)
            and type(slot) is int)
        require(legal and (not desired or current.get('replacing_artifact_id') is None),
            'Fresh equipment state or slot legality changed')
        result[key+'_review'] = case.review(key,current,key+'_once_authorized')
        latest = item_query(case,artifact)
        for field in ('equipped','effective_slot_index' if desired else 'equipped_slot_index',
                      'can_equip_in_effective_slot' if desired else 'can_unequip'):
            require(latest.get(field) == current.get(field),'Native personal terms changed after review: '+field)
        require(not desired or latest.get('replacing_artifact_id') is None,
            'Another artifact entered the personal slot after manual review')
        args = {'artifact_id':artifact,'desired_equipped':desired,'expected_slot_index':slot,
            'expected_replacing_artifact_id':None,'policy_positive':True}
        answer = case.once(key,Q.EQUIP,args)
        result[key+'_submit'] = answer
        sequence = (answer or {}).get('intent_sequence')
        # This provider's ordinary item query has no native-intent recovery field.
        # A missing sequence is a caller boundary, never a fabricated sequence.
        require(type(sequence) is int and sequence > 0,'Unknown item action has no recoverable native intent sequence')
        post = None
        for _ in range(3):
            candidate = case.value(case.call(Q.EQUIP_POST,{'artifact_id':artifact,'expected_intent_sequence':sequence}))
            if candidate and candidate.get('desired_inventory_state_observed') is True:
                post = candidate;break
        if post is None: case.unknown = True
        require(post is not None and post.get('artifact_id') == artifact and post.get('desired_equipped') is desired,
            'Original personal action lacks the exact independent current desired-state proof')
        case.unknown = False
        independent = item_query(case,artifact)
        require(independent.get('available') is True and independent.get('equipped') is desired
            and independent.get('personally_owned') is True,'Separate personal inventory read disagrees with native post')
        result[key+'_post'] = post;result[key+'_independent_item'] = independent

def enshrine_terms(value,site,artifact):
    require(value and value.get('available') is True and value.get('requested_holy_site_id') == site
        and value.get('requested_artifact_id') == artifact and value.get('selected_artifact_matches_request') is True
        and value.get('preview_identity_available') is True,'Actual same-item shrine quote unavailable')
    own = value.get('artifact_ownership',{});destination = value.get('destination',{})
    require(own.get('available') is True and own.get('character_owner_matches_player') is True
        and own.get('player_owned_reference_member') is True,'Same item no longer personally owned')
    equipped = own.get('player_equipped_slot_member',{})
    require(equipped.get('available') is True and equipped.get('value') is False,'Independent original ownership still shows equipment or unknown membership')
    permissions = value.get('permissions',{})
    for group in ('artifact_permissions','current_buttons'):
        p = permissions.get(group,{}).get('can_enshrine',{})
        require(p.get('available') is True and p.get('value') is True,'Fresh original CanEnshrine unavailable/rejected')
    require(destination.get('available') is True and destination.get('action_kind') == 'enshrine'
        and type(destination.get('effective_slot_index')) is int and destination.get('replacing_artifact_id') is None,
        'Only an actual empty original shrine slot is allowed')
    require(value.get('selected_action_effect_description',{}).get('available') is True,'Original shrine effect/price text missing')
    return {'holy_site_id':site,'artifact_id':artifact,'expected_effective_slot_index':destination['effective_slot_index'],
        'expected_replacing_empty':True,'expected_preview_sha256':value['preview_identity_sha256']}

def enshrine(case,site,artifact,result):
    case.presentation('ck3_open_holy_site_window_v1',{'holy_site_id':site},
        'ck3_query_ingame_ui_window_v1',{'window_kind':'holy_site'})
    case.presentation('ck3_select_holy_site_relic_artifact_v1',{'holy_site_id':site,'artifact_id':artifact},
        Q.ACTION_CONTEXT,{'holy_site_id':site,'artifact_id':artifact})
    before = case.domain(Q.ACTION_CONTEXT,{'holy_site_id':site,'artifact_id':artifact})
    args = enshrine_terms(before,site,artifact)
    case.guard();wallet_before = case.client.snapshot();case.calls += 1;S.same_scene(wallet_before,case.binding,case.reader)
    result['enshrine_quote'] = before
    result['enshrine_review'] = case.review('enshrine',before,'enshrine_once_authorized')
    latest = case.domain(Q.ACTION_CONTEXT,{'holy_site_id':site,'artifact_id':artifact})
    require(enshrine_terms(latest,site,artifact) == args,'Original shrine price/ownership/slot changed after review')
    result['enshrine_submit'] = case.once('enshrine',Q.ENSHRINE,args)
    # ACK stays pending. Independent owner, inventory and exact slot facts decide.
    after = case.domain(Q.ACTION_CONTEXT,{'holy_site_id':site,'artifact_id':artifact})
    relic = case.domain(Q.RELIC_CONTEXT,{'holy_site_id':site})
    permissions = case.domain('ck3_query_player_holy_site_relic_permissions_v1',{'holy_site_id':site,'artifact_id':artifact})
    case.guard();wallet_after = case.client.snapshot();case.calls += 1;S.same_scene(wallet_after,case.binding,case.reader)
    own = (after or {}).get('artifact_ownership',{});inventory = (relic or {}).get('inventory',{})
    slot = next((row for row in inventory.get('slots',[]) if row.get('slot_index') == args['expected_effective_slot_index']),None)
    player_inventory = (permissions or {}).get('player_inventory',{})
    observed = bool(after and after.get('available') is True and own.get('available') is True
        and own.get('artifact_id') == artifact and own.get('holy_site_owner_id') == site
        and own.get('character_owner_id') is None and own.get('player_owned_reference_member') is False
        and inventory.get('available') is True and slot and slot.get('artifact_id') == artifact
        and player_inventory.get('available') is True and artifact not in player_inventory.get('artifact_ids',[]))
    if not observed: case.unknown = True
    elif result['enshrine_submit'] is not None: case.unknown = False
    result.update(enshrine_owner_slot_inventory_observed=observed,enshrine_action_after=after,
        enshrine_site_after=relic,enshrine_permissions_after=permissions,
        wallet_before=wallet_before,wallet_after=wallet_after,payment_total_proven=False,
        personal_or_site_net_gain_proven=False)

def run_case(context,client):
    c = validate_contract(context);out = Path(context['output']);first = client.snapshot(require_event_free=False)
    write_once(out/'firstfour-integrated-first-frame.json',{'machine_id':c['machine_id'],'run_id':context['run_id'],'frame':first})
    reader,sources = S.shared_opening_binding(context);binding = reader(first)
    require(binding['played_character_id'] == S.SAVE['player_id'],'Actual original C2 player differs')
    case = Integrated(context,client,binding,reader)
    case.scene(first)
    result = {'schema':'faith-e02-first-four-integrated-result-v1','case':CASE,'machine_id':c['machine_id'],
        'run_id':context['run_id'],'binding':binding,'binding_sources':sources,'status':'PARTIAL',
        'business_pass':False,'product_release_pass':False,'site_attribution_observed':False,
        'selected_site_contribution_raw':None,'automatic_retry':False,'payment_total_proven':False}
    evidence = {};before = {};ids = [binding['played_character_id']]
    try:
        S._review(context,client,'firstfour-integrated-before-scout',{'machine_id':c['machine_id'],
            'run_id':context['run_id'],'scope':SCOPE,'binding':binding,'max_public_calls':MAX_CALLS},180)
        S.collect_scout(case,evidence)
        ids = recipient_ids(evidence,binding['played_character_id'])
        result['actual_recipient_ids'] = ids
        before = actor_read(case,ids);result['actors_before'] = before
        candidates = [x for x in evidence.get('artifact_samples',[]) if x.get('owned_by_player') is True
            and x.get('can_enshrine') is True and x.get('equipped') is False]
        require(candidates,'No actually sampled personally owned unequipped enshrinable artifact')
        selected = candidates[0];site,artifact = selected['site_id'],selected['artifact_id']
        result.update(selected_site_id=site,selected_artifact_id=artifact)
        result['inventory_open'] = ensure_inventory(case)
        equip_unequip(case,artifact,result)
        enshrine(case,site,artifact,result)
        result['status'] = 'MINIMAL_ITEM_CHAIN_OBSERVED_ATTRIBUTION_PENDING' if result.get('enshrine_owner_slot_inventory_observed') else 'PARTIAL_ENSHRINE_POST_UNKNOWN'
    except Exception as error:
        result['failure'] = type(error).__name__+': '+str(error)
    finally:
        try: after = actor_read(case,ids)
        except Exception as error:
            after = {};result['actor_after_failure'] = type(error).__name__+': '+str(error)
        result.update(actors_after=after,actor_pairs=paired_actors(before,after,ids),evidence=evidence,
            submitted_rows=case.rows,world_submissions=case.world,unknown_original_action=case.unknown,
            public_calls_used=case.calls,public_calls_cap=MAX_CALLS,normal_close_pending=True,
            required_slots={'E2-A1':{'closed':False,'reason':'provider explicitly has no selected-site numeric attribution; no promote action in this minimal case'},
                'E2-A2':{'closed':False,'actual_native_refusals':evidence.get('native_refusals',[]),'location_specific_refusal_proven':False},
                'E2-B1-personal':{'independent_equip_observed':bool(result.get('equip_post')),
                    'independent_unequip_observed':bool(result.get('unequip_post')),'personal_net_effect_proven':False},
                'E2-B1-enshrine':{'owner_slot_inventory_observed':result.get('enshrine_owner_slot_inventory_observed',False),
                    'personal_or_site_net_gain_proven':False},'E2-B2':{'required':False,'omitted':True}})
        write_once(out/'firstfour-integrated-result.json',result)
    return result

def verify_case(context):
    c = validate_contract(context);value = read(Path(context['output'])/'firstfour-integrated-result.json')
    require(value.get('case') == CASE and value.get('run_id') == context['run_id'] and value.get('machine_id') == c['machine_id'],
        'Foreign integrated case result')
    require(value.get('public_calls_used',MAX_CALLS+1) <= MAX_CALLS and value.get('site_attribution_observed') is False
        and value.get('selected_site_contribution_raw') is None,'Case must retain finite unattributed outcome')
    return {'status':value['status'],'required_slots':value['required_slots'],'business_pass':False,
        'product_release_pass':False,'automatic_retry':False,'normal_close_verified_by_existing_public_lifecycle':False}
