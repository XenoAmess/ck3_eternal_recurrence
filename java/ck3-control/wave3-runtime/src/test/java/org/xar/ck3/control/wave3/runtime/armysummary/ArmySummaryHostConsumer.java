package org.xar.ck3.control.wave3.runtime.armysummary;

/** Same-process SDK consumer program for Root's one qualified host/overlay runner.
 * Root must bootstrap the canonical client and apply the exact SDK patch before execution.
 * This class launches no JVM, Python process, HTTP service, or replacement authority.
 */
public final class ArmySummaryHostConsumer {
    private ArmySummaryHostConsumer() { }
    public static String program() { return PROGRAM; }
    private static final String PROGRAM = """
            from __future__ import annotations
            import asyncio
            import contextlib
            from datetime import datetime, timezone
            import hashlib
            import inspect
            import io
            import os
            from pathlib import Path
            from typing import TypedDict
            from unittest.mock import patch
            from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1, exact_read
            from tools.g2_saved_campaign import java_map_admission_client_v1 as client
            
            class ArmyCall(TypedDict):
                request_id: str
                operation: str
                payload_bytes: int
                payload_sha256: str
                result_bytes: int
                result_sha256: str
                request_sha256: str
                response_sha256: str
                identity_sha256: str
                java_pid: int
                java_birth: str
                actual_http: bool
            
            def _army_same_json_v1(left: object, right: object) -> bool:
                if type(left) is not type(right):
                    return False
                if isinstance(left, dict) and isinstance(right, dict):
                    return left.keys() == right.keys() and all(_army_same_json_v1(left[key], right[key]) for key in left)
                if isinstance(left, list) and isinstance(right, list):
                    return len(left) == len(right) and all(_army_same_json_v1(a, b) for a, b in zip(left, right))
                return left == right
            
            class ArmyProjectionAttempt(TypedDict):
                config: client.JavaProjectionServiceV1
                operation: client.ProjectionOperation
                payload: bytes
                request_id: str

            class ArmyProjectionEvents(TypedDict):
                config: client.JavaProjectionServiceV1
                attempts: list[ArmyProjectionAttempt]
                completed: list[client.ProjectionResult]
                failed_returns: list[ArmyProjectionAttempt]
                observer_errors: list[str]

            def run_army_summary_java_consumer_v1(*, repository: Path,
                consumer_repository: Path, producer_ref: ExactRefV1, work: Path,
                projection_events: ArmyProjectionEvents) -> dict[str, object]:
                '''Root invokes this in its already bootstrapped SDK process and shared patch overlay.'''
                import sys
                if sys.flags.optimize != 0:
                    raise RuntimeError('all original Army assertions require optimize=0')
                config = client.require_current_projection_config_v1()
                if config.transport is not None:
                    raise RuntimeError('Army differential requires the real resident Java host')
                if (len(client.ProjectionOperation) != 143 or config.client_source_ref.bytes != 77936
                        or config.client_source_ref.sha256 != '238965ac746fcce9d29b353f5972e0daa6e1a1dbc81a4bdf755ec2329bb9f3d7'):
                    raise RuntimeError('Army consumer requires the exact final143 shared client')
                identity = client.qualify_projection_service_v1(config)
                for operation in (client.ProjectionOperation.ARMY_QUERY_SUMMARY_PROJECT,
                                  client.ProjectionOperation.ARMY_AUTO_SUMMARY_PROJECT):
                    profile = identity.profile(operation)
                    if (profile.input_max_bytes, profile.output_max_bytes) != (1048576, 65536):
                        raise RuntimeError('Army host profile differs from the unchanged codec')
                root = repository.resolve()
                consumer_root = consumer_repository.resolve(strict=True)
                if consumer_root == root or consumer_root.is_relative_to(root):
                    raise RuntimeError('actual consumer repository must be the selected fresh D view')
                unit = consumer_root/'ck3_autonomous_player/tests/unit'
                if not unit.is_dir() or not any(isinstance(entry,str) and Path(entry).resolve() == unit.resolve() for entry in sys.path):
                    raise RuntimeError('Root must install the exact selected consumer unit import route')
                fresh = work.resolve()
                if fresh.exists():
                    raise RuntimeError('fresh bounded Army consumer work directory required')
                fresh.mkdir(parents=True)
                original = exact_read(config.reader, producer_ref, 262144)
                corpus = client.decode_projection_object_v1(original, maximum_bytes=262144)
                if (corpus.get('schema') != 'xar.java.army-mcp-summary-producer-golden/v1'
                        or corpus.get('machine_id') != config.machine_id
                        or not _army_same_json_v1(corpus.get('original_consumer_tests'), {'passed':17,'failed':0,'skipped':0})):
                    raise RuntimeError('mandatory actual original Army producer corpus unavailable or incomplete')
                provenance = corpus.get('source_provenance')
                if not isinstance(provenance, dict) or provenance.get('source_pre_post_equal') is not True or provenance.get('unrecorded_repo_sources') != []:
                    raise RuntimeError('original Army corpus lacks the measured complete import closure')
                cases = corpus.get('cases')
                if not isinstance(cases, list) or len(cases) != 24:
                    raise RuntimeError('all 24 original Army producer cases are mandatory')
                # The shared Root overlay must have compiled these patched SDK modules before import.
                from xar_autoplayer.bridge import army_strengths_mcp_result as army
                from xar_autoplayer.bridge import mcp_server
                from test_army_profile_mcp_compact_regression import _registered_army_server
                from mcp.types import CallToolResult
                if hasattr(army, '_army_strengths_summary'):
                    raise RuntimeError('legacy Python Army business builder remains on the candidate path')
                for function in (army.build_army_strengths_mcp_result, army.build_army_auto_turn_mcp_result):
                    filename = inspect.getsourcefile(function)
                    if filename is None or Path(filename).resolve().is_relative_to(root):
                        raise RuntimeError('Army callbacks did not load from the fresh measured D overlay')
                if (mcp_server.build_army_strengths_mcp_result is not army.build_army_strengths_mcp_result
                        or mcp_server.build_army_auto_turn_mcp_result is not army.build_army_auto_turn_mcp_result):
                    raise RuntimeError('registered SDK callbacks do not use the candidate Java adapters')
            
                if (type(projection_events) is not dict or set(projection_events) != {
                        'config','attempts','completed','failed_returns','observer_errors'}
                        or projection_events['config'] is not config):
                    raise RuntimeError('Root must pass the original same-process Army projection journal')
                if any(type(value) is not list for value in (
                        projection_events['attempts'],projection_events['completed'],
                        projection_events['failed_returns'],projection_events['observer_errors'])):
                    raise RuntimeError('Root projection journal lists must be the original live objects')
                if projection_events['observer_errors']:
                    raise RuntimeError('Root issued-context observer already rejected a result')
                attempts_base = len(projection_events['attempts'])
                completed_cursor = len(projection_events['completed'])
                failures_base = len(projection_events['failed_returns'])
                calls: list[ArmyCall] = []
                attempts: list[tuple[str, str]] = []
                client_callable = client.call_projection_v1
                client_code = client_callable.__code__
                hook_before = (sys.getprofile(), sys.gettrace())
                import threading
                thread_hooks_before = (threading.getprofile(), threading.gettrace())
                def sync_army_events() -> None:
                    nonlocal completed_cursor
                    if (client.call_projection_v1 is not client_callable or client_callable.__code__ is not client_code
                            or client.require_current_projection_config_v1() is not config
                            or (sys.getprofile(),sys.gettrace()) != hook_before
                            or (threading.getprofile(),threading.gettrace()) != thread_hooks_before):
                        raise RuntimeError('Army consumer changed the actual shared client/config/observation authority')
                    if projection_events['observer_errors']:
                        raise RuntimeError('actual Root observer recorded a source/context error')
                    army_operations = (client.ProjectionOperation.ARMY_QUERY_SUMMARY_PROJECT,
                        client.ProjectionOperation.ARMY_AUTO_SUMMARY_PROJECT)
                    if any(entry['operation'] in army_operations for entry in projection_events['failed_returns'][failures_base:]):
                        raise RuntimeError('actual Root observer recorded an Army failed exit')
                    original_attempts = projection_events['attempts'][attempts_base:]
                    attempt_by_id: dict[str, ArmyProjectionAttempt] = {}
                    for attempt in original_attempts:
                        if (type(attempt) is not dict or set(attempt) != {'config','operation','payload','request_id'}
                                or attempt['config'] is not config or type(attempt['payload']) is not bytes
                                or type(attempt['request_id']) is not str
                                or not isinstance(attempt['operation'],client.ProjectionOperation)):
                            raise RuntimeError('Root Army attempt journal lost exact original argument custody')
                        if attempt['operation'] not in army_operations:
                            continue
                        if attempt['request_id'] in attempt_by_id:
                            raise RuntimeError('duplicate actual Army request identity')
                        attempt_by_id[attempt['request_id']] = attempt
                    attempts[:] = [(entry['request_id'],entry['operation'].value) for entry in attempt_by_id.values()]
                    new_completed = projection_events['completed'][completed_cursor:]
                    for result in new_completed:
                        if not isinstance(result, client.ProjectionResult):
                            raise RuntimeError('Root Army completion journal must retain the original issued result object')
                        if result.operation not in army_operations:
                            continue
                        attempt = attempt_by_id.get(result.request_id)
                        if attempt is None:
                            raise RuntimeError('actual Army result has no matching observed original call attempt')
                        context = client.require_result_context_v1(result, config=config, operation=attempt['operation'],
                            request_id=attempt['request_id'], payload=attempt['payload'])
                        call = result.http_call
                        if (call.transport_kind != 'stdlib-http-loopback/v1' or not call.actual_http_invoked
                                or call.status != 'completed' or context.process != identity.process):
                            raise RuntimeError('Army summary lacks same-host successful actual HTTP/issuance custody')
                        calls.append({'request_id':result.request_id,'operation':result.operation.value,
                            'payload_bytes':len(result.payload_bytes),'payload_sha256':result.payload_sha256,
                            'result_bytes':len(result.result_bytes),'result_sha256':hashlib.sha256(result.result_bytes).hexdigest(),
                            'request_sha256':result.request_sha256,'response_sha256':result.response_sha256,
                            'identity_sha256':result.host_identity.identity_sha256,
                            'java_pid':context.process.pid,'java_birth':context.process.creation_filetime,'actual_http':True})
                    completed_cursor += len(new_completed)
                def measured_call(*, config: client.JavaProjectionServiceV1,
                    operation: client.ProjectionOperation, payload: bytes,
                    request_id: str) -> client.ProjectionResult:
                    result = client_callable(config=config, operation=operation, payload=payload, request_id=request_id)
                    client.require_result_context_v1(result,config=config,operation=operation,request_id=request_id,payload=payload)
                    sync_army_events()
                    return result

                corpus_results: list[dict[str, object]] = []
                route_results: list[dict[str, object]] = []
                test_results: list[dict[str, object]] = []
                names = ('test_army_strengths_mcp_result_serialization_performance.py',
                         'test_army_profile_mcp_compact_regression.py',
                         'test_army_auto_scalar_projection_v1.py')
                import pytest
                class Outcomes:
                    passed: int = 0
                    failed: int = 0
                    skipped: int = 0
                    before: int = 0
                    before_attempts: int = 0
                    current: str = ''
                    def pytest_runtest_setup(self, item: pytest.Item) -> None:
                        # GET qualification also precedes Service-only synthetic native actions.
                        client.qualify_projection_service_v1(config)
                        sync_army_events()
                        self.before = len(calls)
                        self.before_attempts = len(attempts)
                        self.current = item.nodeid
                    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
                        if report.skipped:
                            self.skipped += 1
                        if report.when == 'call':
                            sync_army_events()
                            if report.passed:
                                self.passed += 1
                            else:
                                self.failed += 1
                            node = report.nodeid
                            is_guard = '::test_army_strengths_full_failure_is_visible_without_core_retry[' in node
                            is_service_only = names[2] in node
                            count = len(calls) - self.before
                            attempted = len(attempts) - self.before_attempts
                            reason = ('original native profile rejection before summary' if is_guard else
                                      'original Service/Driver scalar and cache assertions do not request MCP summary'
                                      if is_service_only else 'original consumer must use actual Java summary')
                            test_results.append({'nodeid': node, 'passed': report.passed,
                                'java_calls': count, 'java_call_attempts': attempted,
                                'zero_java_expected': is_guard or is_service_only,
                                'reason': reason})
                            if (attempted != count or (is_guard or is_service_only) and attempted != 0
                                    or not (is_guard or is_service_only) and count == 0):
                                self.failed += 1
            
                outcomes = Outcomes()
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch.dict(os.environ, {'XAR_ARMY_RESULT_PERFORMANCE_CASE_OUTPUT':
                        str(fresh/'existing-serialization-metrics.json')}, clear=False):
                    for index, case in enumerate(cases):
                        if not isinstance(case, dict):
                            raise RuntimeError('original Army corpus case object required')
                        name = case.get('name')
                        kind = case.get('kind')
                        raw_input = case.get('input_json')
                        expected = case.get('expected')
                        if not isinstance(name, str) or kind not in ('query','auto') or not isinstance(raw_input, str):
                            raise RuntimeError('exact original Army case identity/input required')
                        payload = raw_input.encode('utf-8')
                        operation = (client.ProjectionOperation.ARMY_AUTO_SUMMARY_PROJECT if kind == 'auto'
                                     else client.ProjectionOperation.ARMY_QUERY_SUMMARY_PROJECT)
                        observed = measured_call(config=config, operation=operation, payload=payload,
                            request_id='army-corpus-' + str(index))
                        actual = client.decode_projection_json_v1(observed.require_success(), maximum_bytes=65536)
                        if not _army_same_json_v1(expected, actual):
                            raise RuntimeError('actual Java output differs from original producer case: ' + name)
                        CallToolResult.model_validate_json(observed.result_bytes)
                        corpus_results.append({'name': name, 'kind': kind, 'matched': True,
                            'input_bytes_preserved': True, 'java_calls': 1})
                    for route in ('direct','execute','auto','full'):
                        sync_army_events()
                        before = len(calls)
                        client.qualify_projection_service_v1(config)
                        with _registered_army_server() as (server, driver, snapshot, requests):
                            if route == 'auto':
                                with patch('xar_autoplayer.bridge.service.choose_one_life_turn', return_value={
                                    'selected_step':'query-army-strengths-v1','phase':'synthetic_army_query'}):
                                    result = asyncio.run(server.call_tool('ck3_auto_turn', {}))
                            elif route == 'execute':
                                result = asyncio.run(server.call_tool('ck3_execute_step', {
                                    'step':'query-army-strengths-v1','expected_revision':snapshot['revision']}))
                            else:
                                arguments = {'army_ids':[82,81], 'expected_revision':snapshot['revision']}
                                if route == 'full':
                                    arguments['profile'] = 'observed_history_full_v1'
                                result = asyncio.run(server.call_tool('ck3_query_army_strengths', arguments))
                            sync_army_events()
                            if result.is_error or result.result_type != 'complete' or len(calls) - before != 1:
                                raise RuntimeError('actual registered Army route lacks exactly one complete Java result: ' + route)
                            if not isinstance(result.structured_content, dict):
                                raise RuntimeError('actual Java route did not reach SDK structured consumer')
                            text_value = client.decode_projection_json_v1(result.content[0].text.encode('utf-8'), maximum_bytes=65536)
                            if not _army_same_json_v1(text_value, result.structured_content):
                                raise RuntimeError('actual Java text and structured SDK results disagree')
                            route_results.append({'route':route, 'java_calls':len(calls)-before,
                                'registered_native_requests':len(requests), 'complete':True})
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        code = pytest.main(['-q','--assert=plain','-p','no:cacheprovider',
                            '--basetemp',str(fresh/'pytest-tmp'),
                            *[str(consumer_root/'ck3_autonomous_player/tests/unit'/name) for name in names]], plugins=[outcomes])
                sync_army_events()
                for label, stream in (('stdout',stdout),('stderr',stderr)):
                    raw = stream.getvalue().encode('utf-8')
                    with (fresh/('java-consumer-'+label+'.log')).open('xb') as output:
                        output.write(raw[:32768])
                    if len(raw) > 32768:
                        raise RuntimeError('bounded original consumer log exceeded: ' + label)
                if (code != 0 or outcomes.passed != 17 or outcomes.failed or outcomes.skipped
                        or len(test_results) != 17 or len(attempts) != len(calls)
                        or sum(row['zero_java_expected'] is True for row in test_results) != 8):
                    raise RuntimeError('Army original consumer closure failed: code=' + str(code)
                        + ' passed=' + str(outcomes.passed) + ' failed=' + str(outcomes.failed)
                        + ' skipped=' + str(outcomes.skipped))
                client.qualify_projection_service_v1(config)
                return {'schema':'xar.java.army-mcp-summary-host-consumer/v1','status':'PASS',
                    'original_consumer_case_count':17,'java_positive_case_count':9,'java_zero_case_count':8,
                    'consumer_repository':str(consumer_root),'client_source_ref':config.client_source_ref.to_wire(),
                    'machine_id':config.machine_id, 'observed_at_utc':datetime.now(timezone.utc).isoformat(),
                    'producer_ref':producer_ref.to_wire(),
                    'corpus_cases':corpus_results, 'registered_routes':route_results,
                    'original_consumer_tests':{'passed':outcomes.passed,'failed':outcomes.failed,'skipped':outcomes.skipped,
                        'case_results':test_results},
                    'java_calls':calls, 'java_call_attempts':len(attempts),
                    'old_python_business_builder_calls':0,
                    'python_fallback_used':False, 'actual_same_host_http':True,
                    'game_calls':0, 'new_save_days_credit':0, 'runtime_cutover':False}
            
            """;
}


