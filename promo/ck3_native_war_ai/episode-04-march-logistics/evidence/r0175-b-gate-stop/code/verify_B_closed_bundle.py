"""Offline small-file B gate-stop bundle verifier. Default PLAN; no locator opens."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[4]
SCOPES = (
    'promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/',
    'promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap/',
)
DOCS = {
    'docs/ck3-native-ai/army-episode04-B-gate-stopped-12003.md',
    'docs/ck3-native-ai/army-r0175-B-merge-upper-cap-runtime-12003.md',
}


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def small_file(repo, relative, expected=None):
    parsed = PurePosixPath(relative)
    need(not parsed.is_absolute() and relative == parsed.as_posix()
         and '..' not in parsed.parts and ':' not in relative and '\\' not in relative,
         'unsafe relative source path')
    need(relative in DOCS or relative.startswith(SCOPES), 'path outside the two closed B scopes')
    path = repo.joinpath(*parsed.parts)
    need(not any(p.is_symlink() for p in (path, *path.parents) if p != repo.parent), 'symlink source forbidden')
    path = path.resolve(strict=True)
    need(path.is_relative_to(repo.resolve()) and path.is_file(), 'source leaves archive')
    need(path.suffix.lower() in {'.json', '.py', '.md', '.bin', '.txt', ''}, 'media/save/binary source forbidden')
    need(path.stat().st_size < 1048576, 'not a small source')
    raw = path.read_bytes()
    if expected is not None:
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'],
             'source bytes/SHA differ: ' + relative)
    return raw


def json_leaf(relative):
    return json.loads((HERE / relative).read_bytes())


def load_consumer(relative):
    path = HERE / relative
    spec = importlib.util.spec_from_file_location('B_bundle_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(repo=REPO):
    repo = repo.resolve(strict=True)
    manifest = json_leaf('bundle-manifest.json')
    need(manifest['schema'] == 'ck3.e04.B.closed-bundle-files.v1', 'unsupported bundle manifest')
    seen = set()
    for row in manifest['files']:
        need(row['repo_relative_path'] not in seen, 'duplicate source pin')
        seen.add(row['repo_relative_path'])
        small_file(repo, row['repo_relative_path'], row)
    index = json_leaf('INDEX.json')
    copied = json_leaf('source-copy-catalog.json')
    need(len(copied['sources']) == 132 and len({r['repo_relative_path'] for r in copied['sources']}) == 132,
         'original closed-source inventory differs')
    need(all(row['repo_relative_path'] in seen for row in copied['sources']), 'copied source absent')
    need(all(next(r for r in manifest['files'] if r['repo_relative_path'] == row['repo_relative_path'])['sha256']
             == row['sha256'] for row in copied['sources']), 'original source was rewritten')
    closed_module = load_consumer('closed-terminal/code/verify_B_closed_terminal.py')
    closed = closed_module.verify()
    need(closed == json_leaf('closed-terminal/B-closed-terminal-values.json'), 'closed metadata projection differs')
    media_module = load_consumer('media-review/code/verify_B_S02_metadata.py')
    media = media_module.derive(HERE / 'media-review')
    need(media == json_leaf('media-review/B-S02-media-review-values.json'), 'media metadata projection differs')
    base = json_leaf('merge-exception/B-merge-exception-values.json')
    terminal = json_leaf('closed-terminal/terminal-stage/inputs/terminal.json')
    release = json_leaf('source-events/actual-release.json')
    release_raw = json_leaf('closed-terminal/inputs/B-release-stdout.bin')
    need(release['actual_returncode'] == 0 and release['actual_release'] == release_raw
         and release['expected_keeper_last_sequence'] == 5113, 'Root release wrapper differs from exact stdout')
    stdout = (HERE / 'closed-terminal/inputs/B-release-stdout.bin').read_bytes()
    need(release['original_stdout']['bytes'] == len(stdout)
         and release['original_stdout']['sha256'] == hashlib.sha256(stdout).hexdigest(), 'release original pin differs')
    need(base['episode_run_id'] == terminal['episode_run_id'] == 'native-33388-23726fbd8a80'
         and base['actual_raw'] == terminal['observed_stop_raw'] == 53149344, 'same B/date join fails')
    need(base['global_END'] == terminal['absolute_end_raw'] == 53150592
         and terminal['start_raw'] == 53148432
         and (53149344 - 53148432) // 24 == closed['days_used'] == 38
         and (53150592 - 53149344) // 24 == closed['remaining_days'] == 52, '90-day budget was reset')
    need(base['commander_preserved'] is False and base['original27_entire_rows_unchanged'] is True
         and base['original37_DATA_entire_row_diffs'] == []
         and base['post_metrics']['regiment_count'] == 28
         and base['post_metrics']['current_soldiers'] == 6690
         and base['post_metrics']['maximum_soldiers'] == 6748, 'recorded merge gate failure differs')
    need(base['new_regiment_entire_row']['army_regiment_id'] == 16778273
         and base['new_regiment_entire_row']['current_soldiers'] == base['new_regiment_entire_row']['maximum_soldiers'] == 1
         and base['new_unit_type_knight_or_cause'] is None, 'new unit type/cause was inferred')
    local_catalog = HERE / 'merge-exception/manifest-final-a02.json'
    linked = json_leaf('closed-terminal/terminal-stage/B-terminal-append-values.json')
    # The terminal package records the old base by pin; the native observer is preserved, not run.
    base_catalog_sha = hashlib.sha256(local_catalog.read_bytes()).hexdigest()
    need(base_catalog_sha == '4b1666df2a17a075e7d5f6ac79e9493f7b4492cd592fcf5088aca1d0b484dc64'
         and linked['preserved_base_catalog']['sha256'] == base_catalog_sha
         and linked['preserved_base_catalog']['bytes'] == local_catalog.stat().st_size
         and (HERE / 'closed-terminal/terminal-stage/inputs/base-73-pin-catalog.json').read_bytes()
             == local_catalog.read_bytes(), 'closed terminal base catalogue join differs')
    math_path = repo / 'promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap'
    arithmetic = json.loads((math_path / 'arithmetic-result.json').read_bytes())
    need(arithmetic['arithmetic']['preclamp_raw'] == 11306109
         and arithmetic['observed_post_stock_raw'] == arithmetic['observed_post_capacity_raw'] == 10000000,
         'bounded upper-cap arithmetic differs')
    observed = {
        'B_disposition': 'STOPPED_GATE_INCOMPLETE',
        'episode_run_id': terminal['episode_run_id'],
        'start_raw': 53148432, 'stopped_raw': 53149344, 'absolute_end_raw': 53150592,
        'actual_days_used': 38, 'remaining_days': 52, 'deadline_reached': False,
        'frozen_cohort_gate_pass': False, 'commander_preserved': False,
        'actual_owned_runtime_closed': True, 'actual_release_sequence': 5115,
        'original_pending_fields_retained': True,
        'B_London_endpoint': None, 'C_terminal': None, 'winner': None,
        'S02_machine_audit': 'PASS', 'S02_reviewed_single_frames': 3,
        'continuous_clean_span': None, 'human_1x_complete_watch': False, 'human_signoff': False,
        'new_unit_type_or_cause': None,
    }
    need(index['observed'] == observed, 'INDEX overstates or changes the closed outcome')
    return {'status': 'PASS_CLOSED_B_RELATIVE_SMALL_BYTES_AND_METADATA_JOINS',
            'source_files_preserved': 132, 'bundle_files_verified': len(seen),
            'observed': observed, 'native_cohort_observer_reexecuted': False,
            'referenced_media_or_PNG_opened': False, 'Game_SDK_UI_Git_actions': 0,
            'original_manifest_values_pending_fields_rewritten': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        print(json.dumps({'status': 'PLAN_ONLY_NO_SOURCE_READS', 'entry': '--verify', 'side_effects': 0}))
        return 0
    try:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as exc:
        print(json.dumps({'status': 'FAIL_CLOSED_B_BUNDLE_METADATA', 'reason': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
