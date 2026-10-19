"""Pure one-leaf alliance warm SDK over the actual C17 source14 tree.

No current runtime/ledger, Game, output SDK tree or Git object is changed.  The
explicit canonical recipe requires Root's own writer callback and release SHA.
"""
from __future__ import annotations
import ast
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import sys

import prepare_c16_perf_warm_sdk_v1 as exact

REPO=Path(__file__).resolve().parents[2]
MACHINE='xenoamess-full-tower-eb9d2c1186'
N=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
BASE_ROOT=N/'sdk-v20261019-candidate/src14'
BASE_FREEZE=N/'robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C17.json'
FREEZE_PIN=(375058,'abea90e330961720d50ec433de215bfe151c2d3c35688fc0ac03cbf73d5e8b86')
BASE='04a87c1ec6fd4a0d59e6237af3158ce797c7cbe4'
LEAF='xar_autoplayer/family_marriage_formal_consumer.py'
BEFORE=(59889,'1e8f19eafca8b83601de84c74fb30f40b173932570587cacd15be590d72f357c')
AFTER=(61273,'d8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf')
REF='refs/heads/campaign/robert-v20261019-c18-alliance-warm-01'
HELPER_PIN=(25869,'ed79fdb82f422c4cd17dc9fc1c00a133603dbea2ca4374b980172c1eb33a916b')


