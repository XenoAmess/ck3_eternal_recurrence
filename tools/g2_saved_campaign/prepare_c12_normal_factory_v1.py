"""Port the reviewed normal warm factory to C12 over physical C11, no RPC."""
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

MACHINE='xenoamess-full-tower-eb9d2c1186'
BASE_SHA='24bc6c9cc732344152c2b6a1bacab34be9678ed06618b7b871888ae29d5fb209'
EXECUTION_FLAG='--private-active-scheme-sway-completion-execution-query'
MASK="            self.flags = [flag for flag in self.flags if flag != '--private-active-scheme-sway-completion-execution-query']\n"
PORTS=(('root_p37c9_sdk_queue.py','root_p37c12_sdk_queue.py'),
 ('root_p37c9_mcp_entry.py','root_p37c12_mcp_entry.py'),
 ('root_native_build_binding_p37c9.py','root_native_build_binding_p37c12.py'),
 ('ROOT-FINAL-SDK-FREEZE-P37C9.json','ROOT-FINAL-SDK-FREEZE-P37C12.json'),
 ('ROOT-CAMPAIGN-MAP-ADMITTED-C9.json','ROOT-CAMPAIGN-MAP-ADMITTED-C12.json'),
 ('ROOT-C9-NORMAL-SOURCE-WARM-BOUND.json','ROOT-C12-NORMAL-SOURCE-WARM-BOUND.json'),
 ('root_continuous_segment_auto_c6','root_continuous_segment_auto_c11'),
 ('root_decision_text_api_c6','root_decision_text_api_c11'),
 ('root_p37c6_overlay_relay','root_p37c11_overlay_relay'),
 ('root_score_month_samples_c4','root_score_month_samples_c11'),
 ('retained_C6_publisher_started','retained_C11_publisher_started'),
 ('retained C6 publisher','retained C11 publisher'))


def require(ok,why):
    if not ok:raise ValueError('C12 normal factory denied: '+why)


def mapped(value):
    for old,new in PORTS:value=value.replace(old,new)
    return value


def transform(source):
    require(hashlib.sha256(source.encode()).hexdigest()==BASE_SHA,'reviewed normal factory bytes differ')
    class Namespace(ast.NodeTransformer):
        def visit_Constant(self,n):
            if isinstance(n.value,str):return ast.copy_location(ast.Constant(mapped(n.value)),n)
            return n
        def visit_ImportFrom(self,n):
            n.module=mapped(n.module) if n.module else n.module
            return self.generic_visit(n)
    expected=Namespace().visit(ast.parse(source))
    ported=mapped(source)
    require(ast.dump(ast.parse(ported),include_attributes=False)==ast.dump(expected,include_attributes=False),
        'namespace port changed code or guards')
    seam="            admission=env['read'](Path(admission_path),65536);state,gov,seed,post,b,refs=normal_warm_inputs(admission)\n"
    require(ported.count(seam)==1,'reviewed preflight seam differs')
    result=ported.replace(seam,seam+MASK)
    require(result.replace(MASK,'',1)==ported,'more than inherited capability mask changed')
    compile(result,'root_p37c12_warm_resume.py','exec')
    return result


def pin(path):
    p=Path(path);raw=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def main():
    base=Path(__file__).with_name('normal_source_warm_queue_v1.py')
    result=transform(base.read_text(encoding='utf-8'))
    flags=Path('D:/codex-ck3-background-spill/g2-remediation-20261013/fresh-run-plan/prepare_fresh_robert_source_candidate.py')
    require(pin(flags)['sha256']=='b1aaa42e5a38c53772f572170f541727555f76cae6969248c5ad9ceaf5375c1b','actual frozen policy source differs')
    node=next(n for n in ast.parse(flags.read_bytes()).body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='PRIVATE_FLAGS' for t in n.targets))
    original=ast.literal_eval(node.value)
    require(isinstance(original,tuple) and original.count(EXECUTION_FLAG)==1,'one original unsupported capability required')
    holder=SimpleNamespace(flags=list(original))
    exec(compile(ast.parse(MASK.strip()),'inherited-C11-capability-mask','exec'),{'self':holder})
    require(holder.flags==[x for x in original if x!=EXECUTION_FLAG]
        and all(flag in holder.flags for flag in ('--private-active-scheme-sway-completion-query',
            '--private-active-scheme-sway-completion-termination-query')),'other flag order/capability differs')
    review=Path('Z:/ck3_mod_rewrite/_runtime/c12-normal-factory-review86')
    require(not review.exists(),'create-only review already exists')
    review.mkdir(parents=True)
    target=review/'root_p37c12_warm_resume.py'
    with target.open('xb') as f:f.write(result.encode())
    report={'schema':'xar.C12-normal-source-factory-ready/v1','machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'SOURCE_ONLY_WAITING_ACTUAL_CLEAN_BOUNDARY_AND_C12_QUEUE','producer':pin(__file__),'base':pin(base),'factory':pin(target),
        'policy':pin(flags),'only_changes':'6 current-view names, physical C11 display/score/provider key, inherited single execution-query mask',
        'namespace_AST_and_compile_PASS':True,'all_original_flags_except_execution_preserved_in_order':True,
        'ordinary_guards_and_startup_order_unchanged':True,'actual_constructor_or_warm_credit':False,'RPC_or_live_writes':0,
        'future_admission':'xar.normal-clean-source-warm/v1; retained_C11_publisher_started; boundary from actual clean seed/post-close, no fixed date/actor/sequence'}
    with (review/'QUALIFICATION.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(pin(target)));print(json.dumps(pin(review/'QUALIFICATION.json')))


if __name__=='__main__':main()
