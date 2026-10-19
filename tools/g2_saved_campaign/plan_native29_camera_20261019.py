"""Source-only Native29 plan: exact Native28 inputs plus one stock -1 sentinel fix."""
from pathlib import Path
import hashlib
import json
import sys
sys.dont_write_bytecode=True
import build_native26_performance_20261019 as b

REPO=Path(__file__).resolve().parents[2]
P28=REPO/'docs/ck3-native-ai/evidence/native28-camera-build-plan-2026-10-19.json'
P29=REPO/'docs/ck3-native-ai/evidence/native29-camera-build-plan-2026-10-19.json'
R28=Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-native28-camera01')
OLD=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/realm-camera-native-candidate01/sources/include/xar_bridge/realm_camera_geometry_v1.hpp')
NEW=REPO/'ck3_autonomous_player/native_bridge/include/xar_bridge/realm_camera_geometry_v1.hpp'
assert b.sha(P28)=='2afd58621ac49e972e80c046ecd8dd8f3ae4ebf840016cac66f9edfa1484bdb1'
assert b.sha(R28/'FILES-CLOSED.json')=='959aa9909b3f4ff123f0ebbacc620fe3aeb155e484ad696e2a0fff5c9fa0ad4f'
assert b.sha(OLD)=='50bd950871c4fef4b9b9366910684eab43fb8cee1cb15e8e6853a82c394ba20c'
assert b.sha(NEW)=='bf38c223793d44d2904a62fe2903078f37079c9c5562abf9d8bc679536ecc80a'
before,after=OLD.read_bytes(),NEW.read_bytes()
assert before.count(b'thresholds[i] < 0')==1
assert before.replace(b'thresholds[i] < 0',b'thresholds[i] < -1')==after
plan=b.read(P28)
plan['schema']='xar.ck3.native29-camera-source-plan/v1'
plan['observed_at_utc']=b.now()
plan['proposed_root']='D:/codex-ck3-demos/2026-10-19-robert-v20261019-native29-camera01'
plan['source_pins']['candidate_geometry']=b.pin(NEW)
plan['source_pins']['original_geometry']=b.pin(OLD)
plan['geometry_change']={'exact_old':'thresholds[i] < 0','exact_new':'thresholds[i] < -1',
 'only_one_replacement_and_other_bytes_equal':True,
 'existing_repo_source_commit':'87b64c8579ac3e0232c72ec3774918b23da1caaf',
 'reason':'Actual stock descending zoom table has terminal -1; accept -1 while rejecting <-1, preserving monotonicity and all original bucket boundary selection.',
 'production_consumer':'camera_presentation_v1.cpp includes the inline geometry header; current bounded source include search has only this production consumer plus realm_camera_geometry_v1_test.cpp. All protocol/data layouts remain unchanged.'}
plan['native28_failure']={'manifest':b.pin(R28/'FILES-CLOSED.json'),'failure':b.pin(R28/'FAILED01.json'),
 'run_log':b.pin(R28/'offline01/run.log'),
 'status':'RED closed/future0; original fixture returned -99 at first stock sentinel row; Native28 production DLL never loaded and remains ineligible.',
 'source_plan':b.pin(P28)}
plan['build_scope']['compile']=plan['build_scope']['compile'].replace('only the revised camera_presentation_v1.hpp','only the revised camera_presentation_v1.hpp and the exact one-token geometry fix')
plan['build_scope']['include_check']='Actual395 Includes retain order; replace exactly the original camera and geometry header paths by their two explicit overlay pins. Every other395-header input SHA remains original. No other current-repo header is copied or resolved.'
plan['build_scope']['reuse_basis']+=' Geometry header delta is only inline NativeBucket threshold lower bound0 to-1; this TU is the actual production consumer and is rebuilt. Its struct/API/type layout is unchanged.'
plan['source_behavior'].append('Adopt existing exact single-token stock terminal -1 bucket fix; retain invalid <-1/order/extent/table-size rejection. Original43 offline checks unchanged and must all actually pass.')
plan['offline']['checks'][2]='Use explicit one-token revised geometry header: stock terminal-1 positive boundary matrix, invalid<-1/nonmonotonic/empty/negative extent, wide/tall/small viewport and bounds/union checks. Exact43 prior tests unchanged; no live projection claim.'
for inherited in ('named_actual_headers','exact4_camera_source_comparison','old_failure_limit'):
    del plan[inherited]
plan['inherited_evidence']='Native28 source-plan pin above retains exact named actual header pins, exact.4 successful resolver comparison, and old seq106 failure limit; no new Game observations or old failure attribution.'
encoded=json.dumps(plan,ensure_ascii=True,indent=2).encode()+b'\n'
assert len(encoded)<=16*1024
P29.write_bytes(encoded)
sha=hashlib.sha256(encoded).hexdigest()
oldbuilder=REPO/'tools/g2_saved_campaign/build_native28_camera_20261019.py'
assert b.sha(oldbuilder)=='a7c7ed8e9bdaeb3493b9cd28a7ad19d600aa7b235548143b326f198686906622'
body=oldbuilder.read_text(encoding='utf-8')
body=body.replace('Native28','Native29').replace('native28','native29')
body=body.replace("PLAN_SHA = '2afd58621ac49e972e80c046ecd8dd8f3ae4ebf840016cac66f9edfa1484bdb1'", "PLAN_SHA = '"+sha+"'")
body=body.replace('PLAN.stat().st_size==14203','PLAN.stat().st_size=='+str(len(encoded)))
anchor="        env,tools=b.environment(root)\n"
assert body.count(anchor)==1
body=body.replace(anchor,"        geometry=overlay/'xar_bridge/realm_camera_geometry_v1.hpp'; geometry.write_bytes(Path(plan['source_pins']['candidate_geometry']['path']).read_bytes())\n"+anchor)
old="        expected=[b.norm(header) if b.norm(p)==oldheader else b.norm(p) for p in original_deps]\n"
assert body.count(old)==1
body=body.replace(old,"        oldgeometry=b.norm(plan['source_pins']['original_geometry']['path'])\n        expected=[b.norm(header) if b.norm(p)==oldheader else b.norm(geometry) if b.norm(p)==oldgeometry else b.norm(p) for p in original_deps]\n")
body=body.replace("'original395_order_preserved_except_one_header':True", "'original395_order_preserved_except_two_explicit_headers':True,'geometry':b.pin(geometry)")
body=body.replace("require(sum(b.norm(p)==b.norm(header) for p in actual_deps)==1,'overlay header not unique')", "require(sum(b.norm(p)==b.norm(header) for p in actual_deps)==sum(b.norm(p)==b.norm(geometry) for p in actual_deps)==1,'two overlay headers not unique')")
body=body.replace("'overlay':b.pin(header)","'overlay':b.pin(header),'geometry_overlay':b.pin(geometry)")
body=body.replace("'header':b.pin(header),'candidate_DLL'","'header':b.pin(header),'geometry':b.pin(geometry),'candidate_DLL'")
builder=REPO/'tools/g2_saved_campaign/build_native29_camera_20261019.py'
builder.write_text(body,encoding='utf-8',newline='\n')
assert builder.stat().st_size<=24*1024
print(json.dumps({'plan':b.pin(P29),'producer':b.pin(__file__),'actual_builder':b.pin(builder),'geometry':b.pin(NEW)}))
