from pathlib import Path
import hashlib, json, zipfile

root = Path(__file__).resolve().parent
index = json.loads((root / 'source-index.json').read_bytes())
archive = root / index['archive']['path']
raw = archive.read_bytes()
if len(raw) != index['archive']['bytes'] or hashlib.sha256(raw).hexdigest() != index['archive']['sha256']:
    raise ValueError('archive pin')
with zipfile.ZipFile(archive) as z:
    if set(z.namelist()) != {r['member'] for r in index['originals']}:
        raise ValueError('member set')
    for row in index['originals']:
        b = z.read(row['member'])
        if len(b) != row['bytes'] or hashlib.sha256(b).hexdigest() != row['sha256']:
            raise ValueError(row['member'])
    ui = json.loads(z.read('ARMY93-UI-SELECT.actual-a01.json'))
    correction = json.loads(z.read('R192-UI-CUNIT-CARMY-CORRECTION.actual-a02.json'))
    frame = json.loads(z.read('r192-pre-film-frame-a01.actual.json'))
    review = json.loads(z.read('R09-FRAME-REVIEW.actual-a01.json'))
    for row in [ui, correction, frame, review]:
        if row['machine_id'] != index['machine_id'] or row['source_head'] != index['source_head'] or row['run_id'] != ui['run_id'] or row['identity'] != ui['identity']:
            raise ValueError('identity scope')
    if ui['selected_army_id'] != 93 or ui['native_carmy_id_from_actual_baseline'] != 85 or correction['selected_army_id'] != 93 or correction['native_carmy_id_from_actual_baseline'] != 85:
        raise ValueError('distinct ID spaces')
    for ref, member in [(correction['sealed_UI_receipt'], 'ARMY93-UI-SELECT.actual-a01.json'), (review['native_army_UI_receipt'], 'ARMY93-UI-SELECT.actual-a01.json'), (review['original_frame'], 'r192-pre-film-frame-a01.actual.json')]:
        b = z.read(member)
        if ref['bytes'] != len(b) or ref['sha256'] != hashlib.sha256(b).hexdigest():
            raise ValueError('receipt reference')
    if review['human_approval'] or review['business_or_clean_span_qualified']:
        raise ValueError('scope changed')
print(json.dumps({'status': 'PASS', 'machine_id': index['machine_id'], 'members': len(index['originals']), 'public_id': 93, 'native_id': 85, 'raw_or_images_reopened': 0, 'baseline_and_UI_packet_replay': False, 'SDK_calls': 0}))
