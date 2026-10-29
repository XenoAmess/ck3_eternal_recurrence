package org.xar.ck3.control.wave3.runtime.timelineowner;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Managed, explicit actual-producer capture; ordinary JUnit never starts Python or a game. */
public final class CaptureTimelineOwnerGolden {
    private CaptureTimelineOwnerGolden() { }

    enum CaptureMode { GOLDEN, DIFFERENTIAL }
    record Invocation(CaptureMode mode, String python, String root, String inputs,
            String output, FileRef selectedActual) { }

    static Invocation invocation(String[] args) {
        if (args.length != 7 && (args.length != 8 || !"DIFFERENTIAL".equals(args[7]))) {
            throw new IllegalArgumentException("python root inputs new-output selected-actual-path bytes sha256 [DIFFERENTIAL] required");
        }
        for (int index : new int[] {0, 1, 2, 3, 4}) {
            if (!Path.of(args[index]).isAbsolute()) throw new IllegalArgumentException("Explicit absolute capture paths required");
        }
        if (!args[5].matches("[1-9][0-9]{0,7}")) throw new IllegalArgumentException("Canonical positive actual byte count required");
        var selected = new FileRef(args[4], Long.parseLong(args[5]), args[6]);
        if (selected.bytes() > 2_097_152) throw new IllegalArgumentException("Bounded selected actual required");
        return new Invocation(args.length == 8 ? CaptureMode.DIFFERENTIAL : CaptureMode.GOLDEN,
                args[0], args[1], args[2], args[3], selected);
    }

    static java.util.List<String> programArguments(Invocation invocation, String javaExecutable, String classpath) {
        var result = new java.util.ArrayList<>(java.util.List.of(invocation.root(), invocation.inputs(), invocation.output(),
                invocation.selectedActual().path(), Long.toString(invocation.selectedActual().bytes()), invocation.selectedActual().sha256()));
        if (invocation.mode() == CaptureMode.DIFFERENTIAL) {
            if (!Path.of(javaExecutable).isAbsolute() || classpath == null || classpath.isBlank()) {
                throw new IllegalArgumentException("Current qualified child JVM and complete classpath required");
            }
            result.add(javaExecutable); result.add(classpath);
        }
        return java.util.List.copyOf(result);
    }

