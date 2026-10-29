package org.xar.ck3.control.score;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Live unchanged dec/fmt differential, including the real Unicode conversion failure. */
final class ScoreDecimalOriginalBoundaryTest {
    private static final String ORIGINAL_SHA = "ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d";
    private static final String SCRIPT = """
        import hashlib, json, sys
        from decimal import DecimalException, getcontext
        from pathlib import Path
        root = Path(sys.argv[1]).resolve()
        source = root / 'ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py'
        expected = sys.argv[2]
        def pin():
            return hashlib.sha256(source.read_bytes()).hexdigest()
        if pin() != expected:
            raise SystemExit('unchanged actual score producer required')
        sys.path.insert(0, str(root / 'ck3_autonomous_player/src'))
        from xar_autoplayer import campaign_development_score_v1 as original
        cases = ['1.2300', '-0', '-0.00', '-0E+2', '1E+2', '0.0000001',
                 '12345678901234567890123456789012345678901234567890',
                 '_1_', '__1__', '1_._2', '+1.00', '1 2', '_ 1 _', '_\\u00a01_',
                 '1_\\u00a0', '', 'NaN', 'Infinity']
        for point in [9, 10, 11, 12, 13, 28, 29, 30, 31, 32, 0x85, 0xa0,
                      0x1680, *range(0x2000, 0x200b), 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]:
            cases.extend([chr(point) + '1.25' + chr(point), '1' + chr(point) + '2'])
        for value in ['١٢.٥', '１２.５', '१२.५', '𝟙𝟚.𝟝', '𐒡𐒢.𐒥', '²', '①', 'Ⅻ', '−1']:
            cases.append(value)
        rows = []
        for text in cases:
            try:
                value = original.fmt(original.dec(text))
                rows.append({'input': text, 'kind': 'result', 'expected': value})
            except (ValueError, DecimalException):
                rows.append({'input': text, 'kind': 'invalid'})
        if pin() != expected:
            raise SystemExit('actual score producer changed during differential')
        print(json.dumps({'source_sha256': expected, 'decimal_default_precision': getcontext().prec,
                         'decimal_default_rounding': getcontext().rounding, 'vectors': rows}, ensure_ascii=True,
                         allow_nan=False, separators=(',', ':')))
        """;

    @Test void exactOriginalDecimalUnicodeBoundaryAndIntervalRoundtrip() throws Exception {
        JsonNode captured = capture();
        assertEquals(ORIGINAL_SHA, captured.path("source_sha256").textValue());
        assertEquals(28, captured.path("decimal_default_precision").intValue());
        assertEquals("ROUND_HALF_EVEN", captured.path("decimal_default_rounding").textValue());
        assertTrue(captured.path("vectors").size() > 80);
        int results = 0, rejected = 0;
        for (JsonNode row : captured.path("vectors")) {
            assertTrue(row.get("input").isTextual());
            String value = row.get("input").textValue();
            if ("invalid".equals(row.path("kind").textValue())) {
                assertThrows(ContractViolationException.class, () -> ScoreDecimal.parse(value), value);
                rejected++;
            } else {
                ScoreDecimal parsed = ScoreDecimal.parse(value);
                assertEquals(row.path("expected").textValue(), parsed.lexical(), value);
                ScoreInterval interval = ScoreInterval.exact(parsed);
                byte[] wire = CampaignScoreCodec.encodeInterval(interval);
                assertEquals(interval, CampaignScoreCodec.decodeInterval(wire));
                assertArrayEquals(wire, CampaignScoreCodec.encodeInterval(CampaignScoreCodec.decodeInterval(wire)));
                results++;
            }
        }
        assertTrue(results > 30); assertTrue(rejected > 30);
        System.out.println("ORIGINAL_SCORE_DECIMAL_BOUNDARY vectors=" + captured.path("vectors").size()
                + " results=" + results + " rejected=" + rejected);
    }

    @Test void decimalProfileRemainsFiniteTextAndPreservesSignedZero() {
        for (String raw : List.of("true", "false", "1.0", "1", "null", "[]", "{}")) {
            assertThrows(ContractViolationException.class,
                    () -> CampaignScoreCodec.decimal(StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8))));
        }
        assertEquals("-0", ScoreDecimal.parse("\u00a0-0.00\u00a0").lexical());
        assertThrows(ContractViolationException.class, () -> ScoreDecimal.parse("1e9999999999"));
    }

    private static JsonNode capture() throws Exception {
        Path repo = requiredPath("XAR_ORACLE_REPO"), python = requiredPath("XAR_ORACLE_PYTHON");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-",
                repo.toString(), ORIGINAL_SHA).directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), 65536));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 16384));
            try {
                try (var input = process.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
                assertTrue(process.waitFor(30, TimeUnit.SECONDS), "unchanged original oracle timed out");
                byte[] output = stdout.get(5, TimeUnit.SECONDS), error = stderr.get(5, TimeUnit.SECONDS);
                assertEquals(0, process.exitValue(), new String(error, StandardCharsets.UTF_8));
                assertTrue(output.length > 0); return StrictJson.parse(output);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }
    private static Path requiredPath(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) { throw new AssertionError(name + " required; absent oracle is NOT_RUN, never skipped PASS"); }
        Path path = Path.of(value).toAbsolutePath().normalize();
        assertTrue(Files.exists(path), name + " must exist"); return path;
    }
    private static byte[] bounded(java.io.InputStream stream, int limit) throws IOException {
        try (stream) {
            byte[] result = stream.readNBytes(limit + 1);
            if (result.length > limit) { throw new IOException("bounded original decimal oracle output exceeded"); }
            return result;
        }
    }
}
