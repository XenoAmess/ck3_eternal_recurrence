"""Finite Source26/A05 storage cards; observations outside shared CAS locks.

This coordinator never creates a SDK ref, anchor, export, runtime or process.
Run only the reviewed stage. An unknown result requires diagnosis, not replay.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
R = Path('Z:/ck3_mod_rewrite')
B = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01')
BUS = Path('Z:/.codex-task-bus')
N = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
O = N/'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100'
MID = 'xenoamess-full-tower-eb9d2c1186'
REVIEW = '2026-10-20T06:30:00+00:00'
sys.path[:0] = [str(R/'tools'), str(BUS/'bin')]
from storage_short_commit import (Snapshot, Prepared, snapshot_json, exact_identity,
                                  prepare as _prepare, publish)

from collections.abc import Sequence
from storage_pin_contract_v1 import require_sha256_pins


def prepare(head: Snapshot, value: dict[str, object], *,
            report: Path | None = None, report_bytes: bytes | None = None,
            guards: Sequence[tuple[Path, object]] = ()) -> Prepared:
    """Reject malformed pins before report/head staging or publication."""
    require_sha256_pins(value)
    if report_bytes is not None:
        require_sha256_pins(json.loads(report_bytes), path="$report")
    return _prepare(head, value, report=report, report_bytes=report_bytes,
                    guards=guards)




def pin(p):
    p = Path(p)
    raw = p.read_bytes()
    assert len(raw) <= 65536
    return {'path': str(p.resolve()), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def read(p):
    return json.loads(Path(p).read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def checked(p, digest):
    value = pin(p)
    assert value['sha256'] == digest, str(p)
    return value


def observation():
    assert subprocess.check_output([sys.executable, '-B', str(R/'tools/ck3_live_run_id.py'),
                                    'machine'], text=True).strip() == MID
    now = datetime.now(timezone.utc).isoformat()
    assert now < REVIEW
    checked(R/'docs/storage-retention-policy.json',
            'ca60e36bef8e59ffafa939689a6ba4106420f20b7c2db19a1199d6408b3131e5')
    # Exact previously sealed read-only helpers: no old producer is executed.
    source = B/'resume_sources0630_20261020.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    namespace = {'ctypes': __import__('ctypes')}
    namespace['W'] = __import__('ctypes.wintypes', fromlist=['wintypes'])
    defs = [n for n in tree.body if isinstance(n, ast.FunctionDef)
            and n.name in ('vol', 'processes')]
    assert len(defs) == 2
    exec(compile(ast.Module(body=defs, type_ignores=[]), 'read-only-observers', 'exec'), namespace)
    profile = read(B/'machine-profile-manual-A05-review-0630-20261020.json')
    assert profile['machine_id'] == MID
    volumes = {}
    for root, peak, other, quota in (
        ('D:/', 44268175360, 767836272612, 13950000000000),
        ('Z:/', 8388608, 48398823424 + 524288, 4000000000000)):
        identity = namespace['vol'](root)
        assert identity == profile['volume_map'][root]['identity']
        disk = shutil.disk_usage(root)._asdict()
        safety = max(2147483648, min(21474836480, disk['total']//20))
        physical = peak + other + 21474836480 + safety
        qfloor = disk['total'] - quota + peak + other + 2147483648
        floor = max(physical, qfloor)
        assert disk['free'] > floor and quota - disk['used'] - peak - other >= 0
        volumes[root] = dict(disk=disk, volume_identity=identity, this_write_peak=peak,
            other_unspent_reservations=other, system_growth_reserve_bytes=21474836480,
            safety_margin_bytes=safety, effective_project_quota=quota,
            current_project_usage_upper_bound=disk['used'], physical_required_free=physical,
            quota_derived_disk_reserve_bytes=qfloor, disk_reserve_bytes=floor,
            margin_bytes=disk['free']-floor, quota_margin_bytes=quota-disk['used']-peak-other)
    processes = namespace['processes']()
    assert not any(p['name'].casefold() == 'ck3.exe' and not p['positively_signaled_dead']
                   for p in processes)
    active = []
    for p in (BUS/'tasks').glob('*.json'):
        row = read(p)
        if row.get('state') == 'done':
            continue
        if 'ck3-screen:acquired' in row.get('resources', []):
            raise RuntimeError('Screen consumer requires independent owner review: '+str(p))
        age = (datetime.now(timezone.utc)-datetime.fromisoformat(row['updated_at_utc'])).total_seconds()
        if age < 900:
            active.append({k: row.get(k) for k in ('task_id','state','updated_at_utc',
                                                  'last_sequence','resources')})
    return now, volumes, processes, active


def adopt(head, card, value, changes, guards):
    raw = encoded(value)
    assert len(raw) <= 32768
    ref = dict(path=str(card), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    nxt = dict(changes)
    nxt['latest_Source26_exact_storage_card'] = ref
    result = publish(prepare(head, nxt, report=card, report_bytes=raw, guards=guards), bus=BUS)
    print(json.dumps({'card': ref, 'commit': result}, ensure_ascii=False))
    return ref


def compact(head):
    # Archive exact bytes once; old references remain readable through this chain.
    name = B/('STORAGE-SHORT-COMMIT-HEAD-ARCHIVE-REV%d-A05-RESUME.json'
              % head.value['storage_revision'])
    if name.exists():
        assert name.read_bytes() == head.path.read_bytes(), 'archive differs'
    else:
        with name.open('xb') as f:
            f.write(head.path.read_bytes())
    value = dict(head.value)
    for k in ('latest_vacation_closeout', 'latest_Root_source_C20_increment',
              'latest_Source25_CI25_scratch1MiB', 'latest_A05_source_qualification',
              'latest_G2_parallel_source_qualification', 'latest_actual_consumer_binding',
              'A03_actual_recording_job', 'A03_actual_prepared', 'A03_cold_owner_metadata_actual',
              'latest_resume_source_screen_card'):
        value.pop(k, None)
    value['latest_exact_operational_archive'] = pin(name)
    return value


def git_release():
    h = snapshot_json(B/'STORAGE-SHORT-COMMIT-HEAD-V1.json')
    a = snapshot_json(B/'ALL-HOLDS-CAPACITY-HEAD-V1.json')
    assert h.value['storage_revision'] == 209 and a.value['storage_revision'] == 26
    assert h.value['C20_guard_remaining_bytes'] == 6950912
    now, volumes, processes, active = observation()
    Q = B/'A05-SOURCE26-QUALIFICATION0630-01/source26_writer'
    writer = R/'tools/g2_saved_campaign/write_source26_canonical_ref_v1.py'
    composer = R/'tools/g2_saved_campaign/prepare_source26_sdk_v1.py'
    source = B/'A05-SOURCE26-SOURCE-QUALIFICATION704KiB0630-ADMITTED01.json'
    checked(writer, 'fa4a2d2a428a7d6d216f40d41759ef31e83af941ba066163413f1d7db53e74b3')
    checked(composer, '0b733348998422f780c6393a79d23ace1b40e1354f661718ed7dec0d6dc6b63f')
    checked(Q/'PLAN.json', 'a2b3ba812b56361d7c4040c5c68fde3671c21bc2ff2302dda66c847c4307c51b')
    assert read(Q/'PLAN.json')['Git_object_quote']['peak_upper'] == 4620288
    integration = R/'_runtime/source26-integration17'
    assert not integration.exists()
    future = 'refs/heads/campaign/robert-v20261019-source26-unified-cold-01'
    assert subprocess.run(['git','-C',str(R),'show-ref','--verify','--quiet',future]).returncode == 1
    # KiB pairs are source plus focused small evidence. Allocated highwater applies.
    caps = {'storage':(16,48), 'display':(32,32), 'export':(48,16),
            'union_guard':(48,16), 'm6':(40,8), 'm7':(32,16),
            'performance':(32,16), 'owner_preflight':(24,24),
            'Root':(32,0), 'progress_ci':(16,0), 'unassigned_guard':(0,16)}
    assert sum(sum(pair) for pair in caps.values()) == 512
    lanes = {k: {'source_allocated_hard_bytes': v[0]*1024,
        'artifact_allocated_hard_bytes': v[1]*1024,
        'artifact_root': str(B/'A05-RESUME-SMALL-QUALIFICATION0630-01'/k)}
        for k,v in caps.items()}
    card = B/'SOURCE26-EXACT-GIT-ROOT-RELEASE0630-01.json'
    value = {'schema':'xar.storage.Source26-root-canonical-Git.v1',
        'machine_id':MID, 'owner':'Root', 'status':'ADMITTED',
        'root_direct_execution_release':True, 'observed_at_utc':now,
        'review_at_utc':REVIEW, 'canonical_parent':'9b791aae9bb1314162aa5cab923e6cca2892e6d8',
        'source_admission':pin(source), 'writer':pin(writer), 'composer':pin(composer),
        'source_plan':pin(Q/'PLAN.json'), 'source_qualification':pin(Q/'QUALIFICATION.json'),
        'resume_source_card':pin(B/'A05-RESUME-SOURCE512KiB0630-ADMITTED01.json'),
        'Git':{'root':str(R/'.git'), 'hard_bytes':4620288, 'peak_upper_bytes':4620288,
               'prior_holds_retained':True},
        'integration_root':str(integration), 'future_anchor':str(integration/'SOURCE26-CANONICAL-ANCHOR.json'),
        'anchor_hard_bytes':16384, 'metadata_hard_bytes':16384,
        'capacity':{'Z_conservative_floor_bytes':volumes['Z:/']['disk_reserve_bytes'],
            'Z_disk':volumes['Z:/']['disk'], 'D_floor_bytes':volumes['D:/']['disk_reserve_bytes'],
            'D_disk':volumes['D:/']['disk'], 'fresh_complete_capacity':volumes,
            'independent_stage_budget':pin(B/'SOURCE26-A05-Z8MiB-D20MiB-BUDGET0630-PREPARED01.json')},
        'execution_rule':'Root one explicit writer execute only;create-only ref/anchor. No master/index/worktree/push/export/runtime/Task/Game. Unknown outcome never auto-retry.',
        'all_prior_holds_retained':True, 'all_old_global_forecast_bytes':44276563968,
        'source_only_dispatch':{'total_allocated_hard_bytes':524288, 'lanes':lanes,
            'source_root':str(R), 'review_at_utc':REVIEW,
            'finite_path_rule':'Lane exact paths reported to sole coordinator beforewrite. All source/doc/proof/edit/temp/dirs highwater counted; no pycache; oldsource holds retained. Root read_slice/adopter inside Root32KiB. war_events newsource cancelled0.',
            'authority':'Root dispatches concurrent source and focused RAM/small qualification only; no deploy/runtime/Game.'},
        'storage_coordination_D_hard_total':196608,
        'storage_coordination_release_for_exact_cards_and_fresh_full_only':True,
        'storage_coordination_charged_inside_A05_runtime4MiB':True,
        'actual_active_tasks':active, 'process_evidence':processes,
        'retention_review_unchanged':REVIEW, 'deletions':0, 'refunds':0,
        'producer':pin(Path(__file__))}
    changes = compact(h)
    changes.update(new_work_authority='SOURCE512KiB_AND_ROOT_SOURCE26_GIT_ONLY_RELEASED',
        Source26_canonical_Git_execution_released=True,
        Source26_A05_storage_coordination_cards_hard_bytes=196608,
        Source26_A05_storage_coordination_cards_release=True)
    adopt(h, card, value, changes, [(a.path,a.identity),
        (Q/'PLAN.json',exact_identity(Q/'PLAN.json')),
        (source,exact_identity(source)),
        (B/'SOURCE26-A05-Z8MiB-D20MiB-BUDGET0630-PREPARED01.json',
         exact_identity(B/'SOURCE26-A05-Z8MiB-D20MiB-BUDGET0630-PREPARED01.json'))])


def full_export_release():
    from storage_canonical_compat_v1 import compose_canonical_storage_v1, storage_binding_v1, validate_new_bundle_v1
    import prepare_source26_export_base_v1 as e
    h=snapshot_json(B/'STORAGE-SHORT-COMMIT-HEAD-V1.json'); a=snapshot_json(B/'ALL-HOLDS-CAPACITY-HEAD-V1.json')
    assert h.value['storage_revision']==210 and a.value['storage_revision']==26
    now,volumes,processes,active=observation()
    anchor=checked(e.ANCHOR,'d2bf903d4a0f18cc819721451d42e390a58529f76a19ad2df301e85df5b78e85')
    assert e.actual_anchor_v1(anchor)['commit']=='394865df3259be5db29014ab1d17db7bdd48c21d'
    def new(path,value,cap=32768,body=None):
        data=encoded(value) if body is None else body
        assert len(data)<=cap and not path.exists()
        with path.open('xb') as f:f.write(data)
        return pin(path)
    archive=B/'ALL-HOLDS-CAPACITY-HEAD-ARCHIVE-REV26-A05-RESUME.json'
    ap=new(archive,None,body=a.path.read_bytes())
    profile=read(B/'machine-profile-manual-A05-review-0630-20261020.json')
    profile.update(observed_at_utc=now,operator='Codex /root/storage_a05',prior_profile=pin(B/'machine-profile-manual-A05-review-0630-20261020.json'))
    config=N/'obs-portable/config/obs-studio'
    profile['project_root_map']['A05_private_OBS_config']=str(config)
    for root,v in volumes.items():
        profile['volume_map'][root].update(identity=v['volume_identity'],disk=v['disk'],current_project_usage_bytes=v['disk']['used'],other_unspent_reservations_bytes=v['other_unspent_reservations'],remaining_peak_bytes=v['this_write_peak'])
    profile['fresh_capacity_source']='Source26 concrete resume full/export admission; wholevolume used upper and all oldholds retained'
    pp=new(B/'machine-profile-manual-A05-resume-0630-20261020.json',profile)
    co=read(B/'CURRENT-FULL-HOLDS-CANONICAL-INPUT-A05-0630-02.json')
    co.update(observed_at_utc=now,active_holds_source=ap)
    def fresh(c,v):
        c.update(disk=v['disk'],current_project_usage_upper_bound=v['disk']['used'],other_unspent_reservations=v['other_unspent_reservations'],retained_other_reservations=v['other_unspent_reservations']-c['retained_old_first30_OUT'],observed_at_utc=now,at_utc=now,machine_profile=pp)
        c['physical_required_free']=c['physical_disk_reserve_bytes']=v['physical_required_free']
        c['quota_derived_disk_reserve_bytes']=v['quota_derived_disk_reserve_bytes'];c['disk_reserve_bytes']=v['disk_reserve_bytes']
        c['physical_margin_bytes']=v['disk']['free']-v['physical_required_free']
        c['quota_reserved_upper_bound']=v['disk']['used']+c['this_write_peak']+c['other_unspent_reservations']
        c['quota_margin_bytes']=c['effective_project_quota']-c['quota_reserved_upper_bound']
    fresh(co['current_capacity'],volumes['D:/']);fresh(co['capacity_by_volume']['Z:/'],volumes['Z:/'])
    roots=co['current_capacity']['approved_output_roots'];assert str(config) not in roots;roots.append(str(config))
    cp=new(B/'CURRENT-FULL-HOLDS-CANONICAL-INPUT-A05-RESUME-0630-01.json',co)
    legacy=O/'STORAGE-CANONICAL-FULL-C23-A03-0630.json'; fullpath=O/'STORAGE-CANONICAL-FULL-C23-A05-RESUME-0630-01.json'
    full=compose_canonical_storage_v1(legacy.read_bytes(),Path(cp['path']).read_bytes(),legacy_pin=pin(legacy),coordinator_pin=cp,policy_raw=(R/'docs/storage-retention-policy.json').read_bytes(),now_utc=now)
    fp=new(fullpath,None,body=full)
    binding=storage_binding_v1(full,canonical_path=str(fullpath))
    checks=validate_new_bundle_v1(full,canonical_path=str(fullpath),profile_storage=binding,job_storage=binding,launch_review=REVIEW,keeper_review=REVIEW)
    assert pin(N/'robert30-v20261019-campaign01/runtime/STORAGE-ADMISSION.json')['sha256']=='332fabb30cc6f6a62d2f8974cd6e55d12036425f5b7f02aa8cf56709af6ee42a'
    value=e.card_template_v1(anchor_ref=anchor,stage_admission_ref=fp,review_at_utc=REVIEW,disk_reserve_bytes=volumes['D:/']['disk_reserve_bytes'])
    value.update(owner='Root',root_direct_execution_release=True,capacity_by_volume=volumes,source_profile=pp,coordinator_input=cp,four_consumer_RAM_compatibility=checks,actual_active_consumers=0,actual_active_tasks=active,process_evidence=processes,old_live_replaced=False,retention_review_unchanged=REVIEW,Source26_Git_actual_anchor=anchor,execution_rule='Root unchanged generic exporter once then create-only actual BASE<=524288; no runtime/Game/Task. Unknown outcome no retry.',storage_coordination_peak_allocated_hard_bytes=196608,producer=pin(Path(__file__)))
    card=B/'SOURCE26-EXACT-DUAL-EXPORT-ROOT-RELEASE0630-01.json'
    changes=dict(h.value);changes.update(next_A05_fullcanonical=fp,next_A05_manual_machine_profile=pp,Source26_actual_Git_commit='394865df3259be5db29014ab1d17db7bdd48c21d',Source26_actual_Git_anchor=anchor,new_work_authority='SOURCE512KiB_ROOT_SOURCE26_GIT_EXPORT_BASE_ONLY',Source26_dual_export_execution_released=True)
    ep=adopt(h,card,value,changes,[(a.path,a.identity),(fullpath,exact_identity(fullpath)),(e.ANCHOR,exact_identity(e.ANCHOR))])
    av=dict(a.value);av.update(next_A05_immutable_fullview=fp,next_A05_manual_machine_profile=pp,next_A05_coordinator_input=cp,Source26_actual_Git_anchor=anchor,Source26_actual_Git_commit='394865df3259be5db29014ab1d17db7bdd48c21d',Source26_dual_export_execution_card=ep,Source26_canonical_Git_executions=1,C20_guard_remaining_bytes=6950912,canonical_input_status='A05_RESUME_COMPLETE_IMMUTABLE_NOT_DEPLOYED',observed_at_utc=now)
    result=publish(prepare(a,av,guards=[(h.path,exact_identity(h.path)),(fullpath,exact_identity(fullpath))]),bus=BUS)
    print(json.dumps({'full':fp,'four_consumers_RAM':checks,'ALLHEAD_commit':result,'oldlive_preserved':True}))


def runtime_release(planpath,quotepath):
    h=snapshot_json(B/'STORAGE-SHORT-COMMIT-HEAD-V1.json');a=snapshot_json(B/'ALL-HOLDS-CAPACITY-HEAD-V1.json')
    assert h.value['storage_revision']==212 and a.value['storage_revision']==27
    now,volumes,processes,active=observation()
    def bigpin(path,cap):
        data=Path(path).read_bytes();assert 0<len(data)<=cap
        return dict(path=str(Path(path).resolve()),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    pr=checked(planpath,'8669661838e24e09f4505575edb94be4be672b7dc1e7a3a2d08a32bff5f02a25')
    qr=bigpin(quotepath,262144);assert qr['sha256']=='e2a43d2e53c596c0f414373e9af7952458c5732ea3aff2aaf587dee7531117c9'
    p=read(planpath);q=read(quotepath);full=p['full_storage_ref'];f=read(full['path'])
    assert full==pin(full['path'])==h.value['next_A05_fullcanonical'] and p['live_storage_ref']==full
    assert q['full_storage_ref']==full and q['review_at_utc']==REVIEW and q['machine_id']==MID
    assert q['prepare_peak_upper']==sum(q[k] for k in ('fresh_allocation_upper','max_atomic_copy','future_owner_metadata_upper','control_probe_atomic_peak','intent_receipt_and_FS_upper'))
    assert q['unique_files']==len(q['files'])==119 and q['prepare_peak_upper']==1781760
    assert all(any(Path(r['path']).resolve().is_relative_to(Path(root).resolve()) for root in f['approved_output_roots']) for r in q['files'])
    assert not (N/'robert30-v20261019-campaign01/runtime-a05').exists()
    for item in (p['union_producer'],p['display_producer'],q['adopter']):assert pin(item['path'])==item
    extra=sum(((v['bytes']+4095)//4096)*4096 for v in (pr,qr))
    assert q['prepare_peak_upper']+extra+196608<=4194304
    base=bigpin(O/'ROOT-FINAL-SDK-SOURCE26-BASE.json',524288);assert base['sha256']=='30ba9778f6d4be917d29f1ab9a2a2b2aa414f5fedbfa03cdb7a8a9bebebd0517'
    complete=checked(O/'immutable-source-export-a05/COMPLETE.json','3f8a95a08790e0e2168f64547192b4fc9937a3fa0809536daf5f662c86673cc8')
    v=dict(schema='xar.C23-A05-runtime-prepare-admission/v1',machine_id=MID,owner='Root',status='ADMITTED',root_direct_execution_release=True,observed_at_utc=now,review_at_utc=REVIEW,plan=pr,quote=qr,full_storage_ref=full,hard_bytes=4194304,canonical_capacity_review_passed=True,capacity=dict(D_conservative_floor_bytes=volumes['D:/']['disk_reserve_bytes'],full_formula_by_volume=volumes),complete_runtime_peak_with_coord_plan_quote=q['prepare_peak_upper']+extra+196608,Source26_BASE_actual=base,Source26_export_actual=complete,old_live_replaced=False,actual_active_consumers=0,actual_active_tasks=active,process_evidence=processes,execution_rule='Root one create-only adopter prepare; same SAVE/Driver junction verified by FileID; no Task registration/Run/Game/OBS/RPC. Actual supervisor/profile/job/keeper binding required before launch.',producer=pin(Path(__file__)))
    n=dict(h.value);n.update(new_work_authority='ROOT_SOURCE26_GIT_EXPORT_BASE_A05_PREPARE_ONLY',Source26_dual_export_executions=1,Source26_BASE_actual=base,A05_runtime_prepare_released=True)
    adopt(h,B/'A05-EXACT-RUNTIME-PREPARE-ROOT-RELEASE0630-01.json',v,n,[(a.path,a.identity),(Path(quotepath),exact_identity(Path(quotepath))),(Path(full['path']),exact_identity(Path(full['path'])))])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--stage', choices=['git','full-export','runtime'], required=True)
    parser.add_argument('--plan',type=Path);parser.add_argument('--quote',type=Path)
    args = parser.parse_args()
    if args.stage=='git':git_release()
    elif args.stage=='full-export':full_export_release()
    else:runtime_release(args.plan,args.quote)
