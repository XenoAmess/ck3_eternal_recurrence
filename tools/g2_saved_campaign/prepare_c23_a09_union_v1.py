"""A09 exact closed-pair cold projection; Root-only adopter."""
import ast,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(OWN))
import prepare_c23_a08_union_v1 as previous
prior=previous.prior
MACHINE,O,T0=previous.MACHINE,previous.O,previous.T0
U8,U9=previous.U8,previous.U8.with_name('runtime-a09')
T5,HELPER=U9,previous.HELPER
require,exact=previous.require,previous.exact
PREVIOUS_PIN=(24462,'4f1a15c11cd6bea3e76e9ff42ab87719e0227861652275db9e02c2b3231e695d')
INDEX=O/'A08-SOURCE-CLOCK-FAILURE-INDEX01.json'
INDEX_PIN=(5914,'43b28b31461e601ee1982667c92a00f2d0e0b3cfb02027e2aa9490c1e1ba0abf')
REVIEW_PIN=(7092,'0916e20ead84c1f81b6ea738cb91b6e9a333d5c2e076c568a74e26248adeb9e1')
PRE_PIN=(5188,'c15941b0c8832bfb2263ee0e66952b35329aa2675339820150435bc1ff0cdf48')
DRIVER_PIN=(38421979,'a56291189c65c558f1c46d5959dab198dd553774d95293c85b40cb20c776ee76')
UNION_PIN,ADOPTER_PIN=previous.UNION_PIN,previous.ADOPTER_PIN

def function(module,name):
    text=exact(module.__file__,PREVIOUS_PIN).decode()
    return ast.get_source_segment(text,next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name))

def expanded(index):
    require(index['roots']=={'U8':str(U8),'O':str(O)},'evidence roots')
    return {r['relative']:{'path':str(Path(index['roots'][r['root']])/r['relative']),'bytes':r['bytes'],'sha256':r['sha256']} for r in index['files']}

def actual_graph():
    text=function(previous,'actual_graph')
    a=text.index("    index = json.loads(exact(INDEX, INDEX_PIN))")
    text=text[:a]+"    return values, quote, rows, observations\n"
    scope={**vars(previous),'previous':previous,'U7':U8,'PREVIOUS_PIN':PREVIOUS_PIN,
        'PREPARED':O/'A08-PREPARED01.json','PREPARED_PIN':(32718,'06c234ce1ee6aaf9a1001b2d20a721ed1963e6bba07b113150738321156a5230'),
        'NEXT_PIN':(67,'c7823eef307c7511ba239888e2ecf60e8f1e56922496fdf7396ac479304cd1b5')}
    exec(text,scope);values,quote,rows,observed=scope['actual_graph']()
    refs=expanded(json.loads(exact(INDEX,INDEX_PIN)));extras=[]
    for rel,key in [('ROOT-A08-CLASSIFIER-DEPENDENCIES-RESTORED01.json','actual_links'),('ROOT-A08-READONLY-RECOVERY-CLOSURE01.json','same_volume_hardlinks')]:
        doc=prior.checked(refs[rel],16384)
        for item in doc[key]:
            row=item['target'] if 'target' in item else prior.ref(U8/item['name']);p=Path(row['path']).resolve()
            require(p.parent==U8 and prior.ref(p)==row and row['sha256']==item.get('sha256',row['sha256'])
                and str(p.stat().st_ino)==str(item['same_FileID']) and p not in values,'A09 exact contract')
            values[p]=prior.raw(p,524288);rows[p]=row;extras.append(row)
    require(len(extras)==len({r['path'] for r in extras})==16,'A09 exact contract')
    return values,quote,rows,observed,extras

