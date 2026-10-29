package org.xar.ck3.control.wave3.planning.realmmembership;

/** Fixed test-only source. Root bootstraps the real single client, then executes this in that same Python process. */
public final class CaptureRealmConsumerAdoption {
    private CaptureRealmConsumerAdoption() { }
    public static String source() { return SOURCE; }
    public static String legacySource() { return LEGACY; }
    public static void main(String[] arguments) {
        if (arguments.length != 1 || !(arguments[0].equals("--emit-consumer-harness") || arguments[0].equals("--emit-legacy-collector"))) {
            throw new IllegalArgumentException("only --emit-consumer-harness; Root must first bootstrap the actual shared client in its Python process");
        }
        System.out.print(arguments[0].equals("--emit-legacy-collector") ? LEGACY : SOURCE);
    }
    private static final String SOURCE = """
        from pathlib import Path
        from tools.g2_saved_campaign import java_map_admission_client_v1 as client

        def run_realm_java_consumers_v1(*, config: client.JavaProjectionServiceV1,
                baseline_ref: client.ExactRefV1, legacy_actual_ref: client.ExactRefV1,
                repo: Path | str, candidate_root: Path | str, oracle_fixture: Path | str,
                candidate_bindings: Path | str, output: Path | str,
                issued_projection_results: list[client.ProjectionResult]) -> client.JsonObject:
            '''Root bootstraps the real shared client first, in this same Python process.'''
            import base64
            import copy
            import dataclasses
            from datetime import datetime, timezone
            from decimal import Decimal
            import gzip
            import hashlib
            import importlib
            import io
            import json
            from pathlib import Path
            import sys
            from types import ModuleType, SimpleNamespace
            import unittest
            from tools.g2_saved_campaign import java_map_admission_client_v1 as client
            if client.require_current_projection_config_v1() is not config or config.transport is not None:
                raise ValueError('same actual Root-issued stdlib projection configuration required; no JSON reconstruction')
            if type(issued_projection_results) is not list:
                raise TypeError('Root must supply its actual shared issued-result observer list')
            def projection_results() -> tuple[client.ProjectionResult, ...]:
                if client.require_current_projection_config_v1() is not config:
                    raise ValueError('actual Root configuration changed before cash fixture observation')
                snapshot = tuple(issued_projection_results)
                for proof in snapshot:
                    if not isinstance(proof, client.ProjectionResult):
                        raise TypeError('shared observer contains a non-issued projection result')
                    client.require_result_context_v1(proof, config=config, operation=proof.operation,
                        request_id=proof.request_id, payload=proof.payload_bytes)
                return snapshot
            repo = Path(repo).resolve()
            candidate_root = Path(candidate_root).resolve()
            if candidate_root != repo:
                raise ValueError('one complete consumerActualRef source tree required; mixed original/overlay imports rejected')
            oracle_fixture = Path(oracle_fixture).resolve()
            candidate_bindings = Path(candidate_bindings).resolve()
            output = Path(output).resolve()
            if output.exists() or not output.parent.is_dir():
                raise ValueError('fresh output inside an already admitted parent required')
            def sha(raw):
                return hashlib.sha256(raw).hexdigest()
            def ref(path):
                path = Path(path)
                raw = path.read_bytes()
                return dict(path=str(path), bytes=len(raw), sha256=sha(raw))
            def wire(value):
                return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            def domain(raw):
                value = json.loads(raw.decode('utf-8'), parse_float=Decimal)
                def tag(item):
                    if item is None:
                        return ('null',)
                    if type(item) is bool:
                        return ('bool', item)
                    if type(item) is int:
                        return ('integer', item)
                    if isinstance(item, Decimal):
                        return ('decimal', Decimal(0) if item.is_zero() else item.normalize())
                    if type(item) is str:
                        return ('text', item)
                    if type(item) is list:
                        return ('array', tuple(tag(child) for child in item))
                    if type(item) is dict:
                        return ('object', tuple((key, tag(item[key])) for key in sorted(item)))
                    raise TypeError('undeclared JSON comparison domain')
                return tag(value)
            def recipe_key(operation, raw):
                normalized = json.dumps(domain(raw), ensure_ascii=False, allow_nan=False,
                    separators=(',', ':'), default=str).encode('utf-8')
                return operation + ':' + hashlib.sha256(normalized).hexdigest()
            if not isinstance(baseline_ref, client.ExactRefV1) or not isinstance(legacy_actual_ref, client.ExactRefV1):
                raise TypeError('unique argument_value must supply verified baseline/view ExactRefs')
            baseline_packed = Path(baseline_ref.path).read_bytes()
            if (len(baseline_packed), sha(baseline_packed)) != (baseline_ref.bytes, baseline_ref.sha256) or len(baseline_packed) > 49152:
                raise ValueError('immutable separately captured original baseline ExactRef changed')
            with gzip.GzipFile(fileobj=io.BytesIO(baseline_packed)) as stream:
                baseline_raw = stream.read(2097153)
            if len(baseline_raw) > 2097152:
                raise ValueError('bounded original baseline required')
            reference = json.loads(baseline_raw)
            if (reference['schema'] != 'xar.ck3.realm-original-consumer-baseline/v2' or reference['status'] != 'PASS'
                    or reference['machine_id'] != config.machine_id or reference['legacy_actual_ref'] != legacy_actual_ref.to_wire()
                    or (reference['original_tests'], reference['original_vectors'], reference['skipped'],
                        reference['failures'], reference['errors']) != (31, 29, 0, 0, 0)):
                raise ValueError('complete separately qualified original legacy31/vector baseline required')
            baseline = dict(tests=31, failures=0, errors=0, skipped=0, diagnostic=reference['diagnostic'])
            def original_entry(operation, request):
                key = recipe_key(operation, wire(request))
                entry = reference['entries'].get(key)
                if entry is None or entry['operation'] != operation or domain(entry['request_utf8'].encode('utf-8')) != domain(wire(request)):
                    raise ValueError('actual consumer request is absent from the immutable original baseline')
                return entry
            bundle_raw = oracle_fixture.read_bytes()
            bundle = json.loads(bundle_raw)
            packed = base64.b64decode(bundle['gzip_base64'], validate=True)
            if len(packed) != bundle['gzip_bytes'] or sha(packed) != bundle['gzip_sha256']:
                raise ValueError('immutable original source compression binding changed')
            decoded = gzip.decompress(packed)
            if len(decoded) != bundle['decoded_bytes'] or len(decoded) > 65536 or sha(decoded) != bundle['decoded_sha256']:
                raise ValueError('immutable original source archive binding changed')
            members = json.loads(decoded)
            originals = {}
            for entry in members['entries']:
                raw = entry['source_utf8'].encode('utf-8')
                if len(raw) != entry['bytes'] or sha(raw) != entry['sha256']:
                    raise ValueError('original oracle source byte binding changed')
                originals[entry['path']] = raw
            required = {
                'ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/realm_membership_after_query_v1.py',
            }
            if set(originals) != required | {'ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py'}:
                raise ValueError('exact three original source members required; cash is an immutable reference only')
            for relative, raw in originals.items():
                original_refs = [row for row in reference['frozen_original_sources']
                    if str(row['path']).replace('\\\\', '/').endswith('/' + relative)]
                if len(original_refs) != 1 or (original_refs[0]['bytes'], original_refs[0]['sha256']) != (len(raw), sha(raw)):
                    raise ValueError('immutable archived oracle differs from the separately qualified original baseline')
            declarations = json.loads(candidate_bindings.read_bytes())
            declared = {row['path']: row for row in declarations['candidate_source_refs']}
            if len(declared) != 8:
                raise ValueError('complete eight-source candidate binding required')
            candidate_paths = {relative: candidate_root / relative for relative in required}
            for relative, path in candidate_paths.items():
                actual = ref(path)
                if actual['bytes'] != declared[relative]['bytes'] or actual['sha256'] != declared[relative]['sha256']:
                    raise ValueError('candidate adapter source drift: ' + relative)
            client_key = 'tools/g2_saved_campaign/java_map_admission_client_v1.py'
            current_client = ref(client.__file__)
            if (current_client['bytes'], current_client['sha256']) != (declared[client_key]['bytes'], declared[client_key]['sha256']):
                raise ValueError('single qualified projection client source drift')
            service_java_refs = []
            for relative, expected in declared.items():
                if not relative.endswith('.java'):
                    continue
                matches = [item for item in config.service.source_refs
                           if Path(item.path).name == Path(relative).name
                           and item.bytes == expected['bytes'] and item.sha256 == expected['sha256']]
                if len(matches) != 1:
                    raise ValueError('actual admitted Java deployment lacks exact candidate source: ' + relative)
                service_java_refs.append(matches[0].to_wire())
            cash_key = 'ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py'
            related = declarations['related_consumer_source_refs']
            if len(related) != 1 or related[0]['path'] != cash_key:
                raise ValueError('the actual cash adapter is a required related consumer dependency')
            cash_observed = ref(repo / cash_key)
            if (cash_observed['bytes'], cash_observed['sha256']) != (related[0]['bytes'], related[0]['sha256']):
                raise ValueError('actual monthly consumer still lacks the selected cash Java adapter')
            sys.path[:0] = [str(repo), str(repo / 'ck3_autonomous_player/src'),
                           str(repo / 'ck3_autonomous_player/tests/unit')]
            import xar_autoplayer
            import xar_autoplayer.bridge
            def module_from_source(name, raw, origin):
                module = ModuleType(name)
                module.__file__ = origin
                module.__package__ = name.rsplit('.', 1)[0]
                sys.modules[name] = module
                parent_name, attribute = name.rsplit('.', 1)
                setattr(sys.modules[parent_name], attribute, module)
                exec(compile(raw, origin, 'exec'), module.__dict__)
                return module
            realm_name = 'xar_autoplayer.realm_membership_feedback_v1'
            after_name = 'xar_autoplayer.bridge.realm_membership_after_query_v1'
            realm_relative = 'ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py'
            after_relative = 'ck3_autonomous_player/src/xar_autoplayer/bridge/realm_membership_after_query_v1.py'
            modules = [
                'test_realm_membership_feedback_v1', 'test_realm_membership_after_query_v1',
                'test_realm_membership_service_v1', 'test_campaign_score_existing_inputs_v1',
            ]
            def suite_modules():
                loaded = []
                for name in modules:
                    module = importlib.import_module(name)
                    loaded.append(importlib.reload(module))
                cash_tests = loaded[-1]
                if (cash_tests.__name__ != 'test_campaign_score_existing_inputs_v1'
                        or cash_tests.projection_client is not client
                        or not issubclass(cash_tests.ExistingMonthInputsTests, cash_tests.CashMetricsSameHostMixin)):
                    raise ValueError('the reloaded cash fixture must use Root canonical shared client and existing mixin')
                cash_tests.ExistingMonthInputsTests.provided_projection_results = staticmethod(projection_results)
                return loaded
            def run_suite():
                suite = unittest.TestSuite()
                for module in suite_modules():
                    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
                diagnostic = io.StringIO()
                result = unittest.TextTestRunner(stream=diagnostic, verbosity=1).run(suite)
                summary = dict(tests=result.testsRun, failures=len(result.failures),
                               errors=len(result.errors), skipped=len(result.skipped),
                               diagnostic=diagnostic.getvalue())
                if result.testsRun != 33 or result.skipped or result.expectedFailures or result.unexpectedSuccesses:
                    raise ValueError('all33 complete candidate methods required: original31 plus2 current cash adapter tests')
                return summary
            warmup = dict(tests=0, scope='no original imports in the consumer process; legacy31 is an immutable ExactRef')
            watched = {str(path.resolve()) for tree in (repo / 'ck3_autonomous_player/src',
                       repo / 'ck3_autonomous_player/tests/unit') for path in tree.rglob('*.py') if path.is_file()}
            for module in list(sys.modules.values()):
                path = getattr(module, '__file__', None)
                if not isinstance(path, str):
                    continue
                candidate = Path(path)
                if candidate.suffix == '.py' and candidate.is_file() and candidate.resolve().is_relative_to(repo):
                    watched.add(str(candidate.resolve()))
            watched.update(str(path) for path in candidate_paths.values())
            captured_path = repo / 'java/ck3-control/wave3-planning/src/test/resources/realmmembership/original-producer-golden.json'
            cash_path = repo / 'ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py'
            watched.update([str(oracle_fixture), str(candidate_bindings), str(Path(client.__file__).resolve()),
                            str(captured_path), str(cash_path)])
            frozen = {path: ref(path) for path in sorted(watched)}
            candidate_realm = module_from_source(realm_name, candidate_paths[realm_relative].read_bytes(),
                                                 str(candidate_paths[realm_relative]))
            candidate_after = module_from_source(after_name, candidate_paths[after_relative].read_bytes(),
                                                 str(candidate_paths[after_relative]))
            calls = []
            differences = []
            common_http_source_refs = [item.to_wire() for item in config.service.source_refs]
            common_http_bytes = wire(common_http_source_refs)
            def compact_http_call(call):
                item = call.to_wire()
                if item.pop('source_refs') != common_http_source_refs:
                    raise ValueError('actual call changed its complete qualified source closure')
                item['source_refs_binding'] = dict(bytes=len(common_http_bytes), sha256=sha(common_http_bytes))
                return item
            contract_changes = []
            actual_projection = candidate_realm._java_projection
            last_result = []
            def record_projection(operation, request):
                entry = original_entry(operation, request)
                try:
                    actual = actual_projection(operation, request)
                except client.ProjectionDomainRejected as error:
                    if not entry.get('legacy_value_error', False):
                        raise AssertionError('actual host refused a request accepted by the original producer') from error
                    calls.append(dict(operation=operation, payload_utf8=wire(request).decode('utf-8'),
                        payload_sha256=sha(wire(request)), expected_legacy_value_error=True, code=error.code,
                        result_rejected=True, response_body_base64=base64.b64encode(error.response_body).decode('ascii'),
                        response_sha256=sha(error.response_body), http_call=compact_http_call(error.http_call)))
                    raise
                if 'result_utf8' not in entry:
                    raise AssertionError('actual host accepted an original explicit input refusal')
                expected = json.loads(entry['result_utf8'])
                equal = domain(wire(expected)) == domain(actual.response_bytes)
                malformed_binding = (operation == 'feedback' and type(request.get('faction_result')) is dict
                    and request['faction_result'].get('binding') == 'not-a-mapping'
                    and actual.value.get('status') == 'unavailable'
                    and actual.value.get('unavailable_reason') == 'faction_result_binding_invalid'
                    and expected.get('status') == 'available')
                decimal_frame_alias = False
                if operation == 'summary' and expected.get('status') == 'current' and actual.value.get('status') == 'historical':
                    supplied = request.get('current_source_frame')
                    retained = expected.get('source_frame')
                    if type(supplied) is dict and type(retained) is dict:
                        if (type(retained.get('sdk_extension')) is float and retained['sdk_extension'] == 1.0
                                and type(supplied.get('sdk_extension')) is int and supplied['sdk_extension'] == 1):
                            restored = dict(supplied, sdk_extension=retained['sdk_extension'])
                            decimal_frame_alias = domain(wire(restored)) == domain(wire(retained))
                if not equal and malformed_binding:
                    contract_changes.append(dict(kind='explicit_malformed_binding_type_rejection',
                        original_status='available', candidate_status='unavailable', reason='faction_result_binding_invalid'))
                elif not equal and decimal_frame_alias:
                    contract_changes.append(dict(kind='opaque_decimal_integer_frame_equality_is_not_coercive',
                        original_status='current', candidate_status='historical'))
                elif not equal:
                    differences.append(dict(operation=operation, expected=expected, actual=actual.value))
                proof = actual.issued_result
                client.require_result_context_v1(proof, config=config, operation=proof.operation,
                    request_id=proof.request_id, payload=actual.request_bytes)
                calls.append(dict(operation=operation, payload_utf8=actual.request_bytes.decode('utf-8'),
                    payload_sha256=sha(actual.request_bytes), result_utf8=actual.response_bytes.decode('utf-8'),
                    result_sha256=sha(actual.response_bytes), equal_original=equal,
                    explicit_contract_change=malformed_binding or decimal_frame_alias,
                    request_utf8=proof.request_bytes.decode('utf-8'), request_sha256=proof.request_sha256,
                    response_utf8=proof.response_bytes.decode('utf-8'), response_sha256=proof.response_sha256,
                    http_call=compact_http_call(proof.http_call)))
                last_result[:] = [actual]
                return actual
            candidate_realm._java_projection = record_projection
            candidate = run_suite()
            captured_raw = captured_path.read_bytes()
            captured = json.loads(captured_raw)
            original_golden_ref = reference['original_golden_ref']
            if (original_golden_ref['bytes'], original_golden_ref['sha256']) != (len(captured_raw), sha(captured_raw)):
                raise ValueError('consumer and separately qualified legacy view use different original golden bytes')
            if len(captured['cases']) != 29:
                raise ValueError('all 29 immutable original feedback vectors required')
            vector_results = []
            for vector in captured['cases']:
                request = copy.deepcopy(captured['bases'][vector['base']])
                for change in vector['operations']:
                    parts = change['path'].strip('/').split('/')
                    parent = request
                    for part in parts[:-1]:
                        parent = parent[int(part)] if type(parent) is list else parent[part]
                    key = int(parts[-1]) if type(parent) is list else parts[-1]
                    if change.get('remove', False):
                        del parent[key]
                    else:
                        parent[key] = copy.deepcopy(change['value'])
                candidate_realm.project_realm_membership_feedback_v1(request['snapshot'],
                    faction_result=request['faction_result'], source_frame=request['source_frame'], previous=request['previous'])
                call = calls[-1]
                strict_binding = vector['name'] == 'nonobject-binding-keeps-original-envelope-semantics'
                vector_results.append(dict(name=vector['name'], call_index=len(calls)-1,
                    expected_equivalent=not strict_binding, actual_equivalent=call.get('equal_original'),
                    expected_contract_change='faction_result_binding_invalid' if strict_binding else None,
                    actual_contract_change=call.get('explicit_contract_change', False)))
                if call.get('equal_original') is not (not strict_binding) or call.get('explicit_contract_change', False) is not strict_binding:
                    differences.append(dict(operation='feedback-vector', name=vector['name'],
                                            reason='unexpected per-case equivalence/strict-binding classification'))
        
            fixture = sys.modules['test_realm_membership_feedback_v1']
            first_arguments = fixture.inputs()
            before_request = dict(snapshot=first_arguments[0], faction_result=first_arguments[2],
                source_frame=first_arguments[1], previous=None)
            before = json.loads(original_entry('feedback', before_request)['result_utf8'])['observation']
            now_args = fixture.inputs((2231, 2262), native=42, public=10, date=53144352, query=2)
            now_request = dict(snapshot=now_args[0], faction_result=now_args[2], source_frame=now_args[1], previous=before)
            now = json.loads(original_entry('feedback', now_request)['result_utf8'])['observation']
            candidate_realm._difference(before, now)
            owner_fixture = sys.modules['test_realm_membership_after_query_v1']
            probes = []
            for value in (1.0, True, 9007199254740993):
                owner = owner_fixture.Owner()
                arguments = fixture.inputs()
                arguments[1]['sdk_extension'] = value
                planned, outcome = owner_fixture.turn(arguments, owner)
                candidate_after.observe_realm_membership_after_query_v1(owner, planned, outcome)
                summary = candidate_after.realm_membership_summary_for_plan_v1(owner, planned['planning_source_frame'])
                if type(summary['source_frame']['sdk_extension']) is not type(value):
                    raise ValueError('opaque SDK source token category changed in actual owner-to-summary consumer')
                if summary['source_frame']['sdk_extension'] != value:
                    raise ValueError('opaque SDK source token value changed')
                probes.append(dict(token_type=type(value).__name__, summary=summary))
            owner = owner_fixture.Owner()
            arguments = fixture.inputs()
            arguments[1]['sdk_extension'] = 1.0
            planned, outcome = owner_fixture.turn(arguments, owner)
            candidate_after.observe_realm_membership_after_query_v1(owner, planned, outcome)
            changed = copy.deepcopy(planned['planning_source_frame']); changed['sdk_extension'] = 1
            actual_summary = record_projection('summary', {'feedback': owner._realm_membership_feedback_v1,
                'current_source_frame': changed})
            if actual_summary.value['status'] != 'historical':
                raise ValueError('integer alias relabelled opaque decimal source frame as current')
            shape_rejections = []
            by_operation = {entry['operation']: json.loads(entry['result_utf8']) for entry in calls if 'result_utf8' in entry}
            if set(by_operation) != {'feedback', 'difference', 'summary'}:
                raise ValueError('all three actual registered outputs are required before shape mutation probes')
            for operation, valid in by_operation.items():
                invalids = []
                missing = copy.deepcopy(valid); missing.pop('status'); invalids.append(('missing-status', missing))
                wrong = copy.deepcopy(valid); wrong['status'] = 'invented'; invalids.append(('unknown-status', wrong))
                wrong_type = copy.deepcopy(valid)
                if operation == 'feedback':
                    wrong_type['new_RPC_calls'] = False
                elif operation == 'difference':
                    wrong_type['lost_county_title_ids'] = [True]
                else:
                    wrong_type['query_sequence'] = True
                invalids.append(('integer-boolean-alias-or-wrong-branch', wrong_type))
                for case, invalid in invalids:
                    try:
                        candidate_realm._validate_result(operation, invalid)
                    except candidate_realm.BridgeUnavailableError:
                        shape_rejections.append(dict(operation=operation, case=case))
                    else:
                        raise ValueError('malformed Java output crossed the mechanical result boundary')
            candidate_realm._java_projection = actual_projection
            actual = last_result[0]
            proof = actual.issued_result
            other_operation = next(operation for operation in (client.ProjectionOperation.REALM_DIFFERENCE,
                client.ProjectionOperation.REALM_DATED_SUMMARY) if operation is not proof.operation)
            negative_contexts = [
                ('copied-result', dataclasses.replace(proof), proof.operation, proof.request_id, actual.request_bytes),
                ('wrong-operation', proof, other_operation, proof.request_id, actual.request_bytes),
                ('wrong-request-id', proof, proof.operation, 'foreign:' + proof.request_id, actual.request_bytes),
                ('different-raw-payload', proof, proof.operation, proof.request_id, actual.request_bytes + b' '),
            ]
            context_rejections = []
            for case, result, operation, request_id, payload in negative_contexts:
                try:
                    client.require_result_context_v1(result, config=config, operation=operation,
                        request_id=request_id, payload=payload)
                except client.ProjectionUnavailable as error:
                    if isinstance(error, ValueError):
                        raise AssertionError('provenance uncertainty cannot become legacy domain ValueError')
                    context_rejections.append(dict(case=case, error_category='projection-unavailable'))
                else:
                    raise ValueError('altered/copied result reconstructed issued Java provenance')
            rejection_probes = []
            for label, operation, payload, code in (
                ('decode-shape', client.ProjectionOperation.REALM_DIFFERENCE, b'{"previous":null}', 'invalid-payload'),
                ('explicit-project-validator', client.ProjectionOperation.REALM_DATED_SUMMARY,
                 b'{"feedback":{"status":"available","schema":"wrong"},"current_source_frame":null}', 'domain-rejected')):
                try:
                    client.call_projection_v1(config=config, operation=operation, payload=payload,
                        request_id='realm-negative:' + label)
                except client.ProjectionDomainRejected as error:
                    if error.code != code or not isinstance(error, ValueError):
                        raise AssertionError('only the explicit input/domain refusal preserves legacy ValueError')
                    rejection_probes.append(dict(case=label, code=error.code,
                        error_category='domain-rejected', payload_base64=base64.b64encode(payload).decode('ascii'),
                        payload_sha256=sha(payload), response_body_base64=base64.b64encode(error.response_body).decode('ascii'),
                        response_body_sha256=sha(error.response_body), http_call=compact_http_call(error.http_call)))
                else:
                    raise AssertionError('malformed explicit boundary request was accepted')
            after = {path: ref(path) for path in sorted(watched)}
            for name, module in list(sys.modules.items()):
                if name == 'xar_autoplayer' or name.startswith('xar_autoplayer.'):
                    path = getattr(module, '__file__', None)
                    if not isinstance(path, str) or str(Path(path).resolve()) not in frozen:
                        raise ValueError('consumer imported outside the complete frozen consumerActualRef tree: ' + name)
            if ref(baseline_ref.path)['sha256'] != baseline_ref.sha256:
                raise ValueError('immutable original baseline changed during consumer execution')
            if frozen != after:
                raise ValueError('original/candidate/imported consumer sources changed during the complete differential')
            if not calls or any(call['http_call']['actual_HTTP_call'] is not True for call in calls):
                raise ValueError('actual source-qualified HTTP result custody required for every accepted consumer call')
            status = 'PASS' if not differences and not baseline['failures'] and not baseline['errors'] and not candidate['failures'] and not candidate['errors'] else 'RED'
            document = dict(schema='xar.ck3.realm-java-whole-consumer-differential/v1',
                machine_id=config.machine_id, observed_at_utc=datetime.now(timezone.utc).isoformat(),
                status=status, boundary='actual Java pure projection to all original feedback/owner/Service/monthly consumers; no Game/SDK/action/writer authority',
                baseline=baseline, candidate=candidate, discovery=warmup,
                original_tests_scope='independent qualified legacy31 baseline ExactRef; samehost consumer all33 complete methods',
                immutable_baseline_ref=baseline_ref.to_wire(), legacy_actual_ref=legacy_actual_ref.to_wire(),
                cash_metrics_migration_owner='/root/planning/constructionrelease',
                cash_metrics_current_source_ref=ref(cash_path), cash_metrics_equivalence_claimed=False,
                original_vectors_replayed=len(captured['cases']), original_vector_results=vector_results,
                calls=calls, differences=differences,
                explicit_contract_changes=contract_changes, opaque_owner_summary_probes=probes,
                reconstructed_result_rejected=True, context_rejections=context_rejections,
                actual_explicit_rejection_probes=rejection_probes, actual_common_http_source_refs=common_http_source_refs,
                malformed_output_shape_rejections=shape_rejections,
                malformed_output_scope='boundary-only mutations of actual results; no simulated HTTP adoption',
                frozen_sources=list(frozen.values()),
                oracle_ref=ref(oracle_fixture), original_golden_ref=ref(captured_path),
                candidate_bindings_ref=ref(candidate_bindings), actual_java_source_refs=service_java_refs,
                service_evidence_ref=config.service.service_evidence_ref.to_wire(),
                program_ref=config.service.program_ref.to_wire(), common_client_ref=current_client,
                native_RPC_calls=0, SAVE_exports=0, canonical_writes=0, Python_fallback_used=False)
            raw = wire(document)
            compressed = gzip.compress(raw, mtime=0)
            if len(raw) > 2 * 1024 * 1024 or len(compressed) > 48 * 1024:
                raise ValueError('whole-consumer differential exceeds its explicit in-memory/output budget')
            with output.open('xb') as stream:
                stream.write(compressed)
                stream.flush()
                import os
                os.fsync(stream.fileno())
            print(json.dumps(dict(status=status, output=str(output), bytes=len(compressed), sha256=sha(compressed),
                original_tests=baseline['tests'], candidate_tests=candidate['tests'], original_vectors=len(captured['cases']),
                accepted_java_calls=sum(not call.get('result_rejected', False) for call in calls), differences=len(differences), explicit_contract_changes=len(contract_changes))))
            if status != 'PASS':
                raise AssertionError('whole original consumer differential is RED; preserved original and Java byte evidence')
            return dict(status=status, original_tests=31, candidate_tests=candidate['tests'], original_vectors=29,
                        accepted_java_calls=len(calls), differences=len(differences), output_ref=ref(output))
        """;
    private static final String LEGACY = """
        def collect_realm_original_consumers_v2(*, repo, legacy_actual_ref, original_golden, machine_id, output):
            '''Only the existing Java sequencer runs this in the separately qualified legacy view process.'''
            import base64
            import copy
            from datetime import datetime, timezone
            from decimal import Decimal
            import gzip
            import hashlib
            import importlib
            import io
            import json
            from pathlib import Path
            import sys
            import unittest
            repo = Path(repo).resolve()
            output = Path(output).resolve()
            golden_path = Path(original_golden).resolve()
            if output.exists() or not output.parent.is_dir():
                raise ValueError('fresh legacy baseline output under an admitted parent required')
            view_raw = Path(legacy_actual_ref.path).read_bytes()
            if (len(view_raw), hashlib.sha256(view_raw).hexdigest()) != (legacy_actual_ref.bytes, legacy_actual_ref.sha256):
                raise ValueError('actual legacy view ExactRef changed')
            sys.path[:0] = [str(repo / 'ck3_autonomous_player/tests/unit'),
                           str(repo / 'ck3_autonomous_player/src'), str(repo)]
            def wire(value):
                return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            def domain(raw):
                value = json.loads(raw.decode('utf-8'), parse_float=Decimal)
                def tag(item):
                    if item is None:
                        return ('null',)
                    if type(item) is bool:
                        return ('bool', item)
                    if type(item) is int:
                        return ('integer', item)
                    if isinstance(item, Decimal):
                        return ('decimal', Decimal(0) if item.is_zero() else item.normalize())
                    if type(item) is str:
                        return ('text', item)
                    if type(item) is list:
                        return ('array', tuple(tag(child) for child in item))
                    if type(item) is dict:
                        return ('object', tuple((key, tag(item[key])) for key in sorted(item)))
                    raise TypeError('undeclared JSON comparison domain')
                return tag(value)
            def recipe_key(operation, raw):
                normalized = json.dumps(domain(raw), ensure_ascii=False, allow_nan=False,
                    separators=(',', ':'), default=str).encode('utf-8')
                return operation + ':' + hashlib.sha256(normalized).hexdigest()
            def ref(path):
                path = Path(path); raw = path.read_bytes()
                return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            import xar_autoplayer.realm_membership_feedback_v1 as realm
            import xar_autoplayer.bridge.realm_membership_after_query_v1 as after
            source_refs = {}
            for path in (repo / 'ck3_autonomous_player/src').rglob('*.py'):
                if path.is_file():
                    source_refs[str(path.resolve())] = ref(path.resolve())
            names = ('test_realm_membership_feedback_v1', 'test_realm_membership_after_query_v1',
                     'test_realm_membership_service_v1', 'test_campaign_score_existing_inputs_v1')
            for name in names:
                path = repo / 'ck3_autonomous_player/tests/unit' / (name + '.py')
                source_refs[str(path.resolve())] = ref(path.resolve())
            golden_ref = ref(golden_path)
            pool = {}
            def remember(operation, request, function):
                raw = wire(request)
                key = recipe_key(operation, raw)
                try:
                    result = function()
                except (ValueError, TypeError) as error:
                    entry = dict(operation=operation, request_utf8=raw.decode('utf-8'), error_type=type(error).__name__,
                                 error_message=str(error), legacy_value_error=isinstance(error, ValueError))
                    if key in pool and pool[key] != entry:
                        raise ValueError('original producer is not deterministic for one JSON-domain request')
                    pool[key] = entry
                    raise
                body = wire(result)
                entry = dict(operation=operation, request_utf8=raw.decode('utf-8'),
                             result_utf8=body.decode('utf-8'), result_sha256=hashlib.sha256(body).hexdigest())
                if key in pool and pool[key] != entry:
                    raise ValueError('original producer is not deterministic for one JSON-domain request')
                pool[key] = entry
                return result
            original_feedback, original_difference = realm.project_realm_membership_feedback_v1, realm._difference
            original_summary = after.realm_membership_summary_for_plan_v1
            def feedback(snapshot, *, faction_result=None, source_frame=None, previous=None):
                request = dict(snapshot=snapshot, faction_result=faction_result, source_frame=source_frame, previous=previous)
                return remember('feedback', request, lambda: original_feedback(snapshot, faction_result=faction_result,
                    source_frame=source_frame, previous=previous))
            def difference(previous, observation):
                return remember('difference', dict(previous=previous, observation=observation),
                                lambda: original_difference(previous, observation))
            def summary(owner, current_source_frame):
                request = dict(feedback=getattr(owner, '_realm_membership_feedback_v1', None),
                               current_source_frame=current_source_frame)
                return remember('summary', request, lambda: original_summary(owner, current_source_frame))
            realm.project_realm_membership_feedback_v1 = feedback
            realm._difference = difference
            after.project_realm_membership_feedback_v1 = feedback
            after.realm_membership_summary_for_plan_v1 = summary
            suite = unittest.TestSuite()
            for name in names:
                suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
            diagnostic = io.StringIO()
            run = unittest.TextTestRunner(stream=diagnostic, verbosity=1).run(suite)
            if run.testsRun != 31 or not run.wasSuccessful() or run.skipped or run.expectedFailures or run.unexpectedSuccesses:
                raise AssertionError('complete original legacy31 failed: ' + diagnostic.getvalue())
            captured = json.loads(golden_path.read_bytes())
            if len(captured['cases']) != 29:
                raise ValueError('all29 immutable feedback vectors required')
            for vector in captured['cases']:
                request = copy.deepcopy(captured['bases'][vector['base']])
                for change in vector['operations']:
                    parts = change['path'].strip('/').split('/'); parent = request
                    for part in parts[:-1]:
                        parent = parent[int(part)] if type(parent) is list else parent[part]
                    key = int(parts[-1]) if type(parent) is list else parts[-1]
                    if change.get('remove', False):
                        del parent[key]
                    else:
                        parent[key] = copy.deepcopy(change['value'])
                feedback(request['snapshot'], faction_result=request['faction_result'],
                         source_frame=request['source_frame'], previous=request['previous'])
            fixture = sys.modules[names[0]]
            first = fixture.inputs()
            before = feedback(first[0], faction_result=first[2], source_frame=first[1])['observation']
            next_args = fixture.inputs((2231, 2262), native=42, public=10, date=53144352, query=2)
            now = feedback(next_args[0], faction_result=next_args[2], source_frame=next_args[1], previous=before)['observation']
            difference(before, now)
            owner_fixture = sys.modules[names[1]]
            for value in (1.0, True, 9007199254740993):
                owner = owner_fixture.Owner(); arguments = fixture.inputs(); arguments[1]['sdk_extension'] = value
                planned, outcome = owner_fixture.turn(arguments, owner)
                after.observe_realm_membership_after_query_v1(owner, planned, outcome)
                summary(owner, planned['planning_source_frame'])
            owner = owner_fixture.Owner(); arguments = fixture.inputs(); arguments[1]['sdk_extension'] = 1.0
            planned, outcome = owner_fixture.turn(arguments, owner)
            after.observe_realm_membership_after_query_v1(owner, planned, outcome)
            changed = copy.deepcopy(planned['planning_source_frame']); changed['sdk_extension'] = 1
            summary(owner, changed)
            for name, module in list(sys.modules.items()):
                if name == 'xar_autoplayer' or name.startswith('xar_autoplayer.'):
                    path = getattr(module, '__file__', None)
                    if not isinstance(path, str) or str(Path(path).resolve()) not in source_refs:
                        raise ValueError('legacy import is outside its closed original source root: ' + name)
            for path, expected in source_refs.items():
                if ref(path) != expected:
                    raise ValueError('original source changed during legacy31/vector capture: ' + path)
            if ref(golden_path) != golden_ref:
                raise ValueError('immutable original golden changed during legacy capture')
            document = dict(schema='xar.ck3.realm-original-consumer-baseline/v2', status='PASS', machine_id=machine_id,
                observed_at_utc=datetime.now(timezone.utc).isoformat(), legacy_actual_ref=legacy_actual_ref.to_wire(),
                original_tests=31, original_vectors=29, skipped=0, failures=0, errors=0,
                diagnostic=diagnostic.getvalue(), entries=pool, frozen_original_sources=list(source_refs.values()),
                original_golden_ref=golden_ref, native_RPC_calls=0, SAVE_exports=0, canonical_writes=0)
            raw = wire(document); packed = gzip.compress(raw, mtime=0)
            if len(raw) > 2097152 or len(packed) > 49152:
                raise ValueError('original baseline exceeds its explicit artifact budget')
            with output.open('xb') as stream:
                stream.write(packed); stream.flush()
                import os
                os.fsync(stream.fileno())
            return dict(status='PASS', original_tests=31, original_vectors=29, skipped=0,
                        baseline_ref=ref(output), recorded_requests=len(pool))
        """;
}

