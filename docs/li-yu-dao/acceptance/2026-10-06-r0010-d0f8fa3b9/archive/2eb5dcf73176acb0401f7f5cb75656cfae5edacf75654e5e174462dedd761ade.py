import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).parent
author=Path('C:/workspace/ck3_lyd_runtime_20261004/c3-i3b-detached-authority-implementation-20261005-001')
candidate=author/'candidate-003/mod_li_yu_dao'
out=root/'review-package-002';out.mkdir(exist_ok=False)
def fact(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
rels=[p.relative_to(candidate).as_posix() for sub in ['common/scripted_triggers','common/scripted_effects','common/decisions','events'] for p in (candidate/sub).glob('*i3b*')]
rels+=['tools/gen_institution.py']
manifest=[];asts={}
parser_src=Path('C:/workspace/ck3_lyd_runtime_20261004/lyd-c3-native-primitives-independent-review-20261005-001/review-package-001/parser/extract_auto_upgrade_buildings.py')
assert fact(parser_src)['sha256']=='f37063db3e2322dbad713f5b58fa75287970f462402e94c0efea54ea154d8286'
target=out/'parser/extract_auto_upgrade_buildings.py';target.parent.mkdir(parents=True);shutil.copyfile(parser_src,target)
spec=importlib.util.spec_from_file_location('_i3b_frozen_actual_parser',target);parser=importlib.util.module_from_spec(spec);sys.modules[spec.name]=parser;spec.loader.exec_module(parser)
for rel in rels:
    path=candidate/rel;raw=path.read_bytes()
    dst=out/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
    d=fact(path);d['path']=rel;manifest.append(d)
    if not rel.startswith('tools/'):
        ast=parser.parse_clausewitz(raw.decode('utf-8-sig'))
        for e in ast.entries:
            if isinstance(e.value,parser.Block):asts[e.key]=e.value
assert fact(candidate/'common/scripted_triggers/lyd_i3b_institution_triggers.txt')['sha256']=='7b063867cfd25a76d2209010e7417f220e16f3c63333ef957a380687a08b3c58'
assert fact(candidate/'tools/gen_institution.py')['sha256']=='1243dc72037a0bdf3fd660f781ee13af232f9bd20828fc930b87033733884f24'
def one(body,key):
    vals=[e.value for e in body.entries if e.key==key and isinstance(e.value,parser.Block)]
    assert len(vals)==1,(key,len(vals));return vals[0]
def vals(body,key):return [e.value for e in body.entries if e.key==key and isinstance(e.value,str)]
def walk(body):
    for e in body.entries:
        yield e
        if isinstance(e.value,parser.Block):yield from walk(e.value)
def has(body,key,value='yes'):return any(e.key==key and (value is None or e.value==value) for e in walk(body))
checks=[]
def check(name,fn):fn();checks.append({'name':name,'result':'PASS'})
def detached():
    b=asts['lyd_i3b_detached_authority_trigger']
    assert has(b,'exists','rite.head_of_rite')
    assert has(b,'this','rite.head_of_rite')
    assert has(b,'rite','faith.main_rite')
    assert has(one(b,'faith'),'lyd_i3b_only_owned_rites_faith_trigger')
    assert has(one(b,'NOT'),'faith','faith:lyd_common_faith')
check('detached admission reads actual current main Rite.head_of_rite and requires actor identity',detached)
def captured():
    body=asts['lyd_i3b_captured_authority_trigger']
    branches=[e.value for e in one(body,'OR').entries if e.key=='AND']
    assert len(branches)==2
    common,detached_branch=branches
    assert has(common,'var:lyd_i3b_authority_mode','0') and has(common,'faith','faith:lyd_common_faith')
    assert has(detached_branch,'var:lyd_i3b_authority_mode','1')
    assert has(detached_branch,'lyd_i3b_detached_authority_trigger')
    assert has(detached_branch,'exists','var:lyd_i3b_required_native_hor')
    assert has(detached_branch,'this','var:lyd_i3b_required_native_hor')
    assert has(detached_branch,'var:lyd_i3b_main.head_of_rite','var:lyd_i3b_required_native_hor')
    current=asts['lyd_i3b_current_trigger']
    assert has(current,'lyd_i3b_actor_trigger') and has(current,'lyd_i3b_captured_authority_trigger')
    context=one(asts['lyd_i3b_event_context_trigger'],'scope:lyd_i3b_actor')
    assert has(context,'lyd_i3b_current_trigger',None)
    assert has(context,'var:lyd_i3b_serial','scope:lyd_i3b_event_serial')
    assert has(context,'var:lyd_i3b_nonce','scope:lyd_i3b_event_nonce')
check('captured common/detached modes are separately gated; actor-current context binds actual HoR plus serial and nonce',captured)
def title_guard():
    b=asts['lyd_i3b_no_other_office_trigger']
    title=next(one(x,'any_held_title') for x in [e.value for e in b.entries if e.key=='NOT'] if any(e.key=='any_held_title' for e in x.entries))
    roles=one(title,'OR')
    assert has(roles,'is_head_of_faith')
    assert has(roles,'pam_title_is_antipope_office_trigger')
    assert has(roles,'has_variable','lyd_c3_owned_claim_title')
    assert has(b,'pam_is_antipope_trigger','no') and has(b,'pam_is_antipope_sponsor_trigger','no')
    assert any(e.key=='NOT' and has(e.value,'has_variable','lyd_c3_claim_title') for e in b.entries if isinstance(e.value,parser.Block))
check('foreign held legit/stock marked/LYD marked offices veto in real Title scope; current-Faith native roles separately veto',title_guard)
def faith_guard():
    b=asts['lyd_i3b_headless_faith_trigger']
    negatives=[e.value for e in b.entries if e.key=='NOT']
    assert any(has(n,'exists','religious_head_title') for n in negatives)
    assert any(has(n,'exists','religious_head') for n in negatives)
    assert any(has(n,'any_religious_head_challenger',None) for n in negatives)
    assert has(b,'has_doctrine','doctrine_no_head')
check('headless current Faith vetoes actual legitimate title/head and unmarked native challenger collection',faith_guard)
def postcondition():
    b=asts['lyd_i3b_native_authority_postcondition_trigger']
    branches=[e.value for e in one(b,'OR').entries if e.key=='AND']
    assert len(branches)==1;detached_branch=branches[0]
    assert has(detached_branch,'var:lyd_i3b_result_authority_mode','1')
    assert has(detached_branch,'exists','var:lyd_i3b_result_native_hor')
    assert has(detached_branch,'this','var:lyd_i3b_result_native_hor')
    assert has(detached_branch,'var:lyd_i3b_main.head_of_rite','var:lyd_i3b_result_native_hor')
    commit=one(asts['lyd_i3b_commit_effect'],'if')
    keys=[e.key for e in commit.entries]
    assert keys.index('lyd_i3b_capture_authority_receipt_effect')<keys.index('var:lyd_i3b_faith')
    success=one(next(e.value for e in commit.entries if e.key=='if'),'limit')
    assert has(success,'lyd_i3b_native_authority_postcondition_trigger')
    receipt=asts['lyd_i3b_capture_authority_receipt_effect']
    assert any(vals(e.value,'name')==['lyd_i3b_result_authority_mode'] and vals(e.value,'value')==['var:lyd_i3b_authority_mode'] for e in receipt.entries if e.key=='set_variable')
    assert not any(e.key.startswith('set_head_of_rite') or e.key in ['set_rite_head','set_religious_head'] for b in asts.values() for e in walk(b))
check('before-write receipt preserves captured actor HoR; success afterwrite independently reads actual main HoR without fake setter',postcondition)

def reaches(name,target,seen=None):
    if name==target:return True
    seen=set() if seen is None else seen
    if name in seen or name not in asts:return False
    seen.add(name)
    return any(e.key==target or (e.key.startswith('lyd_i3b_') and reaches(e.key,target,seen.copy())) for e in walk(asts[name]))
callbacks=['lyd_i3b_accept_nomination_effect','lyd_i3b_vote_effect','lyd_i3b_player_yes_effect','lyd_i3b_sign_effect','lyd_i3b_request_signatures_effect','lyd_i3b_commit_effect']
callback_checks=[]
for name in callbacks:
    assert name in asts,name
    assert reaches(name,'lyd_i3b_captured_authority_trigger'),name
    callback_checks.append({'callback':name,'actual_ast_callgraph_reaches_captured_current_authority':True})
for d in manifest:assert fact(candidate/d['path'])['sha256']==d['sha256']
game=Path('C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game')
native={}
for rel,ranges in [('common/scripted_triggers/pam_antipope_triggers.txt',[(1,38)]),('common/scripted_effects/pam_antipope_effects.txt',[(124,134),(238,246),(282,298)])]:
    path=game/rel;raw=path.read_bytes();lines=raw.decode('utf-8-sig').splitlines()
    native[rel]={**fact(path),'ranges':[{'start':a,'end':b,'lines':[{'line':i,'text':lines[i-1]} for i in range(a,b+1)]} for a,b in ranges]}
(out/'NATIVE-TITLE-GUARD-SOURCE-PROOF.json').write_bytes((json.dumps(native,indent=2)+'\n').encode())
shutil.copyfile(root/'finish_review_002.py',out/'finish_review_002.py'); (out/'executed-review-source.py').write_bytes(source.encode())
report={'schema':'lyd.i3b.detached-authority.independent-source-review.v1','status':'FINITE_SOURCE_SCOPE_PASS_NATIVE_NOT_RUN','utc':datetime.now(timezone.utc).isoformat(),'candidate_root':str(candidate),'candidate_source_manifest':manifest,'checks':checks,'callback_scope_checks':callback_checks,'author_final_binding':fact(author/'TARGETBEFORE-SHA-003-FINAL-002.json'),'head_of_faith_trigger_scope':'Actual installed stock pam_antipope_triggers:10 uses any_held_title.is_head_of_faith; current Title scope supported. No claim it includes challenger Title.','foreign_held_office_fix':'Final successor adds real stock Title pam_title_is_antipope_office_trigger=has_variable pam_antipope_office, plus LYD owned title marker. Those held Title checks do not depend on current Faith.','foreign_sponsor_character_marker':None,'unproved_foreign_scope_cases':['Unmarked third-party challenger title held outside actor current Faith','Sponsor title of another Faith whose current native collection is not enumerated by the two stock helper queries'],'foreign_scope_boundary':'Current-Faith actual native challenger collection catches even unmarked challengers in that Faith. Held Title marker veto catches stock/PAM and LYD offices independently of current Faith. It does not prove every external native sponsor/office across all Faiths is rejected.','captured_mode':'0 original common Faith scholar route; 1 detached actual current main Rite.head_of_rite equals actor; phase, serial, nonce, captured main/faith and actual HoR are rechecked before positive nomination/ballot/signature/enactment callbacks.','postcondition':'Actual main Rite.head_of_rite read compared to prewrite saved actor after enactment; no fabricated setter. Source result class7 on mismatch.','cleanup_exceptions':'Cancellation, expiration and result receipt display intentionally do not require a still-valid positive authority; they do not nominate, vote or enact. No blanket everycallback authority claim.','no_further_source_change':'Final source target hashes matched before/after independent read. Initially frozen003 pre-marker source retained separately, final reviewed trigger7b063867 and author1243dc720.','native_acceptance':'NOT_RUN','all_author_tests_or_native_rerun':False,'mutations':{'main':False,'candidate':False,'git':False,'game':False,'pipe':False,'bus':False}}
(out/'REPORT.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
files=[]
for p in sorted(out.rglob('*')):
    if p.is_file():
        d=fact(p);d['path']=p.relative_to(out).as_posix();files.append(d)
(out/'INDEX.json').write_bytes((json.dumps({'schema':'external-review-index.v1','status':report['status'],'files':files},indent=2)+'\n').encode())
for d in files:assert fact(out/d['path'])['sha256']==d['sha256']
print(json.dumps({'index':fact(out/'INDEX.json'),'report':fact(out/'REPORT.json'),'payload_count':len(files),'checks':len(checks),'positive_callback_graphs':len(callback_checks)},indent=2))
