"""Two current-production wiring checks, not the prior WAL/a0 matrices.

Evidence: canonical production imports, one real synthetic WAL append/replay
case, and actual method/MCP AST execution with explicit fake native boundaries.
No driver constructor, endpoint, SDK, Game, Native call, Git or live state input.
"""
from __future__ import annotations

import ast
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import prepare_master_wal_clock_diagnostic_integration_v1 as producer

REPO = producer.REPO
PREFIX = producer.PREFIX
SCRATCH = REPO / '.task-tmp/master-wal-a0-integration-20261020-qualification01'
PROOF = REPO / 'docs/ck3-native-ai/evidence/master-wal-clock-diagnostic-integration-source-2026-10-20.json'
DELTA = REPO / 'docs/ck3-native-ai/evidence/master-wal-clock-diagnostic-integration-v1.patch'
CARD = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/INTEGRATION16MiB-MASTER2MiB-SOURCE-SOURCE22-GIT-EXPORT-BUDGET01.json')
CARD_SHA = 'e8726e7cdd6fa93d80c7d283afca9c3bd1115dd3be30270c51c39535bb807e25'
OWN = [PREFIX + n for n in ('native_driver.py', 'mcp_server.py', producer.HELPER)] + [
    'tools/g2_saved_campaign/prepare_master_wal_clock_diagnostic_integration_v1.py',
    'tools/g2_saved_campaign/qualify_master_wal_clock_diagnostic_integration_v1.py']
WAL_INPUT = PREFIX + 'succession_binding_refresh_wal_v1.py'
HARD = 2097152
SCRATCH_HARD = 32768
METRICS = {'synthetic_writes': 0, 'scratch_conservative_prewrite_bound': 0}
BEFORE = None


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def cleanup_owned(root):
    require(root.resolve() == SCRATCH.parent.resolve() / SCRATCH.name
            and root.parent.resolve() == SCRATCH.parent.resolve(), 'cleanup escaped owned root')
    nodes = list(root.rglob('*'))
    for node in [root, *nodes]:
        stat = node.lstat()
        require(not node.is_symlink() and not (getattr(stat, 'st_file_attributes', 0) & 0x400),
                'unexpected reparse node in scratch')
    for node in sorted(nodes, key=lambda x: len(x.parts), reverse=True):
        node.rmdir() if node.is_dir() else node.unlink()
    root.rmdir()


