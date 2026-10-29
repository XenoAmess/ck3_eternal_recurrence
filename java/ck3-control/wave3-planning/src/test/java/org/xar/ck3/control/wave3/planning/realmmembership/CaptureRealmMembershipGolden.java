package org.xar.ck3.control.wave3.planning.realmmembership;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Shared scheduler only: original feedback producer and actual existing after-query/service consumers. */
public final class CaptureRealmMembershipGolden {
    private CaptureRealmMembershipGolden() { }
    private static final String ORACLE = """
        import copy
        import datetime
        import hashlib
        import io
        import json
        from pathlib import Path
        import runpy
        import sys
        import unittest
        ROOT = Path(sys.argv[1])
        TESTROOT = ROOT / 'ck3_autonomous_player/tests/unit'
        sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
        sys.path.insert(0, str(ROOT / 'tools'))
        sys.path.insert(0, str(TESTROOT))
        from ck3_live_run_id import current_machine_id
        from xar_autoplayer.realm_membership_feedback_v1 import project_realm_membership_feedback_v1 as producer
        from xar_autoplayer.bridge.version_identity import CK3_11906
        TEST = TESTROOT / 'test_realm_membership_feedback_v1.py'
        fixtures = runpy.run_path(str(TEST))
        def request(arguments, previous=None):
            return {'snapshot': arguments[0], 'source_frame': arguments[1], 'faction_result': arguments[2], 'previous': previous}
        first = request(fixtures['inputs']())
        old_observation = producer(first['snapshot'], faction_result=first['faction_result'], source_frame=first['source_frame'])['observation']
        advanced = request(fixtures['inputs']((2231, 2262), native=42, public=10, date=53144352, query=2), old_observation)
        ordinary = copy.deepcopy(first)
        packet = ordinary['faction_result']
        del packet['binding']
        frame = ordinary['source_frame']
        packet.update(step='query-player-faction-alerts-v1', accepted=True, status='available',
                      snapshot_revision=frame['native_revision'], player_faction_alerts_ready=True,
                      queried_snapshot_id=frame['snapshot_id'], queried_revision=frame['revision'],
                      queried_native_revision=frame['native_revision'])
        bases = {'first': first, 'advanced': advanced, 'ordinary': ordinary,
                 'zero': request(fixtures['inputs'](()))}
        cases = []
        def operation(path, value=None, remove=False):
            return {'path': path, 'remove': True} if remove else {'path': path, 'value': value}
        def apply(specification, operations):
            for operation in operations:
                parts = operation['path'].strip('/').split('/')
                parent = specification
                for part in parts[:-1]:
                    parent = parent[int(part)] if isinstance(parent, list) else parent[part]
                key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
                if operation.get('remove', False):
                    del parent[key]
                else:
                    parent[key] = copy.deepcopy(operation['value'])
        def add(name, base='first', operations=()):
            specification = copy.deepcopy(bases[base])
            apply(specification, operations)
            expected = producer(specification['snapshot'], faction_result=specification['faction_result'],
                                source_frame=specification['source_frame'], previous=specification['previous'])
            cases.append({'name': name, 'base': base, 'operations': operations, 'expected': expected})
        add('complete-first-observation')
        add('complete-empty-is-zero', 'zero')
        add('actual-loss-after-complete-prior', 'advanced')
        add('ordinary-native-queried-envelope', 'ordinary')
        add('no-faction-input', operations=[operation('/faction_result', None)])
        add('no-source-frame', operations=[operation('/source_frame', None)])
        add('snapshot-date-drift', operations=[operation('/snapshot/date_raw', 53144329)])
        add('source-actor-drift', operations=[operation('/source_frame/actor_character_id', 7)])
        add('binding-native-drift', operations=[operation('/faction_result/binding/native_revision', 40)])
        add('binding-expected-public-drift', operations=[operation('/faction_result/binding/expected_revision', 8)])
        add('missing-original-sequence', operations=[operation('/faction_result/query_sequence', remove=True)])
        add('boolean-is-not-query-sequence', operations=[operation('/faction_result/query_sequence', True)])
        add('invalid-exact-current-build', operations=[operation('/snapshot/diagnostics/hello/game_version', 'unknown')])
        add('expected-null-does-not-fallback', operations=[operation('/snapshot/diagnostics/hello/expected_ck3_version', None)])
        add('legacy-hello-absence-cannot-label-modern-alert', operations=[operation('/snapshot/diagnostics/hello', remove=True)])
        add('ordinary-queried-public-drift', 'ordinary', [operation('/faction_result/queried_revision', 8)])
        add('ordinary-envelope-readiness-disagrees', 'ordinary', [operation('/faction_result/player_faction_alerts_ready', False)])
        add('ordinary-explicit-null-binding', 'ordinary', [operation('/faction_result/binding', None)])
        add('nonobject-binding-keeps-original-envelope-semantics', 'ordinary',
            [operation('/faction_result/binding', 'not-a-mapping'), operation('/faction_result/player_faction_alerts_ready', False)])
        component = '/faction_result/player_faction_alerts/player_subrealm_geographic_counties_v1/'
        add('optional-component-missing', operations=[operation(component.rstrip('/'), remove=True)])
        add('component-owner-mismatch', operations=[operation(component + 'actor_character_id', 7)])
        add('component-native-mismatch', operations=[operation(component + 'snapshot_revision', 40)])
        add('component-date-mismatch', operations=[operation(component + 'date_raw', 53144304)])
        incomplete = copy.deepcopy(first['faction_result']['player_faction_alerts']['player_subrealm_geographic_counties_v1'])
        incomplete.update(status='unavailable', complete=False, county_title_ids=None, unavailable_reason='native_membership_unavailable')
        add('component-incomplete-never-empty', operations=[operation(component.rstrip('/'), incomplete)])
        incomplete_bad = dict(incomplete, county_title_ids=[2231])
        add('partial-set-rejected', operations=[operation(component.rstrip('/'), incomplete_bad)])
        add('repeated-prior-is-not-earlier', operations=[operation('/previous', old_observation)])
        add('prior-owner-does-not-carry', 'advanced', [operation('/previous/source_frame/episode_run_id', 'other')])
        add('prior-full-id-replacement', 'advanced', [operation('/previous/component/county_title_ids', [11, 2231, 2262])])
        legacy = {'game_version': CK3_11906.game_version, 'executable_sha256': CK3_11906.executable_sha256,
                  'backend_id': CK3_11906.backend_id('player-faction-alerts-v1')}
        add('archived-legacy-input-without-hello', operations=[operation('/snapshot/diagnostics/hello', remove=True),
                                                            operation('/faction_result/player_faction_alerts/provenance', legacy)])
        suite = unittest.TestSuite()
        consumer_paths = [TEST, TESTROOT / 'test_realm_membership_after_query_v1.py', TESTROOT / 'test_realm_membership_service_v1.py']
        for path in consumer_paths:
            for value in runpy.run_path(str(path)).values():
                if isinstance(value, type) and value is not unittest.TestCase and issubclass(value, unittest.TestCase):
                    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(value))
        diagnostic = io.StringIO()
        result = unittest.TextTestRunner(stream=diagnostic, verbosity=1).run(suite)
        if not result.wasSuccessful() or result.skipped:
            raise RuntimeError('original feedback consumers did not fully execute: ' + diagnostic.getvalue())
        def ref(path):
            data = path.read_bytes()
            return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        sources = [ROOT / 'ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/realm_membership_after_query_v1.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/player_faction_alerts_contract.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py', *consumer_paths]
        document = {'schema': 'xar.ck3.java.realm-membership-producer-golden/v1',
                    'capture': {'machine_id': current_machine_id(), 'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                'method': 'unchanged real feedback producer with original synthetic source fixtures and complete original consumer tests',
                                'native_rpc_count': 0, 'ledger_writes': 0, 'historical_machine_id': 'unknown',
                                'boundary': 'original DTO parity, not native current-source qualification'},
                    'sources': [ref(path) for path in sources], 'bases': bases, 'cases': cases,
                    'consumer_tests': {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)}}
        encoded = (json.dumps(document, ensure_ascii=False, separators=(',', ':')) + '\\n').encode('utf-8')
        if len(encoded) > 85000:
            raise ValueError('realm-membership golden byte budget exceeded')
        output = Path(sys.argv[2])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded)
        print(json.dumps({'status': 'ORIGINAL_PRODUCER_CAPTURED', 'cases': len(cases), 'bytes': len(encoded),
                          'sha256': hashlib.sha256(encoded).hexdigest(), 'consumer_tests': document['consumer_tests'],
                          'native_rpc_count': 0, 'ledger_writes': 0}))
        """;
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("source-root python output-path required");
        Path root = Path.of(args[0]).toAbsolutePath().normalize(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("new capture output required");
        ProcessBuilder command = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", ORACLE, root.toString(), output.toString());
        command.directory(root.toFile()); command.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        command.environment().put("OPENBLAS_NUM_THREADS", "1"); command.environment().put("OMP_NUM_THREADS", "1");
        command.environment().put("TEMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch"); command.environment().put("TMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch");
        command.redirectErrorStream(true); Process child = command.start(); byte[] log = child.getInputStream().readNBytes(65537);
        int exit = child.waitFor(); if (log.length > 65536) throw new IllegalStateException("capture log budget");
        System.out.print(new String(log, StandardCharsets.UTF_8)); if (exit != 0) throw new IllegalStateException("original producer capture exit " + exit);
        if (!Files.isRegularFile(output) || Files.size(output) > 85000) throw new IllegalStateException("capture output budget");
    }
}
