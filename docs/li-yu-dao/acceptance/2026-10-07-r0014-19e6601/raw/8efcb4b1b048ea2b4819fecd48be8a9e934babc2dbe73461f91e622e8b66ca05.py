"""Author/read one preserved R14 SDK checkpoint against actual clean004 producer. No game, provider or MCP calls.

Default is source-only request authoring. --read-checkpoint explicitly reads the
SDK-named actual save once; --convert additionally joins preserved G2/G3 JSON.
Every request/output is create-only. Unobserved leaves remain null.
"""
from pathlib import Path
from copy import deepcopy
from decimal import Decimal
import argparse, datetime, hashlib, importlib.util, json, sys, traceback
sys.dont_write_bytecode=True
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004')
ADAPTER=BASE/'r13-checkpoint-transition-v2-20261006-005'
PYTHON='C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
def need(condition, message):
    if not condition: raise ValueError(message)
def digest(data):return hashlib.sha256(data).hexdigest()
def reference(path):
    path=Path(path);data=path.read_bytes()
    return {'path':path.as_posix(),'bytes':len(data),'sha256':digest(data)}
def write_new(path,obj):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def load_json(path):
    data=Path(path).read_bytes()
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'duplicate JSON key '+key);result[key]=value
        return result
    return json.loads(data.decode('utf-8-sig'),object_pairs_hook=pairs)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
sys.path.insert(0,str(ADAPTER/'reader/dependencies'))
EXECUTING_READER=Path(__file__).parent/'reader/i3b_checkpoint_reader.py'
reader=module('actual_bound_i3b_reader',EXECUTING_READER)
converter=module('actual_metadata_checkpoint_transition_converter_v2',ADAPTER/'reader/sdk_checkpoint_transition_qualification_v2.py')

# An explicit source-only compatibility leaf. The input-copy shape run below
# supplies actual evidence for top-level Rite storage; both locations are kept.
original_raw_character=reader.raw_character
def actual_raw_character(cid,entries):
    row=original_raw_character(cid,entries)
    top=reader.one(entries,'rite');nested=reader.one(row['alive_data'],'rite')
    need(top is None or nested is None or top==nested,'actual top/alive Rite representations contradict')
    row['raw_top_rite']=top;row['raw_alive_rite']=nested
    if top is not None:row['rite_id']=reader.scalar_id(top,'actual top-level character Rite',allow_zero=True)
    return row
reader.raw_character=actual_raw_character
def exact_number(value):
    if value is None:return None
    if isinstance(value,list):
        need(len(value)==1 and value[0]['key']=='value','unsupported actual resource numeric structure')
        value=reader.one(value,'value',required=True)
    need(isinstance(value,str),'unsupported actual resource numeric shape')
    return str(Decimal(value))