def compose(*,verify_all_base=True):
    exact.check_bytes(Path(exact.__file__).read_bytes(),HELPER_PIN,'existing exact-hunk helper')
    raw=exact.check_bytes(BASE_FREEZE.read_bytes(),FREEZE_PIN,'actual full source14 freeze')
    base=json.loads(raw)
    exact.require(base['machine_id']==MACHINE and base['status']=='FINAL_SOURCE_FROZEN'
        and base['source_file_count']==1445 and base['source_bytes']==59051187
        and base['business_source_commit']==BASE and Path(base['source_root']).resolve()==BASE_ROOT.resolve(),
        'actual source14 tree binding differs')
    rows={}
    for row in base['files']:
        name=exact.safe_relative(row['relative'])
        exact.require(name not in rows,'duplicate actual source row')
        rows[name]=dict(row)
    exact.require(len(rows)==1445,'actual full source set differs')
    def read(name):
        row=rows[name]
        with (BASE_ROOT/name).open('rb') as stream:data=stream.read(8*1024**2+1)
        exact.check_bytes(data,(row['bytes'],row['sha256']),'actual '+name)
        exact.require(exact.blob_sha(data)==row['git_blob_sha1'],'actual Gitblob differs '+name)
        return data
    old=exact.check_bytes(read(LEAF),BEFORE,'actual family consumer')
    donor=exact.check_bytes((REPO/exact.PREFIX/LEAF).read_bytes(),AFTER,'frozen M5 family consumer')
    exact.require(exact.git_source(BASE,LEAF)==old,'family canonical baseline differs')
    diff=exact.git('diff','--no-ext-diff','--no-color','--unified=3',BASE,'--',exact.PREFIX+LEAF)
    hunks=exact.parse_hunks(diff)
    new=exact.transfer_exact_hunks(old,hunks)
    exact.require(new==donor and len(hunks)==4,'one exact frozen family delta required')
    compile(new,LEAF,'exec',dont_inherit=True)
    a=exact.function_asts(old);b=exact.function_asts(new)
    changes=sorted(name for name in set(a)|set(b) if a.get(name)!=b.get(name))
    exact.require(changes==['_plan_existing_resolution','plan_family_marriage_private'],'unrelated family AST changed')
    imports=lambda data:[ast.dump(n,include_attributes=False) for n in ast.parse(data).body
                         if isinstance(n,(ast.Import,ast.ImportFrom))]
    exact.require(imports(old)==imports(new),'family dependencies/imports changed')
    if verify_all_base:
        for name in rows:read(name)
    before=dict(rows[LEAF])
    after={'relative':LEAF,**exact.pin(new),'git_blob_sha1':exact.blob_sha(new),'git_mode':before['git_mode']}
    rows[LEAF]=after
    stable=[rows[name] for name in sorted(rows)]
    encoded=json.dumps(stable,sort_keys=True,separators=(',',':')).encode()
    plan={'schema':'xar.c18.alliance-one-leaf-warm-sdk/v1','machine_id':MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'SOURCE_ONLY_NOT_ADOPTED',
        'base_freeze':{'path':str(BASE_FREEZE),'bytes':FREEZE_PIN[0],'sha256':FREEZE_PIN[1]},
        'base_business_commit':BASE,'base_source_root':str(BASE_ROOT),
        'all1445_actual_base_content_verified':verify_all_base,
        'complete_manifest':{'file_count':len(stable),'source_bytes':sum(r['bytes'] for r in stable),
            'canonical_rows_JSON':exact.pin(encoded),'all_rows_available':'compose() second return value'},
        'delta':{'relative':LEAF,'before':before,'after':after,'net_bytes':len(new)-len(old),
            'exact_patch':exact.pin(diff),'hunk_count':len(hunks),'full_inverse_bytes_equal':True},
        'changed_function_ASTs':changes,'imports_equal':True,'other1444_leaves_unchanged':True,
        'prospective_dual_changed_logical_bytes':2*len(new),
        'prospective_dual4096cluster_allocation_upper_bytes':2*((len(new)+4095)//4096)*4096,
        'preserved':['actual Drivercc60/WAL/same-speed','Native29','Service/strategy/transports','all existing ledgers','M2/M5/M6 fixes'],
        'root_owned_anchor_ref':REF,'Git_D_SDK_Task_Game_DriverSAVE_body_writes':0,
        'current_C17_new_gates':0,
        'future_M7':'Old frozen C18 M7 proposal is future C19 only and must rebase on this family fix; do not overwrite it or deploy its old src14 baseline.'}
    return {LEAF:new},stable,plan


def canonical_anchor_with_root_writer(git_writer,*,root_release_sha256,anchor_ref=REF):
    """Root-only executable recipe; never called by compose or the CLI."""
    exact.require(callable(git_writer) and re.fullmatch('[0-9a-f]{64}',root_release_sha256),'Root writer/release required')
    exact.require(anchor_ref==REF,'exact create-only alliance anchor required')
    exact.require(anchor_ref not in exact.git('for-each-ref','--format=%(refname)',anchor_ref).decode().splitlines(),
                  'alliance anchor already exists')
    changed,rows,plan=compose()
    row=plan['delta']['after'];new=changed[LEAF]
    actual=git_writer(['hash-object','-w','--stdin'],new).decode().strip()
    exact.require(actual==row['git_blob_sha1'],'Root wrote a different family blob')
    def splice(tree,parts):
        result=[];found=0
        for raw in exact.git('ls-tree','-z',tree).split(b'\0'):
            if not raw:continue
            header,name=raw.split(b'\t',1)
            mode,kind,oid=header.decode().split()
            if name.decode()==parts[0]:
                found+=1
                if len(parts)==1:
                    exact.require(kind=='blob' and mode==row['git_mode'],'original family mode/type differs')
                    oid=actual
                else:
                    exact.require(kind=='tree','original source ancestor type differs')
                    oid=splice(oid,parts[1:])
            result.append(f'{mode} {kind} {oid}'.encode()+b'\t'+name+b'\0')
        exact.require(found==1,'original SDK path missing/ambiguous')
        return git_writer(['mktree','-z'],b''.join(result)).decode().strip()
    tree=splice(exact.git('rev-parse',BASE+'^{tree}').decode().strip(),
                (exact.PREFIX+LEAF).split('/'))
    message=('C18 one-leaf alliance warm SDK over actual C17\n\nRoot release SHA256: '+root_release_sha256+
             '\nFull rows SHA256: '+plan['complete_manifest']['canonical_rows_JSON']['sha256']+'\n').encode()
    commit=git_writer(['commit-tree',tree,'-p',BASE],message).decode().strip()
    actual_rows={}
    for raw in exact.git('ls-tree','-r','-l','-z',commit,'--',exact.PREFIX[:-1]).split(b'\0'):
        if raw:
            header,name=raw.split(b'\t',1)
            mode,kind,oid,size=header.decode().split()
            exact.require(kind=='blob','SDK row must remain a blob')
            actual_rows[name.decode()[len(exact.PREFIX):]]=(mode,oid,int(size))
    expected={r['relative']:(r['git_mode'],r['git_blob_sha1'],r['bytes']) for r in rows}
    exact.require(actual_rows==expected,'Root full1445-row canonical SDK differs')
    git_writer(['update-ref',anchor_ref,commit,'0'*40],None)
    return {'business_source_commit':commit,'business_source_ref':anchor_ref,'parent':BASE,
        'complete_manifest':plan['complete_manifest'],'master_index_worktree_changed':False}


if __name__=='__main__':
    _,_,report=compose()
    if len(sys.argv)==2:
        path=Path(sys.argv[1]).resolve();exact.require(path.is_relative_to(REPO.resolve()),'small report outside workspace')
        raw=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
        with path.open('xb') as stream:stream.write(raw)
        print(json.dumps({'report':{'path':str(path),**exact.pin(raw)}}))
    else:print(json.dumps(report,ensure_ascii=False,indent=2))
