from __future__ import annotations
import hashlib,json,pathlib,shutil,subprocess,sys
from datetime import datetime,timezone
OUT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('D:/workspace/ck3_eternal_recurrence')
audit=json.loads((OUT/'SOURCE-AUDIT.actual.json').read_bytes())
check=json.loads((OUT/'PURE-CONTRACT-CHECK.actual.json').read_bytes())
contract=json.loads((OUT/'R06-ADAPTER-CONTRACT.UNIMPLEMENTED.json').read_bytes())
assert audit['selected_source_only']['current_save_stat_only']['bytes']==74273410
assert audit['existing_producer_only']['current_HEAD_native_tree_differs_from_existing_a39'] is True
assert all(x['actual_bytes_match_HEAD_blob'] for x in audit['current_sources'])
assert check['status']=='PASS' and len(check['cases'])==7
assert contract['current_public_actor_implemented'] is False
pins=[]
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name!='DELIVERY.actual.json':
        b=p.read_bytes();pins.append(dict(name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
record=dict(schema='xar.e04.r06.minimal_readonly_plan_delivery.v1',machine_id=audit['machine_id'],
 observed_at_utc=datetime.now(timezone.utc).isoformat(),source_head=audit['HEAD'],native_tree=audit['native_tree'],
 public_actor_status='EXACT_IMPLEMENTATION_GAP_IDENTIFIED_NOT_IMPLEMENTED',
 selected_single_save_sha256=contract['saved_campaign']['sha256'],source_original_pins_rechecked=True,
 saved_payload_read_or_rehashed=False,EXE_payload_reads=0,SDK_calls=0,game_launches=0,screen_calls=0,DR_calls=0,
 repo_edits=0,D_writes=0,capacity_scope='parent collective128MiB metadata; this package<=256KiB; native/game/scene execution not admitted here',
 package_ceiling_bytes=262144,pinned_files_bytes=sum(x['bytes'] for x in pins),files=pins,
 capacity_at_close={v:dict(zip(('total','used','free'),shutil.disk_usage(v))) for v in ('C:/','D:/')},
 review_at_utc='2026-10-20T08:00:00Z',automatic_renewal=False,
 retention_reason='Small source-bound plan needed for the one Root-owned R06 continuation; review after integration or deadline',
 all_future_READY_ADD_business_or_full_card_credit=False,
 pure_contract_checks=dict(status=check['status'],cases=len(check['cases']),actual_native_qualification=False))
b=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
assert record['pinned_files_bytes']+len(b)<=262144
(OUT/'DELIVERY.actual.json').write_bytes(b)
print(json.dumps(dict(path=str(OUT/'DELIVERY.actual.json'),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),package_bytes=record['pinned_files_bytes']+len(b),pins=[x for x in pins if x['name'] in ('R06-MINIMAL-PLAN.md','SOURCE-AUDIT.actual.json','R06-ADAPTER-CONTRACT.UNIMPLEMENTED.json','PURE-CONTRACT-CHECK.actual.json')]),ensure_ascii=False,indent=2))