def bridge_source():
    return """def validate_actual_a08_index_v1(ref,checked):
    require((ref.get('bytes'),ref.get('sha256'))==INDEX_PIN,'actual closed A08 index')
    x=checked(ref,16384)
    require(x['machine_id']==MACHINE and x['schema']=='xar.A08-source-clock-failure-index/v1'
        and (x['completed_cycles'],x['date_raw'],x['saved_cycles'],x['saved_date_raw'],x['actual_next_sequence'])==(4760,53274648,4753,53274624,10502)
        and x['pending_cycle']=={'global_turn':4761,'auto_sequence':10501,'stage':'auto_unsettled'}
        and x['closure']=={'Game_exit':1,'forced_owned_cleanup':True,'sdk_queue_exit':1,'sdk_application_exit':0,'recording_worker_exit':0,'publisher_exit':0,'all_Task_Job_active':0},'A09 exact contract')
    rows={}
    for z in x['files']:
        base=Path(x['roots'][z['root']]);p=(base/z['relative']).resolve()
        require(p.is_relative_to(base.resolve()) and z['relative'] not in rows,'closed evidence scope')
        rows[z['relative']]=checked({'path':str(p),'bytes':z['bytes'],'sha256':z['sha256']},65536)
    q=rows['ROOT-P37C23-OWNER-CLOSED.json'];g=rows['ROOT-ACTUAL-GAME-EXIT-C23.json']
    require(q['machine_id']==g['machine_id']==MACHINE and q['normal'] is False and q['launcher_exit_code']==1
        and {(p['role'],p['pid'],p['creation_filetime'],p['exit_code']) for p in q['processes']}=={('sdk_queue',25252,134369540603293690,1),('sdk_application',265520,134369540626721526,0)}
        and all(p['kernel_exit_observed'] is True and p['wait_result']==0 and p['observation_error'] is None for p in q['processes'])
        and (g['pid'],g['creation_filetime'],g['exit_code'])==(126468,134369537928979603,1)
        and g['kernel_signaled'] is True and g['forced_owned_job_cleanup'] is True,'A09 exact contract')
    a=rows['p37-responses/10501-1-result.json']
    require(a['request']['sequence']==10501 and a['request']['tool']=='ck3_auto_turn' and a['request']['arguments']=={}
        and a['result']['is_error'] is True and a['result']['result_type']=='complete'
        and 'exact-day native clock did not stop the map' in a['result']['content'][0]['text']
        and rows['NEXT-SEQUENCE-P37.json']['next_sequence']==10502,'unknown10501 never replayed')
    for name,v in rows.items():
        if name.startswith('tasks/') and name.endswith('/CLOSED.json'):require(v['job_active_after_stage']==0,'actual old Task Job zero')
    return x

def validate_post_sem_driver(pre,close,checked,verify_current_stat=True):
    ref=pre['materialized_driver_review']
    require((ref['bytes'],ref['sha256'])==REVIEW_PIN,'actual materialized A09 review')
    r=checked(ref,32768)
    require((pre['final_driver_close']['bytes'],pre['final_driver_close']['sha256'])==(3972,'0128e254c37fda68c9a79508d4878d670bded05a78a83eb6d738b1694fbb3bf2'),'A09 exact contract')
    x=validate_actual_a08_index_v1(r['actual_A08_index'],checked)
    require(r['machine_id']==MACHINE and r['driver_state']==pre['driver_state']
        and (r['driver_state']['bytes'],r['driver_state']['sha256'])==DRIVER_PIN
        and r['checkpoint']==pre['checkpoint']==x['saved_checkpoint']==close['checkpoint']
        and r['canonical_validation']==pre['validation'] and [z['ref'] for z in r['sidecars']]==pre['sidecars']
        and r['persisted_pair_history_rows']==5277 and r['in_memory_history_reconstructed'] is False
        and r['SDK_normal'] is False and r['Game_normal'] is False,'A09 exact contract')
    receipt=checked(r['materialization_receipt'],16384);quote=checked(r['materialization_quote'],16384)
    require(receipt['machine_id']==quote['machine_id']==MACHINE and receipt['actual_materialization']['status']=='materialized_v2'
        and receipt['actual_materialization']['history_rows']==quote['persisted_pair_history_rows']==5277
        and receipt['actual_readback']['sha256']==pre['driver_state']['sha256']
        and receipt['actual_readback']['bytes']==pre['driver_state']['bytes']
        and receipt['source_pair_retained'] is True and receipt['in_memory_history_reconstructed'] is False
        and quote['in_memory_history_reconstructed'] is False,'A09 exact contract')
    if verify_current_stat:
        for z in quote['closed_pair']:
            s=(Path(r['closed_pair_archive'])/Path(z['path']).name).stat()
            require((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==tuple(z['identity'][:4]),'retained original pair identity')
        s=Path(pre['driver_state']['path']).stat();d=r['driver_stat']
        require((s.st_size,s.st_mtime_ns,str(s.st_ino))==(d['size'],d['mtime_ns'],str(d['FileID'])),'A09 exact contract')
    for row in pre['sidecars']:
        value=checked(row,65536);require(value.get('pending') is None,'actual pending sidecar')
    return True

def historical_saved_basis_view(admission):
    require(admission['next_sequence']==10502,'actual A09 NEXT10502')
    pre=checked(admission['cold_prelaunch'],16384);close=checked(pre['final_driver_close'],16384)
    validate_post_sem_driver(pre,close,checked,verify_current_stat=False)
    return {**admission,'next_sequence':10481}

""".replace('INDEX_PIN',repr(INDEX_PIN)).replace('REVIEW_PIN',repr(REVIEW_PIN)).replace('DRIVER_PIN',repr(DRIVER_PIN))