    public static void main(String[] args) throws Exception {
        Invocation invocation = invocation(args);
        Path root = Path.of(args[1]).toRealPath();
        Path inputs = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (!Files.isDirectory(root) || !Files.isRegularFile(inputs) || Files.exists(output)
                || !Files.isDirectory(output.getParent())) { throw new IllegalArgumentException("existing root/inputs and new output in declared scratch required"); }
        FileRef selectedRef = invocation.selectedActual();
        TimelineOwnerSourceView.Proof selected = TimelineOwnerSourceView.readLive(selectedRef, root);
        Path scratch = output.resolveSibling(output.getFileName() + ".tmp");
        Files.createDirectory(scratch);
        ProcessBuilder builder = new ProcessBuilder(args[0], "-B", "-X", "utf8", "-c", PROGRAM)
                .directory(root.toFile()).inheritIO();
        // The shared capture child has already verified its complete qualified JVM classpath.
        builder.command().addAll(programArguments(invocation,
                Path.of(System.getProperty("java.home"), "bin", "java.exe").toRealPath().toString(),
                System.getProperty("java.class.path")));
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1");
        builder.environment().put("PYTHONIOENCODING", "utf-8");
        builder.environment().put("PYTHONOPTIMIZE", "0");
        builder.environment().put("XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1", "0");
        for (String name : java.util.List.of("TMP", "TEMP", "TMPDIR")) { builder.environment().put(name, scratch.toString()); }
        Process process = builder.start();
        try {
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.destroyForcibly(); process.waitFor(10, TimeUnit.SECONDS);
                throw new IllegalStateException("timeline owner actual-producer capture timed out");
            }
            if (process.exitValue() != 0) { throw new IllegalStateException("timeline owner capture exit" + process.exitValue()); }
        } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        TimelineOwnerSourceView.requireSameProof(selected, TimelineOwnerSourceView.readLive(selectedRef, root));
        try (InputStream input = Files.newInputStream(output)) {
            TimelineOwnerSourceView.requireSameProof(selected, TimelineOwnerSourceView.readProvenance(
                    StrictJson.parse(input.readNBytes(98_305), 98_304)));
        }
    }

    private static final String PROGRAM = """
            import atexit, copy, hashlib, importlib.abc, importlib.machinery, inspect, json, os, pathlib, subprocess, sys, unittest
            from collections.abc import Sequence
            from contextlib import ExitStack
            from datetime import datetime, timezone
            from types import CodeType, ModuleType
            from typing import TypedDict
            from unittest.mock import patch
            root, spec_path, output_path = (pathlib.Path(value).resolve() for value in sys.argv[1:4])
            differential = len(sys.argv) == 9
            if os.environ.get('XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1') != '0' or sys.flags.optimize != 0:
                raise ValueError('isolated fixture WAL and enabled assertions required before SDK import')
            sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'src'))
            sys.path.insert(0, str(root))
            sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'tests' / 'unit'))
            _interpreter_prefixes = tuple({pathlib.Path(sys.prefix).resolve(), pathlib.Path(sys.base_prefix).resolve()})
            class _SourceRef(TypedDict):
                path: str
                bytes: int
                sha256: str
            _measured_sources: dict[str, _SourceRef] = {}
            if len(sys.argv) not in (7, 9):
             raise ValueError('exact selected view ref required')
            _view_ref = {'path': sys.argv[4], 'bytes': int(sys.argv[5]), 'sha256': sys.argv[6]}
            def _view_bytes() -> bytes:
             with pathlib.Path(_view_ref['path']).open('rb') as stream:
              data = stream.read(2097153)
             if not 0 < len(data) <= 2097152 or len(data) != _view_ref['bytes'] or hashlib.sha256(data).hexdigest() != _view_ref['sha256']:
              raise ValueError('selected assembly actual changed')
             return data
            def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
             result: dict[str, object] = {}
             for name, value in pairs:
              if name in result:
               raise ValueError('duplicate assembly field')
              result[name] = value
             return result
            _view = json.loads(_view_bytes(), object_pairs_hook=_unique_fields)
            _reference_view = _view.get('schema') == 'xar.sdk-reference-actual/v1'
            if _reference_view:
             if (_view.get('status') != 'REFERENCE_INPUTS_ASSEMBLED_NOT_IMPORTED'
               or _view.get('purpose') not in ('LEGACY_REFERENCE_ONLY', 'REFERENCE_ORACLE_ONLY')
               or any(_view.get(key) is not False for key in ('actual_imports_observed', 'runtime_qualified', 'prepared'))):
              raise ValueError('explicit unchanged legacy reference inputs required')
            elif (_view.get('schema') != 'xar.sdk-source-assembly-actual/v1'
              or _view.get('status') != 'SOURCE_ASSEMBLED_NOT_IMPORTED'):
             raise ValueError('explicit selected actual schema/status required')
            if pathlib.Path(_view['graph_root']).resolve() != root:
             raise ValueError('selected actual physical root differs')
            _expected_sources: dict[str, _SourceRef] = {}
            for row in _view['actual_source_closure']:
             name, ref = row['relative_path'], row['actual']
             if (not isinstance(name, str) or not isinstance(ref, dict) or set(ref) != {'path', 'bytes', 'sha256'}
               or not isinstance(ref['path'], str) or type(ref['bytes']) is not int
               or ref['bytes'] < 0 or not isinstance(ref['sha256'], str)
               or pathlib.Path(ref['path']).resolve() != (root / name).resolve()
               or not pathlib.Path(ref['path']).resolve().is_relative_to(root)):
              raise ValueError('invalid selected actual source')
             if name.endswith('.py'):
              if name in _expected_sources:
               raise ValueError('duplicate selected source')
              _expected_sources[name] = {'path': name, 'bytes': ref['bytes'], 'sha256': ref['sha256']}
            _import_roots = tuple(pathlib.Path(p).resolve(strict=True) for p in _view['import_roots'])
            if (not _expected_sources or any(not p.is_relative_to(root) for p in _import_roots)
              or not {root, root / 'ck3_autonomous_player/src', root / 'ck3_autonomous_player/tests/unit'}.issubset(_import_roots)):
             raise ValueError('fresh import roots required')
            for p in reversed(_import_roots):
             sys.path.insert(0, str(p))
            _routes = {r['module']: r for r in _view['selected_import_routes']}
            for name in ('tools.ck3_live_run_id', 'xar_autoplayer.bridge.native_driver',
              'ck3_autonomous_player.tests.unit.test_life_advance_pause_map_unavailable_retry',
              'ck3_autonomous_player.tests.unit.test_native_bridge_driver',
              'test_war_termination_terms_contract', 'test_raiktor_war_bound_regiment_contract'):
             if name not in _routes or _routes[name]['location'] != 'FRESH_GRAPH':
              raise ValueError('fresh route required: ' + name)
            def _repo_source(filename: str | pathlib.Path) -> pathlib.Path | None:
                original = pathlib.Path(filename).absolute()
                source = original.resolve()
                if original.is_relative_to(root) and not source.is_relative_to(root) and not any(original.is_relative_to(prefix) for prefix in _interpreter_prefixes):
                    raise ValueError('repository import escaped the resolved source root:' + str(original))
                if any(source.is_relative_to(prefix) for prefix in _interpreter_prefixes):
                    return None
                if not source.is_relative_to(root):
                    raise ValueError('module source outside repository and declared interpreter prefixes:' + str(source))
                if source.suffix != '.py':
                    raise ValueError('repository import has unsupported non-source origin:' + str(source))
                return source
            def _measure_source(source: pathlib.Path, raw: bytes | None = None) -> _SourceRef:
                content = source.read_bytes() if raw is None else raw
                return {'path': source.relative_to(root).as_posix(), 'bytes': len(content),
                    'sha256': hashlib.sha256(content).hexdigest()}
            def _record_source(source: pathlib.Path, raw: bytes) -> None:
                measured = _measure_source(source, raw)
                if _expected_sources.get(measured["path"]) != measured:
                    raise ValueError("source differs from actual:" + measured["path"])
                previous = _measured_sources.setdefault(measured['path'], measured)
                if previous != measured:
                    raise ValueError('repository source changed before repeated execution:' + measured['path'])
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
                raise ValueError('repository modules loaded before source observation:' + str(sorted(_initial_repo_sources)[:8]))
            class _MeasuredRepoSourceLoader(importlib.machinery.SourceFileLoader):
                def get_code(self, fullname: str) -> CodeType:
                    source = _repo_source(self.get_filename(fullname))
                    if source is None:
                        raise ValueError('measured loader escaped repository scope')
                    raw = source.read_bytes()
                    _record_source(source, raw)
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
                        raise ValueError('repository source has unsupported loader:' + fullname)
                    spec.loader = _MeasuredRepoSourceLoader(fullname, str(source))
                    return spec
            sys.meta_path.insert(sys.meta_path.index(importlib.machinery.PathFinder), _RepoSourceObserver())
            def _verify_routes() -> None:
             for name, module in tuple(sys.modules.items()):
              filename = getattr(module, '__file__', None)
              if isinstance(filename, str) and name in _routes:
               if pathlib.Path(filename).resolve() != pathlib.Path(_routes[name]['physical_ref']['path']).resolve():
                raise ValueError('module selected wrong view: ' + name)
              spec = getattr(module, '__spec__', None)
              locations = None if spec is None else spec.submodule_search_locations
              if filename is not None or locations is None:
               continue
              actual = {pathlib.Path(p).resolve() for p in locations}
              if actual and all(any(p.is_relative_to(prefix) for prefix in _interpreter_prefixes) for p in actual):
               continue
              wanted = {p.joinpath(*name.split('.')).resolve() for p in _import_roots}
              wanted = {p for p in wanted if p.is_dir() and not (p / '__init__.py').exists()}
              if not wanted or actual != wanted:
               raise ValueError('namespace escaped view: ' + name)
            def _verify_sources(stage: str) -> int:
                _view_bytes()
                _verify_routes()
                loaded = _repo_modules()
                unrecorded = loaded.difference(_measured_sources)
                if unrecorded:
                    raise ValueError(stage + ' has unrecorded repository modules:' + str(sorted(unrecorded)[:8]))
                for name, before_ref in tuple(_measured_sources.items()):
                    if _measure_source(root / name) != before_ref:
                        raise ValueError(stage + ' repository source changed:' + name)
                return len(loaded)
            from tools.ck3_live_run_id import current_machine_id
            from xar_autoplayer.bridge import native_driver as n
            from ck3_autonomous_player.tests.unit.test_life_advance_pause_map_unavailable_retry import LifeAdvancePauseMapUnavailableRetryTests
            from ck3_autonomous_player.tests.unit.test_native_bridge_driver import NativeHeadlessGameplayDriverTests
            _machine_id = current_machine_id()
            _after_imports_repo_sources = _verify_sources('after actual fixture imports')
            spec_bytes = spec_path.read_bytes()
            if len(spec_bytes) > 32768:
                raise ValueError('timeline owner input manifest exceeds32KiB')
            spec = json.loads(spec_bytes)
            if (set(spec) != {'schema', 'cases'}
                    or spec['schema'] != 'xar.ck3.java-timeline-owner-producer-inputs/v1'
                    or len(spec['cases']) != 38 or len({row['id'] for row in spec['cases']}) != 38):
                raise ValueError('wrong timeline owner fixture version')
            fields = ('date_raw', 'paused', 'speed', 'map_ready', 'active_event', 'pending_character_interaction',
                'one_life_terminal_reason', 'episode_character_id', 'episode_run_id', 'local_player_id',
                'played_character', 'diagnostics', 'revision', 'native_revision')
            def projection(frame):
                result = {key: copy.deepcopy(frame[key]) for key in fields if key in frame}
                for key, selected in [('diagnostics', ('bridge_pid', 'connection_generation')),
                        ('played_character', ('character_id', 'alive'))]:
                    if isinstance(result.get(key), dict):
                        result[key] = {name: result[key][name] for name in selected if name in result[key]}
                return result
            probe = None
            java_calls = {'manual_cases': 0, 'consumers': 0}
            if differential:
                probe = subprocess.Popen([sys.argv[7], '-Xms16m', '-Xmx64m',
                    '-XX:MaxMetaspaceSize=64m', '-XX:ReservedCodeCacheSize=32m',
                    '-XX:MaxDirectMemorySize=16m', '-Xss512k',
                    '-Djava.io.tmpdir=' + str(output_path.with_name(output_path.name + '.tmp')),
                    '-cp', sys.argv[8],
                    'org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwnerProbe'],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, cwd=root)
                def close_probe():
                    if probe.poll() is None:
                        try:
                            probe.stdin.close()
                        except BrokenPipeError:
                            pass
                        try:
                            probe.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            probe.kill(); probe.wait(timeout=5)
                atexit.register(close_probe)
            def java_result(request, scope):
                raw = json.dumps(request, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
                if len(raw) > 32768:
                    raise ValueError('timeline owner request exceeds32KiB pipe budget')
                probe.stdin.write(raw + b'\\n'); probe.stdin.flush()
                wire = probe.stdout.readline(1025)
                if len(wire) > 1024 or not wire.endswith(b'\\n'):
                    raise ValueError('missing or oversized Java timeline owner result')
                result = json.loads(wire)
                java_calls[scope] += 1
                if result == {'test_transport_status': 'invalid_contract'}:
                    return result
                required = {'schema', 'kind', 'reason', 'replay_allowed', 'action_admission_granted',
                    'source_admission_granted', 'saved_day_credit'}
                if (set(result) != required or result['schema'] != 'xar.ck3.timeline-owner-facts/v1'
                        or result['kind'] not in ('same_facts', 'changed', 'unavailable')
                        or not isinstance(result['reason'], str) or not result['reason']
                        or any(result[name] is not False for name in ('replay_allowed',
                            'action_admission_granted', 'source_admission_granted'))
                        or type(result['saved_day_credit']) is not int or result['saved_day_credit'] != 0):
                    raise ValueError('Java result is not bounded non-authoritative timeline facts')
                return result
            fixture = LifeAdvancePauseMapUnavailableRetryTests()
            fixture.setUp()
            try:
                paused = projection(fixture.driver.take_internal_semantic_snapshot())
                fixture.date_raw += 24; fixture.revision += 1; fixture._publish(paused=False)
                running = projection(fixture.driver.take_internal_semantic_snapshot())
                fixture.popup_after_rejection = 1; fixture.pause_count = 1
                fixture.revision += 1; fixture._publish(paused=False)
                popup = projection(fixture.driver.take_internal_semantic_snapshot())
                fixture.revision += 1; fixture._publish(paused=False)
                settled = projection(fixture.driver.take_internal_semantic_snapshot())
            finally:
                fixture.tearDown()
            bases = {'paused': {'previous': paused, 'refreshed': paused},
                'running': {'previous': running, 'refreshed': running},
                'popup': {'previous': paused, 'refreshed': popup, 'settled': settled}}
            rows = []
            for case in spec['cases']:
                request = {'schema': 'xar.ck3.timeline-owner-facts-request/v1', 'operation': case['operation'],
                    **{name: copy.deepcopy(frame) for name, frame in bases[case['base']].items()}}
                for mutation in case['mutations']:
                    node = request[mutation['frame']]
                    for key in mutation['path'][:-1]:
                        node = node[key]
                    key = mutation['path'][-1]
                    if mutation['operation'] == 'remove':
                        del node[key]
                    else:
                        node[key] = copy.deepcopy(mutation['value'])
                previous, refreshed = request['previous'], request['refreshed']
                operation = case['operation']
                if operation == 'change':
                    result = n._retryable_life_advance_change(previous, refreshed)
                elif operation == 'pause_owner':
                    result = n._retryable_life_advance_pause_owner(previous, refreshed)
                elif operation == 'resume_owner':
                    result = n._retryable_life_advance_resume_owner(previous, refreshed)
                elif operation == 'popup_owner':
                    result = n._same_life_advance_popup_pause_owner(previous, refreshed, request['settled'])
                else:
                    raise ValueError('unexpected fixture operation')
                if type(result) is not bool:
                    raise ValueError('actual producer did not return a bool')
                rows.append({'id': case['id'], 'java_expected': case['java_expected'],
                    'compatibility': case['compatibility'], 'legacy_result': result,
                    'input_json': json.dumps(request, ensure_ascii=False, allow_nan=False, separators=(',', ':'))})
                if differential:
                    actual = java_result(request, 'manual_cases')
                    if case['java_expected'] == 'rejected':
                        if actual != {'test_transport_status': 'invalid_contract'}:
                            raise ValueError('Java accepted malformed original fixture:' + case['id'])
                    elif actual.get('kind') != case['java_expected']:
                        raise ValueError('Java fixture facts differ:' + case['id'])
                    elif case['compatibility'] == 'equivalent' and (actual['kind'] == 'same_facts') != result:
                        raise ValueError('Java differs from equivalent actual producer:' + case['id'])
            names = ('_retryable_life_advance_change', '_retryable_life_advance_timeline_owner',
                '_retryable_life_advance_resume_owner', '_retryable_life_advance_pause_owner',
                '_same_life_advance_popup_pause_owner')
            consumer_calls = {name: {'calls': 0, 'true': 0, 'false': 0} for name in names}
            def instrument(name, original):
                signature = inspect.signature(original)
                def observed(*args, **kwargs):
                    result = original(*args, **kwargs)
                    if type(result) is not bool:
                        raise ValueError('original owner function did not return bool:' + name)
                    row = consumer_calls[name]; row['calls'] += 1; row['true' if result else 'false'] += 1
                    if differential:
                        bound = signature.bind(*args, **kwargs).arguments
                        operation = {'_retryable_life_advance_change': 'change',
                            '_retryable_life_advance_resume_owner': 'resume_owner',
                            '_retryable_life_advance_pause_owner': 'pause_owner',
                            '_same_life_advance_popup_pause_owner': 'popup_owner'}.get(name)
                        if name == '_retryable_life_advance_timeline_owner':
                            if type(bound['expected_paused']) is not bool:
                                raise ValueError('original timeline expected_paused is not boolean')
                            operation = 'resume_owner' if bound['expected_paused'] else 'pause_owner'
                        previous = bound['starting'] if operation == 'popup_owner' else bound['previous']
                        request = {'schema': 'xar.ck3.timeline-owner-facts-request/v1', 'operation': operation,
                            'previous': projection(previous), 'refreshed': projection(bound['refreshed'])}
                        if operation == 'popup_owner':
                            request['settled'] = projection(bound['settled'])
                        actual = java_result(request, 'consumers')
                        if 'kind' not in actual:
                            raise ValueError('actual original consumer supplied invalid Java boundary:' + name)
                        java_value = actual['kind'] == 'same_facts'
                        if java_value != result:
                            raise ValueError('Java changed original fixture consumer outcome:' + name)
                        row['java_calls'] += 1
                        return java_value
                    return result
                return observed
            selected = [name for name in unittest.defaultTestLoader.getTestCaseNames(NativeHeadlessGameplayDriverTests)
                if name.startswith('test_resume_life_advance_') or name.startswith('test_pause_life_advance_')
                or name == 'test_composite_life_advance_retries_one_natural_revision_race']
            suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(LifeAdvancePauseMapUnavailableRetryTests),
                unittest.TestSuite(NativeHeadlessGameplayDriverTests(name) for name in selected)])
            for row in consumer_calls.values():
                row['java_calls'] = 0
            with ExitStack() as stack:
                for name in names:
                    stack.enter_context(patch.object(n, name, instrument(name, getattr(n, name))))
                tested = unittest.TextTestRunner(verbosity=2).run(suite)
            if not tested.wasSuccessful() or tested.skipped or any(row['calls'] == 0 for row in consumer_calls.values()):
                raise ValueError('actual consumer regression failed, skipped or missed an owned producer')
            if differential:
                probe.stdin.close()
                if probe.wait(timeout=10) != 0 or probe.stdout.read(1):
                    raise ValueError('Java pipe did not finish cleanly at EOF')
                if java_calls['manual_cases'] != len(rows) or any(row['calls'] != row['java_calls'] for row in consumer_calls.values()):
                    raise ValueError('Java did not return through every original consumer call')
            _after_suite_repo_sources = _verify_sources('after complete original consumer suite')
            before = sorted(_measured_sources.values(), key=lambda row: row['path'])
            result = {'schema': ('xar.ck3.java-timeline-owner-producer-differential/v1' if differential
                    else 'xar.ck3.java-timeline-owner-producer-golden/v1'),
                'machine_id': _machine_id, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
                'source_provenance': {'schema': 'xar.ck3.measured-repo-import-closure/v1',
                    'scope': 'repo-python-excluding-interpreter-prefixes/v1',
                    'assembly_actual_ref': _view_ref, 'selected_view': 'legacy',
                    'interpreter_prefixes': sorted(str(prefix) for prefix in _interpreter_prefixes),
                    'external_dependency_qualification': 'not_granted_by_repo_source_observer',
                    'initial_repo_sources': 0, 'after_imports_repo_sources': _after_imports_repo_sources,
                    'after_suite_repo_sources': _after_suite_repo_sources,
                    'recorded_repo_sources': len(_measured_sources), 'source_pre_post_equal': True,
                    'unrecorded_repo_sources': []},
                'source_refs': before, 'input_spec_sha256': hashlib.sha256(spec_bytes).hexdigest(),
                'method': ('actual_compiled_java_to_original_fixture_consumers' if differential
                    else 'actual_native_driver_pure_owner_leaves_and_existing_fake_wire_consumers'),
                'original_tests': tested.testsRun, 'original_skipped': len(tested.skipped),
                'full_pause_test_case': 'LifeAdvancePauseMapUnavailableRetryTests',
                'selected_native_driver_tests': selected, 'consumer_calls': consumer_calls, 'cases': rows,
                'java_calls': java_calls,
                'fixture_environment': {'XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1': os.environ['XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1'],
                    'PYTHONOPTIMIZE': os.environ['PYTHONOPTIMIZE'], 'python_optimize_level': sys.flags.optimize},
                'game_rpc': 0, 'native_calls': 0, 'ledger_writes': 0, 'saved_day_credit': 0}
            if _reference_view:
             provenance = result['source_provenance']
             del provenance['assembly_actual_ref']
             provenance.update({'schema': 'xar.ck3.measured-repo-import-closure/' + ('v3' if _view['purpose'] == 'REFERENCE_ORACLE_ONLY' else 'v2'),
               'selected_view': 'oracle_reference' if _view['purpose'] == 'REFERENCE_ORACLE_ONLY' else 'legacy_reference', 'reference_actual_ref': _view_ref,
               'reference_actual_schema': _view['schema'], 'reference_purpose': _view['purpose'],
               'reference_status': _view['status'],
               'reference_actual_imports_observed': _view['actual_imports_observed'],
               'reference_runtime_qualified': _view['runtime_qualified'], 'reference_prepared': _view['prepared']})
            raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\\n').encode('utf-8')
            if len(raw) > 98304:
                print(json.dumps({'status': 'GOLDEN_OVER_CAP', 'golden_bytes': len(raw),
                    'maximum_bytes': 98304, 'recorded_repo_sources': len(_measured_sources),
                    'compact_source_refs_bytes': len(json.dumps(before, sort_keys=True, separators=(',', ':')).encode('utf-8'))}))
                raise ValueError('complete original import closure and cases exceed96KiB finite budget')
            with output_path.open('xb') as stream:
                stream.write(raw)
            print(json.dumps({'status': 'CAPTURED', 'cases': len(rows), 'original_tests': tested.testsRun,
                'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'consumer_calls': consumer_calls,
                'java_calls': java_calls, 'differential': differential}))
            """;
}
