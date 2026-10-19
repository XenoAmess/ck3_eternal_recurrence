"""Small repository delivery from closed Native29; retains Native28's true RED."""
from pathlib import Path
import hashlib
import json
import sys
sys.dont_write_bytecode=True
import build_native26_performance_20261019 as b

ROOT=Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-native29-camera01')
OLD=Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-native28-camera01')
OUT=Path('docs/ck3-native-ai/evidence/native29-camera-build-qualification-2026-10-19.json')
manifest=ROOT/'FILES-CLOSED.json'
assert manifest.stat().st_size==11524 and b.sha(manifest)=='2ee5a67003ad2d9a3d1a6ee11f44c2bc02288c357f4410ea9112e119f7b0e206'
closed=b.read(manifest)
pins={row['relative_path'].replace('\\','/'):row for row in closed['files_excluding_this_manifest']}


def small(name):
    pin=pins[name]
    assert pin['bytes']<256*1024 and b.sha(pin['path'])==pin['sha256']
    return b.read(pin['path'])


result=small('QUALIFICATION.json')
compiled=small('COMPILE-RESULT.json')
result['source_qualification']=pins['QUALIFICATION.json']
result['closed_manifest']=b.pin(manifest)
result['producer_used']=pins['producer-used.py']
result['production_object']=compiled['object']
result['compile_source_closure']={
 'actual395_order_preserved_except_two_explicit_headers':compiled['original395_order_preserved_except_two_explicit_headers'],
 'source_dependencies':compiled['dependencies'],
 'headers_and_retained_input_manifest':pins['PREPARED.json'],
 'new_three_leaf_source_sha256':hashlib.sha256(b.canonical([result[key] for key in ('source','header','geometry')])).hexdigest(),
 'source_sha_scope':'Exact compiled cpp/status header/one-token geometry header pin aggregate; not a claim to rewrite the retained BridgeIdentity embedded build label.'}
result['storage']={key:closed[key] for key in ('logical_bytes_including_manifest','future_writes_bytes','owned_build_or_fixture_subprocesses_remaining')}
result['storage'].update({'files_including_manifest':len(pins)+1,'allocated_bytes_including_manifest':44278600,
 'allocation_source':'Build final FileStandardInfo exact-child usage after closed manifest; coordinator independent closure follows.',
 'physical_credit_released':0,'root_closed_no_future_writes':True})
assert b.sha(OLD/'FILES-CLOSED.json')=='959aa9909b3f4ff123f0ebbacc620fe3aeb155e484ad696e2a0fff5c9fa0ad4f'
failure=b.read(OLD/'FAILED01.json')
result['prior_native28_failure']={
 'status':'RED_SINGLE_ATTEMPT_RETAINED_NOT_DEPLOYABLE','closed_manifest':b.pin(OLD/'FILES-CLOSED.json'),
 'failure':b.pin(OLD/'FAILED01.json'),'run_log':b.pin(OLD/'offline01/run.log'),
 'original_observed_result':'Fixture -99 at stock8-bucket sentinel matrix first row; actual frozen header rejected all negative thresholds.',
 'corrective_delta':'Only thresholds[i] < 0 to thresholds[i] < -1 in original frozen geometry header; all other bytes equal. Existing repo commit87b64c8579ac3e0232c72ec3774918b23da1caaf.',
 'native28_root_future_writes':0,'old_DLL_qualified_or_loaded':False,
 'tool_windows':failure['tool_windows']}
result['scope']='Exact Native27 baseline plus1camera production TU and2explicit frozen-header overlays. Other355 direct objects including27 termination registration and original612 archive members retained unchanged, no archive copy or M1 ABI. Independent mock windows and geometry fixture43checks PASS; original v1 sizes/offsets and enum0-8/16-28 static_assert PASS;9-15 reserved. No Game, RPC, desktop action, newEXE, PDB or production DLL load.'
result['actual_camera_acceptance']='PENDING runtime-owned fresh SAVE, cold DLL/binder adoption, native target/current outcome and original-pixel movement/coverage verification. Old seq106 had bbox/client but reason was not observed; no claim window fix or sentinel fix proves its specific cause. Presentation grants no gameplay credit.'
encoded=json.dumps(result,ensure_ascii=True,indent=2).encode()+b'\n'
assert len(encoded)<=12*1024
OUT.write_bytes(encoded)
print(json.dumps({'receipt':b.pin(OUT),'producer':b.pin(__file__),'DLL':result['candidate_DLL'],'exports':result['exports'],'source_sha':result['compile_source_closure']['new_three_leaf_source_sha256']}))