def guard_source():
    return """
def _validate_a09_attempt(args,config):
    value=_validate_a08_attempt(args,config)
    from root_checkpoint_bootstrap_c23 import validate_actual_a08_index_v1
    index=validate_actual_a08_index_v1(value['prior_failure_a08'],_a03_checked)
    require(read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10502,'new A09 consumes actual NEXT10502')
    old=_a03_checked({'path':str(Path(index['roots']['U8'])/'ROOT-FRESH-SUPERVISOR-CLOSED-C23-A08.json'),'bytes':3107,'sha256':'05c7c6dc75dd476a052af3dde7c9f4499cc06080cf92ca4dcb2d417775c3cbea'})
    require(args.attempt_nonce not in (old['attempt_nonce'],old['task_nonce']) and args.task_nonce not in (old['attempt_nonce'],old['task_nonce']),'independent A09 nonces')
    freeze=read(N/'ROOT-FINAL-SDK-FREEZE-P37C23-A09.json',524288);policy=_a03_checked(freeze['canonical_preload_policy'],32768)
    for row in policy['runtime_import_source_pins']:
        p=Path(row['path']);raw=p.read_bytes()
        require(p.parent==N and len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'A09 exact contract')
    return value

""".encode()

def build_sources():
    values,quote,rows,mutable,extras=actual_graph()
    names=[Path(r['path']).relative_to(previous.U7).as_posix() for r in quote['sources']['actual_source_rows']]
    require(len(names)==89 and len(set(names))==89,'actual89 previous source graph')
    source={name:values[(U8/name).resolve()].replace(b'C23-A08',b'C23-A09') for name in names}
    for row in extras:source[Path(row['path']).name]=values[Path(row['path']).resolve()]
    s=source['root_native30_supervisor_c23.py']
    for a,b,n in (("args.attempt=='a08'","args.attempt=='a09'",1),("value.get('attempt_id')=='a08'","value.get('attempt_id')=='a09'",1),
        ('choices=("a08",)','choices=("a09",)',1),('"attempt_id":"a08"','"attempt_id":"a09"',2),
        ('_validate_a08_attempt(args, config)','_validate_a09_attempt(args, config)',1),
        ("and read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10482","",1)):
        s=prior.swap(s,a,b,n)
    source['root_native30_supervisor_c23.py']=prior.swap(s,'def main(args):',guard_source().decode()+'def main(args):',1)
    b=source['root_checkpoint_bootstrap_c23.py'];text=b.decode();a=text.index('def validate_post_sem_driver(');end=text.index('def verify_cold_profile(spec):',a)
    source['root_checkpoint_bootstrap_c23.py']=(text[:a]+bridge_source()+text[end:]).encode()
    b=source['root_p37c23_cold_resume.py']
    b=prior.swap(b,"and close['sidecars'] == pre['sidecars']","",1)
    source['root_p37c23_cold_resume.py']=b
    b=source['root_checkpoint_bootstrap_c23.py'];b=prior.swap(b,"and close['sidecars'] == pre['sidecars']","",1);source['root_checkpoint_bootstrap_c23.py']=b
    name='launch_sdk_p37c23_owner.py'
    b=source[name]
    b=prior.swap(b,"'old_actual_exit_codes':","'historical_saved_basis_exit_codes':",1)
    b=prior.swap(b,"'normal_old_sdk_claimed':closed['normal'],","'historical_saved_basis_normal':closed['normal'],'actual_previous_A08_exit_codes':{'sdk_queue':1,'sdk_application':0},'actual_previous_A08_normal':False,",1)
    source[name]=b
    require((len(source[HELPER]),prior.sha(source[HELPER]))==(17637,'bae312f0fb07d370252ecc5714666fe1790a4db33bca32599e0e9bcb56d64a8e'),'A09 exact contract')
    for name,data in source.items():
        if name.endswith('.py'):compile(data,name,'exec')
    return source,{'schema':'xar.A09-source/v1','machine_id':MACHINE,'feeder':{},
        'actual_source_rows':[rows[(U8/name).resolve()] for name in source],'supplemental_import_rows':extras,
        'mutable_OBS_config_observations':mutable,'new_day_credit':0}

