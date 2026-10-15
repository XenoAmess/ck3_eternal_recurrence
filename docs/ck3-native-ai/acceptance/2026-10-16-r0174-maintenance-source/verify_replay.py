from pathlib import Path
import copy
import hashlib
import json
import sys
import argparse
import re
import urllib.parse
import zipfile
PARSER=argparse.ArgumentParser(description="Offline exact R0174 source/raw replay; no game/EXE/SDK access")
PARSER.add_argument('--repo-root',type=Path)
PARSER.add_argument('--overlay',type=Path)
PARSER.add_argument('--extract-source-attempts',type=Path)
ARGS=PARSER.parse_args()
ROOT=(ARGS.repo_root or Path(__file__).resolve().parents[4]).resolve()
OVERLAY=ARGS.overlay.resolve() if ARGS.overlay else None
def resolve(rel):
    relative=Path(rel)
    if relative.is_absolute() or '..' in relative.parts:raise RuntimeError('Unsafe repository path')
    if OVERLAY is not None and (OVERLAY/relative).is_file():return OVERLAY/relative
    return ROOT/relative
def require(ok,message):
    if not ok:raise RuntimeError(message)
def get(rel):return json.loads(resolve(rel).read_bytes())
A='docs/ck3-native-ai/acceptance/2026-10-16-r0174-maintenance-source/'
CAT=get(A+'FILE-MANIFEST.json')
for item in CAT['files']:
    p=resolve(item['path']);require(p.is_file(),'Catalog path not held')
    raw=p.read_bytes();require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'Exact bytes differ '+item['path'])
A='docs/ck3-native-ai/acceptance/2026-10-16-r0174-maintenance-source/'
facts=get(A+'FACTS.actual.json');expected=facts['actual_independent_expectation'];saved=[]
for day,revision,native,date in [(17,53,52,53145456),(21,63,62,53145552)]:
    result=get(A+f'day{day}/STRICT-CONSUMER.actual.json')
    require(result['status']=='PASS' and result['maintenance_attribution']=='unclosed' and result['loss_free'] is True,'Actual original strict consumer not PASS')
    s=result['current_session']
    for key in ['pid','process_create_time_100ns','connection_generation','player_character_full_id','controlled_window_id']:
        require(type(s[key]) is int and s[key]==expected[key],'Independent Root session mismatch '+key)
    require(type(result['sampling']['epoch']) is int and result['sampling']['epoch']==expected['payment_epoch'],'Independent Root epoch mismatch')
    require(result['snapshot_binding']==dict(revision=revision,native_revision=native,snapshot_id=f'native:{native}',date_raw=date,episode_run_id=expected['episode_run_id']),'Paired snapshot binding differs')
    rows=get(A+f'day{day}/GENERIC-RAW-WITNESSES.actual.json');require(len(rows)==1,'Actual unique generic row differs')
    record=rows[0]['raw_record'];g=record['generic_wallet_context_v1']
    require(rows[0]['own_current_personal_account_callback'] is True and rows[0]['whole_callback_ADD_balance_reconciles'] is True,'Whole account qualification absent')
    for key,val in [('journal_sequence',12),('kind',2),('caller_return_rva',0x28A6D7C),('amount_raw',282364)]:require(type(record[key]) is int and record[key]==val,'Raw source field differs '+key)
    for ss in ('session_entry','session_return'):
        for key in ['pid','process_create_time_100ns','connection_generation','player_character_full_id','controlled_window_id']:
            require(type(record[ss][key]) is int and record[ss][key]==expected[key],'Record Root identity differs '+key)
        require(record[ss]['native_date_raw']&0xffffffff==53145456 and record[ss]['same_owned_process_no_load_window'] is True,'Raw callback date/window differs')
    require(record['original_called'] is True and record['original_returned'] is True and record['tls_depth_exceeded'] is False,'Callback completion differs')
    for side in ('before','after'):
        c=g[side];require(c['capture_complete'] is True and c['context_stable'] is True and c['failed_reads']==0,'Raw context incomplete')
        require(c['context_identity_before']==c['context_identity_after']==2867562606880,'Raw context identity differs')
        for key,val in [('value_2c0',500974),('value_2c8',0),('value_28',218610),('value_30',0)]:require(type(c[key]) is int and c[key]==val,'Raw term differs '+key)
    require(g['maintenance_attribution']=='unclosed' and g['before_computed_add_raw']==282364 and g['before_formula_matches_amount'] is True and g['context_values_stable'] is True,'Source formula/boundary differs')
    before=record['before'];after=record['after'];require(before['personal_gold_bits']==25166043 and after['personal_gold_bits']==25448407 and after['personal_gold_bits']-before['personal_gold_bits']==record['amount_raw'],'Whole balance delta differs')
    trace=g['parent_trace'];require(trace['reported_frame_count']==18 and trace['capture_succeeded'] is True and trace['truncated'] is False,'Stack boundary differs')
    base=trace['module_base'];rvas=[x-base if base<=x<base+trace['module_image_size'] else None for x in trace['frames_absolute']]
    require(rvas[5:11]==[0x28A6D7C,0x28F7939,0x3978BF8,0x3978C4C,0x290DD46,0x3F90A72],'Actual chain differs')
    saved.append(rows)
