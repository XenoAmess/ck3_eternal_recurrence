"""Read-only assembly of the current native appointment window, never signoff."""
from __future__ import annotations
import copy
from decimal import Decimal
import re

TOOL = 'ck3_query_current_title_appointment_v1'
CASES = frozenset({'ui_tail','administrative_appointments','meritocratic_appointments'})
EXE_SHA = '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
SCOPE = 'complete_native_base_list_joined_to_source_pool_and_score_cache'
ELIGIBILITY = {
    'kind':'engine_appointment_candidate_pool_after_rule_rejection',
    'game_version':'1.20.0.4','executable_sha256':EXE_SHA,
    'population_rva':'171BCD0','pool_rva':'273A390','reject_predicate_rva':'273AA40',
    'reject_loop':'273A741..273A790: true removes pointer and decrements count',
    'base_list':'171BCD0 populates every retained pool character into base+18; UI sort/filter uses +48',
    'authored_definition':'game/gui/window_title_appointment.gui:43-62 (candidates that could be appointed)',
    'score_present_is_not_eligibility':True,
}

def require(value, message):
    if not value: raise ValueError('Appointment collection rejected: '+message)

def positive(value):
    return type(value) is int and 0 < value < 2**32-1

def frame_binding(frame):
    require(isinstance(frame,dict) and frame.get('paused') is True and frame.get('map_ready') is True,
            'current paused native map required')
    d=frame.get('diagnostics',{}); h=d.get('hello',{}); actor=frame.get('played_character',{})
    require(frame.get('source')=='injected-dll-named-pipe' and frame.get('backend_id')=='native-headless'
            and frame.get('episode_projection')=='native_campaign' and actor.get('alive') is True
            and actor.get('source')=='native', 'actual native campaign/actor required')
    require(h.get('game_version')=='1.20.0.4' and str(h.get('executable_sha256','')).lower()==EXE_SHA,
            'eligibility proof requires exact executable')
    values=(d.get('bridge_pid'),d.get('connection_generation'),actor.get('character_id'))
    require(all(positive(v) for v in values) and h.get('bridge_pid')==values[0]
            and h.get('connection_generation')==values[1], 'same PID/generation missing')
    require(type(frame.get('native_revision')) is int and type(frame.get('date_raw')) is int
            and isinstance(d.get('pipe_name'),str) and d['pipe_name'], 'native frame/date/pipe missing')
    return (*values,d['pipe_name'],frame['native_revision'],frame['date_raw'],frame.get('episode_run_id'))

def navigation_anchor(row, frame, requested_title_id, requested_title_key):
    require(isinstance(row,dict) and row.get('ok') is True and not row.get('error') and row.get('finished_at'),
            'completed actual typed navigation row required')
    result=row.get('result',{}); title=result.get('title',{}); binding=result.get('binding',{})
    require(result.get('accepted') is True and result.get('step')=='center-map-on-landed-title-v1'
            and result.get('status') in {'centered','already_centered'}
            and title.get('title_id')==requested_title_id and title.get('key')==requested_title_key,
            'requested full title ID/key differs from independent typed navigation')
    fb=frame_binding(frame)
    require(binding.get('bridge_pid')==fb[0] and binding.get('connection_generation')==fb[1]
            and binding.get('played_character_id')==fb[2] and binding.get('date_raw')==fb[5]
            and binding.get('native_revision')==fb[4], 'navigation crossed current native frame')
    require(frame_binding(row.get('after_snapshot'))==fb, 'navigation snapshot crossed current scene')
    return {'step_id':row['id'],'requested_title_id':requested_title_id,'requested_title_key':requested_title_key}