def state_guard(plan):
    pre=prior.checked(plan['cold_prelaunch_ref'],16384);review=prior.checked(plan['driver_review_ref'],32768)
    require((plan['cold_prelaunch_ref']['bytes'],plan['cold_prelaunch_ref']['sha256'])==PRE_PIN and
        (plan['driver_review_ref']['bytes'],plan['driver_review_ref']['sha256'])==REVIEW_PIN and pre['materialized_driver_review']==plan['driver_review_ref'],'A09 exact contract')
    scope={'MACHINE':MACHINE,'Path':Path,'require':require,'json':json,'checked':prior.checked};exec(bridge_source(),scope)
    scope['validate_post_sem_driver'](pre,prior.checked(pre['final_driver_close'],16384),prior.checked)
    save=Path(pre['checkpoint']['path']).stat()
    require((save.st_size,save.st_mtime_ns,save.st_ino)==(116203629,1792449304215108900,281474988852756),'original SAVE stat')
    return {'machine_id':MACHINE,'cold_prelaunch':plan['cold_prelaunch_ref'],'driver_review':plan['driver_review_ref'],'Driver_prefix_bytes_read':0,
        'large_input_hash_bytes_read':0,'persisted_pair_history_rows':5277,'in_memory_history_reconstructed':False}

def campaign_score_guard(*,alias_required=False):
    scope={**vars(prior),'MACHINE':MACHINE,'_a03_checked':prior.checked}
    exec(previous.score_source(),scope)
    return scope['_a08_campaign_score'](U9,alias_required)