def raw_scan(text,binding,original_baseline):
    """Actual save framing/AST helpers are unchanged existing reader functions."""
    text=text.replace('\r\n','\n')
    faiths=reader.graph(text,'faiths','main_rite');rites=reader.graph(text,'rites','faith')
    parents={rid:reader.scalar_id(row['faith'],'Rite parent',absent=True,allow_zero=True) for rid,row in rites.items()}
    actor_id=converter.full_actor(binding['played_character_id'])
    living={};count=0;section_count=0;excluded_explicit_dead=[];unclassified=[]
    protected_ids={int(k) for k in original_baseline['character_protections']}
    # Faith is taken from the actual played actor's saved Rite, never a hint.
    actor=None
    for cid,entries in reader.records(reader.section(text,'living','dead_unprunable'),'living character'):
        section_count+=1
        if not reader.saved_character_is_alive(cid,entries):
            excluded_explicit_dead.append({'character_id':cid,'AST_sha256':reader.ast_sha(entries),'dead_data':reader.one(entries,'dead_data')})
            continue
        count+=1
        row=reader.raw_character(cid,entries)
        if row['rite_id'] is None or row['rite_id'] not in parents or parents[row['rite_id']] is None:
            unclassified.append(cid)
        if cid==actor_id:actor=row
        # Keep compact membership identities for all world living records. Full
        # ASTs are retained only for current Faith members/protected characters.
        living[cid]={'rite_id':row['rite_id'],'faith_id':parents.get(row['rite_id'])}
        if cid in protected_ids:living[cid]['record']=row
    need(actor is not None,'actual played actor is not a living saved record')
    rite_id=actor['rite_id'];faith_id=parents.get(rite_id)
    need(faith_id is not None and faith_id in faiths,'actual saved actor Faith/Rite not classifiable')
    # Full selected Faith ASTs require a second numeric-record pass on the same
    # verified byte buffer, never a second file read or altered parser.
    selected_ids={cid for cid,row in living.items() if row['faith_id']==faith_id}|protected_ids
    selected={actor_id:actor}
    for cid,entries in reader.records(reader.section(text,'living','dead_unprunable'),'living character'):
        if cid in selected_ids: selected[cid]=reader.raw_character(cid,entries)
    faith_members=sorted(cid for cid,row in living.items() if row['faith_id']==faith_id)
    actual_rites=sorted(rid for rid,fid in parents.items() if fid==faith_id)
    humans=[reader.scalar_id(r['value'],'saved currently played character') for r in reader.exact_root_block(text,'currently_played_characters')]
    current_head=reader.native_link_id(faiths[faith_id]['heads']['religious_head_title'],'actual Faith head Title')
    held_by_protected={cid:[] for cid in protected_ids};titles={}
    political_ids={int(k) for k in original_baseline['political7']}
    for tid,entries in reader.title_database_records(text):
        holder=reader.native_link_id(reader.one(entries,'holder'),'saved Title holder')
        if holder in held_by_protected:held_by_protected[holder].append(tid)
        if tid in political_ids or tid==current_head:titles[tid]=reader.title_row(tid,entries)
    return {'text':text,'actor':actor,'faith_id':faith_id,'rite_id':rite_id,'faiths':faiths,'rites':rites,
            'parents':parents,'selected':selected,'living_count':count,'living_section_count':section_count,'excluded_explicit_dead':excluded_explicit_dead,'unclassified':unclassified,
            'faith_members':faith_members,'actual_rites':actual_rites,'humans':humans,
            'titles':titles,'current_head':current_head,'held_by_protected':held_by_protected}

def baseline_state(scan,identity,save_sha):
    actor=scan['actor'];variables=actor['variables'];fid=scan['faith_id']
    political=[deepcopy(row) for tid,row in scan['titles'].items() if tid!=scan['current_head']]
    state={'schema':'lyd.i3b.checkpoint-observations.v1','source_head':reader.HEAD,
           'mode':'future_actual','stage':'pre_proposal_baseline','identity':identity,'checkpoint_sha256':save_sha,
           'actual_pass':None,'actual_native_runtime_pass':None,'formal_mandate_credit':None,
           'round':{'serial':reader.number(variables,'lyd_i3b_serial',required=False),
                    'nonce':reader.number(variables,'lyd_i3b_nonce',required=False),
                    'phase':reader.number(variables,'lyd_i3b_phase',required=False),
                    'result_code':reader.number(variables,'lyd_i3b_result_code',required=False)},
           'actor':actor,'faith':scan['faiths'][fid],'rites':[scan['rites'][i] for i in scan['actual_rites']],
           'roster':{'whole_world_living_records_scanned':True,'living_records_scanned':scan['living_count'],'living_section_numeric_records_scanned':scan['living_section_count'],'excluded_explicit_dead_records':scan['excluded_explicit_dead'],
                     'faith_classification_complete':not scan['unclassified'],'unclassified_living_ids':scan['unclassified'],
                     'living_faith_ids':scan['faith_members'],'captured_member_ids':None,
                     'saved_current_human_ids':scan['humans'],
                     'saved_current_human_faith_ids':sorted(set(scan['humans'])&set(scan['faith_members'])),
                     'members':[scan['selected'][i] for i in scan['faith_members']]},
           'schools':None,'native_title':scan['titles'].get(scan['current_head']),
           'result_head_title_reference':variables.get('lyd_i3b_result_head_title'),
           'protected_titles':political,'checks':[], 'assessment':'INCOMPLETE_NATIVE_QUALIFICATION',
           'native_predicate_qualification':{'status':'UNKNOWN','reason':'baseline is before formal round; native G2 independently joins only complete current Faith observations'},
           'native_reference_qualification':{'status':'UNKNOWN','binding':None},
           'formal_event_context_qualification':{'status':'NOT_A_FORMAL_ROUND','actor':None,'serial':None,'nonce':None,'phase':None},
           'authority':'Observed baseline save via exact existing reader parser/AST helpers; strict formal-round reader has not executed.'}
    return state