def join_pages(rows, anchor, *, requested_title_id, requested_title_key, expected_law, breakdown_character_id=None):
    binding=frame_binding(anchor)
    require(positive(requested_title_id) and isinstance(requested_title_key,str) and requested_title_key
            and isinstance(expected_law,str) and expected_law and isinstance(rows,list) and rows,
            'explicit independent title/law/pages required')
    common=None; candidates=[]; offset=0; breakdown=None
    fields=('requested_title_id','requested_holder_character_id','native_group_branch','group_first_title_id',
            'resolved_title_id','current_window_title_id','current_holder_character_id','current_title_key',
            'resolved_title_key','effective_succession_law_key','full_candidate_count','source_pool_count',
            'pool_consistency_token','score_fixed_point_scale','candidate_scope')
    for row in rows:
        require(row.get('ok') is True and not row.get('error') and row.get('finished_at'), 'failed/unfinished native page')
        require(frame_binding(row.get('after_snapshot'))==binding, 'page crossed PID/generation/actor/native revision/date')
        raw=row.get('result',{}); v=raw.get('title_appointment',{})
        for k,e in {'schema':'ck3-ingame-ui-window-v1','accepted':True,'available':True,'status':'observed',
                'window_kind':'title_appointment','window_name':'title_appointment','window_exists':True,
                'effective_visible':True,'enabled':True,'dispatch_invoked':False,'verification_pending':False,
                'paused':True,'played_character_id':binding[2],'native_revision':binding[4],
                'queried_native_revision':binding[4],'date_raw':binding[5],
                'queried_connection_generation':binding[1],'episode_run_id':binding[6],
                'application_owner_thread_verified':True,'gui_owner_binding_verified':True,'game_version':'1.20.0.4'}.items():
            require(type(raw.get(k)) is type(e) and raw[k]==e, 'wrong wrapper '+k)
        require(str(raw.get('executable_sha256','')).lower()==EXE_SHA, 'wrong page executable')
        require(v.get('schema')=='ck3-current-title-appointment-v1' and v.get('available') is True
                and v.get('requested_title_id')==requested_title_id and v.get('requested_resolves_to_current') is True,
                'input does not resolve to this current window')
        tid=v.get('current_window_title_id'); holder=v.get('current_holder_character_id')
        require(positive(tid) and positive(holder) and tid==v.get('group_first_title_id')==v.get('resolved_title_id')
                and v.get('requested_holder_character_id')==holder and v.get('resolved_title_key')==v.get('current_title_key')
                and v.get('native_group_branch') in {'character_1c0','character_1d0'}
                and raw.get('current_subject_id')==tid and raw.get('owner_character_id')==holder,
                'actual requested holder/group-first/resolved/current relationship differs')
        require(v.get('effective_succession_law_key')==expected_law and v.get('candidate_scope')==SCOPE
                and v.get('ai_control_available') is True and v.get('score_fixed_point_scale')==100000,
                'effective law/full pool/AI/scale unavailable')
        count=v.get('full_candidate_count'); token=v.get('pool_consistency_token')
        require(type(count) is int and 0<count<=4096 and count==v.get('source_pool_count')
                and isinstance(token,str) and re.fullmatch(r'fnv1a64:[0-9a-f]{16}',token), 'pool count/token missing')
        state={k:v.get(k) for k in fields}
        if common is None: common=state
        require(state==common, 'page title/law/count/token/scope changed')
        page=v.get('candidates'); end=v.get('next_offset')
        require(v.get('candidate_offset')==offset and type(end) is int and offset<end<=min(count,offset+64)
                and isinstance(page,list) and len(page)==end-offset, 'page skipped/truncated/duplicated')
        for index,c in enumerate(page,offset):
            require(isinstance(c,dict) and c.get('list_index')==index and positive(c.get('character_id'))
                    and c.get('candidate_pool_member') is True and c.get('alive') is True
                    and type(c.get('is_human_player')) is bool and type(c.get('is_ai')) is bool
                    and c['is_ai']==(not c['is_human_player'])
                    and type(c.get('native_rank')) is int and -1<=c['native_rank']<=count
                    and c.get('score_present') is (c['native_rank']>0) and type(c.get('score_raw')) is int,
                    'candidate full ID/order/engine eligibility/AI/score facts invalid')
            candidates.append({**copy.deepcopy(c),'eligible':True,'eligibility_source':ELIGIBILITY['kind']})
        require(v.get('breakdown_character_id')==(breakdown_character_id or 0)
                and v.get('breakdown_cache_refresh_only') is True, 'breakdown target crossed request')
        if breakdown_character_id:
            require(v.get('breakdown_getter_invoked') is True and v.get('breakdown_available') is True
                    and isinstance(v.get('breakdown'),dict), 'requested actual score breakdown unavailable')
            if breakdown is None: breakdown=copy.deepcopy(v['breakdown'])
            require(breakdown==v['breakdown'], 'score breakdown changed across pages')
        offset=end
    require(offset==common['full_candidate_count'] and len({c['character_id'] for c in candidates})==offset,
            'complete unique full pool not assembled')
    if breakdown_character_id:
        target=[c for c in candidates if c['character_id']==breakdown_character_id]
        require(len(target)==1 and target[0]['score_present'] is True
                and breakdown.get('value_raw')==target[0]['score_raw'], 'full candidate score/breakdown total differs')
    return {'schema':'ck3-appointment-complete-pool-acceptance-v1','binding':list(binding),
            'requested_title_id':requested_title_id,'requested_title_key':requested_title_key, **common,
            'candidates':candidates,'eligibility_provenance':copy.deepcopy(ELIGIBILITY),
            'breakdown_character_id':breakdown_character_id,'breakdown':breakdown,
            'page_step_ids':[r['id'] for r in rows],'business_acceptance':'NOT_ASSESSED'}