def compose(plan,*,display_values,display_review,companion_values):
    text=exact(prior.__file__,UNION_PIN).decode();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='compose')
    source=ast.get_source_segment(text,node).replace('C23-A05','C23-A09').replace('C23-A04','C23-A08').replace("'a05'","'a09'").replace('spec-supervisor-a05','spec-supervisor-a09')
    source=source.replace('2026-10-20T06:30:00+00:00','2026-10-20T10:30:00+00:00')
    seam="prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'))"
    source=prior.swap(source.encode(),seam,seam[:-1]+',prior_failure_a08=ref(INDEX))',1).decode()
    source=prior.swap(source.encode(),"T5/name:raw(T4/name)","T5/name:(cold_prelaunch_bytes if name=='ROOT-C23-COLD-PRELAUNCH.json' else raw(T4/name))",1).decode()
    seam="policy_ref=put('ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json',policy)"
    add="policy['runtime_import_source_pins']=[original.target_ref(T5/Path(r['path']).name,source[Path(r['path']).name]) for r in source_review['supplemental_import_rows']]\n    "
    source=prior.swap(source.encode(),seam,add+seam,1).decode()
    scope={**vars(prior),'__file__':__file__,'T4':U8,'T5':U9,'INDEX':INDEX,'build_sources':build_sources,'state_guard':lambda:state_guard(plan),
        'cold_prelaunch_bytes':prior.raw(plan['cold_prelaunch_ref']['path'],16384)}
    exec(compile(source,'A09-original-union-RAM','exec'),scope)
    outputs,quote=scope['compose'](plan,display_values=display_values,display_review=display_review,companion_values=companion_values)
    quote.update(campaign_score_junction=campaign_score_guard(),actual_A08_index=prior.ref(INDEX),new_first_sequence=10502,
        saved_basis_next_sequence=10481,unknown10501_credit=0)
    quote['prerequisite_directories'].append(str(U9/'campaign-score'))
    return outputs,quote

def compose_plan(plan_ref):
    plan=prior.checked(plan_ref,131072);require(prior.ref(__file__)==plan['union_producer'],'A09 exact contract')
    p=Path(plan['display_producer']['path']).resolve()
    require(p==OWN/'prepare_c23_a09_display_v1.py' and prior.ref(p)==plan['display_producer'],'A09 exact contract')
    display=prior._module(p,'_a09_exact_display');v,r,c=display.compose(plan['display'])
    outputs,quote=compose(plan,display_values=v,display_review=r,companion_values=c)
    quote.update(adopter=prior.ref(__file__),input_plan=plan_ref,original_adopter_source=prior.ref(OWN/'adopt_c23_a05_union_v1.py'))
    return plan,outputs,quote

def metadata_source(source):
    data=previous.metadata_source(source)
    data=prior.swap(data.encode(),"'next_sequence':10482","'next_sequence':10502",3)
    data=prior.swap(data,".get('next_sequence')==10482",".get('next_sequence')==10502",1)
    seam="sourcepins={str(path.relative_to(runtime)):digest for path,digest in entries.items() if path.is_relative_to(runtime)}"
    after=seam+"\n    for item in policy['runtime_import_source_pins']:\n        require(ref(item['path'])==item,'A09 exact contract')\n        sourcepins[str(Path(item['path']).relative_to(runtime))]=item['sha256']"
    return prior.swap(data,seam,after,1).decode()

def metadata_scope(scope,runtime):
    pre=prior.ref(runtime/'ROOT-C23-COLD-PRELAUNCH.json')
    require((pre['bytes'],pre['sha256'])==PRE_PIN,'A09 exact contract')
    scope['COLD_PRE_PIN']=PRE_PIN
    scope['historical_saved_basis_view']=prior._module(runtime/'root_checkpoint_bootstrap_c23.py','_a09_checked_bootstrap_metadata').historical_saved_basis_view

def adopt(plan_ref,quote_ref,card_ref):
    source=function(previous,'adopt').replace('A08','A09').replace('a08','a09')
    scope={**vars(previous),'__file__':__file__,'U8':U9,'T5':U9,'compose_plan':compose_plan,'campaign_score_guard':campaign_score_guard,
        'metadata_source':metadata_source,'metadata_scope':metadata_scope}
    exec(compile(source,'A09-adopt','exec'),scope)
    return scope['adopt'](plan_ref,quote_ref,card_ref)

def cold_owner(inputs):
    source=function(previous,'cold_owner').replace('A08','A09').replace('a08','a09')
    scope={**vars(previous),'U8':U9,'T5':U9,'metadata_source':metadata_source,'metadata_scope':metadata_scope}
    exec(compile(source,'A09-owner','exec'),scope)
    return scope['cold_owner'](inputs)
