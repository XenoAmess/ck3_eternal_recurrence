package org.xar.ck3.control.wave2.planning.scoretarget;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** One-off oracle capture only. Normal JUnit consumes the committed corpus without Python. */
public final class PlayerWarGoldenExporter {
    private static final int MAXIMUM_BYTES = 96 * 1024;
    private static final String SCRIPT = """
        from copy import deepcopy
        from datetime import datetime, timezone
        import hashlib
        import json
        from pathlib import Path
        import sys
        import unittest
        repo = Path(sys.argv[1]).resolve()
        machine = sys.argv[2]
        if not machine or len(machine) > 256:
            raise SystemExit('explicit machine identity required')
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import campaign_score_save_reader as reader
        import test_campaign_development_score_v1 as suite
        expected_pins = {
            'ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py':
                'ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e',
            'ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py':
                'ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d',
            'ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py':
                '0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2',
        }
        def pins():
            return {path: hashlib.sha256((repo / path).read_bytes()).hexdigest() for path in expected_pins}
        if pins() != expected_pins:
            raise SystemExit('unchanged oracle/test pins required')
        original = reader.player_war_defence
        vectors = []
        case = 'original-regression'
        def capture(character_fields, wars, *, actor):
            request = deepcopy({'actor': actor, 'character_fields': character_fields, 'wars': wars})
            row = {'ordinal': len(vectors) + 1, 'case': case,
                'input_json': json.dumps(request, allow_nan=False, ensure_ascii=False, sort_keys=False, separators=(',', ':'))}
            try:
                own, audit = original(character_fields, wars, actor=actor)
            except ValueError:
                row['expected_kind'] = 'invalid_contract'
                vectors.append(row)
                raise
            row['expected_kind'] = 'result'
            row['expected'] = {'own_defence': own, 'audit': deepcopy(audit)}
            vectors.append(row)
            return own, audit
        method = 'test_explicit_player_wars_ignore_unrelated_shells_but_not_missing_or_conflicts'
        case = method
        reader.player_war_defence = capture
        try:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(
                unittest.TestSuite([suite.CampaignScoreTests(method)]))
        finally:
            reader.player_war_defence = original
        if not result.wasSuccessful() or result.testsRun != 1 or result.skipped:
            raise SystemExit('original complete player-war regression did not pass')
        def run(label, fields, wars, actor=3):
            global case
            case = label
            return capture(fields, wars, actor=actor)
        run('explicit-empty-presence', {'present:landed_data.wars': 'true'}, {})
        run('explicit-null-is-invalid-list', {'present:landed_data.wars': 'true', 'landed_data.wars': None}, {})
        for value in (True, 9, 9.0, [], {}):
            run('wrong-list-token-' + type(value).__name__, {'landed_data.wars': value}, {})
        for marker in ('nonunique:landed_data.wars', 'incomplete:landed_data.wars'):
            for value in (False, None, ''):
                run('marker-presence-over-value', {'landed_data.wars': '9', marker: value}, {'9': {'casus_belli.defender': '3'}})
        for row in (None, [], True, 9, 9.0, '9', {}):
            run('wrong-war-row-' + type(row).__name__, {'landed_data.wars': '9'}, {'9': row})
        for defender in (None, True, 3, 3.0, [], {}, '3.0', '-3', '+3', ' 3'):
            run('wrong-defender-token-or-grammar', {'landed_data.wars': '9'}, {'9': {'casus_belli.defender': defender}})
        run('verify-all-after-positive-match', {'landed_data.wars': '9 10'}, {'9': {'casus_belli.defender': '3'}})
        run('leading-zero-ids-normalize-for-lookup', {'landed_data.wars': '0009'}, {'9': {'casus_belli.defender': '0003'}})
        run('noncanonical-table-key-does-not-alias', {'landed_data.wars': '9'}, {'09': {'casus_belli.defender': '3'}})
        run('numeric-duplicate-after-normalization', {'landed_data.wars': '9 0009'}, {'9': {'casus_belli.defender': '3'}})
        run('unicode-digits-and-whitespace', {'landed_data.wars': '٩' + chr(0x85) + '１０'},
            {'9': {'casus_belli.defender': '٣'}, '10': {'casus_belli.defender': '7'}})
        large = 18446744073709551617
        run('python-integer-above-uint64-exact', {'landed_data.wars': str(large)},
            {str(large): {'casus_belli.defender': str(large)}}, large)
        run('zero-retains-legacy-parser-domain', {'landed_data.wars': '0'}, {'0': {'casus_belli.defender': '0'}}, 0)
        run('complete-1024-ids', {'landed_data.wars': ' '.join(str(n) for n in range(1024))},
            {str(n): {'casus_belli.defender': '7'} for n in range(1024)})
        run('over-1024-ids-rejects-before-lookup', {'landed_data.wars': ' '.join(str(n) for n in range(1025))}, {})
        run('extensions-are-declared-projection', {'landed_data.wars': '9', 'new_sdk_field': {'nested': [None, 1.0]}},
            {'9': {'casus_belli.defender': '7', 'another_sdk_extension': []}})
        if pins() != expected_pins:
            raise SystemExit('source changed during oracle capture')
        header = {'schema': 'g2.scoretarget-player-war-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': expected_pins, 'original_test_methods': [method],
            'original_tests_run': result.testsRun, 'original_skips': 0, 'vector_count': len(vectors),
            'native_game_rpc_count': 0, 'python_int_max_str_digits': sys.get_int_max_str_digits(),
            'consumer': 'campaign_score_save_reader._project_metrics:825',
            'scope': 'pure_saved_player_war_defence_only', 'production_consumer_switched': False}
        for row in [header, *vectors]:
            raw = json.dumps(row, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            if len(raw) > 65536:
                raise SystemExit('one golden row exceeds shared strict parser budget')
            sys.stdout.buffer.write(raw + bytes([10]))
        """;

    private PlayerWarGoldenExporter() { }

    /** Arguments: exact repo, existing Python interpreter, observed machine_id. */
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python machine_id required"); }
        Path repo = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path output = repo.resolve("java/ck3-control/wave2-planning/src/test/resources/scoretarget/player_war_defence_python_v1.jsonl");
        if (Files.exists(output)) { throw new IOException("create-only golden already exists"); }
        ProcessBuilder builder = new ProcessBuilder(arguments[1], "-B", "-X", "utf8", "-c", SCRIPT,
                repo.toString(), arguments[2]);
        builder.directory(repo.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> read(process.getInputStream(), MAXIMUM_BYTES));
            var stderr = executor.submit(() -> read(process.getErrorStream(), 16384));
            try {
                if (!process.waitFor(90, TimeUnit.SECONDS)) { throw new IOException("oracle capture timed out"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS);
                byte[] errors = stderr.get(10, TimeUnit.SECONDS);
                System.err.write(errors);
                if (process.exitValue() != 0 || raw.length == 0 || raw[raw.length - 1] != 10) {
                    throw new IOException("oracle failed, exit=" + process.exitValue());
                }
                Files.createDirectories(output.getParent());
                Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
                System.out.println("WROTE " + output + " bytes=" + raw.length);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }

    private static byte[] read(InputStream stream, int maximum) throws IOException {
        try (stream; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = stream.read(buffer)) != -1) {
                if (output.size() + count > maximum) { throw new IOException("bounded oracle output exceeded"); }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}