class MasterClockWiring(unittest.TestCase):
    def test_actual_method_normal_parity_and_typed_MCP_error_dispatch(self):
        from xar_autoplayer.bridge import native_driver as nd, driver as api
        from xar_autoplayer.bridge import exact_clock_failure_diagnostic_v1 as diagnostic
        from xar_autoplayer.bridge import exact_day_speed_configuration_v1 as speed_module
        from xar_autoplayer.bridge import clock_observation_timing_v1 as clock_module

        # Reuse the already reviewed small I/O fixture declarations only. Its
        # module/main/Git loader is deliberately never imported or executed.
        fixture = REPO / producer.A0 / 'test_candidate.py'
        raw = fixture.read_bytes()
        require(pin(raw) == {'bytes': 15114, 'sha256': '2c35d6b53794c3a01c190ce3f4ee753dcfc0c08ad2f652ff5f8ffeb46fcb4dba'},
                'reviewed a0 fake boundaries changed')
        declarations = [node for node in ast.parse(raw).body
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in {'frame', 'Fake'}]
        require({n.name for n in declarations} == {'frame', 'Fake'} and len(declarations) == 2,
                'fake declarations not unique')
        fixture_ns = {'BridgeUnavailableError': api.BridgeUnavailableError}
        exec(compile(ast.Module(body=declarations, type_ignores=[]), '<reviewed-a0-fake-boundaries>', 'exec'), fixture_ns)
        frame, Fake = fixture_ns['frame'], fixture_ns['Fake']

        def execute(fake, original=False):
            actions = [{'step': 'previous-horizon-day', 'result': {'request_id': 'DO_NOT_EXPORT'}}]
            overrides = {
                '_date_raw': lambda value, _: value['date_raw'],
                '_TACTICAL_DAILY_SENTINEL_ARM_PREFIX': 'arm-',
                '_TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX': 'cancel-',
                '_TACTICAL_DAILY_SENTINEL_STATUS_STEP': 'status',
                '_TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY': 'arm-cap',
                '_TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY': 'cancel-cap',
                '_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY': 'status-cap',
                '_normalize_tactical_daily_sentinel_status': lambda value: copy.deepcopy(value),
                '_validate_tactical_daily_sentinel_arm': lambda *a, **kw: fake.events.append(('validate-arm', kw)),
                '_validate_tactical_daily_sentinel_stop': lambda *a, **kw: fake.events.append(('validate-stop', kw)),
                '_life_advance_new_modal_hint': lambda *a: None,
                'start_army_timing': lambda stage: fake.events.append(('timing-start', stage)),
                'finish_army_timing': lambda *a, **kw: fake.events.append(('timing-end', kw)),
            }
            def speed(driver, current, *, speed, actions):
                fake.events.append(('prepare-speed', speed))
                return current
            with patch.multiple(nd, **overrides), \
                 patch.object(speed_module, 'prepare_exact_day_speed_v1', speed), \
                 patch.object(clock_module, 'start_clock_observation_v1', lambda *a: fake.events.append(('clock-start',))), \
                 patch.object(clock_module, 'finish_clock_observation_v1', lambda *a: fake.events.append(('clock-finish',))):
                fn = nd.NativeHeadlessGameplayDriver._advance_exact_day_with_sentinel
                if original:
                    node = copy.deepcopy(producer.function(BEFORE['native_driver.py'], '_advance_exact_day_with_sentinel'))
                    node.decorator_list = []
                    namespace = dict(nd.__dict__)
                    exec(compile(ast.Module(body=[node], type_ignores=[]), '<pre-integration-Master-method>', 'exec'), namespace)
                    fn = namespace[node.name]
                result = fn(fake, frame(), speed=3, actions=actions)
            return result, actions, fake.events

        self.assertEqual(execute(Fake('normal'), original=True), execute(Fake('normal')))
        fake = Fake()
        with self.assertRaises(api.StepPostconditionError) as caught:
            execute(fake)
        failure = caught.exception
        self.assertIs(type(failure.__cause__), api.BridgeUnavailableError)
        self.assertEqual(str(failure), diagnostic.MESSAGE)
        self.assertIs(failure.step_result['never_replay'], True)
        self.assertEqual(failure.step_result['credit'], 0)
        self.assertIs(failure.step_result['stop_credit'], False)
        self.assertIs(failure.step_result['normal_status_query_attempted'], False)
        self.assertLessEqual(len(diagnostic._encode(failure.step_result)), 8192)
        self.assertEqual([e[1] for e in fake.events if e[0] == 'primitive'],
                         ['arm-100-to-124-speed-3-mode-terminal-a-0', 'cancel-147'])

        # Actual nested MCP function, with only service/I/O boundaries replaced.
        from mcp.types import CallToolResult
        mcp_raw = (REPO / PREFIX / 'mcp_server.py').read_bytes()
        foreign = api.BridgeUnavailableError(diagnostic.MESSAGE)
        foreign.step_result = copy.deepcopy(failure.step_result)
        foreign.selected_step = 'life-advance-one-day'
        for error in (failure, foreign):
            def auto_turn(**kwargs):
                raise error
            namespace = {'__package__': 'xar_autoplayer.bridge',
                'BridgeUnavailableError': api.BridgeUnavailableError,
                'start_army_timing': lambda *a: None, 'successor_owner': None,
                'before_auto_turn_submit': None, 'service': types.SimpleNamespace(auto_turn=auto_turn),
                '_native_command_rejection_diagnostic': lambda e: None}
            node = copy.deepcopy(producer.function(mcp_raw, 'ck3_auto_turn'))
            node.decorator_list = []
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual-Master-MCP-auto>', 'exec'), namespace)
            if error is foreign:
                with self.assertRaises(api.BridgeUnavailableError) as again:
                    namespace['ck3_auto_turn']()
                self.assertIs(again.exception, foreign)
            else:
                result = namespace['ck3_auto_turn']()
                self.assertIsInstance(result, CallToolResult)
                content = result.model_dump()
                self.assertIs(content['is_error'], True)
                self.assertIn('exact_day_clock_failure_v1', content['structured_content']['diagnostics'])
                self.assertIn(diagnostic.MESSAGE, content['content'][0]['text'])


