#!/usr/bin/env python3
"""Offline actual conversion-input providers/mailbox/command-result fixture."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / 'ck3_autonomous_player/native_bridge'
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    installed = subprocess.run([str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / 'VC/Auxiliary/Build/vcvars64.bat'
    sources = [native/'src'/n for n in ('ck3_12002.cpp', 'ck3_12002_religion_context.cpp',
        'religion_rite_governance12002_state_rite.cpp', 'ck3_12002_religion_conversion_gates.cpp',
        'ck3_12002_religion_conversion_ai_inputs.cpp', 'ck3_12002_query_mailbox.cpp',
        'main_thread_query_mailbox_v1.cpp', 'protocol.cpp',
        'ck3_12002_religion_conversion_inputs_mailbox.cpp', 'ck3_12002_religion_conversion_inputs_mailbox_test.cpp')]
    pins = sources + [native/'include/xar_bridge'/n for n in (
        'ck3_12002_religion_conversion_gates.hpp', 'ck3_12002_religion_conversion_ai_inputs.hpp',
        'religion_rite_governance12002_state_rite.hpp', 'ck3_12002_religion_conversion_inputs_mailbox.hpp',
        'ck3_12002_query_mailbox.hpp', 'main_thread_query_mailbox_v1.hpp')]
    wires = ('current-zero.json', 'signed-prediction.json', 'target-zero.json', 'gates-unavailable.json',
             'prediction-unavailable.json', 'stale-target-generation.json')
    runs = []
    for mode in ('Od', 'O2'):
        target = output/mode; target.mkdir(exist_ok=True)
        temp = target/'tmp'; temp.mkdir(exist_ok=True)
        executable = target/'religion-conversion-inputs-mailbox-test.exe'
        command = subprocess.list2cmdline(['cl.exe', '/nologo', '/std:c++20', '/EHsc', '/'+mode,
            '/W4', '/WX', '/utf-8', '/I'+str(native/'include'),
            '/DXAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1',
            '/DXAR_RELIGION_CONVERSION_INPUTS_MAILBOX_STANDALONE_ADAPTER=1',
            *map(str, sources), '/Fe:'+str(executable), '/link', 'user32.lib'])
        batch = target/'build.cmd'
        batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+
                         command+'\nexit /b %errorlevel%\n', encoding='utf-8')
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        built = subprocess.run(['cmd.exe', '/d', '/c', str(batch)], cwd=target, env=env,
            capture_output=True, text=True, encoding='utf-8', errors='replace')
        (target/'build.log').write_text(built.stdout+built.stderr, encoding='utf-8')
        if built.returncode: raise RuntimeError('Compile failed: '+str(target/'build.log'))
        tested = subprocess.run([str(executable), str(target)], cwd=target, env=env, timeout=60,
            capture_output=True, text=True, encoding='utf-8', errors='replace')
        (target/'test.log').write_text(tested.stdout+tested.stderr, encoding='utf-8')
        if tested.returncode: raise RuntimeError('Fixture failed: '+str(target/'test.log'))
        packets = {name: json.loads((target/name).read_text(encoding='utf-8')) for name in wires}
        for packet in packets.values():
            result = packet['result']; dto = result['player_religion_conversion_inputs']
            gates = dto['conversion_gates']; prediction = dto['predicted_base_fulfillment']
            assert packet['type'] == 'command_result' and packet['protocol_version'] == 1 and packet['ok'] is True
            assert packet['request_id'] == 'inputs"mailbox-fixture'
            assert result['step'] == 'query-player-religion-conversion-inputs-v1'
            assert result['domain_key'] == 'player_religion_conversion_inputs_v1'
            assert result['backend_id'] == 'ck3-1.20.0.2-native-player-religion-conversion-inputs-v1'
            assert result['accepted'] and result['private_build'] and result['read_only'] and result['advertised'] is False
            assert result['snapshot_revision'] == 701 and result['status'] == ('observed' if dto['available'] else 'unavailable')
            assert dto['date_raw'] == gates['date_raw'] == prediction['date_raw'] == 53175816
            assert dto['played_character_id'] == gates['played_character_id'] == prediction['played_character_id'] == 0x03000004
            assert dto['capture_epoch'] == gates['capture_epoch'] == prediction['capture_epoch'] != result['snapshot_revision']
            assert gates['requested_target_rite_id'] == prediction['target_rite_id'] == dto['target_rite_id']
            assert prediction['is_current_fulfillment'] is False and prediction['is_observed_conversion_gain'] is False
            assert prediction['is_final_ai_desire'] is False and prediction['raw_scale'] == gates['raw_scale'] == 100000
        positive = packets['current-zero.json']['result']['player_religion_conversion_inputs']
        assert positive['available'] and positive['conversion_gates']['knowledge_level_raw'] == 40000
        assert positive['conversion_gates']['recently_converted'] and positive['predicted_base_fulfillment']['expected_base_change_raw'] == 0
        signed = packets['signed-prediction.json']['result']['player_religion_conversion_inputs']['predicted_base_fulfillment']
        assert signed['current_rite_base_raw'] == -2500000 and signed['target_rite_base_raw'] == 1250000
        assert signed['expected_base_change_raw'] == 3750000
        zero = packets['target-zero.json']['result']['player_religion_conversion_inputs']
        assert zero['available'] and zero['target_rite_id'] == 0 and zero['conversion_gates']['target_rite_id'] == 0
        gates_missing = packets['gates-unavailable.json']['result']['player_religion_conversion_inputs']
        assert not gates_missing['available'] and gates_missing['conversion_gates']['recently_converted'] is None
        assert gates_missing['predicted_base_fulfillment']['available']
        prediction_missing = packets['prediction-unavailable.json']['result']['player_religion_conversion_inputs']
        assert not prediction_missing['available'] and prediction_missing['conversion_gates']['available']
        assert prediction_missing['predicted_base_fulfillment']['expected_base_change_raw'] is None
        runs.append({'mode': mode, 'returncode': tested.returncode, 'stdout': tested.stdout.strip(),
            'actual_wire_sha256': {name: digest(target/name) for name in wires},
            'fixture_executable_sha256': digest(executable)})
        print(mode, tested.stdout.strip())
    result = {'status': 'GREEN', 'readiness': 'static-ready', 'live_verified': False,
        'local_ck3_touched': False, 'actual_core': True, 'actual_conversion_gates_provider': True,
        'actual_predicted_base_provider': True, 'actual_mailbox_submit_drain_wait_reclaim': True,
        'actual_command_result_serializer': True, 'fixture_executor_permit': 'Existing offline primary slot; central uses independent named inputs slot',
        'fixture_native_callbacks': 'Synthetic objects and native getter callback behavior in fixture-owned memory',
        'fixture_adapter_unwrap': 'Bare GameAdapter identity branch only; no WorkerAdapter implementation substituted',
        'compiler': 'MSVC /W4 /WX /Od and /O2', 'runs': runs,
        'source_sha256': {str(p.relative_to(root)): digest(p) for p in pins}}
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
