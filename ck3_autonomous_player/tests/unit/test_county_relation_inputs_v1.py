"""Five authored DTO cases for the optional relation leaf; no native/game execution."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
REL = Path('ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_predicate_trace_contract.py')


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def pin(path):
    raw = path.read_bytes()
    return dict(path=path.as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def leaf(*, same=False, returned=False, sampled=True):
    return dict(schema_version=1, source='native_original_relation_entry_return_12004',
        status='available', unavailable_reason=None, call_count=1,
        actual_bridge_caller_return_rva=0x713A,
        argument_identity_matched=True, same_thread=True, identity_before_after_match=True,
        receiver_full_id=0x100007A, actor_full_id=0x100007A if same else 0x100007B,
        auxiliary_identity='native:8192', returned=returned,
        sampled_relation_available=sampled,
        sampled_relation_unavailable_reason=None if sampled else 'same_FullID_native_early_return',
        sampled_relation_identity='native:12288' if sampled else None,
        sampled_relation_full_war_id=61 if sampled else None,
        sampled_selected_war_identity='native:16384' if sampled else None,
        sampled_selected_war_used_fallback=False if sampled else None,
        sampled_selected_war_byte_358_u8=1 if sampled else None,
        sampled_direct_war_matches_aux=False if sampled else None,
        sampled_direct_war_gate=False if sampled else None,
        unknown_or_inputs=True)


def stage(index, returned):
    return dict(call_count=1 if returned is not None else 0,
        actual_caller_return_rva=(0x24E22B3,0x24E22F1,0x24E2348)[index] if returned is not None else None,
        argument_identity_matched=True if returned is not None else None, returned=returned)


def parent_with_trace():
    return dict(status='available', mode=1, native_condition_passes=False,
        source_definition_1b_u8=1, target_definition_1b_u8=1,
        source_county_present=True, target_county_present=True,
        county_objects_differ=True, target_county_magic_3e0_u32=0x436F4461,
        predicate_trace_v1=dict(schema_version=1, source='same_preview_native_P_returns_12004',
            status='available', unavailable_reason=None, hook_installed=True, scope_entered=True,
            same_thread=True, order_valid=True, native_predicate_returned=True,
            final_condition_passes=False, ignored_foreign_calls=0, ignored_nested_calls=0,
            stages=[stage(0,True),stage(1,False),stage(2,None)],
            additional_native_predicate_calls=0, neighbor_Q_observed=False))


def run(source, candidate):
    module = load(candidate/REL, '_candidate_county_relation_contract')
    baseline = load(source/REL, '_baseline_county_relation_contract')
    checks = []

    same = leaf(same=True, sampled=False)
    before = deepcopy(same)
    result = module.explain_county_relation_inputs_v1(same)
    require(result['status']=='observed' and result['reason']=='actual_relation_same_full_id_returned_false',
            'same FullID and original AL=false produce the narrow actual explanation')
    require(result['actual_relation_returned'] is False and result['unknown_or_result'] is None,
            'native early false is retained without inventing unknown OR returns')
    require(same==before and result['direct_war_sample']['sampled_direct_war_gate'] is None,
            'same FullID result needs no pure pair or War sample')
    checks.append('same FullID immediate false survives skipped pure sampler and stays readonly')

    different = leaf()
    result = module.explain_county_relation_inputs_v1(different)
    require(result['status']=='observed'
            and result['reason']=='actual_relation_returned_false_with_distinct_full_ids',
            'distinct IDs keep actual relation false, with no invented internal OR cause')
    sample = result['direct_war_sample']
    require(sample['sampled_selected_war_byte_358_u8']==1 and 'sampled_war_ended' not in sample,
            '+358 stays a raw byte without naming an unverified domain meaning')
    require(sample['sampled_direct_war_gate'] is False and result['unknown_or_inputs'] is True
            and result['unknown_or_result'] is None,
            'pure direct sample false does not become an observed OR return')
    checks.append('distinct IDs plus actual AL=false carry raw direct-War sample with unknown OR')

    partial = leaf(sampled=False)
    partial.update(sampled_relation_unavailable_reason='pair_or_war_operand_read_unavailable',
                   sampled_relation_identity='native:12288', sampled_relation_full_war_id=61)
    result = module.explain_county_relation_inputs_v1(partial)
    require(result['status']=='observed' and result['actual_relation_returned'] is False,
            'pure sampler failure does not erase independently complete actual AL')
    require(result['direct_war_sample']['sampled_relation_full_war_id']==61
            and result['direct_war_sample']['sampled_direct_war_gate'] is None,
            'partial pure fields remain typed facts while missing gate remains unknown')
    unavailable = deepcopy(partial)
    unavailable.update(status='unavailable', unavailable_reason='actual_identity_after_unreadable',
                       identity_before_after_match=None)
    require(module.explain_county_relation_inputs_v1(unavailable)['status']=='unavailable',
            'unknown after identity cannot receive a complete actual explanation')
    checks.append('actual and pure sample qualification remain independent; nullable after identity stays unavailable')

    contradicted = leaf()
    contradicted['sampled_direct_war_gate'] = True
    contradicted.update(sampled_selected_war_byte_358_u8=0,
                        auxiliary_identity=contradicted['sampled_selected_war_identity'],
                        sampled_direct_war_matches_aux=True)
    result = module.explain_county_relation_inputs_v1(contradicted)
    require(result['status']=='unavailable' and result['reason']=='source_sample_contradiction'
            and result['actual_relation_returned'] is False and result['unknown_or_result'] is None,
            'pre-read direct true versus actual false is diagnosed without rewriting original AL')
    invalids = []
    for key, bad in [('receiver_full_id',True), ('receiver_full_id',1<<32),
                     ('actual_bridge_caller_return_rva',-1), ('unknown_or_inputs',False),
                     ('sampled_selected_war_byte_358_u8',256),
                     ('sampled_selected_war_identity','native:0001')]:
        item=leaf(); item[key]=bad; invalids.append(item)
    item=leaf(same=True,sampled=False); item['returned']=True; invalids.append(item)
    item=leaf(); item['sampled_war_ended']=False; invalids.append(item)
    for item in invalids:
        try: module.normalize_county_relation_inputs_v1(item)
        except ValueError: pass
        else: raise AssertionError('malformed or source-contradicting relation leaf was accepted')
    checks.append('sample contradiction remains unavailable; new wire strictly rejects forged types/widths/identities')

    parent = parent_with_trace()
    old = baseline.explain_county_predicate_trace_v1(parent)
    require(module.explain_county_predicate_trace_v1(parent)==old,
            'old producer lacking relation child has byte-independent exact existing output')
    current=deepcopy(parent)
    current['predicate_trace_v1']['stages'][0]['relation_inputs_v1']=leaf(returned=True)
    current['predicate_trace_v1']['stages'][1]['relation_inputs_v1']=leaf(same=True,sampled=False)
    before=deepcopy(current)
    normalized=module.normalize_county_predicate_trace_v1(current['predicate_trace_v1'],parent=current)
    result=module.explain_county_predicate_trace_v1(current)
    require(normalized['stages'][0]['returned'] is True and normalized['stages'][1]['returned'] is False,
            'true and false enclosing tail P returns stay unchanged')
    require({key:result[key] for key in old}==old and len(result['relation_inputs_v1'])==2,
            'old branch result is retained with additive read-only per-stage explanations')
    require(result['relation_inputs_v1'][0]['actual_relation_returned'] is True
            and result['relation_inputs_v1'][0]['unknown_or_result'] is None and current==before,
            'actual true with sampled direct false does not manufacture a specific OR true')
    malformed=deepcopy(current['predicate_trace_v1'])
    malformed['stages'][0]['relation_inputs_v1']['returned']=False
    try: module.normalize_county_predicate_trace_v1(malformed,parent=current)
    except ValueError: pass
    else: raise AssertionError('relation AL differing from enclosing tail P was accepted')
    normalized['stages'][0]['relation_inputs_v1']['returned']=False
    require(current==before,'normalized leaf is a separate object, preserving caller input')
    checks.append('legacy output exact; additive new leaf preserves true tail P, binds AL, and deep-copies leaf')
    return dict(status='GREEN', focused_case_count=5, checks=checks,
        malformed_new_leaf_examples=len(invalids)+1, sample_explanation=result,
        fixture_boundary='Authored strict DTO cases only. The existing normalizer and new explanation functions execute; no original native relation, pure native reader, serializer, bridge, game, SDK, desktop, build or EXE executes.',
        game_sdk_calls=0, desktop_calls=0, native_builds=0, native_executions=0,
        source_pins=[pin(source/REL),pin(candidate/REL),pin(Path(__file__))])



def run_ready_regression(source, candidate):
    module=load(candidate/REL, '_candidate_county_relation_ready_contract')
    invalid=[]
    for key in ('sampled_relation_identity','sampled_relation_full_war_id',
                'sampled_selected_war_identity','sampled_selected_war_used_fallback',
                'sampled_selected_war_byte_358_u8','sampled_direct_war_matches_aux'):
        item=leaf(); item[key]=None; invalid.append(item)
    item=leaf(); item['sampled_direct_war_matches_aux']=True; invalid.append(item)
    item=leaf(); item['sampled_direct_war_gate']=True; invalid.append(item)
    item=leaf(same=True); invalid.append(item)
    sentinel=leaf()
    sentinel.update(sampled_relation_full_war_id=-1, sampled_selected_war_identity=None,
                    sampled_selected_war_used_fallback=None, sampled_selected_war_byte_358_u8=None,
                    sampled_direct_war_matches_aux=None, sampled_direct_war_gate=False)
    item=deepcopy(sentinel); item['sampled_selected_war_byte_358_u8']=0; invalid.append(item)
    item=deepcopy(sentinel); item['sampled_direct_war_gate']=True; invalid.append(item)
    for item in invalid:
        try: module.normalize_county_relation_inputs_v1(item)
        except ValueError: pass
        else: raise AssertionError('forged ready pure sample was accepted')
    require(module.normalize_county_relation_inputs_v1(sentinel)==sentinel,
            'pair sentinel -1 requires no selected War and retains computed false gate')
    for auxiliary in (None,'native:16384'):
        item=leaf(returned=True)
        item.update(auxiliary_identity=auxiliary, sampled_selected_war_byte_358_u8=0,
                    sampled_direct_war_matches_aux=True, sampled_direct_war_gate=True)
        require(module.explain_county_relation_inputs_v1(item)['status']=='observed',
                'zero auxiliary and matching selected War both satisfy the pure auxiliary gate')
        item['returned']=False
        explanation=module.explain_county_relation_inputs_v1(item)
        require(explanation['status']=='unavailable' and explanation['reason']=='source_sample_contradiction'
                and explanation['actual_relation_returned'] is False,
                'consistent pure true versus original AL=false is unavailable explanation')
    incomplete=leaf(sampled=False)
    incomplete.update(sampled_relation_unavailable_reason='pure_operand_read_unavailable',
                      sampled_relation_identity='native:12288',sampled_relation_full_war_id=61)
    require(module.explain_county_relation_inputs_v1(incomplete)['status']=='observed',
            'strict readiness does not erase separately qualified actual AL when sampler is unavailable')
    return dict(status='GREEN',focused_case_count=1,selected_case='ready_sampler_regression',
        checks=['11 forged ready samples rejected; sentinel -1, aux null/equal, consistent contradiction and independently unavailable sampler verified'],
        forged_ready_rejections=len(invalid),
        fixture_boundary='One new authored DTO regression only; the prior five-case matrix was not rerun. No native reader, serializer, game, SDK, desktop, build or EXE executes.',
        game_sdk_calls=0,desktop_calls=0,native_builds=0,native_executions=0,
        source_pins=[pin(source/REL),pin(candidate/REL),pin(Path(__file__))])



def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--candidate-root',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--case',choices=('prior-five','ready-sampler-regression'),default='prior-five')
    args=parser.parse_args()
    try:
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.source_root,text=True).strip()
        require(source_head=='611bc985ae95f477dd7314df11f8602cd1e595f3','exact source HEAD remains pinned')
        result=(run_ready_regression(args.source_root,args.candidate_root)
                if args.case=='ready-sampler-regression' else run(args.source_root,args.candidate_root))
        code=0
    except Exception as error:
        import traceback
        result=dict(status='RED',error=str(error),traceback=traceback.format_exc())
        code=1
    result.update(machine_id='desktop-3fevhd2-1c74096080',
                  observed_at_utc=datetime.now(timezone.utc).isoformat(),
                  source_head='611bc985ae95f477dd7314df11f8602cd1e595f3',
                  interpreter=sys.executable, python_version=sys.version,run_exit=code)
    with args.receipt.open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
    print(json.dumps({key:result.get(key) for key in ('status','focused_case_count','error','run_exit')}))
    return code


if __name__=='__main__':
    raise SystemExit(main())
