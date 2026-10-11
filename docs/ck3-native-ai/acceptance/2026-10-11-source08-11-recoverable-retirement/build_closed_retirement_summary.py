"""ROOT executes once, only after actual32 success and actual reservation closure.

Reads small original receipts only. No target/CAS/ledger/source body reads, walks,
deletion, restoration, credit claiming, bus or MAIN operations. Fixed output.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

B = Path('C:/workspace/ck3_lyd_runtime_20261004')
OUT = B / 'source08-11-retirement-permanent-summary-20261011-001'
PLAN = {'path': str(B/'source08-11-retirement-plan-20261011-001/PLAN.actual.json'),
        'bytes': 5687, 'sha256': 'd73dd4f67e9905df92e5caaf57956598281787245939894162aec926e12bbb8c'}
RECOVERY_PATH = B/'source08-11-retirement-recovery-20261011-001/RECOVERY.actual.json'
RECOVERY_SHA = 'ff7de770ddeace434b1f0bce0038b08702de534c0c93d189d9833dd8a018485c'
ADMISSION = {'path': str(B/'source08-11-recovery-admission-20261011-001/ADMISSION.actual.json'),
             'bytes': 13834, 'sha256': 'f61be6ba6dca39d1dc833da8976a2b3898651352c968bf9904b310e41ca1f2a2'}
CLOSED_PATH = B/'source08-11-recovery-admission-20261011-001/CLOSED-RESERVATION.actual.json'
CLOSURE_COMMAND_PATH = B/'source08-11-recovery-closure-command-20261011-001/RESULT.actual.json'
SOURCE = {'path': str(B/'source08-11-retirement-feasibility-readonly-20261011-001/source08_11_retirement.py'),
          'bytes': 24872, 'sha256': 'c7272494dd41c4cf0f94c21983047dc517d9135f96ceb93fba6d5830e6e258a8'}
EVENT_ID = 'lyd-source08-11-indexed-retirement-20261011-001'
GROSS, FILES, CAS = 563263222, 31624, 10721390


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def read_pin(path, expected_sha=None, expected_bytes=None):
    """Small receipt one read; nothing resolves into any retired payload."""
    path = Path(path).absolute()
    need(path.stat().st_size <= 65536, 'Selected receipt exceeds64KiB: '+str(path))
    raw = path.read_bytes()
    ref = {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    need(expected_sha is None or ref['sha256'] == expected_sha, 'Receipt SHA mismatch')
    need(expected_bytes is None or len(raw) == expected_bytes, 'Receipt size mismatch')
    return json.loads(raw), ref


def checked(ref):
    value, actual = read_pin(ref['path'],ref['sha256'],ref['bytes'])
    need(actual == ref, 'Exact receipt path differs')
    return value


def command_zero(ref):
    value = checked(ref)
    need(value.get('schema') == 'ck3-recorded-actual-command-v1' and
         type(value.get('exit_code')) is int and value['exit_code'] == 0,
         'Original outer command did not complete actual0')


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')


def ref_for(name, raw):
    return {'path':str(OUT/name),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--closed-sha256',required=True)
    parser.add_argument('--closure-command-sha256',required=True)
    args = parser.parse_args()
    need(not OUT.exists(), 'Create-only unique canonical event output already exists; no duplicate event/rewrite')
    plan = checked(PLAN)
    need(plan['schema'] == 'source08-11-indexed-ordinal-plan-v1' and len(plan['batches']) == 32 and
         plan['eligible_file_count'] == FILES and plan['declared_logical_bytes'] == GROSS and
         plan['max_files_per_batch'] == 1000 and plan['executor'] == SOURCE, 'Reviewed exact plan differs')
    recovery, recovery_ref = read_pin(RECOVERY_PATH,RECOVERY_SHA)
    need(recovery['schema'] == 'source08-11-recovery-subset-actual-v1' and recovery['plan'] == PLAN and
         recovery['admission_receipt'] == ADMISSION and recovery['copied_and_readback_verified'] is True and
         len(recovery['blobs']) == 141 and sum(r['bytes'] for r in recovery['blobs']) == CAS and
         recovery['actual_deletions'] == 0, 'Actual141-blob restoration source proof differs')
    closed, closed_ref = read_pin(CLOSED_PATH,args.closed_sha256)
    need(closed['schema'] == 'source08-11-recovery-reservation-closure-v1' and
         closed['status'] == 'CLOSED_NO_FURTHER_WRITES_RESERVED' and
         type(closed['remaining_reserved_peak_bytes']) is int and closed['remaining_reserved_peak_bytes'] == 0 and
         closed['original_admission'] == ADMISSION and closed['reviewed_retirement_plan'] == PLAN and
         closed['actual_recovery'] == recovery_ref, 'Actual matching CLOSED reservation required')
    need(closed['this_closure_is_reclamation_credit_event'] is False and closed['new_credit_claim_created'] is False,
         'Closure already created/consumed a credit event')
    need(closed['actual_deleted_files_as_batch_proofs'] == FILES and
         closed['actual_deleted_logical_bytes_as_batch_proofs'] == GROSS, 'Closure deletion totals differ')
    closure_command, closure_command_ref = read_pin(CLOSURE_COMMAND_PATH,args.closure_command_sha256)
    need(closure_command.get('schema') == 'ck3-recorded-actual-command-v1' and
         type(closure_command.get('exit_code')) is int and closure_command['exit_code'] == 0, 'Closure original command must be actual0')
    original_commands = closed['actual_original_commands']
    need(len(original_commands) == 6 and len({r['path'] for r in original_commands}) == 6, 'Need original admit/preserve/4group commands')
    for ref in original_commands:
        command_zero(ref)
    actual_refs, rows = [], []
    total_files = total_logical = total_allocation = 0
    for number, expected in enumerate(plan['batches']):
        need(expected['batch'] == number and expected['end'] - expected['begin'] <= 1000, 'Original ordinal batch differs')
        path = B/('source08-11-retirement-batch-20261011-%03d' % number)/'RESULT.actual.json'
        value, ref = read_pin(path)
        need(value['schema'] == 'source08-11-exact-batch-result-v1' and value['batch'] == expected and
             value['plan'] == PLAN and value['recovery'] == recovery_ref and value['failure'] is None and
             value['deleted_files'] == expected['eligible_files'] and value['deleted_logical_bytes'] == expected['logical_bytes'] and
             value['original_hosts_and_directories_retained'] is True and value['automatic_retry_allowed'] is False and
             value['free_delta_attributed_to_this_task'] is False, 'Actual complete batch required: '+str(number))
        need(type(value['allocation_size_api_bytes']) is int and value['allocation_size_api_bytes'] >= 0, 'Missing allocation API count')
        need(value['ledger']['path'] == str(path.parent/'DETAIL-LEDGER.actual.jsonl'), 'Unexpected detail ledger reference')
        actual_refs.append(ref)
        rows.append([number,expected['r'],value['deleted_files'],value['deleted_logical_bytes'],value['allocation_size_api_bytes']])
        total_files += value['deleted_files']
        total_logical += value['deleted_logical_bytes']
        total_allocation += value['allocation_size_api_bytes']
    need(actual_refs == closed['actual32_batch_results'] and total_files == FILES and total_logical == GROSS,
         'Actual32 receipts are not the closed original result set')
    at = datetime.now(timezone.utc).isoformat()
    event = {
        'schema':'lyd.exact-reclamation-credit-event.v1','event_id':EVENT_ID,'at_utc':at,
        'owner_task':'lyd-transaction-control-scaffold-l0-20261009-root','deduplication_key':EVENT_ID,
        'logical_deleted_bytes':GROSS,'actual_deleted_files':FILES,'actual_batch_results':actual_refs,
        'reviewed_plan':PLAN,'actual_recovery':recovery_ref,'closed_reservation':closed_ref,
        'original_closure_command':closure_command_ref,'allocation_size_api_bytes':total_allocation,
        'original_failed_closure_command':None,'earlier_closure_candidate_status':'SOURCE_ONLY_REVIEW_REJECTED_NOT_EXECUTED',
        'reservation_claimed_or_consumed':False,'future_reservation_reference':None,
        'old_five_SAVE_458348713_or_R52_146942031_credit_repeated':False,'business_credit':False,
        'gross_not_net':True,'CAS_or_ledger_growth_subtracted_from_credit':False,
        'new_retained_bytes_are_separate_closed_reservation_carry':True,
        'free_delta_or_physical_reclaim_claim':False,
    }
    event_raw = encoded(event)
    event_ref = ref_for('CREDIT-EVENT.actual.json',event_raw)
    facts = {
        'schema':'source08-11-closed-retirement-compact-facts-v1','at_utc':at,'status':'ACTUAL32_DELETED_AND_RESERVATION_CLOSED',
        'credit_event':event_ref,'plan':PLAN,'recovery':recovery_ref,'original_admission':ADMISSION,'closed_reservation':closed_ref,
        'original_closure_command':closure_command_ref,'actual_original_commands':original_commands,
        'original_failed_closure_command':None,'earlier_closure_candidate_status':'SOURCE_ONLY_REVIEW_REJECTED_NOT_EXECUTED',
        'source_candidate':SOURCE,'actual_deleted_files':FILES,'actual_deleted_logical_bytes_gross':GROSS,
        'allocation_size_api_bytes':total_allocation,'actual_preserved_CAS_files':141,'actual_preserved_CAS_payload_bytes':CAS,
        'CAS_ledger_and_small_receipt_carry_upper_bound_bytes':closed['known_retained_plus_closing_upper_bound_bytes'],
        'observed_retained_task_logical_bytes_before_closing':closed['observed_retained_task_logical_bytes_known'],
        'remaining_reserved_peak_bytes':0,'credit_claim_created_or_consumed':False,
        'batch_row_columns':['batch','root_ordinal','deleted_files','logical_deleted_bytes','allocation_size_api_bytes'],'batch_rows':rows,
        'old_payload_availability':'INDEXED_NON_HOST_PAYLOAD_RETIRED_RESTORE_REQUIRED',
        'original_hosts_all_directories_all_O7_O8_O10_O11_metadata_gitobjects_Cbr2_Cbr3_current13_14_15_all_CACHE_SAVE_retained':True,
        'recovery_source':'Retained actual Source15 plus original hosts plus actual141-blob CAS; verify bytes when restoring',
        'old_reports_or_failed_runtime_results_rewritten':False,'native_game_business_qualification':False,
        'this_generator_target_CAS_ledger_or_source_body_reads':0,'directory_walks':0,
        'ledger_review_days':30,'summary_review_days':180,
    }
    facts_raw = encoded(facts)
    facts_ref = ref_for('FACTS.actual.json',facts_raw)
    report = f'''# Source08–11 可恢复退役实际结果

32批原始结果均完整成功，按原索引共删除31624个非host文件，gross逻辑字节563,263,222；四个原host与全部目录保留。复用现有排他句柄/父目录非reparse/native身份/SHA guard，逐项恢复来源先验→intent→disposition→close→absent；本摘要只消费原小结果，不再次读取目标或ledger。

141个差异blob已实际复制并读回，共10,721,390 B。Source15及原host覆盖其余旧内容；旧source-index、O7/O8/O10/O11元数据/Git objects、Cbr2/3、当前13–15、所有cache/SAVE不在候选内。原混合commit/host身份不改；旧validator需要旧路径正文时必须先实际恢复，不能声称退役后的旧payload仍完整在线。

最初closure源码在ROOT只读审阅中被拒，原因是parent argv与实际ROOT wrapper不同；它未执行，没有actual失败命令或失败回执。后继仅修该接点，首次实际闭账使用closure-command-001，不重跑preserve/32批。旧源码保留为SOURCE_ONLY_REVIEW_REJECTED_NOT_EXECUTED，actualfailure为NULL。

实际恢复预约已CLOSED，未来预约0。CAS/ledger/小回执新增占用由闭账carry单独进入下一准入；唯一 `CREDIT-EVENT.actual.json` 使用gross563,263,222，不减CAS、不将净量再扣一次。事件尚未claim/consume，不重复旧五SAVE、R52、R54或本轮其他清理credit。实际allocation API总和{total_allocation} B与逻辑字节分列；并发free差值不归因于本批。

事实及32批原件pins见 `FACTS.actual.json` → `CREDIT-EVENT.actual.json`。原PLAN、RECOVERY、ADMISSION、CLOSED和六条原命令均仅精确引用；不复制141条blob索引、逐文件ledger、完整source或大输入。ledger30天、摘要180天复核；恢复链的保留期限仍须由owner管理。

没有CK3/native/business新验收、MAIN/Git修改或自动GC部署事实。旧RED原记录不变。
'''
    report_raw = report.encode('utf-8')
    source_raw = Path(__file__).read_bytes()
    source_ref = ref_for('build_closed_retirement_summary.py',source_raw)
    products = {'CREDIT-EVENT.actual.json':event_raw,'FACTS.actual.json':facts_raw,
                'REPORT.zh.md':report_raw,'build_closed_retirement_summary.py':source_raw}
    index = {'schema':'source08-11-closed-retirement-permanent-small-index-v1','at_utc':at,
             'status':'ACTUAL32_DELETED_AND_CLOSED_NO_NEW_BUSINESS_CREDIT',
             'files':[ref_for(name,raw) for name,raw in products.items()],
             'original_plan':PLAN,'original_recovery':recovery_ref,'original_admission':ADMISSION,
             'original_closed':closed_ref,'original_closure_command':closure_command_ref,
             'original_failed_closure_command':None,'earlier_closure_candidate_status':'SOURCE_ONLY_REVIEW_REJECTED_NOT_EXECUTED',
             'source_execution_origin':{'path':str(Path(__file__).absolute()),'bytes':len(source_raw),'sha256':source_ref['sha256']},
             'huge_original_bodies_not_copied':True,'actual_credit_claim_created':False}
    products['INDEX.actual.json'] = encoded(index)
    need(sum(len(raw) for raw in products.values()) <= 48*1024, 'Permanent packet exceeds48KiB; do not upsize')
    OUT.mkdir()  # all checks complete before any output; root parent must exist.
    # Canonical event is last: a failed earlier write must not leave a new event.
    for name, raw in sorted(products.items(),key=lambda item:item[0] == 'CREDIT-EVENT.actual.json'):
        with (OUT/name).open('xb') as stream:
            stream.write(raw)
    print(json.dumps({'output':str(OUT),'files':len(products),'bytes':sum(len(raw) for raw in products.values()),
                      'index':ref_for('INDEX.actual.json',products['INDEX.actual.json']),
                      'credit_event':event_ref,'actual_deleted_files':FILES,'gross_credit_bytes':GROSS,
                      'claim_or_consumption':False},ensure_ascii=False))


if __name__ == '__main__':
    main()