def protection(scan,baseline,state):
    checks=[]
    def compare(name,actual,wanted):
        checks.append({'name':name,'matches':actual==wanted,'observed':actual,'expected':wanted})
    for tid,expected in baseline['political7'].items():
        actual=scan['titles'].get(int(tid))
        compare('political_'+tid+'_full_AST',actual['AST_sha256'] if actual else None,expected['AST_sha256'])
        compare('political_'+tid+'_holder',str(actual['holder']) if actual else None,expected['holder'])
    protected_characters={}
    for cid,expected in baseline['character_protections'].items():
        actual=scan['selected'].get(int(cid));need(actual is not None,'protected actual character missing '+cid)
        top={k:reader.one(actual['entries'],k) for k in expected['protected_top']}
        alive={k:reader.one(actual['alive_data'],k) for k in expected['protected_alive']}
        compare('character_'+cid+'_rite',str(actual['rite_id']),expected['rite'])
        for k,wanted in expected['protected_top'].items():compare('character_'+cid+'_top_'+k,top[k],wanted)
        for k,wanted in expected['protected_alive'].items():compare('character_'+cid+'_alive_'+k,alive[k],wanted)
        protected_characters[cid]={'entries':actual['entries'],'AST_sha256':actual['AST_sha256'],
                                   'protected_top':top,'protected_alive':alive,
                                   'actual_all_held_title_ids':sorted(scan['held_by_protected'][int(cid)])}
    post=state['stage'] in ('success_postcommit','partial_postcommit')
    expected_title=state.get('native_title');added=expected_title['title_id'] if post and expected_title else None
    actor=scan['actor'];landed=actor['landed_data']
    need(isinstance(landed,list),'actual actor landed_data absent')
    projected=[]
    for expected in baseline['actor_protected_landed']:
        value=deepcopy(reader.one(landed,expected['key']))
        if expected['key']=='domain' and added is not None and isinstance(value,list):
            value=[r for r in value if not(r['key'] is None and r['value']==str(added))]
        projected.append({'key':expected['key'],'value':value})
    compare('actor_complete_protected_landed_projection',projected,baseline['actor_protected_landed'])
    expected_held=sorted(int(i) for i in baseline['actor_domain_ids'])
    actual_held=sorted(scan['held_by_protected'][actor['character_id']])
    compare('actor_actual_all_held_title_set_except_actual_new_religious_T',
            [i for i in actual_held if i!=added],expected_held)
    graphs={}
    for kind in ('faiths','rites'):
        graphs[kind]={}
        for gid,expected in baseline['graphs'][kind].items():
            actual=scan[kind].get(int(gid));need(actual is not None,'protected graph absent '+kind+'/'+gid)
            graphs[kind][gid]=actual
            current=(kind=='faiths' and int(gid)==scan['faith_id']) or (kind=='rites' and int(gid) in scan['actual_rites'])
            if current:
                wanted=reader.replace_no_head(expected['tenet_doctrine_rows']) if state['stage']=='success_postcommit' else expected['tenet_doctrine_rows']
                compare(kind+'_'+gid+'_complete_tenet_status_projection',actual['tenet_doctrine_rows'],wanted)
            else:compare(kind+'_'+gid+'_complete_AST',actual['AST_sha256'],expected['AST_sha256'])
    variables=actor['variables']
    numeric_names=('lyd_i3b_serial','lyd_i3b_nonce','lyd_i3b_phase','lyd_i3b_active','lyd_i3b_authority_mode',
                   'lyd_i3b_result_serial','lyd_i3b_result_nonce','lyd_i3b_result_code','lyd_i3b_result_authority_mode')
    def currency(key,leaf):
        return exact_number(reader.one(reader.one(actor['alive_data'],key) or [],leaf))
    wallet={'gold':currency('gold','value'),'piety':currency('piety','currency'),'prestige':currency('prestige','currency')}
    xp=exact_number(reader.one(reader.one(actor['alive_data'],'lifestyle_xp') or [],'learning_lifestyle'))
    stress=exact_number(reader.one(actor['alive_data'],'stress'))
    for key,wanted in baseline['wallet'].items():compare('historical_0240_wallet_'+key,wallet[key],wanted)
    compare('learning_XP_unchanged',xp,baseline['XP']);compare('saved_stress_unchanged',stress,baseline['saved_stress'])
    for key,wanted in baseline['C2_history'].items():compare('C2_history_'+key,variables.get(key),wanted)
    compare('C2_nonce_serial',variables.get('lyd_c2_serial'),baseline['C2_nonce_serial'])
    compare('reset_count',variables.get('lyd_r4_reset_count'),baseline['reset_count'])
    for key,wanted in baseline['school_study_CD'].items():compare('school_study_CD_'+key,variables.get(key),wanted)
    for rid,expected in baseline['Rite_CD_locks'].items():
        observed={key:scan['rites'][int(rid)]['variables'].get(key) for key in expected}
        compare('Rite_'+rid+'_complete_existing_CD_locks',observed,expected)
    return {'schema':'lyd.actual-i3b-checkpoint-typed-protection.v1','identity':state['identity'],
            'stage':state['stage'],'checkpoint_sha256':state['checkpoint_sha256'],'actor':actor,
            'wallet':wallet,'learning_XP_saved':xp,'stress_saved':stress,'commit_fee_delta':None,
            'fee_delta_qualification':'Requires an independently bound B3/B4 or B5 same-date pair; historical baseline comparison is separately labeled.',
            'typed_round_fields':{k:variables.get(k) for k in variables if k.startswith('lyd_i3b_')},
            'round_numeric_fields':{k:reader.number(variables,k,required=False) for k in numeric_names},
            'C2_history':{k:variables.get(k) for k in baseline['C2_history']},
            'C2_serial':variables.get('lyd_c2_serial'),'reset':variables.get('lyd_r4_reset_count'),
            'school_study_CD':{k:variables.get(k) for k in baseline['school_study_CD']},
            'protected_characters':protected_characters,'protected_graphs':graphs,
            'protected_political_titles':{str(tid):scan['titles'].get(tid) for tid in sorted(int(k) for k in baseline['political7'])},
            'actor_actual_all_held_title_ids':actual_held,'actual_added_religious_title':added,
            'checks':checks,'protection_checks_match':all(r['matches'] for r in checks),
            'actual_pass':None,'formal_mandate_credit':None,'saved_native_Title_field_paths':None}

