package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture. Default JUnit uses the committed result and launches no Python. */
public final class CaptureDeadlineTransportGolden {
    private static final int CORPUS_MAX_BYTES = 196_608;
    private static final String CORPUS_PROFILE = "deadline-transport-producer-corpus/v1";
    private CaptureDeadlineTransportGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("python root input-spec output-golden required"); }
        Process process = new ProcessBuilder(args[0], "-B", "-c", PROGRAM,
                Path.of(args[1]).toAbsolutePath().toString(), Path.of(args[2]).toAbsolutePath().toString(),
                Path.of(args[3]).toAbsolutePath().toString()).inheritIO().start();
        try {
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.destroyForcibly(); process.waitFor(10, TimeUnit.SECONDS);
                throw new IllegalStateException("deadline fake-wire original producer capture timed out");
            }
            if (process.exitValue() != 0) { throw new IllegalStateException("original producer capture exit" + process.exitValue()); }
        } finally { if (process.isAlive()) { process.destroyForcibly(); } }
    }

    private static final String PROGRAM = """
            import copy, hashlib, importlib.abc, importlib.machinery, json, pathlib, sys, unittest
            CORPUS_MAX_BYTES = %d
            CORPUS_PROFILE = '%s'
            from collections.abc import Sequence
            from datetime import datetime, timezone
            from types import CodeType, ModuleType
            from typing import TypedDict
            from unittest.mock import patch
            root, inputs_path, output_path = (pathlib.Path(value).resolve() for value in sys.argv[1:])
            sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'src'))
            sys.path.insert(0, str(root))
            sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'tests' / 'unit'))
            _interpreter_prefixes = tuple({pathlib.Path(sys.prefix).resolve(), pathlib.Path(sys.base_prefix).resolve()})
            class _SourceRef(TypedDict):
                path: str
                bytes: int
                sha256: str
            _measured_sources: dict[str, _SourceRef] = {}
            def _repo_source(filename: str | pathlib.Path) -> pathlib.Path | None:
                original = pathlib.Path(filename).absolute()
                source = original.resolve()
                if original.is_relative_to(root) and not source.is_relative_to(root) and not any(original.is_relative_to(prefix) for prefix in _interpreter_prefixes):
                    raise ValueError('repository import escaped the resolved source root: ' + str(original))
                if not source.is_relative_to(root) or any(source.is_relative_to(prefix) for prefix in _interpreter_prefixes):
                    return None
                if source.suffix != '.py':
                    raise ValueError('repository import has unsupported non-source origin: ' + str(source))
                return source
            def _measure_source(source: pathlib.Path, raw: bytes | None = None) -> _SourceRef:
                content = source.read_bytes() if raw is None else raw
                return {'path': source.relative_to(root).as_posix(), 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
            def _record_source(source: pathlib.Path, raw: bytes) -> None:
                measured = _measure_source(source, raw)
                previous = _measured_sources.setdefault(measured['path'], measured)
                if previous != measured:
                    raise ValueError('repository source changed before a repeated module execution: ' + measured['path'])
            def _repo_modules() -> set[str]:
                sources: set[str] = set()
                for module in tuple(sys.modules.values()):
                    filename = getattr(module, '__file__', None)
                    if isinstance(filename, str):
                        source = _repo_source(filename)
                        if source is not None:
                            sources.add(source.relative_to(root).as_posix())
                return sources
            _initial_repo_sources = _repo_modules()
            if _initial_repo_sources:
                raise ValueError('repository modules were loaded before source observation: ' + str(sorted(_initial_repo_sources)[:8]))
            class _MeasuredRepoSourceLoader(importlib.machinery.SourceFileLoader):
                def get_code(self, fullname: str) -> CodeType:
                    source = _repo_source(self.get_filename(fullname))
                    if source is None:
                        raise ValueError('measured loader escaped repository source scope')
                    raw = source.read_bytes()
                    _record_source(source, raw)
                    # Compile exactly the measured source bytes; never accept a cached pyc.
                    return self.source_to_code(raw, str(source))
            class _RepoSourceObserver(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname: str, path: Sequence[str] | None = None,
                              target: ModuleType | None = None) -> importlib.machinery.ModuleSpec | None:
                    spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
                    if spec is None or spec.origin is None or spec.origin in ('built-in', 'frozen'):
                        return None
                    source = _repo_source(spec.origin)
                    if source is None:
                        return None
                    if not isinstance(spec.loader, importlib.machinery.SourceFileLoader):
                        raise ValueError('repository source has an unsupported loader: ' + fullname)
                    spec.loader = _MeasuredRepoSourceLoader(fullname, str(source))
                    return spec
            _abi_path = root / 'ck3_autonomous_player/native_bridge/include/xar_bridge/tactical_daily_sentinel_v1.hpp'
            _abi_before = _measure_source(_abi_path)
            sys.meta_path.insert(sys.meta_path.index(importlib.machinery.PathFinder), _RepoSourceObserver())
            def _verify_sources(stage: str) -> int:
                loaded = _repo_modules()
                unrecorded = loaded.difference(_measured_sources)
                if unrecorded:
                    raise ValueError(stage + ' has unrecorded repository source modules: ' + str(sorted(unrecorded)[:8]))
                for name, before_ref in tuple(_measured_sources.items()):
                    if _measure_source(root / name) != before_ref:
                        raise ValueError(stage + ' repository source changed: ' + name)
                if _measure_source(_abi_path) != _abi_before:
                    raise ValueError(stage + ' native ABI source changed')
                return len(loaded)
            from tools.ck3_live_run_id import current_machine_id
            from xar_autoplayer.bridge import campaign_deadline_transport_v1 as transport
            from xar_autoplayer.bridge import native_driver as native
            from xar_autoplayer.bridge.campaign_deadline_v1 import deadline_v1
            from ck3_autonomous_player.tests.unit.test_campaign_deadline_transport_v1 import CampaignDeadlineCompoundTests
            _machine_id = current_machine_id()
            _after_imports_repo_sources = _verify_sources('after actual fixture imports')
            spec_bytes = inputs_path.read_bytes()
            spec = json.loads(spec_bytes)
            if spec['schema'] != 'xar.ck3.java-deadline-transport-producer-inputs/v1':
                raise ValueError('wrong input specification')
            original = transport.advance_campaign_deadline_v1
            def frame(value):
                return {key: copy.deepcopy(value.get(key)) for key in ('date_raw', 'paused', 'speed', 'snapshot_id', 'native_revision')}
            transport_rows = []
            first_clock = None
            for index, case in enumerate(spec['transport_cases']):
                fixture = CampaignDeadlineCompoundTests()
                driver, endpoint = fixture.driver(case['date'], initial_speed=case['initial_speed'],
                    early_event_days=case.get('early_event_days'), deferred_native_pause=case.get('deferred_native_pause', False),
                    overshoot=case.get('overshoot', False))
                captured = {}
                if case.get('bad_arm_speed'):
                    publish = endpoint.publish
                    def bad_arm_speed(value):
                        result = value.get('result')
                        if value.get('type') == 'command_result' and isinstance(result, dict) and str(result.get('step')).startswith(native._TACTICAL_DAILY_SENTINEL_ARM_PREFIX):
                            value = copy.deepcopy(value)
                            value['result']['tactical_daily_sentinel']['speed'] = 4
                        publish(value)
                    endpoint.publish = bad_arm_speed
                def observe(actual_driver, starting, *, target_date_raw, speed, actions):
                    captured['request'] = {'invocation_id': format(index + 1, '032x'), 'cap': deadline_v1(actual_driver, starting, target_date_raw),
                        'starting_frame': frame(starting), 'speed': speed}
                    action_offset = len(actions)
                    try:
                        current, clock = original(actual_driver, starting, target_date_raw=target_date_raw, speed=speed, actions=actions)
                    except Exception as error:
                        captured['failed_actions'] = copy.deepcopy(actions[action_offset:])
                        captured['outcome'] = {'status': 'failed', 'error_type': type(error).__name__, 'error': str(error)}
                        raise
                    captured['completion'] = {'current_frame': frame(current), 'actions': copy.deepcopy(actions[action_offset:]), 'clock': copy.deepcopy(clock)}
                    captured['outcome'] = {'status': 'returned', 'value': copy.deepcopy(clock)}
                    return current, clock
                try:
                    with patch.object(transport, 'advance_campaign_deadline_v1', observe):
                        starting = driver.take_internal_semantic_snapshot()
                        try:
                            driver.execute_step('life-advance', expected_revision=int(starting['revision']))
                        except native.BridgeUnavailableError:
                            if not captured or captured.get('outcome', {}).get('status') != 'failed':
                                raise
                    if not captured:
                        raise ValueError('actual transport producer was not called')
                    if captured['outcome']['status'] == 'returned' and first_clock is None:
                        first_clock = copy.deepcopy(captured['completion']['clock'])
                    transport_rows.append({'id': case['id'], **captured})
                finally:
                    fixture.doCleanups()
            if first_clock is None:
                raise ValueError('no real original transport proof captured')
            normalizer_rows = []
            for case in spec['normalizer_cases']:
                value = copy.deepcopy(first_clock[case['source']])
                value.update(case['changes'])
                if 'remove' in case:
                    del value[case['remove']]
                try:
                    expected = {'status': 'returned', 'value': native._normalize_tactical_daily_sentinel_status(value)}
                except ValueError as error:
                    expected = {'status': 'rejected', 'error_type': type(error).__name__}
                normalizer_rows.append({'id': case['id'], 'input_json': json.dumps(value, ensure_ascii=False, separators=(',', ':')), 'expected': expected})
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(CampaignDeadlineCompoundTests)
            tested = unittest.TextTestRunner(verbosity=2).run(suite)
            if not tested.wasSuccessful() or tested.skipped:
                raise ValueError('actual original compound tests did not pass without skip')
            _after_suite_repo_sources = _verify_sources('after complete original compound suite')
            before = sorted([*_measured_sources.values(), _abi_before], key=lambda value: value['path'])
            result = {'schema': 'xar.ck3.java-deadline-transport-producer-golden/v1',
                'corpus_profile': CORPUS_PROFILE, 'corpus_maximum_bytes': CORPUS_MAX_BYTES,
                'machine_id': _machine_id, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
                'source_provenance': {'schema': 'xar.ck3.measured-repo-import-closure/v1',
                    'scope': 'repo-python-excluding-interpreter-prefixes/v1', 'initial_repo_sources': 0,
                    'after_imports_repo_sources': _after_imports_repo_sources,
                    'after_suite_repo_sources': _after_suite_repo_sources,
                    'recorded_repo_sources': len(_measured_sources), 'source_pre_post_equal': True,
                    'unrecorded_repo_sources': []},
                'source_refs': before, 'input_spec_sha256': hashlib.sha256(spec_bytes).hexdigest(),
                'method': 'actual_existing_driver_transport_fake_wire_no_game', 'original_tests': tested.testsRun,
                'original_skipped': len(tested.skipped), 'transport_cases': transport_rows, 'normalizer_cases': normalizer_rows,
                'game_rpc': 0, 'native_calls': 0, 'ledger_writes': 0, 'saved_day_credit': 0}
            raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\\n').encode('utf-8')
            if len(raw) > CORPUS_MAX_BYTES:
                print(json.dumps({'status': 'GOLDEN_OVER_CAP', 'golden_bytes': len(raw), 'maximum_bytes': CORPUS_MAX_BYTES,
                    'recorded_repo_sources': len(_measured_sources), 'compact_source_refs_bytes': len(json.dumps(before, sort_keys=True, separators=(',', ':')).encode('utf-8'))}))
                raise ValueError('complete actual import closure and proofs exceed the explicit deadline corpus budget')
            with output_path.open('xb') as stream:
                stream.write(raw)
            print(json.dumps({'status': 'CAPTURED', 'transport_cases': len(transport_rows), 'normalizer_cases': len(normalizer_rows),
                'original_tests': tested.testsRun, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}))
            """.formatted(CORPUS_MAX_BYTES, CORPUS_PROFILE);
}
