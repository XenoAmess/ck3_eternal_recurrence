package org.xar.ck3.control.wave2.finance.factionculture;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Shared bounded capture owner invokes this once; default JUnit is independent of Python. */
public final class CaptureFactionCultureGolden {
    private CaptureFactionCultureGolden() { }
    private static final String ORACLE = """
        from __future__ import annotations
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
        from xar_autoplayer.bridge.faction_county_culture_inputs_v1 import normalize_county_culture_relation_v1, project_player_faction_county_culture_context_v1
        SOURCE = ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/faction_county_culture_inputs_v1.py'
        TEST = ROOT / 'ck3_autonomous_player/tests/unit/test_player_faction_county_culture_inputs_v1.py'
        scope = runpy.run_path(str(TEST))
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(scope['FactionCountyCultureInputsV1Tests'])
        log = io.StringIO()
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        if not result.wasSuccessful() or result.skipped:
            print(log.getvalue())
            raise ValueError('original complete culture unit tests failed or skipped')
        relation = scope['_relation']
        frame = scope['_frame']
        normalize_alert = scope['_normalize']
        cases = []
        def relation_case(name, value):
            try:
                expected = normalize_county_culture_relation_v1(copy.deepcopy(value), field='county')
                cases.append({'name': name, 'operation': 'normalize', 'input': value, 'accepted': True, 'expected': expected})
            except (TypeError, ValueError) as error:
                cases.append({'name': name, 'operation': 'normalize', 'input': value, 'accepted': False, 'error_class': type(error).__name__})
        relation_case('legacy-no-culture-fields', {'county_title_id': 50331649, 'extension': [None, True]})
        for county, target in ((16777217, 33554433), (0, 0), (0, 1), (-(2**31), 2**31-1), (-2, -2), (0, None), (None, -2), (None, None)):
            relation_case('full-ids-' + str(county) + '-' + str(target), relation(county, target))
        for field, replacement in (('county_culture_id', True), ('target_culture_id', False),
            ('county_culture_id', -1), ('target_culture_id', -(2**31)-1), ('target_culture_id', 2**31),
            ('county_culture_id', '0'), ('county_culture_id', 0.0), ('same_culture_as_target', 0),
            ('same_culture_as_target', 'false'), ('same_culture_as_target', True),
            ('same_culture_as_target', None), ('county_culture_id', None),
            ('culture_relation_status', 'unsupported_build'), ('culture_relation_status', None),
            ('culture_relation_status', 'unavailable')):
            value = relation()
            value[field] = replacement
            relation_case('reject-' + field + '-' + repr(replacement), value)
        for field in relation():
            value = relation()
            del value[field]
            relation_case('reject-missing-group-field-' + field, value)
        value = relation(None, 0)
        value['same_culture_as_target'] = False
        relation_case('reject-unavailable-with-known-relation', value)
        def project_case(name, source):
            normalized = normalize_alert(source)
            projected = {field: copy.deepcopy(normalized[field]) for field in ('snapshot_revision', 'date_raw', 'player_character_id', 'provenance')}
            projected['targeting_factions'] = []
            for faction in normalized['targeting_factions']:
                row = {field: copy.deepcopy(faction[field]) for field in ('faction_id', 'faction_type_key', 'target_character_id', 'county_member_title_ids')}
                if 'county_member_observations' in faction:
                    row['county_member_observations'] = [{field: copy.deepcopy(material[field])
                        for field in ('county_title_id', 'county_culture_id', 'target_culture_id', 'same_culture_as_target', 'culture_relation_status')
                        if field in material} for material in faction['county_member_observations']]
                projected['targeting_factions'].append(row)
            expected = project_player_faction_county_culture_context_v1(normalized)
            actual_projection = project_player_faction_county_culture_context_v1(projected)
            if expected != actual_projection:
                raise ValueError('declared projection changed original producer semantics')
            cases.append({'name': name, 'operation': 'project', 'input': projected, 'accepted': True, 'expected': expected})
        project_case('projection-available-full-generation-ids', frame(relation()))
        project_case('projection-available-zero-id', frame(relation(0, 0)))
        project_case('projection-known-negative-id-partial-read', frame(relation(None, -2)))
        project_case('projection-legacy-county-material', frame(None))
        value = frame(None)
        del value['targeting_factions'][1]['county_member_observations']
        project_case('projection-missing-county-material', value)
        value = frame(relation())
        for faction in value['targeting_factions']:
            faction['county_member_title_ids'] = []
            faction.pop('county_member_observations', None)
        project_case('projection-no-counties-not-applicable', value)
        value = frame(relation())
        faction = value['targeting_factions'][1]
        extra = copy.deepcopy(faction['county_member_observations'][0])
        extra['county_title_id'] += 1
        extra.update(relation(None, 0))
        faction['county_member_title_ids'].append(extra['county_title_id'])
        faction['county_member_observations'].append(extra)
        project_case('projection-mixed-available-and-unavailable', value)
        value = frame(relation())
        value['targeting_factions'][2]['county_member_title_ids'] = [scope['COUNTY_TITLE_ID']]
        value['targeting_factions'][2]['county_member_observations'] = [copy.deepcopy(value['targeting_factions'][1]['county_member_observations'][0])]
        project_case('projection-same-county-distinct-factions-not-merged', value)
        def ref(path):
            data = path.read_bytes()
            return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        document = {'schema': 'xar.ck3.java.faction-culture-producer-golden/v1',
            'capture': {'machine_id': 'xenoamess-full-tower-eb9d2c1186',
                        'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'method': 'unchanged original normalize/project; complete original unittest class; declared input projection checked equal to original normalized full-input outcome',
                        'native_rpc_count': 0, 'ledger_writes': 0},
            'producer': ref(SOURCE), 'fixture_test': ref(TEST),
            'base_fixture': ref(ROOT / 'ck3_autonomous_player/tests/fixtures/native_12002/governance/faction-alerts.json'),
            'original_unit_tests_run': result.testsRun, 'original_unit_tests_skipped': len(result.skipped),
            'cases': cases}
        encoded = (json.dumps(document, ensure_ascii=False, separators=(',', ':')) + '\\n').encode('utf-8')
        if len(encoded) > 70000:
            raise ValueError('culture golden budget exceeded')
        output = Path(sys.argv[2])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded)
        print(json.dumps({'status': 'ORIGINAL_PRODUCER_CAPTURED', 'cases': len(cases), 'bytes': len(encoded),
                          'sha256': hashlib.sha256(encoded).hexdigest(), 'original_tests': result.testsRun,
                          'skipped': len(result.skipped), 'native_rpc_count': 0, 'ledger_writes': 0}))
        
        """;
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("source-root python output-path required");
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("capture output must be new");
        ProcessBuilder command = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", ORACLE, root.toString(), output.toString());
        command.directory(root.toFile());
        command.environment().put("OPENBLAS_NUM_THREADS", "1"); command.environment().put("OMP_NUM_THREADS", "1");
        command.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        command.environment().put("TEMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch");
        command.environment().put("TMP", "D:/codex-ck3-demos/2026-10-22-java-phase1/scratch");
        command.redirectErrorStream(true);
        Process child = command.start(); byte[] log = child.getInputStream().readNBytes(65_537); int exit = child.waitFor();
        if (log.length > 65_536) throw new IllegalStateException("capture diagnostics limit");
        System.out.print(new String(log, StandardCharsets.UTF_8));
        if (exit != 0) throw new IllegalStateException("original culture producer exit " + exit);
        if (!Files.isRegularFile(output) || Files.size(output) > 70_000) throw new IllegalStateException("culture capture output limit");
    }
}

