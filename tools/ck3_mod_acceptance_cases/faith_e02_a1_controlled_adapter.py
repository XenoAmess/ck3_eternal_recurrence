"""One C2/native-only controlled Demote27. No site attribution is inferred."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import faith_e02_a1_controlled_queue as Q
from ck3_mod_acceptance_client import write_once
from ck3_mod_acceptance_cases.faith_e02_d1_readonly_adapter import shared_opening_binding
from ck3_mod_acceptance_cases.faith_e02_pilgrimage_adapter import require_root_visual_review,visual_observation_sha256

CASE='faith-engine-e02-a1-controlled-medina-demote-v1'
PRODUCT='faith-engine'
SAVE={'bytes':50210503,'sha256':'7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e','player_id':15893,'date_raw':51394920}
EXE='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
MAX_CALLS=48
SKILLS=('diplomacy','martial','stewardship','intrigue','learning','prowess')
LIFECYCLE=frozenset({'ck3_query_campaign_root_context_v1','ck3_query_current_event_window_context_v1',
    'ck3_query_pending_character_interaction_context_v1','ck3_reply_pending_character_interaction',
    'ck3_select_event_option','ck3_query_normal_exit_context_v1','ck3_request_normal_exit_v1','ck3_observe_normal_exit_v1'})
REQUIRED=Q.TOOLS|LIFECYCLE
CLOSED=('opt_in_holy_site_creation_ui','opt_in_holy_site_creation_create_once','opt_in_holy_site_relic_actions',
        'opt_in_player_rite_creation_actions','opt_in_player_pilgrimage_execution',
        'opt_in_player_artifact_personal_use_actions','opt_in_player_inventory_window_open')
SCOPE={'one_demote27':True,'other_world_actions':False,'artifact_movement':False,'day_advance':False,
       'new_save':False,'ordinary_campaign_credit':False,'site_attribution_inferred':False,'whole_film_required_slots':24,
       'mandatory_native_interruption_policy':True,'interruption_invalidates_controlled_case':True}
require=Q.require

def eligible_actor(value,faith):
    return type(value) is dict and value.get('available') is True and value.get('faith_id')==faith


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(path):
    path=Path(path).resolve();h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':h.hexdigest()}
def digest(v):return visual_observation_sha256(v)

def validate_contract(context):
    c=context['case_contract'];spec=context['case_spec']
    require(c.get('schema')=='faith-e02-a1-controlled-case-v1' and c.get('case')==context.get('case')==CASE
        and c.get('product')==context.get('product')==PRODUCT,'A1 product/case identity differs')
    saved=c.get('saved_input',{})
    require(set(saved)=={'save',*SAVE} and type(saved.get('save')) is str and all(type(saved.get(k)) is type(v) and saved[k]==v for k,v in SAVE.items()),'Original C2 input identity differs')
    require(c.get('machine_id')=='4-8e1c2f1861' and c.get('scope')==SCOPE
        and c.get('profile')=={'enabled_mods':[],'product_files':[]} and c.get('max_public_calls')==MAX_CALLS,'A1 vanilla scope/identity differs')
    for key,wanted in (('required_mcp_tools',REQUIRED),('opt_in_read_only_mcp_tools',Q.READONLY)):
        rows=spec.get(key);require(type(rows) is list and len(rows)==len(set(rows)) and set(rows)==wanted,'Declare all required tools once before launch: '+key)
    require(all(spec.get(k) is False for k in CLOSED),'Unrelated private operation must stay closed')
    require(spec.get('whole_product_acceptance_credit') is False and spec.get('business_contract_applicable') is False,'No release/whole-film credit')
    require(type(c.get('dependencies')) is list and len(c['dependencies'])==4,'Exact adapter/queue/shared-binding/visual-review pins required')
    expected={Path(__file__).resolve(),Path(Q.__file__).resolve(),Path(shared_opening_binding.__code__.co_filename).resolve(),Path(require_root_visual_review.__code__.co_filename).resolve()}
    require({Path(x['path']).resolve()for x in c['dependencies']}==expected,'A1 helper source escaped declared paths')
    for row in c['dependencies']:require(pin(row['path'])==row,'A1 source dependency changed')
    cohort=c.get('native_cohort')
    require(type(cohort) is dict and set(cohort)=={'dll_sha256','qualification_receipt'}
        and type(cohort['dll_sha256']) is str and len(cohort['dll_sha256'])==64
        and all(x in '0123456789abcdef'for x in cohort['dll_sha256']),'Bind the new actual native cohort before prepare')
    require(pin(cohort['qualification_receipt']['path'])==cohort['qualification_receipt'],'Native cohort receipt changed')
    ledger=Path(c.get('intent_ledger_root',''))
    require(ledger.is_absolute() and c.get('intent_ledger_root')==context.get('case_inputs',{}).get('intent_ledger_root'),'Stable explicit cross-run intent ledger required')
    require(spec.get('budgets',{}).get('hold_seconds',0)>=1500 and spec['budgets'].get('timeout',0)>=2100,'Enough Root review/readback/normal Quit budget required')
    return c

def prepare_case(context):
    from ck3_mod_acceptance_prepare import materialize_product_profile,finish_product_profile
    from ck3_live_run_id import current_machine_id
    c=validate_contract(context);require(current_machine_id()==c['machine_id'],'Executing machine differs')
    ref=context['case_inputs']['storage_admission'];require(pin(ref['path'])==ref,'Fresh admission pin changed')
    grant=read(ref['path']);expiry=datetime.fromisoformat(grant['expires_at_utc'].replace('Z','+00:00'))
    require(grant.get('machine_id')==c['machine_id'] and grant.get('active') is True and expiry.tzinfo
        and datetime.now(timezone.utc)<expiry,'Fresh scene storage admission required')
    saved=dict(context['saved_campaign']);require(saved==c['saved_input'],'Saved case input differs')
    p=Path(saved['save']);require(p.is_file() and not p.is_symlink() and p.suffix.lower()=='.ck3','Immutable original C2 required')
    before=p.stat();actual=pin(p);after=p.stat()
    require(all(actual[k]==saved[k]for k in ('bytes','sha256')) and (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Original C2 bytes changed')
    profile=materialize_product_profile(context,None,context['case_inputs']['configuration'])
    profile=finish_product_profile(context,profile,provenance={'machine_id':c['machine_id'],'kind':'A1-one-Demote27-original-C2',
        'saved_input':saved,'storage_admission':ref,'preparation_mod_mounted':False,'actual_restore_observed':False,'world_actions_performed':False})
    return {'startup':{'mode':'saved_campaign','state_dir':profile['state_dir'],'saved_campaign':{**saved,'product_inventory':profile['product_inventory']['path']}},
        'profile':profile,'initial_plan':context['case_spec']['initial_plan'],'runtime_status':'NOT_RUN','business_pass':False,'product_release_pass':False}

def actor(value,target,played,date):
    require(type(value) is dict and value.get('available') is True and value.get('read_only') is True
        and value.get('character_id')==target and value.get('played_character_id')==played and value.get('date_raw')==date
        and value.get('requested_skill')=='diplomacy' and value.get('requested_skill_enum')==0
        and value.get('game_version')=='1.20.0.4' and str(value.get('executable_sha256','')).lower()==EXE
        and value.get('two_pass_stable') is True and value.get('callback_provenance')=='exact4_native','Actual stable actor observation unavailable')
    require(value.get('site_attribution_observed') is False and value.get('selected_site_contribution_raw') is None
        and value.get('cache_generation_time_known') is False,'Do not upgrade aggregate/cache to single-site attribution')
    require(Q.ref(value.get('rite_id')) and Q.ref(value.get('faith_id')),'Actual actor Rite/Faith references required')
    points=value.get('current_skill_points');require(type(points) is dict and set(points)==set(SKILLS)
        and all(type(x) is int and -(2**31)<=x<2**31 for x in points.values()),'Six actual signed skill points required')
    require(type(value.get('effective_devotion_level')) is int and -(2**31)<=value['effective_devotion_level']<2**31
        and type(value.get('devotion_total_raw')) is int and -(2**63)<=value['devotion_total_raw']<2**63,'Own level/total required')
    require(type(value.get('actual_skill_breakdown')) is str and len(value['actual_skill_breakdown'].encode('utf-8'))<=32768,'Whole original actor text required')
    return value

def actor_projection(v):
    return {k:v[k]for k in ('character_id','rite_id','faith_id','current_skill_points','effective_devotion_level','devotion_total_raw','actual_skill_breakdown')}

def sites(value,faith):
    require(value and value.get('available') is True,'Actual complete site observation required')
    rows=value.get('current_faith_sites');require(type(rows) is list and len(rows)<=64,'Bounded current Faith list required')
    out={}
    for row in rows:
        site=row.get('holy_site_id');require(row.get('available') is True and Q.ref(site) and site not in out,'Site unavailable/duplicate/fullID missing')
        edges=row.get('associated_faiths');require(type(edges) is list,'Actual associated Faith grades required')
        by_faith={}
        for edge in edges:
            f=edge.get('faith_id');require(edge.get('available') is True and Q.ref(f) and f not in by_faith
                and edge.get('faith_lists_site') is True and type(edge.get('eminent')) is bool,'Unobserved or duplicate grade edge')
            by_faith[f]=edge['eminent']
        require(faith in by_faith,'Current Faith edge absent')
        inv=row.get('inventory',{});require(inv.get('available') is True and type(inv.get('artifact_ids')) is list,'Every related inventory must be observed')
        out[site]={'type_key':row.get('type_key'),'barony_title_id':row.get('barony_title_id'),
            'grades':by_faith,'inventory_artifact_ids':inv['artifact_ids']}
    require(27 in out and out[27]['type_key']=='medina' and out[27]['barony_title_id']==8492,'Current selected type/place differs from candidate')
    actual_ids=value.get('current_faith_holy_site_ids')
    require(type(actual_ids) is list and len(actual_ids)==len(out) and set(actual_ids)==set(out),
        'Actual complete current-Faith membership must match observed rows')
    return out

def major_ids(projection,faith):
    return sorted(site for site,row in projection.items()if row['grades'][faith] is True)

def relic(value,faith):
    require(value and value.get('available') is True and value.get('requested_holy_site_id')==27,'Actual selected relic context unavailable')
    county=value.get('county_context',{});cache=value.get('cached_world_state',{});inv=value.get('inventory',{})
    require(county.get('available') is True and county.get('barony_title_id')==8492
        and county.get('county_holder_faith_id')==faith and Q.ref(county.get('county_holder_id')),'Actual county-holder Faith control gate unavailable')
    require(cache.get('available') is True and type(cache.get('is_active')) is bool
        and type(cache.get('total_active_artifact_rarity')) is int and inv.get('available') is True
        and type(inv.get('artifact_ids')) is list and type(inv.get('slots')) is list,'Active/rarity/inventory unknown')
    objects=inv.get('artifact_objects')
    require(type(objects) is list and all(type(x) is dict and x.get('available') is True and Q.ref(x.get('artifact_id'))
        and x.get('native_holy_site_owner_id')==27 for x in objects),'Selected site artifact owner objects must actually resolve')
    require(all(Q.ref(x)for x in inv['artifact_ids']) and all(type(x) is dict and type(x.get('slot_index')) is int
        and (x.get('artifact_id') is None or Q.ref(x['artifact_id']))for x in inv['slots']),'Actual inventory refs/slots required')
    require(set(inv['artifact_ids'])=={x['artifact_id']for x in objects},'Owner object union must cover selected inventory')
    return {'county':{k:county.get(k)for k in ('barony_title_id','county_title_id','county_holder_id','county_holder_rite_id','county_holder_faith_id')},
        'active':cache['is_active'],'rarity':cache['total_active_artifact_rarity'],
        'artifact_ids':inv['artifact_ids'],'slots':inv['slots'],
        'artifact_owners':[{'artifact_id':x.get('artifact_id'),'available':x.get('available'),'rarity_level':x.get('rarity_level'),
            'native_holy_site_owner_id':x.get('native_holy_site_owner_id')}for x in inv.get('artifact_objects',[])]}

def wallet(frame):
    result={}
    for key in ('gold','prestige','piety'):
        v=frame.get('played_character_'+key)
        require(type(v) is dict and set(v)=={'raw','scale'} and type(v.get('raw')) is int and v.get('scale')==100000,'Actual raw wallet missing: '+key)
        result[key]=v['raw']
    return result

def terms(value,played):
    require(value and value.get('available') is True and value.get('read_only') is True
        and value.get('action')=='demote' and value.get('decision_key')==value.get('requested_decision_key')=='demote_holy_site_decision'
        and value.get('detail_actor_id')==value.get('current_actor_id')==played
        and value.get('parameter_holy_site_id')==value.get('selected_holy_site_id')==27
        and value.get('parameter_and_selection_match') is True,'Real selected Demote27 identity unavailable')
    require(value.get('native_detail_context_verified') is True and value.get('normal_requirements_legality_observed') is True
        and value.get('normal_requirements_can_confirm') is True and value.get('native_can_confirm') is True
        and value.get('bypass_requirements_observed') is True and type(value.get('bypass_requirements_raw')) is int
        and value['bypass_requirements_raw']==0,'Original ordinary Demote27 is not explicitly allowed')
    require(value.get('native_resource_quote_available') is True,'Fresh full10 quote required')
    quote=value.get('native_resource_quote',{});vec=quote.get('resource_vector_raw')
    require(quote.get('raw_scale')==100000 and type(vec) is list and len(vec)==10
        and all(type(x) is int and -(2**63)<=x<2**63 for x in vec)
        and quote.get('native_affordable') is True,'Actual full10/affordability unavailable')
    require(all(vec[i]==0 for i in range(10)if i!=2) and vec[2]>=0
        and quote.get('costs_raw')=={'gold':0,'prestige':0,'piety':vec[2],'treasury':0},'Minimal demote case only accepts its complete original piety-only quote')
    for key in ('native_requirements_description','native_cost_description'):
        require(value.get(key+'_available') is True and type(value.get(key)) is str and bool(value[key]),'Actual original terms text required: '+key)
    require(type(value.get('selected_item_token')) is int and 0<=value['selected_item_token']<=0xffffffff,'Actual selected item token required')
    return {'decision':'demote_holy_site_decision','site_id':27,'selected_item_token':value.get('selected_item_token'),
        'quote':quote,'requirements':value['native_requirements_description'],'cost_text':value['native_cost_description']}

def grade_change(before,after,faith):
    if set(before)!=set(after) or 27 not in before:return False
    expected=json.loads(json.dumps(before));expected={int(k):v for k,v in expected.items()}
    for v in expected.values():v['grades']={int(k):x for k,x in v['grades'].items()}
    if expected[27]['grades'].get(faith) is not True:return False
    expected[27]['grades'][faith]=False
    return expected==after

def pairs(before,after,ids):
    result=[]
    for target in ids:
        a=before.get(str(target));b=after.get(str(target));stable=bool(a and b)
        if stable:
            stable=all(a[k]==b[k]for k in ('character_id','rite_id','faith_id','effective_devotion_level','devotion_total_raw'))
            stable=stable and all(a['current_skill_points'][k]==b['current_skill_points'][k]for k in SKILLS if k!='diplomacy')
        result.append({'character_id':target,'independent_pair_observed':bool(a and b),'own_level_and_other_controls_stable':stable,
            'before':a,'after':b,'unattributed_diplomacy_delta':b['current_skill_points']['diplomacy']-a['current_skill_points']['diplomacy']if a and b else None,
            'definition_only_expected_delta_if_all_production_guards_hold':-a['effective_devotion_level']if a else None,
            'site_attribution_observed':False,'selected_site_contribution_raw':None,'cache_generation_time_known':False})
    return result

class Controlled:
    def __init__(self,context,client,binding,reader):
        self.context,self.client,self.binding,self.reader=context,client,binding,reader
        self.calls=1;self.sequence=0;self.rows=[];self.intent=None;self.attempted=False;self.unknown=False;self.confounded=False
        self.existing_intent=None
    def guard(self,n=1):
        require(self.calls+n<=MAX_CALLS,'Finite A1 call budget exhausted')
        # Shared execute_plan has a separate <=300s queue-publication deadline;
        # its timeout only bounds await_steps. Keep this real overhead outside
        # both our 120s normal Quit and 90s final-review reserve on each batch.
        self.client.guard(120+90+300+20*n+10)
    def review(self,name,request):
        self.client.guard(210)
        response=self.client.root_checkpoint('a1-'+name,{'machine_id':self.context['case_contract']['machine_id'],
            'run_id':self.context['run_id'],**request},reserve=210)
        require(response.get('run_id')==self.context['run_id'] and response.get('reviewer')==self.client.operator_reviewer
            and response.get('status')=='complete','Foreign/incomplete actual Root checkpoint')
        return response
    def scene(self,frame):
        now=self.reader(frame)
        require(all(now[k]==self.binding[k]for k in ('played_character_id','date_raw','game_pid','connection_generation','episode_run_id')),'Actual A1 scene identity/date changed')
        if frame.get('active_event') is not None or frame.get('pending_character_interaction') is not None:
            self.confounded=True
            response=self.review('interruption-'+str(self.sequence),{'frame':frame,'native_selection_only':True,
                'policy':'Known dedicated policy first; unknown event save actual native IDs/options then first displayed option; interaction original left semantics; ACK/window disappearance separate; offline registry analysis required',
                'controlled_comparison_invalidated':True,'actual_public_controls_must_be_reported':True})
            used=response.get('actual_public_controls_used');evidence=response.get('evidence')
            require(type(used) is int and 1<=used<=12 and self.calls+used+1<=MAX_CALLS and type(evidence) is list and evidence,'Original interruption controls/evidence required')
            for row in evidence:require(pin(row['path'])==row,'Interruption evidence changed')
            require(response.get('native_selection_only') is True and response.get('ack_and_disappearance_separate') is True
                and response.get('offline_analysis_input_written') is True,'Interruption must retain native/post/offline boundaries')
            self.calls+=used+1;latest=self.client.snapshot(require_event_free=False)
            require(latest.get('active_event') is None and latest.get('pending_character_interaction') is None,'Original interruption remains; no synthetic dismissal')
            actual=self.reader(latest);require(all(actual[k]==self.binding[k]for k in ('played_character_id','date_raw','game_pid','connection_generation','episode_run_id')),'Interruption crossed actual scene')
            raise ValueError('Real interruption resolved and preserved; controlled A1 is confounded, no further mutation')
    def snapshot(self):
        self.guard();self.calls+=1;value=self.client.snapshot(require_event_free=False);self.scene(value);return value
    def batch(self,steps):
        Q.validate({'steps':steps})
        readonly=Q.READONLY|{'ck3_get_capabilities','ck3_take_snapshot','ck3_query_ingame_ui_window_v1'}
        needs_before=any(step['tool'] not in readonly for step in steps)
        self.guard(len(steps)+int(needs_before))
        # The common host publishes actual after_snapshot for actions as well
        # as reads. Acquire our own fresh pre-plan frame; never invent row.before.
        before=self.snapshot() if needs_before else None
        self.guard(len(steps));self.sequence+=1;self.calls+=len(steps)
        name='a1-control-'+str(self.sequence).zfill(4)
        rows=self.client.execute_plan(steps,name,timeout=20*len(steps))
        require(type(rows) is list and len(rows)==len(steps),'Actual public result rows missing')
        for step,row in zip(steps,rows):
            record={'step':step,'row':row}
            if before is not None:record['independent_before_snapshot']=before
            self.rows.append(record)
            if 'before_snapshot' in row:
                require(type(row['before_snapshot']) is dict,'Independent public frame missing');self.scene(row['before_snapshot'])
            require(type(row.get('after_snapshot')) is dict,'Independent public frame missing');self.scene(row['after_snapshot'])
        return rows
    def call(self,tool,args=None):
        name='a1-step-'+str(self.sequence+1).zfill(4)
        row=self.batch([Q.step(name,tool,args)])[0]
        require(row.get('ok') is True and not row.get('error') and type(row.get('result')) is dict,'Original public call unavailable: '+tool)
        value=row['result']
        if tool in Q.READONLY:
            require(value.get('read_only') is True,'Native query lost read-only role')
            if 'played_character_id' in value:require(value['played_character_id']==self.binding['played_character_id'] and value.get('date_raw')==self.binding['date_raw'],'Native domain crossed played actor/date')
            if args and 'holy_site_id' in args:require(value.get('requested_holy_site_id')==args['holy_site_id'],'Native domain crossed selected site')
        return value
    def present(self,tool,args,query,qargs):
        name='a1-present-'+str(self.sequence+1).zfill(4)
        rows=self.batch([Q.step(name,tool,args),Q.step(name+'-read',query,qargs)])
        row=rows[-1];require(row.get('ok') is True and not row.get('error') and type(row.get('result')) is dict,'Original presentation has no independent read')
        return row['result']
    def actors(self,ids):
        return {str(i):actor(self.call(Q.ACTOR,{'character_id':i,'skill':'diplomacy'}),i,self.binding['played_character_id'],self.binding['date_raw'])for i in ids}
    def once(self,observation,review):
        require(not self.attempted and not self.unknown and not self.confounded,'Original action already consumed or comparison confounded')
        self.guard(8) # include explicit world-before read; later enqueues are guarded again
        require_root_visual_review(review,observation,'demote27_once_authorized')
        c=self.context['case_contract'];root=Path(c['intent_ledger_root']);root.mkdir(parents=True,exist_ok=True)
        require(not root.is_symlink(),'Intent ledger must not be a symlink')
        scope={'machine_id':c['machine_id'],'saved_sha256':SAVE['sha256'],'date_raw':self.binding['date_raw'],
            'played_character_id':self.binding['played_character_id'],'action':'demote','holy_site_id':27}
        claim=root/(digest(scope)+'.intent.json')
        if claim.exists():
            self.existing_intent=pin(claim);self.unknown=True
            raise ValueError('Retained consumed A1 intent blocks replay across run/PID/generation: '+str(claim))
        value={'machine_id':c['machine_id'],'run_id':self.context['run_id'],'observed_at_utc':datetime.now(timezone.utc).isoformat(),
            'scope':scope,'original_scene':self.binding,'native_observation_sha256':digest(observation),'Root_review':review,
            'automatic_retry':False,'business_outcome_observed':False,'protected_reason':'Consumed A1 intent; unknown never replayed across run/PID/generation',
            'review_after_utc':c['intent_review_after_utc']}
        # Commit our one case-specific intent before submitting any callback.
        # A failed/partial fsync leaves the exclusive claim and blocks replay.
        with claim.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
            stream.flush();os.fsync(stream.fileno())
        self.intent=pin(claim);self.attempted=True;self.unknown=True
        self.client.checkpoint('a1-demote-once-intent',{'intent':self.intent,**value})
        answer=self.call(Q.CONFIRM,{'action':'demote','holy_site_id':27})
        self.unknown=False
        return answer

def collect(case,result):
    case.call('ck3_get_capabilities')
    religion=case.call(Q.RELIGION);require(religion.get('available') is True and Q.ref(religion.get('rite_id')) and Q.ref(religion.get('faith_id')),'Actual player Rite/Faith unavailable')
    faith,rite_id=religion['faith_id'],religion['rite_id']
    site_raw=case.call(Q.SITES);projection=sites(site_raw,faith)
    require(projection[27]['grades'][faith] is True,'Selected Medina is not currently major')
    ui=case.present('ck3_open_holy_site_window_v1',{'holy_site_id':27},'ck3_query_ingame_ui_window_v1',{'window_kind':'holy_site'})
    require(ui.get('available') is True and ui.get('effective_visible') is True and ui.get('subject_id_available') is True and ui.get('current_subject_id')==27,'Original selected site window not independently visible')
    selected_relic=case.call(Q.RELIC,{'holy_site_id':27});selected_projection=relic(selected_relic,faith)
    played=case.binding['played_character_id'];first=case.actors([played]);require(first[str(played)]['faith_id']==faith and first[str(played)]['rite_id']==rite_id,'Actual player relation differs')
    ids=[played];candidates=[selected_projection['county']['county_holder_id']];tried={played}
    for site in projection:
        if len(ids)==2:break
        if site!=27 and len(candidates)<6:
            context=case.call(Q.RELIC,{'holy_site_id':site});county=context.get('county_context',{})
            if context.get('available') is True and county.get('available') is True:candidates.append(county.get('county_holder_id'))
        for target in list(dict.fromkeys(candidates)):
            if not Q.ref(target) or target in tried:continue
            tried.add(target)
            value=case.actors([target])[str(target)]
            if eligible_actor(value,faith):ids.append(target);break
    require(len(ids)==2 and ids[0]!=ids[1],'No two actual distinct same-Faith recipients; never fabricate a second person')
    baseline=case.actors(ids);repeat=case.actors(ids)
    require({k:actor_projection(v)for k,v in baseline.items()}=={k:actor_projection(v)for k,v in repeat.items()},'Baseline actor values/text changed during independent reads')
    result.update(religion_before=religion,faith_id=faith,rite_id=rite_id,actor_ids=ids,sites_before=site_raw,
        site_projection_before=projection,major_site_ids_before=major_ids(projection,faith),
        relic_before=selected_relic,relic_projection_before=selected_projection,actors_before=repeat)
    opened=case.present('ck3_open_holy_site_decision_v1',{'action':'demote','holy_site_id':27},Q.DETAIL,{'action':'demote','holy_site_id':27})
    frozen_terms=terms(opened,played);cooldown=case.call(Q.COOLDOWN,{'action':'demote'});before_wallet=case.snapshot()
    money=wallet(before_wallet);require(money['piety']>=frozen_terms['quote']['costs_raw']['piety'],'Actual piety wallet cannot fund observed quote')
    observation={'site_id':27,'action':'demote','scene':case.binding,'relation_before':projection,
        'selected_relic':selected_projection,'actors_before':repeat,'terms':opened,'cooldown':cooldown,'wallet':before_wallet}
    result.update(terms_before=opened,cooldown_before=cooldown,wallet_before=before_wallet,review_observation=observation)
    approval=case.review('original-demote27',{'native_observation':observation,'native_observation_sha256':digest(observation),
        'approval_key':'demote27_once_authorized','prepare_original_image':True,'scope':SCOPE,
        'note':'Directly review original PNG and exact native terms. Only one Demote27; current total is not a selected-site source.'})
    require_root_visual_review(approval,observation,'demote27_once_authorized');result['Root_precommit_review']=approval
    latest=case.call(Q.DETAIL,{'action':'demote','holy_site_id':27});require(terms(latest,played)==frozen_terms,'Actual native quote/selection/legality changed after review')
    fresh_sites=case.call(Q.SITES);fresh_relic=case.call(Q.RELIC,{'holy_site_id':27});fresh_actors=case.actors(ids);fresh_wallet=case.snapshot()
    require(sites(fresh_sites,faith)==projection and relic(fresh_relic,faith)==selected_projection,'Actual selected scene facts changed after review')
    require({k:actor_projection(v)for k,v in fresh_actors.items()}=={k:actor_projection(v)for k,v in repeat.items()}
        and wallet(fresh_wallet)==money,'Actor/wallet changed after review')
    result['last_precommit_snapshot']=fresh_wallet
    try:result['confirm_ack']=case.once(observation,approval)
    except Exception as error:result['confirm_error']=type(error).__name__+': '+str(error)
    if case.attempted:collect_post(case,result)

def collect_post(case,result):
    faith=result['faith_id'];ids=result['actor_ids']
    attempts=[]
    for _ in range(3):
        if case.client.remaining()<=540 or case.calls+6>MAX_CALLS:
            result['post_read_remaining_budget_limited']=True
            break
        try:
            after_sites=case.call(Q.SITES);after_relic=case.call(Q.RELIC,{'holy_site_id':27})
            after_actors=case.actors(ids);after_wallet=case.snapshot();after_religion=case.call(Q.RELIGION)
            p=sites(after_sites,faith);r=relic(after_relic,faith);ap=pairs(result['actors_before'],after_actors,ids)
            money_before=wallet(result['last_precommit_snapshot']);money_after=wallet(after_wallet)
            cost=terms(result['terms_before'],case.binding['played_character_id'])['quote']['costs_raw']['piety']
            paid=money_after=={**money_before,'piety':money_before['piety']-cost}
            grade=grade_change(result['site_projection_before'],p,faith)
            controls=bool(not case.confounded and r==result['relic_projection_before'] and len(ap)==2
                and all(x['own_level_and_other_controls_stable']for x in ap)
                and after_religion.get('rite_id')==result['rite_id'] and after_religion.get('faith_id')==faith)
            observed={'sites':after_sites,'relic':after_relic,'actors':after_actors,'religion':after_religion,
                'major_site_ids_after':major_ids(p,faith),
                'wallet':after_wallet,'pairs':ap,'only_selected_major_relation_changed':grade,'wallet_matches_original_quote':paid,
                'selected_relic_identity_and_actor_controls_stable':controls,'cache_refresh_observed':False}
            attempts.append(observed);result['post_observation']=observed
            # An unchanged cached skill is retained as observed, never forced to -L.
            if grade and paid and controls:break
        except Exception as error:attempts.append({'error':type(error).__name__+': '+str(error)})
    result['post_read_attempts']=attempts

def run_case(context,client):
    c=validate_contract(context)
    require(getattr(getattr(client,'selection',None),'normal_quit_automation',None) is None,
        'A1 requires the existing public manual GUI Quit lifecycle, not a product-selected automation helper')
    out=Path(context['output']);first=client.snapshot(require_event_free=False)
    write_once(out/'a1-first-native-frame.json',{'machine_id':c['machine_id'],'run_id':context['run_id'],'frame':first})
    reader,sources=shared_opening_binding(context);binding=reader(first)
    require(binding['played_character_id']==SAVE['player_id'] and binding['date_raw']==SAVE['date_raw'],'Fresh restore differs from explicit C2 expected identity')
    require(client.manifest.get('native',{}).get('dll',{}).get('sha256')==c['native_cohort']['dll_sha256'],'Actual selected DLL differs from bound new cohort')
    case=Controlled(context,client,binding,reader)
    result={'schema':'faith-e02-a1-controlled-result-v1','machine_id':c['machine_id'],'run_id':context['run_id'],'case':CASE,
        'binding':binding,'binding_sources':sources,'scope':SCOPE,'status':'PRECONDITION_OR_REVIEW_BLOCKED',
        'business_pass':False,'product_release_pass':False,'site_attribution_observed':False,'selected_site_contribution_raw':None}
    try:
        case.scene(first);collect(case,result)
    except Exception as error:result['failure']=type(error).__name__+': '+str(error)
    finally:
        if case.attempted and not result.get('post_read_attempts'):
            try:collect_post(case,result)
            except Exception as error:result['post_read_failure']=type(error).__name__+': '+str(error)
        post=result.get('post_observation',{})
        if case.attempted:result['status']='GRADE_AND_TWO_ACTOR_READBACK_OBSERVED_ATTRIBUTION_PENDING' if all(post.get(k) is True for k in ('only_selected_major_relation_changed','wallet_matches_original_quote','selected_relic_identity_and_actor_controls_stable')) else 'DEMOTE_ATTEMPTED_POST_PARTIAL_OR_UNKNOWN'
        result.update(world_confirm_attempts=int(case.attempted),consumed_intent=case.intent,transport_outcome_unknown=case.unknown,
            historical_consumed_intent_blocked=case.existing_intent,
            controlled_comparison_confounded=case.confounded,public_calls_used=case.calls,public_calls_cap=MAX_CALLS,
            submitted_rows=case.rows,automatic_retry=False,normal_close_pending=True,
            required_slots={'E2-A1':{'required':True,'closed':False,'ordinary_major_post_observed':post.get('only_selected_major_relation_changed',False),
                'two_actor_readback_observed':len(post.get('pairs',[]))==2,'source_attribution_observed':False,
                'selected_site_contribution_raw':None,'reason':'Totals/whole Faith breakdown and cache timing cannot independently attribute selected-site contribution; original source evidence still required'},
                'whole_film_required_count':24,'required_slots_waived':0})
        if client.remaining()>230:
            try:result['Root_result_review']=case.review('result-and-normal-quit',{'result':result,
                'native_observation':post,'native_observation_sha256':digest(post),'prepare_original_image':True,
                'note':'Review actual original character/grade/wallet pixels. A1 source attribution remains required-open. Public lifecycle must normal GUI Quit with autosave unchecked.'})
            except Exception as error:result['result_review_failure']=type(error).__name__+': '+str(error)
        write_once(out/'a1-controlled-result.json',result)
    return result

def verify_case(context):
    c=validate_contract(context);v=read(Path(context['output'])/'a1-controlled-result.json')
    require(v.get('machine_id')==c['machine_id'] and v.get('run_id')==context['run_id'] and v.get('case')==CASE,'Foreign A1 result')
    require(type(v.get('world_confirm_attempts')) is int and 0<=v['world_confirm_attempts']<=1 and v.get('public_calls_used',MAX_CALLS+1)<=MAX_CALLS,'A1 finite budget violated')
    require(v.get('site_attribution_observed') is False and v.get('selected_site_contribution_raw') is None
        and v['required_slots']['E2-A1']['closed'] is False and v['required_slots']['whole_film_required_count']==24,'A1 cannot infer source attribution or waive required slots')
    return {'status':v['status'],'required_slots':v['required_slots'],'research_holder_completed':True,
        'case_contract_qualified':False,'gui_contract_qualified':False,'business_pass':False,'product_release_pass':False,
        'automatic_retry':False,'normal_close_verified_by_existing_public_lifecycle':False}
