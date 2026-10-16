"""Stdlib frozen tier source and same-source caller comparison; no game access."""
from pathlib import Path
from io import BytesIO
import argparse, base64, hashlib, json, re, zipfile, zlib

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def pin(raw, row, label):
    need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Pin differs: ' + label)

def load(path, name):
    p = Path(path)
    if p.suffix == '.patch':
        pieces = [s for s in p.read_text(encoding='utf-8').split('diff --git ')[1:]
                  if any(l == '+++ b/' + name for l in s.splitlines())]
        need(len(pieces) == 1 and 'new file mode 100644\n' in pieces[0], 'Complete new-file JSON required')
        raw = ''.join(l[1:] for l in pieces[0].splitlines(keepends=True)
                      if l.startswith('+') and not l.startswith('+++')).encode('utf-8')
    else:
        raw = p.read_bytes()
    return raw, json.loads(raw)

def original(row):
    raw = base64.b64decode(row['payload'], validate=True)
    need(row['encoding'] in ('base64', 'zlib+base64'), 'Unknown encoding')
    if row['encoding'] == 'zlib+base64':
        raw = zlib.decompress(raw)
    pin(raw, row, row['id'])
    return raw

def verify(bundle_path, prior_path):
    member = 'docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/classifier-tier-a06.json'
    _, b = load(bundle_path, member)
    prior_raw, prior = load(prior_path, 'docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/local88-components-a05.json')
    pin(prior_raw, b['prior'], 'd05 local88 bundle')
    originals = {r['id']: original(r) for r in b['originals']}
    need(len(originals) == len(b['originals']), 'Duplicate original ID')
    index = json.loads(originals['PORTABLE-INDEX.json'])
    source = json.loads(originals['SOURCE.actual.json'])
    image = '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
    need(b['image']['sha256'] == source['exe_sha256'] == prior['image']['sha256'] == image, 'Exact image differs')
    for name in ('SOURCE.actual.json', 'INVENTORY.actual.json', 'CALLER-INTAKE.actual.json', 'CAPTURE.actual.json', 'PORTABLE-VERIFY.actual.json'):
        need(json.loads(originals[name])['machine_id'] == b['source_machine_id'], 'Source machine differs')
    need(index['machine_id'] == b['source_machine_id'], 'Index machine differs')
    for row in index['files']:
        pin(originals[row['path']], row, row['path'])
    pin(originals['source-originals.zip'], source['source_archive'], 'SOURCE archive')
    with zipfile.ZipFile(BytesIO(originals['source-originals.zip'])) as z:
        need(len(z.namelist()) == len(set(z.namelist())) and set(z.namelist()) == set(index['archive_members']), 'Archive member set')
        for name, row in index['archive_members'].items():
            pin(z.read(name), row, name)
        body = z.read('tier/function.bin')
        rows = json.loads(z.read('tier/instructions.json'))
        need(len(body) == 140 and sha(body) == '3d26d52728b38c190784831f080f6278c4ee10fde30bb3927f6b033afe5eb5b2', 'Exact140 differs')
        cursor, starts = 0x28AC690, set()
        for row in rows:
            raw = bytes.fromhex(row['hex'])
            need(row['rva'] == cursor and body[cursor-0x28AC690:cursor-0x28AC690+len(raw)] == raw, 'Instruction coverage differs')
            starts.add(cursor)
            cursor += len(raw)
        need(len(rows) == 41 and cursor == 0x28AC71C, 'Complete140 extent differs')
        jumps = []
        for row in rows:
            if row['mnemonic'].startswith('j'):
                raw = bytes.fromhex(row['hex'])
                need(len(raw) == 2 and (0x70 <= raw[0] <= 0x7f or raw[0] == 0xeb), 'Short branch differs')
                target = row['rva'] + 2 + int.from_bytes(raw[1:], 'little', signed=True)
                need(target in starts and target == int(row['operands'], 16), 'Internal branch target differs')
                jumps.append(row)
        need(len(jumps) == 11 and [r['rva'] for r in rows if r['mnemonic'] == 'ret'] == [0x28AC6F8, 0x28AC6F9, 0x28AC71B], 'Branches/RET differ')
        need(not any(r['mnemonic'] == 'call' for r in rows), 'Unexpected CALL')
        for at, hx in {0x28AC690:'488b81c0010000', 0x28AC69C:'488b81d0010000', 0x28AC6B6:'baffffffff', 0x28AC6E5:'395010', 0x28AC6F1:'488b4048', 0x28AC6F5:'8b4064', 0x28AC6FA:'8b88d4010000', 0x28AC700:'83f907', 0x28AC703:'7514', 0x28AC719:'8bc1'}.items():
            expected = bytes.fromhex(hx)
            need(body[at-0x28AC690:at-0x28AC690+len(expected)] == expected, 'Tier path literal differs')
        previous = {r['id']: r for r in prior['originals']}
        need(z.read('caller/SOURCE.actual.json') == original(previous['classifier-source']), 'Caller SOURCE differs from d05')
        need(z.read('caller/TYPE-WIDTH-CORRECTION.actual.json') == original(previous['classifier-width-correction']), 'Historical DWORD correction differs')
        with zipfile.ZipFile(BytesIO(original(previous['classifier-archive']))) as old:
            caller = old.read('function.bin')
        need(z.read('caller/function.bin') == caller and len(caller) == 693, 'Same-source caller693 differs')
        expected_caller = {0x2C6AA4E:'80b8d604000005', 0x2C6AA55:'7533', 0x2C6AA5F:'498bce', 0x2C6AA65:'e8261cc4ff', 0x2C6AA6A:'3b83cc0400007c45', 0x2C6AA72:'b801000000', 0x2C6AAB7:'b802000000'}
        for at, hx in expected_caller.items():
            raw = bytes.fromhex(hx)
            need(caller[at-0x2C6A810:at-0x2C6A810+len(raw)] == raw, 'Caller gate/ABI/compare/result differs')
        call = caller[0x2C6AA65-0x2C6A810:0x2C6AA6A-0x2C6A810]
        need(0x2C6AA6A + int.from_bytes(call[1:], 'little', signed=True) == 0x28AC690, 'Incoming target differs')
        need(0x2C6AA72 + 0x45 == 0x2C6AAB7, 'Signed JL target differs')
        for row in source['repository_inputs']:
            relative = row['path'].replace('\\', '/').split('/ck3_eternal_recurrence/', 1)[1]
            raw = z.read('repo/' + relative)
            pin(raw, row, relative)
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()
            need(blob == row['git_blob'], 'Exact typed Git blob differs: ' + relative)
        reader = z.read('repo/ck3_autonomous_player/native_bridge/src/appointment_character_level12004.cpp').decode('utf-8-sig')
        need('if (s.candidate_tier != 7)' in reader and 'return s.candidate_tier >= 0 && s.candidate_tier <= 6;' in reader and 'full_id != s.candidate_title_id' in reader, 'Guarded source boundary differs')
    need(source['native_cache_range_clamped'] is False and source['guarded_reader_accepted_range'] == [0, 6], 'Native/guard distinction differs')
    need(source['new_code_bytes'] == 140 and source['new_metadata_bytes'] == 0 and source['new_read_calls'] == 1, 'Original read charge differs')
    need(b['business']['maintenance_attribution'] == 'unclosed' and all(b['business'][k] is None for k in ('paid_military_amount_raw', 'cadence', 'currency')) and b['new_live_credit'] == 0, 'Business scope elevated')
    return dict(status='PASS', scope='frozen source integrity and same-source caller composition', source_machine_id=b['source_machine_id'], originals_verified=len(originals), exact_code_bytes=140, instructions=41, internal_short_jumps=11, normal_rets=3, typed_git_blobs_verified=5, same_source_caller_bytes=693, incoming_CALL_and_signed_DWORD_branch=True, native_cache_range_clamped=False, guarded_reader_range=[0,6], semantic_correctness_verified=False, live_execution_performed=False, new_EXE_reads=0, new_live_credit=0, maintenance_attribution='unclosed', paid_military_amount_raw=None, cadence=None)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=Path(__file__).with_name('classifier-tier-a06.json'))
    p.add_argument('--prior-bundle', type=Path, default=Path(__file__).with_name('local88-components-a05.json'))
    p.add_argument('--extract-originals', type=Path)
    a = p.parse_args()
    result = verify(a.bundle, a.prior_bundle)
    if a.extract_originals:
        need(not a.extract_originals.exists(), 'Exclusive extraction directory required')
        _, b = load(a.bundle, 'docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/classifier-tier-a06.json')
        a.extract_originals.mkdir(parents=True, exist_ok=False)
        for row in b['originals']:
            need(re.fullmatch(r'[A-Za-z0-9_.-]+', row['id']) is not None, 'Unsafe original name')
            with (a.extract_originals / row['id']).open('xb') as f:
                f.write(original(row))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == '__main__':
    main()
