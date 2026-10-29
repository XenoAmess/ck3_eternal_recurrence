package org.xar.ck3.control.wave2.finance.factionalerts;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Shared scheduler only: unchanged producer and original native/service/MCP/strategy consumer tests. */
public final class CaptureFactionAlertsGolden {
    private CaptureFactionAlertsGolden() { }
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
        sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
        sys.path.insert(0, str(ROOT / 'tools'))
        from ck3_live_run_id import current_machine_id
        from xar_autoplayer.bridge.player_faction_alerts_contract import normalize_player_faction_alerts_v1 as producer
        from xar_autoplayer.bridge.player_faction_alerts_contract import validate_player_faction_war_handoffs_v1 as handoff
        from xar_autoplayer.bridge.version_identity import NATIVE_BUILD_IDENTITIES
        TEST = ROOT / 'ck3_autonomous_player/tests/unit/test_player_faction_alerts_v1_bridge.py'
        fixtures = runpy.run_path(str(TEST))
        county_test = ROOT / 'ck3_autonomous_player/tests/unit/test_player_faction_county_material_v1.py'
        county = runpy.run_path(str(county_test))
        event_test = ROOT / 'ck3_autonomous_player/tests/unit/test_faction_demand1001_context.py'
        events = runpy.run_path(str(event_test))
        bases = {'full': fixtures['_full_frame'](), 'partial': fixtures['_partial_frame'](),
                 'unavailable': fixtures['_unavailable_frame'](),
                 'county': county['_with_observations']([county['_county_row']()]),
                 'surrender': events['_frames']()[1]}
        cases = []
        def operation(path, value=None, remove=False):
            return {'path': path, 'remove': True} if remove else {'path': path, 'value': value}
        def apply(frame, operations):
            for operation in operations:
                parts = operation['path'].strip('/').split('/')
                parent = frame
                for part in parts[:-1]:
                    parent = parent[int(part)] if isinstance(parent, list) else parent[part]
                key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
                if operation.get('remove', False):
                    del parent[key]
                else:
                    parent[key] = copy.deepcopy(operation['value'])
        def add(name, base='full', operations=(), expected_patch=None, wars=None):
            frame = copy.deepcopy(bases[base])
            apply(frame, operations)
            expected = {'expected_date_raw': bases[base]['date_raw'] if bases[base]['date_raw'] is not None else fixtures['DATE_RAW'],
                        'expected_snapshot_revision': bases[base]['snapshot_revision']}
            expected.update(expected_patch or {})
            active = [{'war_id': 9001}] if wars is None else wars
            try:
                normalized = producer(frame, **expected)
                handoff(normalized, active)
                failure = None
            except Exception as error:
                normalized = None
                failure = {'class': type(error).__name__, 'message': str(error)}
            canonical = None if normalized is None else json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            retained = normalized if name in ('full-derived-classes', 'partial-count-with-unavailable-planner',
                                              'whole-unavailable', 'county-native-material', 'surrender-title-kingdom-closure') else None
            cases.append({'name': name, 'base': base, 'operations': operations, 'expected_frame': expected,
                          'active_wars': active, 'expected': retained,
                          'expected_sha256': None if canonical is None else hashlib.sha256(canonical).hexdigest(), 'failure': failure})
        add('full-derived-classes')
        add('partial-count-with-unavailable-planner', 'partial')
        add('whole-unavailable', 'unavailable')
        add('county-native-material', 'county')
        add('surrender-title-kingdom-closure', 'surrender')
        add('county-empty-vector-is-present', 'county', [operation('/targeting_factions/1/county_member_observations', [])])
        add('county-missing-vector-remains-missing', 'county', [operation('/targeting_factions/1/county_member_observations', remove=True)])
        row_path = '/targeting_factions/1/county_member_observations/0/'
        culture = {'county_culture_id': -2, 'target_culture_id': -2,
                   'same_culture_as_target': True, 'culture_relation_status': 'available'}
        add('signed-full-culture-ids', 'county', [operation(row_path + key, value) for key, value in culture.items()])
        culture_partial = {'county_culture_id': 0, 'target_culture_id': None,
                           'same_culture_as_target': None, 'culture_relation_status': 'unavailable'}
        add('partial-culture-keeps-zero-id', 'county', [operation(row_path + key, value) for key, value in culture_partial.items()])
        add('native-signed-storage-minimum', 'county', [operation(row_path + 'county_opinion/raw', -(2**31)),
            operation(row_path + 'native_county_join_score/raw', -(2**63)), operation(row_path + 'native_leave_score_threshold/raw', -(2**31))])
        add('native-signed-storage-maximum', 'county', [operation(row_path + 'county_opinion/raw', 2**31-1),
            operation(row_path + 'native_county_join_score/raw', 2**63-1), operation(row_path + 'native_leave_score_threshold/raw', 2**31-1)])
        for build in NATIVE_BUILD_IDENTITIES:
            source = {'game_version': build.game_version, 'executable_sha256': build.executable_sha256.lower(),
                      'backend_id': build.backend_id('player-faction-alerts-v1')}
            add('exact-build-' + build.game_version, operations=[operation('/provenance', source)],
                expected_patch={'expected_game_version': build.game_version, 'expected_executable_sha256': build.executable_sha256.lower()})
        invalid = [('extra-root', '/extra', True), ('fixed-scale', '/targeting_factions/0/power/scale', 1000),
                   ('wrong-player-target', '/targeting_factions/0/target_character_id', 1),
                   ('danger-disagrees', '/targeting_factions/1/dangerous_by_stock_rule', False),
                   ('peasant-boundary', '/targeting_factions/2/months_until_max_discontent', 13),
                   ('county-power-equal', '/county_exposures/0/power/raw', 8000000),
                   ('county-wrong-kind', '/county_exposures/0/faction_type_key', 'liberty_faction'),
                   ('county-target-is-player', '/county_exposures/0/target_character_id', fixtures['PLAYER_ID']),
                   ('wrong-planner', '/planner_projection/dangerous_faction_ids', [771]),
                   ('timing-not-qualified', '/readiness/exact_ultimatum_timing_ready', True),
                   ('wrong-count', '/targeting_faction_count', 1),
                   ('duplicate-members', '/targeting_factions/0/character_member_ids', [1, 1]),
                   ('human-without-leader', '/targeting_factions/0/leader_character_id', None),
                   ('war-id-without-war', '/targeting_factions/0/faction_war_id', 9001)]
        for name, path, value in invalid:
            operations = [operation(path, value)]
            if name == 'human-without-leader':
                operations += [operation('/targeting_factions/0/leader_is_human', True),
                               operation('/targeting_factions/0/dangerous_by_stock_rule', True),
                               operation('/targeting_factions/0/danger_reason', 'human_faction_leader')]
            add(name, operations=operations)
        for field, value in [('holder_character_id', True), ('county_opinion', {'raw': 2**31, 'scale': 1}),
                             ('can_add_county', 0), ('native_final_status', 'unknown')]:
            add('county-invalid-' + field, 'county', [operation(row_path + field, value)])
        add('partial-culture-group-rejected', 'county', [operation(row_path + 'county_culture_id', 0)])
        add('partial-component-cannot-guess', 'partial', [operation('/planner_projection/present', True)])
        add('partial-component-fake-ready', 'partial', [operation('/readiness/alert_ready', True)])
        add('connected-build-mismatch', expected_patch={'expected_game_version': '1.20.0.4',
            'expected_executable_sha256': NATIVE_BUILD_IDENTITIES[-1].executable_sha256})
        add('war-handoff-missing', wars=[])
        add('war-handoff-bool-not-id', wars=[{'war_id': True}])
        component = {'status': 'available', 'complete': True, 'scope': 'played_character_own_subrealm_including_vassals',
                     'source': 'native_actor_vassal_held_counties_double_sample_v1', 'snapshot_revision': fixtures['NATIVE_REVISION'],
                     'date_raw': fixtures['DATE_RAW'], 'actor_character_id': fixtures['PLAYER_ID'],
                     'county_title_ids': [101, 102], 'unavailable_reason': None}
        add('complete-subrealm-counties', operations=[operation('/player_subrealm_geographic_counties_v1', component)])
        incomplete = dict(component, status='unavailable', complete=False, county_title_ids=None, unavailable_reason='independent source unavailable')
        add('incomplete-subrealm-is-not-empty', operations=[operation('/player_subrealm_geographic_counties_v1', incomplete)])
        wrong = dict(component, actor_character_id=1)
        add('subrealm-owner-mismatch', operations=[operation('/player_subrealm_geographic_counties_v1', wrong)])
        suite = unittest.TestSuite()
        for name in ('PlayerFactionAlertsContractTests', 'PlayerFactionAlertsNativeDriverTests',
                     'PlayerFactionAlertsServiceTests', 'PlayerFactionAlertsMcpTests'):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(fixtures[name]))
        culture_test = ROOT / 'ck3_autonomous_player/tests/unit/test_player_faction_county_culture_inputs_v1.py'
        feedback_test = ROOT / 'ck3_autonomous_player/tests/unit/test_realm_membership_feedback_v1.py'
        for path in (county_test, event_test, culture_test, feedback_test):
            for value in runpy.run_path(str(path)).values():
                if isinstance(value, type) and value is not unittest.TestCase and issubclass(value, unittest.TestCase):
                    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(value))
        diagnostics = io.StringIO()
        result = unittest.TextTestRunner(stream=diagnostics, verbosity=1).run(suite)
        if not result.wasSuccessful() or result.skipped:
            raise RuntimeError('original consumer suite did not fully execute: ' + diagnostics.getvalue())
        consumer = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                    'skipped': len(result.skipped), 'scope': 'original Native Driver, Hybrid, Service, facade, official MCP Client, strategy culture, event context and realm membership tests'}
        def ref(path):
            raw = path.read_bytes()
            return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        sources = [ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/player_faction_alerts_contract.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/faction_county_culture_inputs_v1.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py', TEST, county_test, event_test, culture_test, feedback_test,
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',
                   ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py']
        output = Path(sys.argv[2])
        document = {'schema': 'xar.ck3.java.faction-alerts-producer-golden/v1',
                    'capture': {'machine_id': current_machine_id(), 'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                'method': 'unchanged original normalizer, original fixture and consumer test modules',
                                'native_rpc_count': 0, 'ledger_writes': 0, 'historical_machine_id': 'unknown',
                                'boundary': 'synthetic offline source parity; no current build or gameplay qualification'},
                    'sources': [ref(path) for path in sources], 'bases': bases, 'cases': cases, 'consumer_tests': consumer}
        encoded = (json.dumps(document, ensure_ascii=False, separators=(',', ':')) + '\\n').encode('utf-8')
        if len(encoded) > 65000:
            raise ValueError('faction-alert golden byte budget exceeded: ' + str(len(encoded)))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded)
        print(json.dumps({'status': 'ORIGINAL_PRODUCER_CAPTURED', 'cases': len(cases), 'bytes': len(encoded),
                          'sha256': hashlib.sha256(encoded).hexdigest(), 'consumer_tests': consumer,
                          'native_rpc_count': 0, 'ledger_writes': 0}))
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
        if (!Files.isRegularFile(output) || Files.size(output) > 65000) throw new IllegalStateException("capture output budget");
    }
}