require(saved[0]==saved[1] and json.dumps(saved[0],sort_keys=True)==json.dumps(saved[1],sort_keys=True),'Same seq12 cannot be deduplicated')
spans=get(A+'SOURCE-SPANS.actual.json')
for item in spans['spans']:
    raw=bytes.fromhex(item['raw_hex']);require(len(raw)==item['bytes'] and item['end_rva_exclusive']-item['begin_rva']==len(raw) and hashlib.sha256(raw).hexdigest()==item['sha256'],'Actual source span pin differs')
require(facts['maintenance_attribution']=='unclosed' and all(x is None for x in facts['field_producers'].values()) and facts['military_applied_component'] is None and facts['date_cadence'] is None,'Unknown business gap overwritten')
require(all(x['code']<=8192 and x['metadata']<=512 and x['read_calls']<=48 for x in facts['new_EXE_scope_totals']),'Per scope read cap exceeded')
# Reuse only the four exact already-tracked raw members, without extracting/copying them.
raw_map=get(A+'RAW-ARCHIVE-MEMBERS.json');packet={}
with zipfile.ZipFile(resolve(raw_map['archive'])) as archive:
    for item in raw_map['members']:
        raw=archive.read(item['member']);require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'Original repository raw member differs')
        packet[(item['day'],item['role'])]=json.loads(raw.decode('utf-8-sig'))
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT),str(ROOT/'ck3_autonomous_player/src')]
from xar_autoplayer.bridge import war_payment_observations_v1 as payment
from xar_autoplayer.bridge.war_cash_private_transport_v1 import normalize_war_cash_current_resources_v1
require(hashlib.sha256(Path(payment.__file__).read_bytes()).hexdigest()=='b5b3d65abc26d5b42cacff197294f94d1f9157890f5838e810772f805360eb25','Exact production payment consumer source changed; qualify replay before updating pin')
for day in (17,21):
    cash=packet[(day,'cash')];before=packet[(day,'before')];snapshot=before['body'];body=cash['body']
    require(cash['machine_id']==before['machine_id']=='desktop-3fevhd2-1c74096080','Source machine differs')
    require(cash['is_error'] is False and before['is_error'] is False,'Original error receipt')
    require(cash['request']['tool']=='ck3_query_war_cash_current_resources_private_v1' and before['request']['tool']=='ck3_take_snapshot','Original paired tools differ')
    args=cash['request']['arguments'];require(args['payment_sampling']=='query' and args['expected_revision']==snapshot['revision']==body['queried_revision'],'Independent expected revision differs')
    require(snapshot['episode_run_id']==expected['episode_run_id'] and snapshot['played_character']['character_id']==31254 and snapshot['paused'] is True and snapshot['map_ready'] is True,'Paired source actor/frame differs')
    require(snapshot['diagnostics']['bridge_pid']==17468 and snapshot['diagnostics']['connection_generation']==1,'Paired PID/generation differs')
    normalize_war_cash_current_resources_v1(body,snapshot=snapshot)
    normalized=payment.normalize_payment_extras(body,snapshot=snapshot,payment_sampling='query')[payment.JOURNAL_KEY]
    require(normalized==body[payment.JOURNAL_KEY] and normalized is not body[payment.JOURNAL_KEY],'Production normalizer journal interpretation changed')
    require(normalized['current_session']['controlled_window_id']==1 and normalized['sampling']['epoch']==1,'Fresh explicit Root window/epoch binding differs')
    witness=get(A+f'day{day}/GENERIC-RAW-WITNESSES.actual.json')[0]['raw_record']
    actual=[r for r in normalized['records'] if r['journal_sequence']==12]
    require(len(actual)==1 and actual[0]==witness,'Raw archived seq12 differs from unique canonical witness')
# Check original source and child archives by their exact index; historical executors are data only.
for index in ['SOURCE-ATTEMPTS-ARCHIVE-INDEX.json','CALLEE-ORIGINAL-ARCHIVE-INDEX.json']:
    indexed=get(A+index)
    with zipfile.ZipFile(resolve(indexed['archive']['path'])) as archive:
        require(set(archive.namelist())==set(i['member'] for i in indexed['members']),'Indexed archive members differ')
        for item in indexed['members']:
            raw=archive.read(item['member']);require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'Indexed source archive member bytes differ')
doc_path='docs/ck3-native-ai/war-payment-r0174-actual-parent-source-12004.md'
text=resolve(doc_path).read_text(encoding='utf-8')
for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
    target=target.split('#',1)[0]
    if not target or '://' in target:continue
    parts=Path(doc_path).parent/urllib.parse.unquote(target)
    require(resolve(parts).is_file(),'Canonical document link not held '+str(parts))
if ARGS.extract_source_attempts is not None:
    destination=ARGS.extract_source_attempts.resolve();require(not destination.exists(),'Append-only extraction target exists');destination.mkdir(parents=True)
    indexed=get(A+'SOURCE-ATTEMPTS-ARCHIVE-INDEX.json')
    with zipfile.ZipFile(resolve(indexed['archive']['path'])) as archive:
        for item in indexed['members']:
            relative=Path(item['member']);require(not relative.is_absolute() and '..' not in relative.parts,'Unsafe archive path')
            target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(archive.read(item['member']))
print(json.dumps(dict(status='PASS',production_normalizer_replays=2,raw_zip_members=4,document_links='all held',source_archives_verified=2,optimization=sys.flags.optimize,catalog_files=len(CAT['files']),unique_actual_callback_count=1,explicit_Root_window_epoch_recheck=True,maintenance_attribution='unclosed',new_runtime_actions=0),ensure_ascii=False))
