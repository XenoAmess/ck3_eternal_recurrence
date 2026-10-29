package org.xar.ck3.control.wave2.planning.savedcountymembership;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Capture the unchanged complete original membership suite; not part of default JUnit execution. */
public final class SavedMembershipGoldenExporter {
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
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import campaign_score_save_reader as reader
        import test_campaign_score_save_membership_v1 as suite
        expected = {
            'ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py':
                'ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e',
            'ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py':
                'ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d',
            'ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py':
                '749742086fa8977c2eafa0593801fe4328228a485ebe5f9178006ee823bb0006',
            'ck3_autonomous_player/tests/unit/test_campaign_score_save_membership_v1.py':
                'db3c8595021908f58162b51eb0c4b9324a1f98ed8d0e19461741c13e3cd2acf7',
        }
        def pins():
            return {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in expected}
        if pins() != expected or sys.get_int_max_str_digits() != 4300:
            raise SystemExit('unchanged qualified producer/test domain required')
        original = reader.audit_saved_county_membership_v1
        vectors, unique = [], {}
        case = 'original-suite'
        calls = 0
        def capture(projection, *, actor, house, dynasty, county_baronies, source_id):
            global calls
            calls += 1
            request = deepcopy({'actor': actor, 'house': house, 'dynasty': dynasty, 'source_ref': source_id,
                'county_baronies': county_baronies, 'projection': {
                    'titles': projection.titles, 'title_order': list(projection.titles), 'houses': projection.houses,
                    'character_houses': projection.character_houses,
                    'character_house_unknown': sorted(projection.character_house_unknown),
                    'character_sources': sorted(projection.character_sources),
                    'stream_complete': projection.stream_complete, 'unknown_key_fields': projection.unknown_key_fields,
                    'root_keys': projection.root_keys, 'metadata': projection.metadata}})
            value = original(projection, actor=actor, house=house, dynasty=dynasty,
                county_baronies=county_baronies, source_id=source_id)
            # Explicit title_order preserves stream semantics through JSON object normalization.
            raw_input = json.dumps(request, allow_nan=False, ensure_ascii=False, sort_keys=False, separators=(',', ':'))
            key = raw_input + json.dumps(value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            if key in unique:
                row = unique[key]
                if case not in row['captured_in']:
                    row['captured_in'].append(case)
            else:
                row = {'ordinal': len(vectors) + 1, 'captured_in': [case], 'input_json': raw_input, 'expected': deepcopy(value)}
                vectors.append(row)
                unique[key] = row
            return value
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                global case
                case = test.id().rsplit('.', 1)[-1]
                super().startTest(test)
        names = unittest.defaultTestLoader.getTestCaseNames(suite.SavedCountyMembershipTests)
        if len(names) != 11:
            raise SystemExit('expected all 11 original membership methods')
        reader.audit_saved_county_membership_v1 = capture
        try:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=Result).run(
                unittest.defaultTestLoader.loadTestsFromTestCase(suite.SavedCountyMembershipTests))
        finally:
            reader.audit_saved_county_membership_v1 = original
        if not result.wasSuccessful() or result.testsRun != 11 or result.skipped:
            raise SystemExit('full original membership suite failed')
        seed, _, _, _ = suite.world()
        mapping = deepcopy(suite.CONTEXT['county_baronies'])
        def run(label, projection=seed, county=mapping, actor=1, house=174, dynasty=174):
            global case
            case = label
            return capture(projection, actor=actor, house=house, dynasty=dynasty,
                county_baronies=county, source_id='synthetic_boundary')
        for label, value in [('bool', True), ('float', 12.0), ('string', '12'), ('zero', 0), ('negative', -1)]:
            changed = deepcopy(mapping); changed['c_a']['b_a'] = value
            run('province-type-or-range-' + label, county=changed)
        changed = deepcopy(mapping); changed['c_b'] = {'b_a': 13}
        run('shared-barony-conflicts-both-counties', county=changed)
        changed = deepcopy(mapping); changed['c_a']['b_extra'] = changed['c_a']['b_a']
        run('duplicate-province-within-county', county=changed)
        run('missing-map-is-unavailable', county=None)
        run('missing-house-anchor', house=None)
        changed = deepcopy(seed); changed.titles[101]['de_facto_liege'] = None
        run('null-liege-is-present-invalid', projection=changed)
        empty = reader.SaveProjection({1}); empty.complete()
        run('absent-census-does-not-prove-zero', projection=empty)
        empty.root_keys.append('landed_titles')
        run('explicit-empty-complete-census', projection=empty)
        cycle = deepcopy(seed)
        cycle.titles[100].update(holder='2', de_facto_liege='101')
        cycle.titles[101].update(holder='2', de_facto_liege='100')
        run('cycle-terminal-stream-order-forward', projection=cycle, actor=99)
        cycle.titles = dict(reversed(list(cycle.titles.items())))
        run('cycle-terminal-stream-order-reverse', projection=cycle, actor=99)
        if pins() != expected:
            raise SystemExit('source changed during capture')
        header = {'schema': 'g2.saved-county-membership-python-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': expected, 'original_tests_run': result.testsRun, 'original_skips': 0,
            'original_test_methods': names, 'captured_calls': calls, 'unique_vector_count': len(vectors),
            'native_game_rpc_count': 0, 'production_consumer_switched': False,
            'deduplication': 'identical exact ordered request and output; all captured lineages retained'}
        for row in [header, *vectors]:
            raw = json.dumps(row, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            if len(raw) > 65536:
                raise SystemExit('one membership vector exceeds parser contract')
            sys.stdout.buffer.write(raw + bytes([10]))
        """;


    public static com.fasterxml.jackson.databind.JsonNode verifyOriginalConsumers() throws Exception {
        return org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.verifyOriginalConsumer(
                org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.ConsumerOperation.SAVED_MEMBERSHIP,
                java.util.List.of(), org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter::throughSavedScorePort);
    }

    private SavedMembershipGoldenExporter() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length < 3 || arguments.length > 4) { throw new IllegalArgumentException("repo python machine_id [D-output] required"); }
        Path repo = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path output = arguments.length == 4 ? Path.of(arguments[3]).toAbsolutePath().normalize()
                : repo.resolve("java/ck3-control/wave2-planning/src/test/resources/savedcountymembership/membership_python_v1.jsonl");
        if (arguments.length == 4 && !output.getParent().equals(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/logs"))) {
            throw new IOException("admitted D logs output required");
        }
        if (Files.exists(output)) { throw new IOException("membership golden is create-only"); }
        Process process = new ProcessBuilder(arguments[1], "-B", "-X", "utf8", "-",
                repo.toString(), arguments[2]).directory(repo.toFile()).start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> read(process.getInputStream(), 96 * 1024));
            var stderr = executor.submit(() -> read(process.getErrorStream(), 16384));
            try {
                try (var stdin = process.getOutputStream()) {
                    stdin.write(SCRIPT.getBytes(StandardCharsets.UTF_8));
                }
                if (!process.waitFor(90, TimeUnit.SECONDS)) { throw new IOException("membership oracle timed out"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS); byte[] error = stderr.get(10, TimeUnit.SECONDS);
                System.err.write(error);
                if (process.exitValue() != 0 || raw.length == 0 || raw[raw.length - 1] != 10) {
                    throw new IOException("membership oracle failed, exit=" + process.exitValue());
                }
                Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
                System.out.println("WROTE " + output + " bytes=" + raw.length);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }
    private static byte[] read(InputStream stream, int maximum) throws IOException {
        try (stream; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = stream.read(buffer)) != -1) {
                if (output.size() + count > maximum) { throw new IOException("membership corpus exceeds finite budget"); }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}

