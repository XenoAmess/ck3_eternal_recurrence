"""Update only two stale handler digests; no C4 eligibility or251 rule is added."""
from __future__ import annotations
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from prepare_c3_life_opening_classifier_v1 import pinned

CHANGES={
    'root_p37_campaign_root_local_revision_readonly.py':(
        '12938caeb7ff567ad65b1f000ce7f88b3ac55fe0d3b5c3df15aba162c4b10e44',
        'e79975d3645f9a64627d8ebac6a7ec37879afc01731c1dbdbca2924bf78d1f8c'),
    'root_p37_native_revision_readonly_v2.py':(
        '93f4b8e86fcdf84462f24fc09b1cc776753e8affd8817e6205e9904454e59f6d',
        '93756fe07f1be858e606b707ba2099ea7256e8c85477917dd901002af390255b'),
}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True)
    args=p.parse_args();root=args.runtime_root.resolve(strict=True)
    raw,oldpin=pinned(root/'ROOT-P37-READONLY-RECOVERY-ALLOWLIST.json',expected='0e8dbea8affc1b3aa2ea530e751fed2815449b4f7385d57ab63db09076f96741')
    registry,registrypin=pinned(root/'root_p37_readonly_recovery_registry.py',expected='9e175be1c57c87f700b4541753ec4221566cfd6120798124e450cd12c73a40dc')
    row,rowpin=pinned(root/'p37-responses/0251-1-result.json',expected='c3ac06a1400157f969cd16fc04120b1f0a27d4548b8694fd64af934ac8fd9597')
    old=json.loads(raw);changed=copy.deepcopy(old);sourcepins=[]
    args.output_root.mkdir(parents=True,exist_ok=False)
    for handler in changed['handlers']:
        expected=CHANGES.get(handler['source'],(handler['sha256'],handler['sha256']))
        if handler['sha256']!=expected[0]:raise AssertionError('Expected old digest differs')
        payload,pin=pinned(root/handler['source'],expected=expected[1],limit=65536)
        (args.output_root/handler['source']).write_bytes(payload);sourcepins.append(pin)
        handler['sha256']=expected[1]
    differences=[]
    for i,(a,b) in enumerate(zip(old['handlers'],changed['handlers'])):
        for key in a:
            if a[key]!=b[key]:differences.append(f'handlers[{i}].{key}')
    if differences!=['handlers[3].sha256','handlers[6].sha256']:raise AssertionError('Only two digest fields may change')
    scope={'__file__':str(root/'root_p37_readonly_recovery_registry.py')}
    exec(compile(registry,str(root/'root_p37_readonly_recovery_registry.py'),'exec'),scope)
    try:scope['qualify_failed_readonly_auto'](json.loads(row))
    except ValueError as error:
        if str(error)!='reviewed read-only handler SHA differs':raise
    else:raise AssertionError('Historical stale digest failure must reproduce')
    target=args.output_root/'ROOT-P37-READONLY-RECOVERY-ALLOWLIST.json'
    target.write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    scope={'__file__':str(args.output_root/'root_p37_readonly_recovery_registry.py')}
    exec(compile(registry,str(args.output_root/'root_p37_readonly_recovery_registry.py'),'exec'),scope)
    if scope['qualify_failed_readonly_auto'](json.loads(row)) is not None:raise AssertionError('251 must remain unqualified')
    result={'schema':'xar.c4-readonly-registry-two-source-digests/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':[oldpin,registrypin,rowpin]+sourcepins,
        'changed_JSON_fields':differences,'original251_result':'ValueError: reviewed read-only handler SHA differs',
        'corrected251_result':None,'handlers_business_bytes_unchanged':True,
        'old_src02_MODE_generation_guards_preserved':True,'C4_business_qualification_migrated':False,
        'new251_classification_added':False,'runtime_files_mutated':0,'actual_Game_Native_MCP_calls':0,
        'candidate':{'path':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','candidate':result['candidate']}))


if __name__=='__main__':main()
