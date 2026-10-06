"""Seal two actual same-file OneDrive client InSync metadata samples.

Only reads bounded local receipts. Does not read movie bytes, contact cloud,
hydrate content, change sync settings or infer human signoff.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('C:/ck3-war-episode04-research-20261004-a01')
DELIVERY = Path('C:/ck3-war-episode04-delivery-20261006-a01')
COPY = DELIVERY / 'attempts/review01-actual-copy-a01/04-local-copy-verified.json'
SHA = 'a1abb0f2abaa06f3fd38839123e9f4ddd4c4218f8dd15e0965732d3596c69346'
BYTES = 1199061934
TARGET = Path('C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-War-AI-Episode04-March-Logistics-Review01.mp4')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def read_pin(path):
    path = Path(path)
    require(path.is_file() and path.stat().st_size < 1_000_000, 'Bounded receipt required')
    raw = path.read_bytes()
    return json.loads(raw.decode('utf-8-sig')), {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

require(len(sys.argv) == 3, 'Supply two actual successful metadata receipt paths')
copy, copy_pin = read_pin(COPY)
require(copy['status'] == 'LOCAL_COPY_VERIFIED_CLOUD_PENDING' and copy['file_count'] == 1, 'Actual single file verified copy required')
for subject in (copy['source'], copy['target']):
    require(subject['bytes'] == BYTES and subject['sha256'].lower() == SHA, 'Wrong exact movie bytes/SHA')
require(Path(copy['target']['path']) == TARGET and copy['copy_stream_bytes'] == BYTES and copy['copy_stream_sha256'].lower() == SHA, 'Copy target/stream differs')
samples, pins = [], []
for name in sys.argv[1:]:
    sample, pin = read_pin(name)
    require(sample['status'] == 'CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED' and sample['client_metadata_in_sync'] is True, 'Actual client InSync sample required')
    require(sample['target'] == copy['target'] and sample['independent_remote_readback'] is False and sample['content_read'] is False, 'Target/evidence scope differs')
    meta = sample['metadata']
    require(meta['sync_root_hresult'] == meta['placeholder_hresult'] == '0x00000000', 'CloudFiles HRESULT failure')
    require(meta['sync_root_file_id'] == 5910974510929700 and meta['in_sync_state'] == 1, 'Wrong syncroot/InSync state')
    require(meta['size'] == meta['on_disk'] == meta['validated'] == BYTES and meta['modified'] == 0 and meta['stable_size_mtime'] is True, 'Resident/validated/modified metadata differs')
    require(meta['file_id'] > 0 and Path(meta['path']) == TARGET, 'Invalid target file identity')
    samples.append(sample)
    pins.append(pin)
first, second = (s['metadata'] for s in samples)
require((first['file_id'],first['size'],first['mtime_ns']) == (second['file_id'],second['size'],second['mtime_ns']), 'Two samples do not bind one stable file')
delta = (datetime.fromisoformat(second['sample_utc']) - datetime.fromisoformat(first['sample_utc'])).total_seconds()
require(delta >= 10, 'Two success samples must be at least10seconds apart')
audit, audit_pin = read_pin(BASE / 'e4-Review01-whole-machine-audit-a01/attempt-a02/report.json')
coded, coded_pin = read_pin(BASE / 'e4-Review01-Root-actual-coded18-review-a01/Root-coded18-NO-BLOCK.json')
require(audit['state'] == 'PASS_MACHINE_STRUCTURE_COUNTS_AND_EXACT_AAC_CLOCK_ONLY' and not audit['errors'], 'Actual wholefilm audit PASS required')
require(coded['state'] == 'ROOT_ACTUAL_18_CODED_IMAGE_REVIEW_NO_BLOCK' and len(coded['samples']) == 18 and not coded['blockers'], 'Actual Root18 image review required')
require(audit['actual_movie_identity_reused']['sha256'].lower() == coded['movie']['sha256'].lower() == SHA, 'Audit/image/movie bindings differ')
out = DELIVERY / 'Review01-actual-client-delivery-a01'
out.mkdir(exist_ok=False)
result = {'schema':'xar.e04.actual-Review01-OneDrive-client-delivery.v1',
          'state':'REVIEW01_LOCAL_SHA_AND_CLIENT_METADATA_IN_SYNC_VERIFIED',
          'created_utc':datetime.now(timezone.utc).isoformat(), 'movie':copy['target'],
          'local_copy':copy_pin,'actual_client_metadata_samples':pins,'metadata_interval_seconds':delta,
          'actual_client_file_id':first['file_id'],'actual_sync_root_file_id':first['sync_root_file_id'],
          'whole_movie_machine_audit':audit_pin,'Root_actual_coded18_image_review':coded_pin,
          'single_video_files_copied':1,'settings_changed':False,'other_cloud_content_downloaded':False,
          'local_source_copy_stream_and_target_SHA_verified':True,'client_metadata_in_sync':True,
          'independent_remote_readback':False,'remote_SHA_verified':False,
          'human_full_1x_review':False,'human_signoff':False,
          'evidence_scope':'Exact local bytes/SHA verified; two stable client CloudFiles InSync samples. Independent cloud remote readback and human full1x review remain unverified.',
          'final_Git_commit_or_CI_assessed_in_this_receipt':False}
path = out / 'Root-actual-OneDrive-delivery.json'
with path.open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps(read_pin(path)[1],ensure_ascii=False))
