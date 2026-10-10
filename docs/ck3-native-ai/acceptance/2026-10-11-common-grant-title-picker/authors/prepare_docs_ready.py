"""Create a compact byte-preserving docs import package; never write MAIN."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE/'docs-ready-001'
ACCEPTANCE = 'docs/ck3-native-ai/acceptance/2026-10-11-common-grant-title-picker'
TOPIC = 'docs/ck3-native-ai/2026-10-11-common-grant-title-picker.md'

# Explicit finite selection. No production source tree, saves, wires, binaries,
# large reports or already-published unrelated history is selected.
SELECTED = [
    ('INDEX.json', 'SOURCE-INDEX.original.json'),
    ('REPORT.md', 'REPORT.source-only.md'),
    ('FUTURE-MANIFEST.fragment.json', 'FUTURE-MANIFEST.fragment.json'),
    ('candidate-002/PUBLIC-GRANT.incremental.patch', 'integration/PUBLIC-GRANT.incremental.patch'),
    ('candidate-002/INTEGRATION-MANIFEST.json', 'integration/INTEGRATION-MANIFEST.json'),
    ('candidate-001/INTEGRATION-MANIFEST.json', 'original-attempt/INTEGRATION-MANIFEST.json'),
    ('ci-001/PUBLIC-GRANT-CI.incremental.patch', 'ci/PUBLIC-GRANT-CI.incremental.patch'),
    ('ci-001/INTEGRATION-MANIFEST.json', 'ci/INTEGRATION-MANIFEST.json'),
    ('focused-001/RESULT.actual.json', 'focused-001/RESULT.actual.json'),
    ('focused-001/stdout.log', 'focused-001/stdout.log'),
    ('focused-001/stderr.log', 'focused-001/stderr.log'),
    ('focused-001/test-source.original.py', 'focused-001/test-source.original.py'),
    ('focused-002/RESULT.actual.json', 'focused-002/RESULT.actual.json'),
    ('focused-002/stdout.log', 'focused-002/stdout.log'),
    ('focused-002/stderr.log', 'focused-002/stderr.log'),
    ('prepare_candidate.py', 'authors/prepare_candidate.py'),
    ('prepare_ci.py', 'authors/prepare_ci.py'),
    ('run_focused.py', 'authors/run_focused.py'),
    ('finish_candidate.py', 'authors/finish_candidate.py'),
    ('run_changed_metadata.py', 'authors/run_changed_metadata.py'),
    ('seal_packet.py', 'authors/seal_packet.py'),
    ('prepare_docs_ready.py', 'authors/prepare_docs_ready.py'),
]


def digest(raw: bytes) -> dict:
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) > 1024**2:
        raise ValueError('Selected record exceeded the 1 MiB cap')
    return {'path': str(path), **digest(raw)}


def create(relative: str, raw: bytes) -> dict:
    path = OUT/relative
    if path.resolve().is_relative_to(OUT.resolve()) is not True:
        raise ValueError('Import path escapes create-only package')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)
    actual = pin(path)
    if any(actual[key] != digest(raw)[key] for key in ('bytes','sha256')):
        raise ValueError('Copied record differs from selected raw bytes')
    return {'relative_path': relative, 'source_path': str(path),
            'before': None, 'after': digest(raw), 'create_only': True}


def main():
    original = json.loads((HERE/'INDEX.json').read_text(encoding='utf-8'))
    expected = {Path(row['path']).resolve(): row for row in original['files']}
    # A source script added after the original INDEX is directly pinned below;
    # every already-sealed selected raw is checked against the original pins.
    OUT.mkdir(exist_ok=False)
    imports, archived = [], []
    for source, relative in SELECTED:
        path = HERE/source
        raw = path.read_bytes()
        if len(raw) > 1024**2:
            raise ValueError('Selected raw record exceeded cap')
        prior = expected.get(path.resolve())
        if prior and any(digest(raw)[key] != prior[key] for key in ('bytes','sha256')):
            raise ValueError('Sealed source changed: '+source)
        target = ACCEPTANCE+'/'+relative
        imports.append(create(target, raw))
        archived.append({'original': {'path': str(path), **digest(raw)},
                         'archive_relative_path': relative,
                         'repository_relative_path': target,
                         'byte_exact_copy': True})
    attributes = b'* -text\n'
    imports.append(create(ACCEPTANCE+'/.gitattributes', attributes))
    # The new topic alone is rendered as LF Markdown. Preserve the B candidate.
    topic = (HERE/'TOPIC.candidate.md').read_text(encoding='utf-8')
    old = '外置证据包为 `C:/workspace/ck3_lyd_runtime_20261004/c3-common-grant-public-route-sourceonly-20261011-001`。'
    new = ('[永久原始回执与字节索引](acceptance/2026-10-11-common-grant-title-picker/INDEX.actual.json)'
           '保留首轮失败和单项后继；外置来源包为 '
           '`C:/workspace/ck3_lyd_runtime_20261004/c3-common-grant-public-route-sourceonly-20261011-001`。')
    if topic.count(old) != 1:
        raise ValueError('Topic source backlink preimage changed')
    topic = topic.replace(old,new,1).replace('\r\n','\n')
    if 'acceptance/2026-10-11-common-grant-title-picker/INDEX.actual.json' not in topic:
        raise ValueError('Required permanent topic backlink absent')
    imports.append(create(TOPIC, topic.encode('utf-8')))
    copied = {Path(row['original']['path']).resolve() for row in archived}
    references = [row for row in original['files'] if Path(row['path']).resolve() not in copied]
    index = {
        'schema':'lyd.common-grant-title-picker-permanent-evidence.v1',
        'status':'STATIC_READY_LIVE_NOT_RUN', 'reviewed_source_head':original['MAIN_head'],
        'original_source_index':pin(HERE/'INDEX.json'), 'files':archived,
        'external_references_only':references+original['source_inputs'],
        'qualification':original['qualification'],
        'readonly_apply_check':original['readonly_apply_check'],
        'production_and_test_patch':next(row for row in archived
            if row['archive_relative_path']=='integration/PUBLIC-GRANT.incremental.patch'),
        'future_source_head':None, 'future_runtime_key':None, 'future_title_full_id':None,
        'business_credit':None, 'existing_O13_R54_unchanged':True,
        'MAIN_mutations':0, 'SDK_calls':0, 'game_calls':0, 'native_builds':0,
        'overall_status':'75_PERCENT_ESTIMATE_NOT_GREEN',
        'retention':original['retention'],
        'no_source_tree_or_large_runtime_bodies':True,
    }
    index_raw = (json.dumps(index,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    if len(index_raw)>65536:
        raise ValueError('Permanent compact index exceeded 64 KiB')
    imports.append(create(ACCEPTANCE+'/INDEX.actual.json', index_raw))
    total = sum(row['after']['bytes'] for row in imports)
    if total > 512*1024:
        raise ValueError('Docs-ready selection exceeded 512 KiB budget')
    manifest = {
        'schema':'lyd.common-grant-title-picker-create-only-import.v1',
        'status':'PREPARED_NOT_IMPORTED', 'reviewed_source_head':original['MAIN_head'],
        'expected_repository_root':'C:/workspace/ck3_eternal_recurrence',
        'source_package_index':pin(HERE/'INDEX.json'),
        'topic_target':TOPIC, 'acceptance_index_target':ACCEPTANCE+'/INDEX.actual.json',
        'files':imports, 'file_count':len(imports), 'total_bytes':total,
        'all_destination_preimages':None, 'require_every_destination_absent':True,
        'raw_copy_policy':'exact bytes; local .gitattributes * -text; only new topic rendered LF',
        'production_source_mutations':0, 'MAIN_mutations':0, 'tests_repeated':False,
        'source_diff_order':['candidate-002/PUBLIC-GRANT.incremental.patch',
                             'ci-001/PUBLIC-GRANT-CI.incremental.patch'],
        'future_adoption_commit':None, 'future_live_credit':None,
    }
    with (OUT/'IMPORT-MANIFEST.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(manifest,stream,indent=2,ensure_ascii=False)
        stream.write('\n')
    result = {'schema':'lyd.common-grant-title-picker-docs-ready-result.v1',
        'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'exit_code':0, 'status':'PREPARED_NOT_IMPORTED',
        'IMPORT_MANIFEST':pin(OUT/'IMPORT-MANIFEST.json'),
        'permanent_index':pin(OUT/ACCEPTANCE/'INDEX.actual.json'),
        'topic':pin(OUT/TOPIC), 'file_count':len(imports), 'total_bytes':total,
        'one_pass_selected_copy_readback_exact':True, 'MAIN_mutations':0,
        'tests_repeated':False}
    with (OUT/'RESULT.actual.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
