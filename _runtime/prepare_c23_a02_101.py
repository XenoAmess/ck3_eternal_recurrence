"""Finite a02 RAM quote and separately admitted single-copy preparation."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,importlib.util,json,os,sys,uuid
R=Path('Z:/ck3_mod_rewrite');N=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T=N/'robert30-v20261019-campaign01/runtime';O=N/'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100'
M='xenoamess-full-tower-eb9d2c1186'
FULL=O/'STORAGE-CANONICAL-FULL-C23-A02-0348.json'
EXPECTED={
'root_p37c23_sdk_queue.py':(269159,'f7dddc9485086ef203a2a169161a7245964d54790c641390ca5af3f4411171e3'),
'root_p37c23_mcp_entry.py':(12908,'04bad62a2d8c65e7d58d563589a77ab6f0e24e42152a7b9b08c5d48604cdd44c'),
'root_native_build_binding_p37c23.py':(4102,'3ccffe28161156d0f0c884165893be337a66c21612630f54669ce4bcc4c30a8e'),
'launch_sdk_p37c23_owner.py':(5888,'e38edb011967ed9c379eea90db39916abb3b67798652ebf3fbb4781f37c443a8'),
'root_p37c23_cold_resume.py':(20078,'92c0e27980d9aad6fbbbef2ed7e5e35e5794be2f0ed0ca892b420b5f07e30b96'),
'root_checkpoint_bootstrap_c23.py':(10600,'c691fe4dbd69974114179f476a72493582c15d3c8815553713810e8061e329ea'),
'root_native30_supervisor_c23.py':(37929,'cd4fbc6ad653be78b6004d3becd79e3fe8e37a759cf5f46a06285f6924db3e8e'),
'root_c23_canonical_outer.py':(18769,'03ed5642e98e69990ee0b0fa75ce709b75f703e1d2457d88dfb42b651855877e')}
SIX={'root_native30_supervisor_c23.py','root_checkpoint_bootstrap_c23.py','launch_sdk_p37c23_owner.py',
     'root_p37c23_sdk_queue.py','root_p37c23_mcp_entry.py','root_c23_canonical_outer.py'}
OLD_META={
'ROOT-CLEAN-SOURCE-FROZEN-C23.json':'2df78dac031eccb1a190a7270e7ac26dd6768ae0607e858ea1625adbab63f25f',
'ROOT-LAUNCH-CONFIG-C23.json':'e7627a553e3dd489ba8b692b1a00952923b2403e5466a3bf469d32ddbf52324c',
'ROOT-NATIVE30-SDK-BINDING-C23.json':'1da5e0a9098dc9c2f8b9af75b370711867f57847a9a86e1ddff475c137df1995',
'ROOT-PROMO-KEEPER-SOURCE-READY-C23.json':'35d3792c43b413a140bb60c477308f1bdb28199af377810ca9c3db3c9e228723',
'ROOT-OBS-PROFILE-C23.json':'5447d5e480a88c39ad4e8776b349516d44c08b2b7ebfe55e3d25d1ca6f84cd78'}
def require(ok,why):
    if not ok:raise ValueError('a02 finite prepare denied: '+why)
def utc():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return json.dumps(v,ensure_ascii=False,separators=(',',':')).encode('utf-8')
def raw(p,cap=1048576):
    p=Path(p);require(p.stat().st_size<=cap,'bounded metadata/source required');return p.read_bytes()
def ref(p):
    p=Path(p).resolve();b=raw(p);return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def old(p,digest):
    b=raw(p);require(sha(b)==digest,'old raw CAS differs: '+str(p));return b,json.loads(b)
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def once(p,b):
    require(len(b)<=524288,'output cap exceeded')
    with p.open('xb')as f:f.write(b);f.flush()
    require(raw(p)==b,'new exact bytes differ');return ref(p)
def full_bytes():
    bpath=Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01')/'C23-A02-RUNTIME2MiB-ANNEX-CAPACITY-AND-FULLINPUT01.json'
    require(ref(bpath)['sha256']=='807f84b7938dbce86658a8cd273f81af0b90cd176fed865dad6f1f3c5e7d4a95','actual fullinput differs')
    prior=O/'STORAGE-CANONICAL-FULL-C23-0348.json'
    require(ref(prior)['sha256']=='1f6b328dd1b07458b51775f1bce214a63de8840b91a5843fa926981c6b69930d','prior complete fullview changed')
    m=load('a02_storage_composer',R/'tools/g2_saved_campaign/storage_canonical_compat_v1.py')
    b=m.compose_canonical_storage_v1(raw(prior),raw(bpath),legacy_pin=ref(prior),coordinator_pin=ref(bpath),
       policy_raw=raw(R/'docs/storage-retention-policy.json'),now_utc=utc())
    require(len(b)==27016 and sha(b)=='62a24182df872934e4244f3a684427f3357c5580ecea5ca56fb5e4f48c91e971','new full candidate changed')
    return b,{'path':str(FULL),'bytes':len(b),'sha256':sha(b)}
def graph():
    src=R/'tools/g2_saved_campaign/prepare_c23_full_enabled_cold_controls_v1.py'
    require(ref(src)['sha256']=='b63eacea6eae778678e7a05f755e033bb426e67da8c0cebc5bb465f3199051d9','actual a02 producer differs')
    constants=load('a01_historical_constants_only',O/'prepare-cold100.py')
    m=load('a02_frozen_graph',src)
    g,report=m.build_sources(native_transition_inputs={'base_freeze_ref':constants.BASE_FREEZE,'base_native_ref':constants.BASE_NATIVE,
       'capacity_ref':constants.EXPORT_CARD,'machine_id':M},business_anchor_ref=constants.ANCHOR,frontier_ref=constants.FRONTIER,full_timing=True)
    require(len(g)==18 and sum(map(len,g.values()))==523301,'complete exact new18 graph required')
    changed={n:b for n,b in g.items()if sha(b)!=ref(T/n)['sha256']}
    require(set(changed)==set(EXPECTED),'exact eight changed source names required')
    for n,b in changed.items():require((len(b),sha(b))==EXPECTED[n],'new source pin differs: '+n);compile(b,str(T/n),'exec')
    return changed,report
def feeder_change():
    src=R/'tools/g2_saved_campaign/prepare_c23_cold_feeder_v1.py'
    require(ref(src)['sha256']=='040f1f7a8a58eb9e739f52d51a6c8f0ea0a94095446b0bc7f5505627e04d12fe','actual new feeder producer differs')
    m=load('a02_frozen_feeder',src);g,_=m.build_sources();name='root_p37c23_same_game_loop_feeder100.py'
    require(len(g[name])==41718 and sha(g[name])=='6147cbc020f4e4c44a6b991d54f3a73830dc1f7b39feba4a002933bb7d045913','exact new feeder main required')
    require(ref(T/name)['sha256']=='59f061fd437db927e4e4497b34f798012a0de9439bbcd622587776b1712487ca','actual old 03:48 feeder main differs')
    for n,b in g.items():
        if n!=name:require(ref(T/n)['sha256']==sha(b),'unchanged ledger/launcher must stay exact')
    return name,g[name]
def compose(attempt_nonce,observed_at_utc=None):
    require(len(attempt_nonce)==32 and all(c in '0123456789abcdef' for c in attempt_nonce),'explicit cold attempt token required')
    at=observed_at_utc or utc();fullraw,fullref=full_bytes();full=json.loads(fullraw);changes,report=graph()
    _,policy=old(T/'ROOT-C23-CANONICAL-PRELOAD-POLICY.json','28d879d547d3cd02e766fa4867ad5863dc2ebe13f460a7183bc98f6587b87bf5')
    _,frozen=old(T/'ROOT-FINAL-SDK-FREEZE-P37C23.json','96ac60103ed59390def6c1b06de541d99b552a1e225fe6178e342989749acdcf')
    rows=policy['entry_source_pins'];require(len(rows)==44 and len({r[0]for r in rows})==44,'all44 exact closure required')
    seen=[]
    for row in rows:
        p=Path(row[0]);require(ref(p)['sha256']==row[1],'actual old all44 file differs: '+str(p))
        if p.parent==T and p.name in changes:row[1]=sha(changes[p.name]);seen.append(p.name)
    require(set(seen)==set(EXPECTED),'all eight new source rows required')
    six=[copy.deepcopy(row)for row in rows if Path(row[0]).parent==T and Path(row[0]).name in SIX]
    require(len(six)==6 and len({r[0]for r in six})==6,'exact six canonical creation entries required')
    policy['canonical_entry_source_pins']=six
    policy_target=T/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A02.json';policyraw=enc(policy)
    frozen['canonical_preload_policy']={'path':str(policy_target),'bytes':len(policyraw),'sha256':sha(policyraw)}
    freeze_target=T/'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json';freezeraw=enc(frozen)
    require(len(freezeraw)<=471040,'new RootFinal exceeded original hardbound')
    freeze_ref={'path':str(freeze_target),'bytes':len(freezeraw),'sha256':sha(freezeraw)}
    outputs={policy_target:policyraw,freeze_target:freezeraw}
    for name,digest in OLD_META.items():
        _,v=old(T/name,digest)
        if name=='ROOT-CLEAN-SOURCE-FROZEN-C23.json':v.update(sdk_freeze=freeze_ref,at_utc=at,observed_at_utc=at)
        elif name=='ROOT-LAUNCH-CONFIG-C23.json':
            v.update(SDK_freeze_sha256=freeze_ref['sha256'],storage_admission_sha256=fullref['sha256'],full_storage_view=fullref,
               review_at_utc=full['review_at_utc'],observed_at_utc=at,cold_attempt={'attempt_id':'a02','nonce':attempt_nonce,
                 'execution_owner':'Root','root_direct_execution_release':True,'prior_failure':ref(O/'C23-FIRST-SUPERVISOR-LAUNCH-FAILED-CLOSED.json')})
        elif name=='ROOT-NATIVE30-SDK-BINDING-C23.json':v.update(sdk_freeze_sha256=freeze_ref['sha256'],observed_at_utc=at)
        elif name=='ROOT-PROMO-KEEPER-SOURCE-READY-C23.json':v.update(full_storage_view=fullref,source_review_at_utc=full['review_at_utc'],observed_at_utc=at,at=at)
        else:
            require(v['profile_name']=='ManagedWindowCapture-cf9ccb6df4b446b2ac31d585932b7271','only never-run profile config may be reused')
            v['storage']={'approved_output_roots':full['approved_output_roots'],'disk_reserve_bytes':full['disk_reserve_bytes'],
              'admission_path':fullref['path'],'admission_sha256':fullref['sha256']}
            v['storage_review_refreshed_at_utc']=at;v['unrun_profile_config_reused']=True
        outputs[T/name]=enc(v)
    name,feederraw=feeder_change();changes[name]=feederraw
    source_rows=[]
    for n,b in changes.items():
        source_rows.append({'path':str(T/n),'bytes':len(b),'sha256':sha(b),'old':ref(T/n),
          'old_FileID':str((T/n).stat().st_ino),'old_archive':str(O/'post-close/a01-control-source'/n)})
    return changes,outputs,{'machine_id':M,'observed_at_utc':at,'status':'A02_RAM_QUOTE_NO_RUNTIME_WRITES',
       'cold_attempt_nonce':attempt_nonce,'newfull':fullref,'changed_sources':source_rows,
       'metadata':[{'path':str(p),'bytes':len(b),'sha256':sha(b)}for p,b in outputs.items()],
       'metadata_old_archives':[{'old':ref(T/n),'old_FileID':str((T/n).stat().st_ino),'archive':str(O/'post-close/a01-metadata'/n)}for n in OLD_META],
       'canonical_entry_source_pins':six,'all_entry_rows':len(rows),'old_policy_and_RootFinal_stay_in_place':True,
       'new_source_logical':sum(map(len,changes.values())),'new_metadata_logical':sum(map(len,outputs.values())),
       'all_changes_logical':sum(map(len,changes.values()))+sum(map(len,outputs.values())),
       'new_source_allocation_upper':sum(((len(b)+4095)//4096)*4096 for b in changes.values()),
       'new_RootFinal_allocation_upper':((len(freezeraw)+4095)//4096)*4096,
       'max_atomic_upper':524288,'FS_upper':65536,'Task_source_operator_future_metadata_upper':262144,
       'supervisor_attempt_outputs':[str(T/n)for n in ('ROOT-SUPERVISOR-ADMITTED-C23-A02.json','ROOT-FRESH-PROFILE-PREPARED-C23-A02.json',
          'ROOT-NATIVE30-GAME-ENVIRONMENT-BOUND-C23-A02.json','ROOT-SCREEN-KEEPER-C23-A02.jsonl','ROOT-FRESH-SUPERVISOR-CLOSED-C23-A02.json')],
       'new_screen_admission':str(T/'ROOT-SCREEN-ADMITTED-C23-A02.json'),'new_Task_root':str(O/'tasks/spec-supervisor-a02'),
       'Task_or_Game_started':False,'profile_secret_printed':False}
if __name__=='__main__':
    require(sys.argv[1]=='quote' and len(sys.argv)==3,'quote only; mutation requires a separately reviewed operator/card')
    changes,outputs,report=compose(sys.argv[2]);print(json.dumps(report,ensure_ascii=False))
