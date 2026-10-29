package org.xar.ck3.control.wave2.finance.giftoutcome;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** One-time capture of the unchanged real producer; JUnit only consumes the committed result. */
public final class CaptureGiftOutcomeGolden {
    private CaptureGiftOutcomeGolden() { }
    private static final String ORACLE = """
        import copy
        import datetime
        import hashlib
        import json
        from pathlib import Path
        import runpy
        import sys
        import tempfile
        from threading import RLock
        ROOT = Path(sys.argv[1])
        sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
        sys.path.insert(0, str(ROOT / 'tools'))
        from ck3_live_run_id import current_machine_id
        from xar_autoplayer.faction_gift_outcome_v1 import query_resolved_faction_gift_outcome_v1 as producer
        from xar_autoplayer.faction_gift_outcome_v1 import COLD_RECOVERY_STEP, QUERY_PLAYER_FACTION_ALERTS_V1_STEP
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        TEST = ROOT / 'ck3_autonomous_player/tests/unit/test_faction_gift_outcome_v1.py'
        namespace = runpy.run_path(str(TEST))
        fixture = namespace['test_resolved_gift_current_material_four_branches']
        base = {}
        class Captured(Exception):
            pass
        def probe(driver, *, request_id, expected_revision):
            snapshot = driver.take_internal_semantic_snapshot()
            base.update({'request': {'request_id': request_id, 'expected_revision': expected_revision},
                         'snapshot': snapshot, 'after_snapshot': copy.deepcopy(snapshot),
                         'history': copy.deepcopy(driver._command_history),
                         'pair_result': driver.wait_for_command_result('capture', 0)['result'],
                         'alert_result': driver.execute_step(QUERY_PLAYER_FACTION_ALERTS_V1_STEP, expected_revision=expected_revision),
                         'pair_error': None, 'alert_error': None})
            raise Captured()
        fixture.__globals__['query_resolved_faction_gift_outcome_v1'] = probe
        with tempfile.TemporaryDirectory(prefix='gift-outcome-fixture-') as temporary:
            try:
                fixture(Path(temporary), 'still_member')
            except Captured:
                pass
        if not base:
            raise RuntimeError('original test fixture was not captured')
        cases = []
        def apply(specification, operations):
            for operation in operations:
                path = operation['path'].strip('/').split('/')
                parent = specification
                for part in path[:-1]:
                    parent = parent[int(part)] if isinstance(parent, list) else parent[part]
                key = int(path[-1]) if isinstance(parent, list) else path[-1]
                if operation.get('remove', False):
                    del parent[key]
                else:
                    parent[key] = copy.deepcopy(operation['value'])
        class Driver:
            _history_lock = RLock()
            def __init__(self, specification):
                self.specification = specification
                self._command_history = copy.deepcopy(specification['history'])
                self.endpoint = self
                self.state = self
                self.snapshots = 0
                self.sent = []
                self.alert_calls = []
                self.recorded = []
            def take_internal_semantic_snapshot(self):
                self.snapshots += 1
                return copy.deepcopy(self.specification['snapshot' if self.snapshots == 1 else 'after_snapshot'])
            def send(self, payload):
                self.sent.append({key: value for key, value in payload.items()
                                  if key not in ('type', 'protocol_version', 'request_id')})
            def wait_for_command_result(self, request_id, timeout_seconds):
                if self.specification['pair_error'] is not None:
                    raise BridgeUnavailableError(self.specification['pair_error'])
                return {'type': 'command_result', 'protocol_version': 1, 'request_id': request_id,
                        'ok': True, 'result': copy.deepcopy(self.specification['pair_result'])}
            def execute_step(self, step, *, expected_revision):
                self.alert_calls.append({'step': step, 'expected_revision': expected_revision})
                if self.specification['alert_error'] is not None:
                    raise BridgeUnavailableError(self.specification['alert_error'])
                return copy.deepcopy(self.specification['alert_result'])
            def _record_command(self, step, *, ok, result):
                self.recorded.append({'step': step, 'ok': ok, 'result': copy.deepcopy(result)})
        def operation(path, value=None, remove=False):
            return {'path': path, 'remove': True} if remove else {'path': path, 'value': value}
        def add(name, *operations):
            specification = copy.deepcopy(base)
            apply(specification, operations)
            driver = Driver(specification)
            try:
                expected = producer(driver, **specification['request'])
                failure = None
            except Exception as error:
                expected = None
                failure = {'class': type(error).__name__, 'message': str(error)}
            cases.append({'name': name, 'operations': operations, 'expected': expected,
                          'failure': failure, 'expected_pair_calls': driver.sent,
                          'expected_alert_calls': driver.alert_calls, 'expected_record_count': len(driver.recorded),
                          'expected_snapshot_count': driver.snapshots})
        P = '/pair_result/native/observation/'
        A = '/alert_result/player_faction_alerts/'
        R = '/history/1/result/receipt/'
        add('still-member')
        add('recipient-left', operation(P + 'source_faction_leader_character_id', 35637),
            operation(P + 'source_faction_member_character_ids', [35637]))
        add('faction-known-absent', operation(P + 'source_faction_present', False),
            operation(P + 'source_faction_leader_character_id', None),
            operation(P + 'source_faction_member_character_ids', []), operation(A + 'targeting_factions', []))
        add('pair-unavailable-observation', operation(P + 'available', False))
        add('current-frame-not-paused', operation('/snapshot/paused', False))
        add('revision-mismatch-raises', operation('/request/expected_revision', 10))
        add('no-original-history', operation('/history', []))
        add('ack-does-not-prove-applied', operation(R + 'postcondition_verified', False))
        add('unknown-does-not-prove-applied', operation(R + 'status', 'unknown'))
        add('original-episode-mismatch', operation('/history/0/result/pending_ledger/pending/episode_run_id', 'other-episode'))
        add('receipt-source-mismatch', operation(R + 'source_faction_id', 77))
        add('current-date-precedes-material', operation('/snapshot/date_raw', 53290175))
        add('native-failure-flags', operation('/pair_result/native/failure_flags', 1))
        add('pair-frame-mismatch', operation(P + 'native_snapshot_revision', 13))
        add('current-faction-metrics-incomplete', operation(P + 'source_faction_metrics_available', False))
        add('current-faction-members-missing', operation(P + 'source_faction_member_character_ids', remove=True))
        add('gift-modifier-absent-is-still-observed', operation(P + 'gift_opinion_present', False))
        add('final-frame-changed', operation('/after_snapshot/date_raw', 53290201))
        add('alert-empty-vector', operation(A + 'targeting_factions', []))
        rows = copy.deepcopy(base['alert_result']['player_faction_alerts']['targeting_factions'])
        add('alert-duplicate-identity', operation(A + 'targeting_factions', rows + rows))
        add('alert-stale', operation(A + 'snapshot_revision', 13))
        add('alert-read-unavailable', operation('/alert_error', 'retained alert unavailable'))
        add('independent-pair-unavailable', operation('/pair_error', 'retained pair unavailable'))
        auto = [{'command': 'auto-turn', 'ok': True, 'result': {'auto_turn': {
            'selected_step': row['command'], 'result': row['result']}}} for row in base['history']]
        add('auto-turn-original-history', operation('/history', auto))
        direct = {'command': QUERY_PLAYER_FACTION_ALERTS_V1_STEP, 'ok': True, 'result': base['alert_result']}
        add('same-frame-alert-reused', operation('/history', base['history'] + [direct]))
        add('missing-optional-original-material-emits-null', operation('/history/0/result/pending_ledger/pending/gold_cost_raw', remove=True))
        import xar_autoplayer.faction_gift_outcome_v1 as producer_module
        REGISTERED = ROOT / 'ck3_autonomous_player/tests/unit/test_faction_gift_outcome_registered_v1.py'
        registered_fixture = runpy.run_path(str(REGISTERED))['test_registered_resolved_gift_reads_original_material_without_resubmit']
        registered = {}
        def registered_probe(driver, *, request_id, expected_revision):
            snapshot = driver.take_internal_semantic_snapshot()
            specification = {'request': {'request_id': request_id, 'expected_revision': expected_revision},
                             'snapshot': snapshot, 'after_snapshot': copy.deepcopy(snapshot),
                             'history': copy.deepcopy(driver._command_history),
                             'pair_result': driver.wait_for_command_result('capture', 0)['result'],
                             'pair_error': None, 'alert_error': None}
            execute = driver.execute_step
            def capture_alert(step, *, expected_revision):
                result = execute(step, expected_revision=expected_revision)
                specification['alert_result'] = copy.deepcopy(result)
                return result
            driver.execute_step = capture_alert
            outcome = producer(driver, request_id=request_id, expected_revision=expected_revision)
            registered.update({'input': specification, 'expected': copy.deepcopy(outcome),
                               'route': ['official MCP Client', 'registered MCP tool', 'GameplayBridgeService',
                                         'inherited real NativeHeadlessGameplayDriver wrapper', 'unchanged original producer'],
                               'original_registered_test_assertions_completed': False})
            return outcome
        producer_module.query_resolved_faction_gift_outcome_v1 = registered_probe
        try:
            with tempfile.TemporaryDirectory(prefix='gift-outcome-registered-') as temporary:
                registered_fixture(Path(temporary))
            registered['original_registered_test_assertions_completed'] = True
        finally:
            producer_module.query_resolved_faction_gift_outcome_v1 = producer
        if not registered.get('original_registered_test_assertions_completed'):
            raise RuntimeError('real registered consumer assertions were not completed')
        def ref(path):
            data = path.read_bytes()
            return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        sources = [ROOT / 'ck3_autonomous_player/src/xar_autoplayer/faction_gift_outcome_v1.py', TEST,
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_private_transport_v1.py',
                   REGISTERED, ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py']
        document = {'schema': 'xar.ck3.java.gift-outcome-producer-golden/v1',
                    'capture': {'machine_id': current_machine_id(),
                                'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                'method': 'unchanged real producer; existing original unit-test fixture, explicit synthetic driver',
                                'native_rpc_count': 0, 'ledger_writes': 0, 'historical_machine_id': 'unknown',
                                'boundary': 'offline producer parity, not native/gameplay qualification'},
                    'sources': [ref(path) for path in sources], 'base': base, 'cases': cases, 'registered_consumer': registered}
        output = Path(sys.argv[2])
        output.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(document, ensure_ascii=False, separators=(',', ':')) + '\\n').encode('utf-8')
        if len(encoded) > 100000:
            raise ValueError('gift-outcome golden budget exceeded')
        output.write_bytes(encoded)
        print(json.dumps({'status': 'ORIGINAL_PRODUCER_CAPTURED', 'cases': len(cases), 'bytes': len(encoded),
                          'sha256': hashlib.sha256(encoded).hexdigest(), 'native_rpc_count': 0, 'ledger_writes': 0}))
        """;

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("source-root python output-path required");
        Path root = Path.of(args[0]).toAbsolutePath().normalize(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("new capture output required");
        ProcessBuilder command = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", ORACLE, root.toString(), output.toString());
        command.directory(root.toFile()); command.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        command.environment().put("OPENBLAS_NUM_THREADS", "1"); command.environment().put("OMP_NUM_THREADS", "1");
        command.environment().put("TEMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch");
        command.environment().put("TMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch");
        command.redirectErrorStream(true); Process child = command.start(); byte[] log = child.getInputStream().readNBytes(65537);
        int exit = child.waitFor(); if (log.length > 65536) throw new IllegalStateException("capture log budget");
        System.out.print(new String(log, StandardCharsets.UTF_8));
        if (exit != 0) throw new IllegalStateException("original producer capture exit " + exit);
        if (!Files.isRegularFile(output) || Files.size(output) > 100000) throw new IllegalStateException("capture output budget");
    }
}
