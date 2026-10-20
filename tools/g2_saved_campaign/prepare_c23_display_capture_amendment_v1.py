"""Pure new-Game display amendment: ordinal/shared I/O + PNG retry + pause.

No Game/publisher/OBS calls or emission. Runtime consumes the 18 values once,
after Root/source/storage review. Existing frozen producers remain unchanged.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import FunctionType, ModuleType

HERE = Path(__file__).resolve().parent
LEGACY_SHA = 'c748f0082b149232f441eb9a4d1683d299818a73dff693045ff19c82f5b14181'
CANONICAL_SHA = '9af7bf7e2faa757ff07f759990cb10a1425852bde001554e924b228598515a0c'
PAUSE_RECIPE_SHA = '1eb24b011e03c70bcf50be94617eb46193a3a162c4e0084861f24bf4a35712a0'
HELPER_SHA = 'b3a645480af6840c3a784336ab03538d918efec6df0faf6134c09fe9440a030c'
PNG_SHA = '20e40e58137ee40ee002e3e6b3cfb670addf12b62c6e2f7f666a4252601759b8'
PAUSED_SHA = '89e7d416bc03863b50e17a4946e77bcc35207081677b7f4f7d34374f1c97efa5'


def require(ok, why):
    if not ok:
        raise ValueError('new-Game pause/PNG source amendment: ' + why)


def pin(raw, path):
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def checked_module(path, expected):
    raw = path.read_bytes()
    require(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == expected,
            'frozen producer changed: ' + str(path))
    value = ModuleType('_reviewed_' + path.stem)
    value.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value, pin(raw, path)


def pause_projection(png, pause, canonical):
    require(len(png) == 71575 and hashlib.sha256(png).hexdigest() == PNG_SHA,
            'exact independently qualified PNG source required')
    require(len(canonical) == 71770 and hashlib.sha256(canonical).hexdigest() == CANONICAL_SHA,
            'exact adopted canonical pause-aware source required')
    helper = pause.HELPER.read_bytes()
    require(len(helper) == 1566 and hashlib.sha256(helper).hexdigest() == HELPER_SHA,
            'exact pure growth helper required')
    functions = [n for n in ast.parse(helper).body if isinstance(n, ast.FunctionDef)
                 and n.name == 'advance_growth_deadline_v1']
    require(len(functions) == 1, 'one exact helper function required')
    inline = ast.get_source_segment(helper.decode('utf-8'), functions[0])
    patches = (('class FileGrowthWatch:', inline + '\n\n\nclass FileGrowthWatch:'), *pause.PATCHES)
    restored = canonical.decode('utf-8')
    for before, after in reversed(patches):
        require(restored.count(after) == 1, 'canonical inverse seam changed')
        restored = restored.replace(after, before, 1)
    require(len(restored.encode()) == 69656 and hashlib.sha256(restored.encode()).hexdigest() == pause.BASE_SHA,
            'canonical inverse must recover original f0e6 source')
    candidate = png.decode('utf-8')
    for before, after in patches:
        require(candidate.count(before) == 1, 'one PNG pause seam required')
        candidate = candidate.replace(before, after, 1)
    restored = candidate
    for before, after in reversed(patches):
        require(restored.count(after) == 1, 'PNG inverse seam changed')
        restored = restored.replace(after, before, 1)
    require(restored.encode() == png, 'PNG bytes changed outside reviewed pause hunks')
    candidate = candidate.encode('utf-8')
    require(len(candidate) == 73689 and hashlib.sha256(candidate).hexdigest() == PAUSED_SHA,
            'exact paused-aware PNG projection differs')
    compile(candidate, 'new-Game-pause-aware-PNG-capture', 'exec')
    return candidate, pin(helper, pause.HELPER)


def plan(source_runtime, target_runtime, output, *, generation, machine_id):
    """Return values/review, preserving every original namespace/input guard."""
    original, legacy_pin = checked_module(HERE / 'prepare_new_game_recording_owner_v1.py', LEGACY_SHA)
    pause, pause_pin = checked_module(HERE / 'prepare_obs_pause_aware_capture_v1.py', PAUSE_RECIPE_SHA)
    # Offline isolated globals, never a patch to the old module/source/runtime.
    # Its helper extraction must still reproduce the exact qualified PNG20e.
    isolated = dict(original.__dict__)
    isolated['HELPER_SHA'] = CANONICAL_SHA
    original_plan = FunctionType(original.plan.__code__, isolated)
    values, _, review = original_plan(source_runtime, target_runtime, output,
                                      generation=generation, machine_id=machine_id)
    target = Path(target_runtime).resolve()
    presentation = 'presentation-' + generation.lower()
    capture_name = presentation + '/ck3_obs_capture_png_retry_' + generation.lower() + '.py'
    canonical = (HERE.parent / 'ck3_obs_capture.py').read_bytes()
    capture, helper_pin = pause_projection(values[capture_name], pause, canonical)
    owner_name = presentation + '/start_new_game_display.py'
    before = values[owner_name]
    require(before.count(b'len(raw)==71575') == 2 and before.count(PNG_SHA.encode()) == 3,
            'exact parent/child/readback source pin seams required')
    owner = before.replace(b'len(raw)==71575', b'len(raw)==73689').replace(PNG_SHA.encode(), PAUSED_SHA.encode())
    require(owner.replace(b'len(raw)==73689', b'len(raw)==71575').replace(PAUSED_SHA.encode(), PNG_SHA.encode()) == before,
            'owner changed outside two length/three SHA pins')
    values[capture_name], values[owner_name] = capture, owner
    manifest = presentation + '/SOURCE-PINS-' + generation + '.json'
    values.pop(manifest)
    files = [pin(raw, target / name) | {'relative_path': name} for name, raw in values.items()]
    values[manifest] = (json.dumps({'machine_id': machine_id, 'files': files}, indent=2) + '\n').encode()
    for name, raw in values.items():
        if name.endswith('.py'):
            compile(raw, name, 'exec')
    require(len(values) == 18, 'original complete 18-leaf graph required')
    external = {Path(row['relative_path']).stem: {k: row[k] for k in ('path', 'bytes', 'sha256')}
                for row in files if '/' not in row['relative_path'] and row['relative_path'].endswith('.py')}
    require(len(external) == 5, 'five explicit SDK display algorithm source identities required')
    review.update(schema='xar.new-Game-paused-PNG-recording-owner-review/v1', files=files,
        inputs=review['inputs'] + [legacy_pin, pause_pin, helper_pin],
        manifest=pin(values[manifest], target / manifest), actual_capture=pin(capture, target / capture_name),
        review_source_bytes=sum(map(len, values.values())), installed_source_bytes=sum(map(len, values.values())),
        external_import_source_pins=external,
        source_delta='exact canonical9af mutable helper -> PNG20e -> reviewed pause hunks89e7; owner only source pins; manifest rebuilt',
        canonical_storage_rule='Before cold launch freeze one complete current full-hold canonical SHA/review into launch/keeper/profile/job; never replace it with a prepare-only card',
        actual_new_Game_or_publisher_identity_invented=False, runtime_admitted=False)
    review_raw = (json.dumps(review, ensure_ascii=False, indent=2) + '\n').encode()
    return values, review_raw, review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source-runtime', 'target-runtime', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--generation', required=True)
    parser.add_argument('--machine-id', required=True)
    args = parser.parse_args()
    values, raw, review = plan(args.source_runtime, args.target_runtime, args.output,
                              generation=args.generation, machine_id=args.machine_id)
    print(json.dumps({'emitted': False, 'leaf_count': len(values), 'singlecopy_bytes': sum(map(len, values.values())),
        'review': pin(raw, args.output / 'REVIEW.json'), 'capture': review['actual_capture'],
        'external_import_source_pins': review['external_import_source_pins']}))


if __name__ == '__main__':
    main()