def bind_observation(observation, proof, *, requested_key=None, law=None):
    require(proof.get('schema')=='ck3-appointment-complete-pool-acceptance-v1', 'generated full pool proof required')
    require(observation.get('requested_title_id')==proof['requested_title_id']
            and observation.get('requested_title_key')==proof['requested_title_key']
            and observation.get('title_id')==proof['current_window_title_id']
            and observation.get('title_key')==proof['current_title_key']
            and observation.get('law')==proof['effective_succession_law_key'], 'observation input/actual title/law differs')
    require(requested_key is None or proof['requested_title_key']==requested_key, 'wrong original requested title')
    require(law is None or proof['effective_succession_law_key']==law, 'wrong original effective law')
    if 'candidates' in observation:
        rows=observation['candidates']; actual=proof['candidates']
        require(isinstance(rows,list) and len(rows)==len(actual), 'manual list is incomplete')
        for o,c in zip(rows,actual):
            require(all(o.get(k)==c[k] and type(o.get(k)) is type(c[k]) for k in ('character_id','eligible','is_ai')),
                    'manual candidate ID/eligibility/AI disagrees with native pool')
    observation['candidates']=copy.deepcopy(proof['candidates'])
    observation['native_title_normalization']={k:proof[k] for k in ('requested_title_id','requested_title_key',
        'requested_holder_character_id','group_first_title_id','resolved_title_id','current_window_title_id',
        'current_title_key','effective_succession_law_key')}
    return proof

def target_score(proof, actor, displayed=None):
    candidates=[c for c in proof['candidates'] if c['character_id']==actor]
    require(len(candidates)==1 and candidates[0]['eligible'] is True and candidates[0]['is_human_player'] is True
            and candidates[0]['is_ai'] is False and candidates[0]['score_present'] is True
            and proof.get('breakdown_character_id')==actor and isinstance(proof.get('breakdown'),dict)
            and proof['breakdown'].get('value_raw')==candidates[0]['score_raw'], 'actual naturally eligible human score/breakdown missing')
    score=candidates[0]['score_raw']
    if displayed is not None:
        require(type(displayed) in (int,float) and Decimal(str(displayed))*100000==score,
                'reviewed score differs from exact native fixed point total')
    return score
