"""Compile the new reasons owner mailbox and decode its actual command_result packets."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess

from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

NATIVE = Path(__file__).resolve().parent.parent
SOURCES = ('ck3_12002.cpp', 'ck3_12002_religion_conversion_rite.cpp',
           'ck3_12002_religion_conversion_reasons.cpp', 'main_thread_query_mailbox_v1.cpp',
           'ck3_12002_query_mailbox.cpp', 'protocol.cpp',
           'ck3_12002_religion_conversion_reasons_mailbox.cpp')
TEST = 'ck3_12002_religion_conversion_reasons_mailbox_test.cpp'
WIRE = ('native-refusal-sso.json', 'native-refusal-heap.json', 'native-allowed-empty.json',
        'native-allowed-with-text.json', 'native-refusal-empty.json', 'target-zero.json',
        'target-unavailable.json', 'native-text-unavailable.json')
EXE_SHA = 'AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_wire(directory):
    pins = {}
    for name in WIRE:
        path = directory / name
        packet = json.loads(path.read_text(encoding='utf-8'))
        require(packet['type'] == 'command_result' and packet['protocol_version'] == 1 and
                packet['ok'] is True and packet['request_id'] == 'reasons"mailbox-fixture',
                'actual protocol and escaped request ID')
        result = packet['result']
        out = result['player_religion_conversion_reasons']
        require(result['step'] == 'query-player-religion-conversion-reasons-v1' and
                result['domain_key'] == 'player_religion_conversion_reasons_v1' and
                result['backend_id'] == 'ck3-1.20.0.2-native-player-religion-conversion-reasons-v1' and
                result['private_build'] is True and result['read_only'] is True and
                result['advertised'] is False and result['accepted'] is True and
                result['game_version'] == '1.20.0.2' and result['executable_sha256'] == EXE_SHA and
                result['snapshot_revision'] == 701 and result['date_raw'] == 53175816,
                'actual complete private metadata and owning revision')
        require(out['schema'] == 'ck3_12002_religion_conversion_reasons_v1' and
                out['game_version'] == '1.20.0.2' and out['executable_sha256'] == EXE_SHA and
                out['read_only'] is True and out['played_character_id'] == 0x03000004 and
                out['date_raw'] == 53175816 and out['capture_epoch'] > 0 and
                out['capture_epoch'] != result['snapshot_revision'] and
                out['reason_codes_available'] is False, 'actual reason serializer and native epoch')
        unavailable = name in ('target-unavailable.json', 'native-text-unavailable.json')
        require(result['status'] == ('unavailable' if unavailable else 'observed') and
                out['available'] is not unavailable and out['native_blocker_text_available'] is not unavailable,
                'known empty reasons differ from actual unavailable')
        if unavailable:
            require(out['raw_native_text'] is None and out['ui_blocker_text'] is None and
                    out['native_paid_validator_passes'] is None,
                    'unavailable read invents neither text nor final boolean')
            require(out['unavailable_reason'] == ('target_rite_unavailable' if name == 'target-unavailable.json'
                                                 else 'native_text_unavailable'), 'typed unavailable source')
        else:
            require(out['unavailable_reason'] is None and out['current_rite_id'] == 0 and
                    out['target_rite_id'] == (0 if name == 'target-zero.json' else 0x82000002),
                    'full ID including zero remains intact')
            require(out['native_paid_validator_passes'] is name.startswith('native-allowed'),
                    'native final bool independent of text length')
            raw = out['raw_native_text']
            require(out['ui_blocker_text'] == raw + ('\n' if raw and not raw.endswith('\n') else ''),
                    'actual UI final LF behavior')
        if name == 'native-refusal-sso.json':
            require(out['raw_native_text'] == 'Not adult.', 'actual inline string wire')
        elif name == 'native-refusal-heap.json':
            require(out['raw_native_text'] == '#N Cannot adopt "target Rite".#!\n知晓程度不足。\n',
                    'native heap UTF8, markup, quotes and existing line ending preserved')
        elif name in ('native-allowed-empty.json', 'native-refusal-empty.json', 'target-zero.json'):
            require(out['raw_native_text'] == '' and out['ui_blocker_text'] == '', 'known empty wire')
        elif name == 'native-allowed-with-text.json':
            require(out['raw_native_text'] == 'A native formatted explanation.', 'allowed native text preserved')
        pins[name] = sha(path)
    require(not (directory / 'frame-drift.json').exists(), 'unstable owner frame emits no command_result')
    rejection = directory / 'frame-drift.json.rejection.json'
    refused = json.loads(rejection.read_text(encoding='utf-8'))
    require(refused['success_wire_emitted'] is False and refused['mailbox_reclaimed'] is True and
            bool(refused['failure']), 'actual post-read owner drift and ticket reclamation')
    stale = directory / 'stale-request-rejection.json'
    refused = json.loads(stale.read_text(encoding='utf-8'))
    require(refused['success_wire_emitted'] is False and refused['native_submit_sequence'] == 0 and
            refused['failure'] == 'player_religion_conversion_reasons_current_frame_unavailable',
            'actual stale handler performs no native submission')
    pins[rejection.name] = sha(rejection)
    pins[stale.name] = sha(stale)
    return pins


def run_mode(shell, root, mode):
    out = root / mode
    out.mkdir(parents=True, exist_ok=True)
    compiler = ['cl.exe', '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX', '/utf-8', '/DNOMINMAX',
                f'/{mode}', '/DXAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1',
                '/DXAR_RELIGION_CONVERSION_REASONS_MAILBOX_STANDALONE_ADAPTER=1', f'/I{NATIVE / "include"}']
    run_batch(command=compiler + ['/c', '/MP32'] + [str(NATIVE / 'src' / name) for name in SOURCES],
              shell=shell, output=out, tag='compile')
    executable = out / 'religion_conversion_reasons_mailbox.exe'
    run_batch(command=compiler + [str(NATIVE / 'src' / TEST)] +
              [str(out / Path(name).with_suffix('.obj')) for name in SOURCES] +
              ['User32.lib', f'/Fe:{executable}'], shell=shell, output=out, tag='link')
    wire = out / 'wire'
    wire.mkdir(exist_ok=True)
    run = subprocess.run([str(executable), str(wire)], cwd=out, capture_output=True, text=True,
                         encoding='utf-8', errors='replace', timeout=15)
    (out / 'run.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    require(run.returncode == 0, f'{mode} owning reasons mailbox failed: {out / "run.log"}')
    return dict(mode=mode, compile='GREEN_W4_WX', stdout=run.stdout.strip(),
                executable_sha256=sha(executable), actual_wire_sha256=validate_wire(wire))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, required=True)
    args = parser.parse_args()
    out = args.artifacts.resolve()
    out.mkdir(parents=True, exist_ok=True)
    temp = out / 'temp'
    temp.mkdir(exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(temp)
    shell = visual_studio_developer_shell()
    source_pins = {name: sha(NATIVE / 'src' / name) for name in SOURCES + (TEST,)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda mode: run_mode(shell, out, mode), ('Od', 'O2')))
    receipt = dict(schema='xar.ck3.religion-conversion-reasons-mailbox-fixture/v1', status='GREEN',
                   time_utc=datetime.now(timezone.utc).isoformat(), results=results, source_sha256=source_pins,
                   original_library_matrix_repeated=False,
                   actual_pipeline='worker TrySubmit -> owning ObservePumpDrain -> actual Core/Reasons provider -> Wait/Reclaim -> actual command_result serializer -> Python json decoder',
                   mailbox_permit='existing primary permitted_executor; named permitted_executor_religion_conversion_reasons12002 integration pending',
                   dedicated_production_registration_tested=False, ck3_accessed=False, live_verified=False,
                   readiness='static-ready')
    (out / 'result.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(status='GREEN', result=str(out / 'result.json'), result_sha256=sha(out / 'result.json'),
                         fixtures=[r['stdout'] for r in results])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
