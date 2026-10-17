"""Local read-only v3 carry admission; no v2 refill or decoder/render side effects."""
from datetime import datetime,timezone
import importlib.util
import os
from pathlib import Path
import shutil
import stat
import time

def admit_v3(repo, ledger_path, package_root, output, machine, peak, allocation_reader):
    from faith_power_promo.production import pin,read
    ledger_path=Path(ledger_path).resolve();ledger=read(ledger_path)
    at=datetime.now(timezone.utc)
    if (ledger.get('schema')!='machine-storage-coordination-episode01-v3'
        or ledger.get('machine_id')!=machine or ledger.get('state')!='ROOT_LOCK_ACTIVATED'
        or ledger.get('capacity_reservation_active') is not True
        or ledger.get('root_supersedes_previous_future_commitments') is not True
        or ledger.get('carry_origin_remains_original') is not True
        or not ledger.get('capacity_passed') or not ledger.get('quota_passed')
        or datetime.fromisoformat(ledger['reservation_review_at_utc'])<=at):
        raise ValueError('Current same-machine root-activated v3 carry ledger required')
    lane=[r for r in ledger['reservations'] if r['task']=='episode01-production']
    if len(lane)!=1:raise ValueError('One production lane required')
    lane=lane[0];root=Path(package_root).resolve();output=Path(output).resolve()
    if (root!=Path(ledger['profile']['project_root_map']['episode01']).resolve()/'production-candidate'
        or not output.is_relative_to(root) or not 0<peak<=lane['remaining_future_upper_bytes']
        or lane['peak_bytes']!=lane['remaining_future_upper_bytes'] or lane['no_new_grant_or_spent_refill'] is not True
        or lane['growth_origin_utc']!=ledger['remaining_growth_origin_utc']):
        raise ValueError('Exact authorized production root/carry lane/peak required')
    for p in (root,*root.parents):
        if p.stat().st_file_attributes&0x400:raise ValueError('Reparse production roots unsupported')
    origin_pin=ledger['remaining_growth_origin_measurement_pin']
    if pin(origin_pin['path'])!=origin_pin:raise ValueError('Carry-origin measurement changed')
    origin=read(origin_pin['path'])
    if origin['machine_id']!=machine or origin['observed_at_utc']!=ledger['remaining_growth_origin_utc'] or not origin['complete_target_scan']:
        raise ValueError('Complete matching carry-origin measurement required')
    ep_root=root.parent
    measured=[r for r in origin['rows'] if Path(r['root']).resolve()==ep_root]
    if len(measured)!=1:raise ValueError('One measured episode root required')
    baseline=measured[0]['groups']['production-candidate']['allocated_path_sum_bytes']
    if baseline!=ledger['remaining_growth_origin_EP_groups_allocated_path_bytes']['production-candidate']:
        raise ValueError('Carry baseline does not match exact measurement')
    provider_path=Path(allocation_reader).resolve();provider_pin=pin(provider_path)
    spec=importlib.util.spec_from_file_location('faith_media_v3_allocation_reader',provider_path)
    provider=importlib.util.module_from_spec(spec);spec.loader.exec_module(provider)
    total=logical=entries=files=0;start=time.monotonic();stack=[root]
    while stack:
        current=stack.pop()
        with os.scandir(current) as items:
            for item in items:
                entries+=1
                if entries>30000 or time.monotonic()-start>45:raise ValueError('Production metadata bound exceeded')
                observed=item.stat(follow_symlinks=False)
                if observed.st_file_attributes&0x400:raise ValueError('Reparse production entry unsupported')
                if item.is_dir(follow_symlinks=False):stack.append(Path(item.path));continue
                if not stat.S_ISREG(observed.st_mode):raise ValueError('Nonregular production entry')
                info,error=provider.allocation(Path(item.path))
                if error is not None or info is None:raise ValueError('Unknown current allocation')
                total+=info['allocated'];logical+=observed.st_size;files+=1
    growth=max(0,total-baseline)
    if growth+peak>lane['remaining_future_upper_bytes']:
        raise ValueError('Growth since v3 origin plus proposed peak exceeds carried remainder')
    policy_path=Path(repo)/'docs/storage-retention-policy.json';policy=read(policy_path)
    disk=shutil.disk_usage(root);cap=policy['capacity']
    safety=max(cap['safety_floor_bytes'],min(cap['safety_ceiling_bytes'],disk.total*cap['safety_volume_fraction']))
    remaining=sum(r['remaining_future_upper_bytes'] for r in ledger['reservations'])
    system=ledger['profile']['system_growth_reserve_bytes_by_volume'][root.anchor.replace('\\','/')]
    if disk.free<remaining+system+safety or ledger['current_project_usage_upper_bound_bytes']+remaining>ledger['effective_project_quota_bytes']:
        raise ValueError('Fresh shared capacity/quota admission failed')
    return {'schema':'ck3-faith-power-v3-production-admission-v1','machine_id':machine,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'evidence_source':'Exact active v3/original14:46 allocation baseline, current complete production-only FileStandardInfo path-sum and fresh shared capacity',
        'ledger':pin(ledger_path),'policy':pin(policy_path),'allocation_reader':provider_pin,'carry_origin_measurement':origin_pin,
        'growth_origin_utc':ledger['remaining_growth_origin_utc'],'baseline_allocated_path_bytes':baseline,
        'current_allocated_path_bytes':total,'current_logical_path_bytes':logical,'files':files,'metadata_entries':entries,
        'new_positive_allocated_growth_since_v3_origin_bytes':growth,'concrete_peak_new_bytes':peak,
        'carried_remaining_production_envelope_bytes':lane['remaining_future_upper_bytes'],
        'remaining_after_current_growth_and_this_peak_bytes':lane['remaining_future_upper_bytes']-growth-peak,
        'original_v2_spent_subtracted_again':False,'spent_refilled':False,
        'disk':disk._asdict(),'all_carried_future_peaks_bytes':remaining,'system_growth_reserve_bytes':system,'safety_bytes':safety,
        'capacity_passed':True,'quota_passed':True,'render_started':False,'decode_started':False,'screen_or_game_access':False}