def qualify():
    global BEFORE
    require(sys.dont_write_bytecode, 'run -B')
    card_raw = CARD.read_bytes()
    require(pin(card_raw) == {'bytes': 3506, 'sha256': CARD_SHA}, 'source card differs')
    card = json.loads(card_raw)
    now = datetime.now(timezone.utc)
    require(now < datetime.fromisoformat(card['review_at_utc'])
            and card['Master_source2MiB']['status'] == 'SOURCE_ONLY_ADMITTED', 'card unavailable/expired')
    machine = subprocess.check_output([sys.executable, '-B', str(REPO / 'tools/ck3_live_run_id.py'), 'machine'],
                                      cwd=REPO, text=True).strip()
    require(machine == card['machine_id'], 'machine differs')
    require(not SCRATCH.exists() and not PROOF.exists() and not DELTA.exists(), 'create-only output already exists')
    require(SCRATCH.parent.resolve().is_relative_to(REPO.resolve()), 'scratch outside workspace')
    BEFORE, after = producer.installed()
    delta = producer.patch_bytes(BEFORE, after)
    require(len(delta) <= 12288, 'patch exceeds quote')
    current = sum((REPO / name).stat().st_size for name in OWN + [WAL_INPUT])
    require(current + len(delta) + 12288 + SCRATCH_HARD <= HARD, 'complete source peak cannot fit')
    SCRATCH.mkdir()
    old_tempdir = tempfile.tempdir
    old_env = {name: os.environ.get(name) for name in ('TEMP', 'TMP')}
    tempfile.tempdir = str(SCRATCH)
    for name in old_env:
        os.environ[name] = str(SCRATCH)
    sink = io.StringIO()
    try:
        sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))
        sys.path.insert(0, str(REPO / 'ck3_autonomous_player/tests/unit'))
        import test_succession_binding_refresh_wal_v1 as fixture
        fixture.configure_scratch(SCRATCH)
        original_write = fixture.bounded_write
        def bounded(path, data, **kwargs):
            target = Path(path).resolve()
            require(target.is_relative_to(SCRATCH.resolve()), 'synthetic write escaped owned scratch')
            total = sum(p.stat().st_size for p in SCRATCH.rglob('*') if p.is_file())
            bound = total + len(data)
            require(bound <= SCRATCH_HARD, 'synthetic prewrite bound exceeds32KiB')
            METRICS['scratch_conservative_prewrite_bound'] = max(METRICS['scratch_conservative_prewrite_bound'], bound)
            METRICS['synthetic_writes'] += 1
            return original_write(path, data, **kwargs)
        fixture.bounded_write = bounded
        suite = unittest.TestSuite([
            fixture.Source20DriverIntegration('test_real_query_record_retain_run_replays_identically_and_reads_once'),
            MasterClockWiring('test_actual_method_normal_parity_and_typed_MCP_error_dispatch')])
        result = unittest.TextTestRunner(stream=sink, verbosity=2).run(suite)
        remaining = sum(p.stat().st_size for p in SCRATCH.rglob('*') if p.is_file())
        require(remaining == 0, 'per-case scratch not clean')
    finally:
        tempfile.tempdir = old_tempdir
        for name, value in old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        cleanup_owned(SCRATCH)
    # Read back the installed files after the checks; no candidate copy on disk.
    producer.installed()
    report = {
        'schema': 'xar.master-wal-clock-diagnostic-production-wiring-source/v1',
        'machine_id': machine, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'SOURCE_QUALIFIED_NOT_DEPLOYED' if result.wasSuccessful() else 'FOCUSED_FAILED_NOT_QUALIFIED',
        'base_master_label': 'c249 source bytes retained through Root f184 extras; no Git read/write',
        'before': {n: pin(b) for n, b in BEFORE.items()}, 'after': {n: pin(b) for n, b in after.items()},
        'source_card': {'path': str(CARD), **pin(card_raw)},
        'whole_inverse': True, 'driver_WAL_a0_commute': True, 'outside_owned_AST_equal': True,
        'Driver_changed_methods': sorted(producer.OWNER_METHODS), 'MCP_changed_function': 'ck3_auto_turn',
        'tests': {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                  'passed': result.wasSuccessful(), 'transcript': sink.getvalue()},
        'scope': 'one existing synthetic WAL retain/append/replay case on canonical production imports; actual canonical sentinel normal A/B plus typed failure and actual MCP AST dispatch',
        'previous_matrices_repeated': False, 'diagnostic_is_clock_fix': False,
        'current_SDK_Game_RPC_Native_Task_Git_changes': 0, 'runtime_speedup_seconds': None,
        'scratch': {'root': str(SCRATCH), 'hard_bytes': SCRATCH_HARD, **METRICS,
                    'removed': not SCRATCH.exists(), 'physical_peak': None, 'allocated_bytes': None},
        'outputs': [{'path': name, **pin((REPO / name).read_bytes())} for name in OWN],
        'unchanged_WAL_helper_input': {'path': WAL_INPUT, **pin((REPO / WAL_INPUT).read_bytes())},
        'patch': {'path': str(DELTA), **pin(delta)}, 'future_writes': 0,
        'physical_credit_bytes': 0}
    encoded = (json.dumps(report, ensure_ascii=True, indent=2) + '\n').encode()
    require(len(encoded) <= 12288, 'proof exceeds quote')
    require(current + len(delta) + len(encoded) + METRICS['scratch_conservative_prewrite_bound'] <= HARD,
            'actual complete source/scratch exceeds2MiB')
    with DELTA.open('xb') as output:
        output.write(delta)
    with PROOF.open('xb') as output:
        output.write(encoded)
    return {'status': report['status'], 'tests': report['tests'],
            'proof': {'path': str(PROOF), **pin(encoded)}, 'patch': pin(delta),
            'retained_gross_including_WAL_input': current + len(delta) + len(encoded),
            'source_scratch_conservative_peak_bound': current + len(delta) + len(encoded) + METRICS['scratch_conservative_prewrite_bound'],
            'scratch': report['scratch']}


if __name__ == '__main__':
    print(json.dumps(qualify(), ensure_ascii=True, indent=2))