def run(request_path,read_save,do_convert):
    config=load_json(request_path);out=Path(config['output'])
    need(not out.exists(),'new output directory required');out.mkdir(parents=True,exist_ok=False)
    (out/'INPUT.exact.json').write_bytes(Path(request_path).read_bytes())
    result={'schema':'lyd.r14.actual-checkpoint-request-author.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'status':'SOURCE_ONLY_PENDING_ACTUAL_CHECKPOINT','game_calls':0,'save_body_reads':0,
            'actual_pass':None,'formal_mandate_credit':None,'source_refs':{},'outputs':[]}
    try:
        refs={name:reference(config[name]) for name in ('profile','source_export_report','compiled_result','metadata_result','original_baseline','reader_request_template','windows')}
        result['source_refs']=refs
        result['executing_author']=reference(Path(__file__))
        result['reader_source_compatibility_projection']={'original_reader':reference(BASE/'r13-sdk-checkpoint-converter-actual-metadata-20261006-001/reader/i3b_checkpoint_reader.py'),'executing_reader':reference(EXECUTING_READER),'leaf':'raw_character.rite_id from actual top-level character.rite; preserve actual alive_data.rite separately','parser_changed':False,'formal_contract_head':reader.HEAD,'actual_acceptance_credit':None}
        profile=load_json(config['profile']);export=load_json(config['source_export_report'])
        compiled=load_json(config['compiled_result']);metadata=load_json(config['metadata_result'])
        original=load_json(config['original_baseline']);template=load_json(config['reader_request_template'])
        windows=load_json(config['windows'])
        need(config['schema']=='lyd.r14.actual-checkpoint-author-request.v1','actual R14 author request schema required')
        need(export['source']['head']==compiled['source_revision']==metadata['head']==windows['source_head'],'actual clean source heads differ')
        gate_path=Path(__file__).parent/'qualification/r14_clean_native_gate.py'
        need(reference(gate_path)['sha256']=='b80db2379f6870bf23395b3c151c395c891b9778f6caea811b02dc9cb1247f51','frozen actual R14 native gate changed')
        sys.path.insert(0,str(gate_path.parent))
        gate=module('actual_r14_clean004_native_gate',gate_path)
        source_inventory_ref=export['source_inventory']
        source_inventory=gate.jread(gate.read_ref(source_inventory_ref))
        qualification=gate.verify_native(refs['compiled_result'],'CLEAN_HEAD_BUILD',refs['source_export_report'],source_inventory,export['source']['head'])
        write_new(out/'NATIVE-CLEAN-QUALIFICATION.actual.json',qualification)
        result['native_clean_gate_source']=reference(gate_path)
        result['native_clean_gate_contract']={'actual_schema':compiled['schema'],'actual_source_binding':compiled['source_binding'],'actual_flags':compiled['actual_flags'],'exact_11_flags':compiled['exact_11_flags'],'six_products':compiled['targets'],'four_actual_focused_tests':compiled['actual_focused_tests'],'new_runtime_library':compiled['new_runtime_library'],'original_outer_exit_code':compiled['original_outer_exit_code'],'runtime_acceptance':compiled['runtime_acceptance']}
        need(profile['dll']['sha256']==qualification['actual_products']['xar_ck3_bridge']['sha256'],'profile DLL differs from actual compiled DLL')
        profile_dll=reference(Path(profile['dll']['path']))
        need(profile_dll['sha256']==profile['dll']['sha256'] and profile_dll['bytes']==qualification['actual_products']['xar_ck3_bridge']['bytes'],'actual profile DLL bytes differ from qualified compiled DLL')
        need(metadata['status']=='ACTUAL_OFFICIAL_CLIENT_METADATA_AND_FRESH_CODE_INVENTORY' and metadata['compiled_verification']==refs['compiled_result'] and metadata['actual_export_report']==refs['source_export_report'],'actual R14 metadata producer source/native references differ')
        metadata_artifact=config.get('sdk_metadata_artifact')
        metadata_variant=config.get('sdk_metadata_variant')
        need(metadata_variant in ('challenger24','private23'),'explicit actual metadata factory variant required')
        expected_metadata=metadata['metadata'] if metadata_variant=='challenger24' else metadata['readonly_metadata']
        expected_count=24 if metadata_variant=='challenger24' else 23
        need(metadata_artifact==expected_metadata and (metadata['tool_count'] if metadata_variant=='challenger24' else metadata['readonly_tool_count'])==expected_count,'actual metadata artifact/variant/count differ from official factory RESULT')
        result['actual_metadata_factory']={'variant':metadata_variant,'artifact':metadata_artifact,'tool_count':expected_count,'independent_actual_RESULT':refs['metadata_result']}
        codec_artifact=config.get('sdk_codec_artifact')
        need(type(codec_artifact)is dict and Path(codec_artifact['path']).resolve()==(Path(export['source_root'])/'ck3_autonomous_player/src/xar_autoplayer/bridge/confucian_readonly_private_v1.py').resolve(),'actual codec must be in exact clean source export')
        result['actual_codec_lineage']=converter.lineage.verify_codec_artifact(codec_artifact,codec_artifact['sha256'])
        actual_tool_rows=converter.load_descriptor(metadata_artifact)
        result['actual_metadata_lineage']=converter.lineage.verify_metadata_artifact(actual_tool_rows,metadata_artifact,metadata_artifact['sha256'])
        result['compiler_Defender_facts']=compiled.get('Defender')
        result['source_export_archive_descriptor']=export['source_archive']
        result['open_kaishek_preflight']={'status':'not-applicable','reason':'This helper reads a preserved native CK3 save with already established bounded parser and joins compact SDK JSON. It does not execute mod triggers/effects or finite-runtime gameplay semantics.'}
        cp_path=config.get('checkpoint_receipt')
        if cp_path is None:
            pending=deepcopy(template);pending['output']=str(out/'reader-state-pending')
            write_new(out/'CHECKPOINT-REQUEST.pending.json',pending)
            provenance=load_json(ADAPTER/'UNBOUND-PROVENANCE.v2.template.json')
            write_new(out/'PROVENANCE.pending.json',provenance)
            return result
        cp=load_json(cp_path);result['source_refs']['checkpoint_receipt']=reference(cp_path)
        need(cp['schema']=='ck3.native-profile-receipt.v1' and cp['profile_sha256']==refs['profile']['sha256'],'actual profile/SDK checkpoint differs')
        prior_binding=converter.frame_binding(cp['snapshot_before'])
        basic_provenance={'session_id':cp['session_id'],'profile_sha256':refs['profile']['sha256'],'pipe_name':cp['pipe_name'],'game_pid':prior_binding['game_pid'],'connection_generation':prior_binding['connection_generation']}
        binding,checkpoint_transition=converter.transition.bind_checkpoint_transition(cp,basic_provenance)
        write_new(out/'CHECKPOINT-TRANSITION.actual.json',checkpoint_transition)
        result['checkpoint_transition_contract']='lyd.sdk-checkpoint-transition.v2'
        result['before_frame_binding']=prior_binding
        result['after_frame_binding']=binding
        need(cp['status']=='native_gameplay_postcondition_verified','actual checkpoint SDK postcondition missing')
        desc=cp['result']['checkpoint'];need(desc['status']=='saved' and desc['date_raw']==binding['date_raw'],'saved checkpoint descriptor mismatch')
        provenance=load_json(ADAPTER/'UNBOUND-PROVENANCE.v2.template.json')
        business=json.loads((ADAPTER/'reader/dependencies/frozen_business_contract.json').read_bytes())['files']
        business_matches={rel:reference(Path(export['source_root'])/'mod_li_yu_dao'/rel)['sha256']==wanted for rel,wanted in business.items()}
        need(all(business_matches.values()),'actual clean export business source bytes differ')
        metadata_artifact=config.get('sdk_metadata_artifact')
        need(type(metadata_artifact) is dict,'actual SDK metadata descriptor required')
        provenance['sdk_metadata_artifact']=metadata_artifact
        provenance['sdk_metadata_sha256']=metadata_artifact['sha256']
        provenance['sdk_codec_artifact']=codec_artifact
        provenance.update(source_head=export['source']['head'],source_export_sha256=export['source_archive']['sha256'],
                          DLL_sha256=profile['dll']['sha256'],session_id=cp['session_id'],profile_sha256=refs['profile']['sha256'],
                          pipe_name=cp['pipe_name'],game_pid=binding['game_pid'],connection_generation=binding['connection_generation'],
                          sdk_codec_sha256=codec_artifact['sha256'],
                          current_business_files=business)
        receipt_objects={}
        for operation,key,nested in (('assembly_predicates','G2_receipt','confucian_assembly_predicates'),('religious_title','G3_receipt','confucian_religious_title')):
            if config.get(key) is not None:
                receipt=load_json(config[key]);converter.outer_identity(receipt,provenance)
                public=converter.sdk.normalize_public_query(receipt['result'],binding,operation)
                provenance['capture_epochs'][operation]=public['native_result'][nested]['capture_epoch']
                receipt_objects[key]=receipt;result['source_refs'][key]=reference(config[key])
        write_new(out/'PROVENANCE.actual-or-pending.json',provenance)
        result['frame_binding']=binding;result['business_source_files_match']=business_matches
        if not read_save:
            result['status']='ACTUAL_COMPACT_FRAME_BOUND_SAVED_ROUND_FIELDS_PENDING_BODY_READ';return result
        preserved=config.get('preserved_checkpoint')
        need(type(preserved) is dict and set(preserved)=={'path','bytes','sha256'},'content-addressed preserved checkpoint descriptor required')
        need(preserved['bytes']==desc['size'] and preserved['sha256']==desc['sha256'],'preserved checkpoint differs from original SDK descriptor')
        save_path=Path(preserved['path']);data=save_path.read_bytes();result['save_body_reads']=1
        result['preserved_checkpoint_descriptor']=preserved
        result['original_sdk_checkpoint_descriptor']=desc
        need(len(data)==desc['size'] and digest(data)==desc['sha256'],'actual checkpoint body size/SHA differs from SDK')
        need(not data.startswith(b'PK'),'compressed actual save unsupported by existing reader')
        scan=raw_scan(data.decode('utf-8-sig'),binding,original)
        identity={'actor_id':converter.full_actor(binding['played_character_id']),'faith_id':scan['faith_id'],'main_rite_id':scan['rite_id'],
                  'pid':binding['game_pid'],'session_id':cp['session_id'],'revision':binding['native_revision'],'checkpoint_id':desc['path']}
        window=config['window'];req=deepcopy(template)
        req.update(mode='future_actual',identity=identity,save={'path':str(save_path),'bytes':desc['size'],'sha256':desc['sha256']},
                   native_predicates=None,native_reference_binding=None,native_title_binding=None,output=str(out/'strict-reader-state'))
        if window=='baseline':
            state=baseline_state(scan,identity,desc['sha256'])
            result['strict_formal_reader_executed']=False
        else:
            selected=[w for w in windows['windows'] if w['label']==window];need(len(selected)==1,'unknown actual checkpoint window')
            stage=selected[0]['reader_stage'];post=window in ('B4-factory-result','B5-final-protection')
            variables=scan['actor']['variables']
            code=reader.number(variables,'lyd_i3b_result_code',required=post) if post else None
            if post:
                need(code in (1,2,3,4,5,6,7),'actual result code missing/unknown');stage='success_postcommit' if code==1 else 'partial_postcommit'
            req['stage']=stage
            req['expected']={'serial':reader.number(variables,'lyd_i3b_result_serial' if post else 'lyd_i3b_serial'),
                             'nonce':reader.number(variables,'lyd_i3b_result_nonce' if post else 'lyd_i3b_nonce'),
                             'phase':2 if post else reader.number(variables,'lyd_i3b_phase')}
            write_new(out/'CHECKPOINT-REQUEST.actual.json',req)
            # Uses the exact CLI reader's implementation on the verified buffer.
            state=reader.observe_text(scan['text'],req,desc['sha256'])
            result['strict_formal_reader_executed']=True
            result['reader_reproduction_argv']=[PYTHON,'-B','-X','utf8',str(EXECUTING_READER),'--request',str(out/'CHECKPOINT-REQUEST.actual.json')]
        write_new(out/'STATE.json',state)
        write_new(out/'TYPED-PROTECTION.json',protection(scan,original,state))
        artifacts={'provenance':reference(out/'PROVENANCE.actual-or-pending.json'),'checkpoint_receipt':reference(cp_path),
                   'saved_state':reference(out/'STATE.json'),'G2_receipt':reference(config['G2_receipt']) if config.get('G2_receipt') else {'path':None,'bytes':None,'sha256':None},
                   'G3_receipt':reference(config['G3_receipt']) if config.get('G3_receipt') else {'path':None,'bytes':None,'sha256':None}}
        conversion={'schema':'lyd.sdk-checkpoint-conversion-request.v2','artifacts':artifacts,'immutable_business_files':business,'output':str(out/'native-qualification')}
        write_new(out/'CONVERSION-REQUEST.actual-or-pending.json',conversion)
        result['status']='ACTUAL_SAVED_TYPED_OBSERVATIONS_NATIVE_JOIN_PENDING'
        if do_convert:
            need(len(receipt_objects)==2,'actual G2/G3 receipts both required for conversion')
            qualified=converter.run_request(conversion);target=out/'native-qualification';target.mkdir(exist_ok=False)
            write_new(target/'QUALIFIED-NATIVE.json',qualified)
            result['G2_status']=qualified['G2_status'];result['G3_status']=qualified['qualified_native_head']['status']
            result['status']='ACTUAL_COMPACT_NATIVE_SAVED_OBSERVATIONS_JOINED'
            if window!='baseline' and qualified['native_predicates'] is not None:
                req['native_predicates']=qualified['native_predicates'];req['output']=str(out/'native-reader-state')
                write_new(out/'CHECKPOINT-REQUEST.native-qualified.json',req)
                joined=reader.observe_text(scan['text'],req,desc['sha256'])
                write_new(out/'STATE.native-qualified.json',joined)
                result['native_reader_assessment']=joined['assessment']
        return result
    except Exception as error:
        result['status']='RED_PRESERVED';result['error_type']=type(error).__name__;result['error']=str(error)
        (out/'stderr.traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        result['outputs']=[reference(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='RESULT.json']
        write_new(out/'RESULT.json',result)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True,type=Path)
    parser.add_argument('--read-checkpoint',action='store_true')
    parser.add_argument('--convert',action='store_true')
    args=parser.parse_args();need(not args.convert or args.read_checkpoint,'conversion requires actual saved STATE readback')
    result=run(args.request,args.read_checkpoint,args.convert)
    print(json.dumps({'status':result['status'],'save_body_reads':result['save_body_reads'],
                      'game_calls':0,'actual_pass':None,'output':load_json(args.request)['output']},ensure_ascii=False))
if __name__=='__main__':main()
