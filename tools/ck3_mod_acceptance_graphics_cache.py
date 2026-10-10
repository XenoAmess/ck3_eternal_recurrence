"""Explicit derivative DX11 input snapshots; never grants startup/business credit."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat

FEATURE = 'shader_cache_reuse'
ORIGIN_SCHEMA = 'ck3-mod-acceptance-shader-cache-origin-v1'
SEED_SCHEMA = 'ck3-mod-acceptance-shader-cache-seed-v1'
PREPARED_SCHEMA = 'ck3-mod-acceptance-prepared-graphics-cache-v1'
QUALIFICATION = 'DERIVATIVE_GRAPHICS_CANDIDATE_NOT_LIVE_NOT_PRODUCT_PASS'
CONFIGS = ('pdx_settings.txt', 'tutorial.txt', 'presets.txt', 'player/game_rules/presets.txt')
PREPARE_ONLY_PATHS = frozenset({
    'tools/ck3_mod_acceptance.py', 'tools/ck3_mod_acceptance_allocate.py',
    'tools/ck3_mod_acceptance_graphics_cache.py', 'tools/test_ck3_mod_acceptance_graphics_cache.py',
})
CACHE_NAME = re.compile(r'dx11/(?:ps_5_0|vs_5_0)/[0-9A-Fa-f]{16}\.(?:bin|scache)')
SHA = re.compile(r'[0-9a-f]{64}')


def require(value, message):
    if not value:
        raise ValueError(message)


def profile_enabled(manifest):
    features = manifest.get('profile_features', {})
    require(isinstance(features, dict) and set(features) <= {FEATURE}, 'Unknown shared profile feature')
    require(all(type(value) is bool for value in features.values()), 'Shared profile features require booleans')
    return features.get(FEATURE, False)


def _pairs(rows):
    value = {}
    for key, item in rows:
        require(key not in value, 'Duplicate JSON key: ' + key)
        value[key] = item
    return value


def _read(path):
    value = json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=_pairs)
    require(isinstance(value, dict), 'JSON object required')
    return value


def _signature(row):
    require(isinstance(row, dict) and type(row.get('bytes')) is int and row['bytes'] >= 0 and
            isinstance(row.get('sha256'), str) and SHA.fullmatch(row['sha256']), 'Exact bytes/SHA required')
    return {key: row[key] for key in ('bytes', 'sha256')}


def _plain_path(path, *, directory=False):
    path = Path(path).absolute()
    for parent in [*reversed(path.parents), path]:
        info = parent.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'Links/reparse points are forbidden: ' + str(parent))
    info = path.stat()
    if directory:
        require(stat.S_ISDIR(info.st_mode), 'Ordinary directory required: ' + str(path))
    else:
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'Ordinary unlinked file required: ' + str(path))
    return path


def _pin(path):
    path = _plain_path(path)
    digest = hashlib.sha256()
    length = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            length += len(block)
            digest.update(block)
    return {'path': str(path.resolve()), 'bytes': length, 'sha256': digest.hexdigest()}


def _checked(row):
    require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'} and
            isinstance(row['path'], str) and Path(row['path']).is_absolute(), 'Exact typed absolute file pin required')
    actual = _pin(row['path'])
    require(actual == row, 'Pinned input changed: ' + row['path'])
    return _read(row['path'])


def _relative(value):
    require(isinstance(value, str) and value and '\\' not in value and ':' not in value and
            not PurePosixPath(value).is_absolute() and not PureWindowsPath(value).is_absolute() and
            all(part not in ('', '.', '..') for part in value.split('/')), 'Path escape or noncanonical relative path')
    return value


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def business_files(preparation):
    rows = (preparation.get('profile', {}).get('files') or
            preparation.get('fixtures', {}).get('profile', {}).get('files') or preparation.get('files'))
    require(isinstance(rows, dict) and rows, 'Declared business profile inventory required')
    for relative, row in rows.items():
        _relative(relative)
        _signature(row)
        require(not relative.casefold().startswith('shadercache/'), 'Business inventory cannot smuggle graphics cache')
    require(len({key.casefold() for key in rows}) == len(rows), 'Duplicate business paths')
    return rows


def _profile_key(rows, profile, read_root):
    profile, read_root = Path(profile).resolve(), _plain_path(read_root, directory=True)
    for relative, expected in rows.items():
        require(_signature(_pin(read_root / relative)) == _signature(expected), 'Business bytes changed before graphics key')
    require(all(name in rows for name in CONFIGS) and 'dlc_load.json' in rows, 'Four configurations and DLC profile required')
    canonical = {key: _signature(row) for key, row in rows.items() if key.startswith('mod-content/')}
    require(canonical, 'Complete canonical mod inventory required')
    outer_names = [key for key in rows if key.startswith('mod/')]
    enabled = _read(read_root / 'dlc_load.json').get('enabled_mods')
    require(isinstance(enabled, list) and len(enabled) == 2 and
            all(isinstance(name, str) and re.fullmatch(r'mod/[A-Za-z0-9_][A-Za-z0-9_-]*\.mod', name)
                for name in enabled), 'Exactly two explicitly enabled canonical outer descriptors required')
    require(len({name.casefold() for name in enabled}) == 2, 'Duplicate enabled outer descriptor')
    require(len(outer_names) == 2 and set(outer_names) == set(enabled),
            'Enabled outer descriptors differ from declared business inventory')
    require(all(len(PurePosixPath(name).parts) >= 3 for name in canonical) and
            {PurePosixPath(name).parts[1] for name in canonical} == {Path(name).stem for name in enabled},
            'Enabled outer descriptors differ from canonical mod-content trees')
    outers = {}
    for relative in enabled:
        raw = (read_root / relative).read_bytes()
        require(len(raw) == rows[relative]['bytes'] and hashlib.sha256(raw).hexdigest() == rows[relative]['sha256'],
                'Declared outer descriptor changed')
        matches = list(re.finditer(rb'^path="([^"\r\n]+)"\r?$', raw, re.MULTILINE))
        require(len(matches) == 1 and len(re.findall(rb'^\s*path\s*=', raw, re.MULTILINE)) == 1,
                'Exactly one canonical quoted outer path required')
        expected = profile / 'mod-content' / Path(relative).stem
        require(Path(matches[0][1].decode('utf-8')).resolve() == expected.resolve(), 'Outer descriptor semantic path mismatch')
        replacement = ('<PROFILE>/mod-content/' + Path(relative).stem).encode()
        normalized = raw[:matches[0].start(1)] + replacement + raw[matches[0].end(1):]
        outers[relative] = {'bytes': len(normalized), 'sha256': hashlib.sha256(normalized).hexdigest()}
    permitted = set(canonical) | set(CONFIGS) | set(outer_names) | {'dlc_load.json'}
    require(set(rows) == permitted, 'Unlisted business profile entry cannot enter a graphics key')
    return {'canonical_mod_files': canonical, 'plain_configuration': {key: _signature(rows[key]) for key in CONFIGS},
            'outer_descriptors': outers, 'dlc_load': _signature(rows['dlc_load.json'])}


def _runtime_key(manifest, runtime, *, target=False):
    def selected(row):
        path = Path(runtime['paths'][row['path_key']]).resolve()
        ref = {'path': str(path), **_signature(row)}
        require(_pin(path) == ref, 'Runtime input changed')
        return ref
    source = _read(selected(manifest['source_index'])['path'])
    native = _read(selected(manifest['native_source_index'])['path'])
    require(source.get('schema') == 'ck3-common-source-index-v1' and
            native.get('schema') == 'ck3-common-native-source-index-v1', 'Exact shared source indexes required')
    for index in (source, native):
        require(isinstance(index.get('files'), dict) and index['files'], 'Nonempty source file index required')
        for key, row in index['files'].items():
            _relative(key)
            _signature(row)
    if target:
        require(_signature(source['files'].get('tools/ck3_mod_acceptance_graphics_cache.py')) ==
                _signature(_pin(__file__)), 'Selected Source06 helper differs from the executing public helper')
    for row in (manifest['host'], manifest['native']['dll'], manifest['native']['injector']):
        selected(row)
    exe = _pin(Path(runtime['game_dir']) / 'binaries/ck3.exe')
    require(exe['sha256'] == manifest['game']['exe_sha256'], 'Actual game EXE differs from exact cache build')
    return {'game': manifest['game'], 'exe': _signature(exe), 'host': _signature(manifest['host']),
            'native': {key: _signature(manifest['native'][key]) for key in ('dll', 'injector')},
            'host_features': manifest.get('host_features', {}),
            'source_core_sha256': _digest({key: _signature(row) for key, row in source['files'].items()
                                         if key not in PREPARE_ONLY_PATHS}),
            'native_files_sha256': _digest(native['files']), 'prepare_only_paths': sorted(PREPARE_ONLY_PATHS)}


def _origin(origin_pin):
    from ck3_mod_acceptance_allocate import previous_session_closure, closed_lease, read_actual_release
    origin = _checked(origin_pin)
    names = {'frozen_argv', 'prepared_case', 'runtime_local', 'native_report', 'host_started', 'host_exit',
             'keeper_report', 'release'}
    require(set(origin) == {'schema', 'source_run_id', 'evidence'} and origin['schema'] == ORIGIN_SCHEMA and
            isinstance(origin['source_run_id'], str) and isinstance(origin['evidence'], dict) and
            set(origin['evidence']) == names, 'Exact typed closed-run origin required')
    refs = origin['evidence']
    values = {key: _checked(row) for key, row in refs.items()}
    freeze = values['frozen_argv']
    previous = Path(refs['frozen_argv']['path']).parent
    require(freeze['run_id'] == origin['source_run_id'], 'Source run crossed frozen argv')
    for key, name in (('native_report', 'native-report.json'), ('host_started', 'host-started.json'),
                      ('host_exit', 'host-original-process-exit.json')):
        require(Path(refs[key]['path']) == previous / name, 'Closed-run evidence crossed original run')
    for key in ('prepared_case', 'runtime_local'):
        require(freeze['files'].get(refs[key]['path']) == _signature(refs[key]), 'Source binding was not frozen by this run')
    runtime = values['runtime_local']
    require(runtime['manifest'] == freeze['runtime_manifest'], 'Source runtime manifest crossed frozen run')
    manifest = _checked(runtime['manifest'])
    prepared = values['prepared_case']
    require(prepared['runtime_manifest'] == runtime['manifest'], 'Source prepared manifest crossed runtime')
    require(Path(prepared['startup']['state_dir']).resolve() == Path(freeze['state_dir']).resolve(),
            'Source prepared state crossed frozen run')
    require(Path(freeze['source_root']).resolve() == Path(runtime['paths']['source_root']).resolve(), 'Source root changed')
    closure = previous_session_closure(previous, freeze, values['native_report'])
    release = read_actual_release(Path(refs['release']['path']))
    require(closed_lease(values['keeper_report'], release, freeze['screen_task']) and
            release['task']['state'] == 'done' and release.get('event', {}).get('task_id') == freeze['screen_task'] and
            release['event'].get('sequence') == release['task']['last_sequence'], 'Source screen is not actually released')
    rows = business_files(prepared['preparation'])
    snapshot_root = previous / 'input-snapshots/profile'
    observed = set()
    for directory, directories, files in os.walk(_plain_path(snapshot_root, directory=True), followlinks=False):
        for name in directories:
            _plain_path(Path(directory) / name, directory=True)
        for name in files:
            path = _plain_path(Path(directory) / name)
            observed.add(path.relative_to(snapshot_root).as_posix())
    require(observed == set(rows), 'Source before-launch business snapshot has unlisted/missing entries')
    for relative, row in rows.items():
        snapshot = str((snapshot_root / relative).resolve())
        require(freeze['files'].get(snapshot) == _signature(row) and _signature(_pin(snapshot)) == _signature(row),
                'Source before-launch business bytes are not frozen/exact')
    runtime_key = _runtime_key(manifest, runtime)
    exe_path = str((Path(runtime['game_dir']) / 'binaries/ck3.exe').resolve())
    require(freeze['files'].get(exe_path) == runtime_key['exe'], 'Source EXE identity was not frozen by this run')
    key = {'runtime': runtime_key,
           'profile': _profile_key(rows, Path(freeze['state_dir']) / 'profile', snapshot_root)}
    return origin, freeze, runtime, key, closure


def _cache_tree(root):
    root = _plain_path(root, directory=True)
    result, seen = {}, set()
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories:
            path = _plain_path(Path(directory) / name, directory=True)
            relative = path.relative_to(root).as_posix()
            require(relative in ('dx11', 'dx11/ps_5_0', 'dx11/vs_5_0'), 'Unlisted graphics directory')
        for name in files:
            path = _plain_path(Path(directory) / name)
            relative = path.relative_to(root).as_posix()
            require(CACHE_NAME.fullmatch(_relative(relative)), 'Unlisted graphics file')
            require(relative.casefold() not in seen, 'Duplicate graphics path')
            seen.add(relative.casefold())
            result[relative] = path
    require(result, 'Nonempty derivative graphics cache required')
    return result


def _copy(source, target, expected=None):
    source = _plain_path(source)
    before = source.stat()
    target = Path(target)
    require(not target.exists() and not target.is_symlink(), 'Graphics destination conflict')
    target.parent.mkdir(parents=True, exist_ok=True)
    _plain_path(target.parent, directory=True)
    digest, length = hashlib.sha256(), 0
    with source.open('rb') as incoming, target.open('xb') as outgoing:
        for block in iter(lambda: incoming.read(1024 * 1024), b''):
            outgoing.write(block)
            length += len(block)
            digest.update(block)
        outgoing.flush()
        os.fsync(outgoing.fileno())
    after = source.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Graphics source changed during copy')
    row = {'bytes': length, 'sha256': digest.hexdigest()}
    require(expected is None or row == _signature(expected), 'Graphics bytes/SHA changed')
    require(_signature(_pin(target)) == row, 'Copied graphics bytes differ')
    return {'path': str(target.resolve()), **row}


def freeze_shader_cache_seed(origin_pin, output):
    """Explicit future action only; caller must first select and review the actual source."""
    from ck3_mod_acceptance_allocate import runtime_process_inventory
    import psutil
    origin, freeze, runtime, key, closure = _origin(origin_pin)
    inventory = runtime_process_inventory(psutil, os.getpid())
    require(not inventory['blockers'], 'Active game/keeper/controller blocks derivative snapshot')
    source = Path(freeze['state_dir']) / 'profile/shadercache'
    output = Path(output).absolute()
    require(not output.exists(), 'New external immutable snapshot directory required')
    for protected in (freeze['state_dir'], freeze['source_root'], runtime['repo_root'], runtime['game_dir']):
        require(not output.resolve().is_relative_to(Path(protected).resolve()), 'Snapshot must remain external to old/game/source trees')
    original_files = _cache_tree(source)
    output.mkdir(parents=True)
    rows = []
    for relative, path in sorted(original_files.items()):
        copied = _copy(path, output / 'shadercache' / relative)
        rows.append({'relative_path': relative, **_signature(copied)})
    final_sources = _cache_tree(source)
    require(set(final_sources) == set(original_files), 'Source cache inventory changed during snapshot')
    require(set(_cache_tree(output / 'shadercache')) == set(original_files), 'Snapshot contains unlisted cache entries')
    for row in rows:
        require(_signature(_pin(final_sources[row['relative_path']])) == _signature(row),
                'Source cache bytes/SHA changed before snapshot completion')
    final_inventory = runtime_process_inventory(psutil, os.getpid())
    require(not final_inventory['blockers'], 'Active game/keeper/controller appeared during derivative snapshot')
    _origin(origin_pin)
    manifest = {'schema': SEED_SCHEMA, 'snapshot_root': str(output.resolve()), 'source_origin': origin_pin,
                'cache_key': key, 'cache_key_sha256': _digest(key), 'files': rows,
                'source_closure': closure, 'qualification': QUALIFICATION,
                'startup_qualified': False, 'business_pass': False,
                'actual_process_inventory': {'before': inventory, 'after': final_inventory}}
    path = output / 'manifest.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    return _pin(path)


def _seed(seed_pin, selection, preparation):
    seed = _checked(seed_pin)
    require(seed.get('schema') == SEED_SCHEMA and seed.get('qualification') == QUALIFICATION and
            seed.get('startup_qualified') is False and seed.get('business_pass') is False, 'Derivative seed cannot claim qualification')
    origin, freeze, runtime, original_key, closure = _origin(seed['source_origin'])
    profile = selection.state_dir / 'profile'
    current_key = {'runtime': _runtime_key(selection.manifest, selection.runtime, target=True),
                   'profile': _profile_key(business_files(preparation), profile, profile)}
    require(seed.get('cache_key') == original_key == current_key and
            seed.get('cache_key_sha256') == _digest(current_key), 'Graphics cache key mismatch')
    snapshot = _plain_path(seed['snapshot_root'], directory=True)
    require(Path(seed_pin['path']).resolve() == snapshot / 'manifest.json', 'Seed manifest crossed its immutable snapshot')
    require(set(path.name for path in snapshot.iterdir()) == {'manifest.json', 'shadercache'}, 'Unlisted snapshot entry')
    rows = seed.get('files')
    require(isinstance(rows, list) and rows, 'Exact graphics file list required')
    declared = {}
    seen = set()
    for row in rows:
        require(isinstance(row, dict) and set(row) == {'relative_path', 'bytes', 'sha256'}, 'Typed graphics file row required')
        relative = _relative(row['relative_path'])
        require(CACHE_NAME.fullmatch(relative), 'Graphics path escaped derivative-only tree')
        require(relative.casefold() not in seen, 'Duplicate graphics file')
        seen.add(relative.casefold())
        declared[relative] = _signature(row)
    observed = _cache_tree(snapshot / 'shadercache')
    require(set(observed) == set(declared), 'Unlisted or missing snapshot graphics entry')
    for relative, path in observed.items():
        require(_signature(_pin(path)) == declared[relative], 'Snapshot graphics bytes/SHA changed')
    return seed, declared, closure


def prepare_graphics_cache(selection, seed_pin, preparation, output):
    require(profile_enabled(selection.manifest), 'Shared shader cache reuse is default OFF')
    seed, rows, closure = _seed(seed_pin, selection, preparation)
    profile = selection.state_dir / 'profile'
    destination = profile / 'shadercache'
    require(not destination.exists() and not destination.is_symlink(), 'New graphics destination required')
    files = { 'shadercache/' + relative: _copy(Path(seed['snapshot_root']) / 'shadercache' / relative,
                                              destination / relative, row) for relative, row in rows.items() }
    receipt = {'schema': PREPARED_SCHEMA, 'profile_dir': str(profile.resolve()), 'seed': seed_pin,
               'cache_key_sha256': seed['cache_key_sha256'], 'files': files,
               'source_closure': closure, 'qualification': QUALIFICATION, 'business_pass': False}
    path = Path(output) / 'graphics-cache-preparation.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    return {**receipt, 'receipt': _pin(path)}


def graphics_union(business, graphics, profile):
    require(isinstance(business, dict) and business, 'Original business inventory is mandatory')
    for relative, row in business.items():
        _relative(relative)
        _signature(row)
        require(not relative.casefold().startswith('shadercache/'), 'Business/cache inventories overlap')
    require(graphics.get('schema') == PREPARED_SCHEMA and graphics.get('qualification') == QUALIFICATION and
            graphics.get('business_pass') is False and graphics.get('profile_dir') == str(Path(profile).resolve()),
            'Prepared graphics crossed actual profile/qualification')
    receipt = _checked(graphics['receipt'])
    require(receipt == {key: value for key, value in graphics.items() if key != 'receipt'}, 'Prepared graphics receipt changed')
    rows = graphics.get('files')
    require(isinstance(rows, dict) and rows, 'Declared graphics file map required')
    combined = dict(business)
    seen = {key.casefold() for key in business}
    for relative, row in rows.items():
        _relative(relative)
        require(relative.startswith('shadercache/') and CACHE_NAME.fullmatch(relative[len('shadercache/'):]),
                'Graphics files cannot enter business/product directories')
        require(relative.casefold() not in seen, 'Duplicate/overlapping business and graphics path')
        seen.add(relative.casefold())
        require(set(row) == {'path', 'bytes', 'sha256'} and
                row['path'] == str((Path(profile) / relative).resolve()), 'Graphics file crossed actual profile path')
        _signature(row)
        combined[relative] = row
    return combined


def validate_prepared_graphics(selection):
    require(profile_enabled(selection.manifest), 'Prepared graphics require shared manifest opt-in')
    graphics = selection.prepared['graphics_cache']
    profile = selection.state_dir / 'profile'
    graphics_union(business_files(selection.prepared['preparation']), graphics, profile)
    seed, rows, closure = _seed(graphics['seed'], selection, selection.prepared['preparation'])
    require(graphics['cache_key_sha256'] == seed['cache_key_sha256'], 'Prepared graphics key changed')
    observed = _cache_tree(profile / 'shadercache')
    require(set(observed) == set(rows), 'Unlisted or missing prepared graphics entry')
    pins = [_pin(__file__), graphics['receipt'], graphics['seed'], seed['source_origin']]
    origin = _checked(seed['source_origin'])
    pins.extend(origin['evidence'].values())
    runtime = _checked(origin['evidence']['runtime_local'])
    pins.append(runtime['manifest'])
    for relative, expected in rows.items():
        target = _pin(observed[relative])
        require(_signature(target) == expected and target == graphics['files']['shadercache/' + relative],
                'Prepared graphics bytes/SHA changed')
        pins.extend((target, _pin(Path(seed['snapshot_root']) / 'shadercache' / relative)))
    return pins
