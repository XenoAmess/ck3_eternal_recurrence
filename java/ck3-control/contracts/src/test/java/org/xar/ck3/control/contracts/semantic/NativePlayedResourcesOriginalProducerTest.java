package org.xar.ck3.control.contracts.semantic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual unchanged Python producers are an oracle in this compatibility regression only. */
final class NativePlayedResourcesOriginalProducerTest {
    private static final String ORIGINAL = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py";
    private static final String ORIGINAL_SHA = "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String SCRIPT = """
            import hashlib
            import json
            from pathlib import Path
            import sys
            repo = Path(sys.argv[1]).resolve()
            source = repo / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
            expected = sys.argv[2]
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            if before != expected:
                raise RuntimeError('actual original producer source changed')
            sys.path.insert(0, str(repo / 'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import native_driver
            names = ('played_character_gold', 'played_character_prestige', 'played_character_piety')
            producers = {name: getattr(native_driver, '_' + name) for name in names}
            for producer in producers.values():
                if Path(producer.__code__.co_filename).resolve() != source.resolve():
                    raise RuntimeError('oracle is not the actual native_driver producer')
            cases = json.load(sys.stdin)['cases']
            results = []
            for case in cases:
                value = None if case['missing'] else json.loads(case['input_json'])
                for name, producer in producers.items():
                    try:
                        result = producer(value)
                    except ValueError:
                        row = {'case_id': case['case_id'], 'field': name, 'status': 'rejected'}
                    else:
                        row = {'case_id': case['case_id'], 'field': name,
                               'status': 'accepted', 'value': result}
                    results.append(row)
            if hashlib.sha256(source.read_bytes()).hexdigest() != before:
                raise RuntimeError('actual original source drifted during oracle calls')
            json.dump({'source_sha256': before, 'results': results}, sys.stdout,
                      ensure_ascii=False, allow_nan=False, separators=(',', ':'))
            """;

    private record Case(String inputJson, boolean missing, boolean strictScaleFloatDifference) { }

    private static List<Case> cases() {
        List<Case> result = new ArrayList<>();
        result.add(new Case("null", true, false));
        for (String text : List.of("null", "{\"raw\":-9223372036854775808,\"scale\":100000}",
                "{\"raw\":9223372036854775807,\"scale\":100000}",
                "{\"raw\":9007199254740993,\"scale\":100000}",
                "{\"raw\":-9007199254740993,\"scale\":100000}",
                "{\"raw\":0,\"scale\":100000}", "{\"raw\":-1,\"scale\":100000}",
                "{\"raw\":true,\"scale\":100000}", "{\"raw\":1.0,\"scale\":100000}",
                "{\"raw\":1e0,\"scale\":100000}", "{\"raw\":\"1\",\"scale\":100000}",
                "{\"raw\":9223372036854775808,\"scale\":100000}",
                "{\"raw\":-9223372036854775809,\"scale\":100000}",
                "{\"raw\":1,\"scale\":true}", "{\"raw\":1,\"scale\":\"100000\"}",
                "{\"raw\":1,\"scale\":99999}", "{\"raw\":1,\"scale\":null}",
                "{\"raw\":1}", "{\"scale\":100000}",
                "{\"raw\":1,\"scale\":100000,\"extra\":0}", "{}", "[]", "false")) {
            result.add(new Case(text, false, false));
        }
        // Python equality accepts these scales. The user requires integer tokens
        // at the Java boundary; this deliberate restriction is tested explicitly.
        result.add(new Case("{\"raw\":1,\"scale\":100000.0}", false, true));
        result.add(new Case("{\"raw\":1,\"scale\":1e5}", false, true));
        return List.copyOf(result);
    }

    @Test
    void actualThreePythonProducersAgreeExceptTheDeclaredStrictScaleTokenBoundary() throws Exception {
        Path python = Path.of(required("xar.python")).toRealPath();
        Path repository = Path.of(required("xar.repository.root")).toRealPath();
        Path original = repository.resolve(ORIGINAL).toRealPath();
        assertEquals(ORIGINAL_SHA, HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(original))));
        List<Case> cases = cases();
        ObjectNode request = StrictJson.object();
        ArrayNode values = request.putArray("cases");
        for (int index = 0; index < cases.size(); index++) {
            Case vector = cases.get(index);
            values.addObject().put("case_id", index).put("input_json", vector.inputJson())
                    .put("missing", vector.missing());
        }
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8",
                "-c", SCRIPT, repository.toString(), ORIGINAL_SHA).directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        byte[] output;
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), 131_072));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 131_072));
            try {
                try (var input = process.getOutputStream()) { input.write(StrictJson.canonical(request)); }
                if (!process.waitFor(60, TimeUnit.SECONDS)) { throw new IOException("original producer oracle timed out"); }
                output = stdout.get(10, TimeUnit.SECONDS);
                assertEquals(0, process.exitValue(), new String(stderr.get(10, TimeUnit.SECONDS), StandardCharsets.UTF_8));
            } finally {
                if (process.isAlive()) {
                    process.destroyForcibly();
                    if (!process.waitFor(10, TimeUnit.SECONDS)) { throw new IOException("oracle child did not terminate"); }
                }
            }
        }
        JsonNode oracle = StrictJson.parse(output, 131_072);
        assertEquals(ORIGINAL_SHA, oracle.get("source_sha256").textValue());
        JsonNode rows = oracle.get("results");
        assertEquals(cases.size() * NativePlayedResources.Resource.values().length, rows.size());
        int rowIndex = 0;
        for (Case vector : cases) {
            for (NativePlayedResources.Resource resource : NativePlayedResources.Resource.values()) {
                JsonNode observed = rows.get(rowIndex++);
                assertEquals((rowIndex - 1) / 3, observed.get("case_id").intValue());
                assertEquals(resource.wire(), observed.get("field").textValue());
                JsonNode originalValue = vector.missing() ? null
                        : StrictJson.parse(vector.inputJson().getBytes(StandardCharsets.UTF_8));
                if (vector.strictScaleFloatDifference()) {
                    assertEquals("accepted", observed.get("status").textValue());
                    assertEquals(StrictJson.parse("{\"raw\":1,\"scale\":100000}".getBytes(StandardCharsets.UTF_8)),
                            observed.get("value"));
                    assertThrows(ContractViolationException.class,
                            () -> NativePlayedResources.normalize(originalValue, resource));
                } else if (observed.get("status").textValue().equals("rejected")) {
                    assertThrows(ContractViolationException.class,
                            () -> NativePlayedResources.normalize(originalValue, resource));
                } else {
                    assertEquals("accepted", observed.get("status").textValue());
                    assertArrayEquals(StrictJson.canonical(observed.get("value")),
                            StrictJson.canonical(NativePlayedResources.normalize(originalValue, resource)));
                }
            }
        }
    }

    private static String required(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException(property + " required; actual original producer NOT_RUN; no skip credit");
        }
        return value;
    }

    private static byte[] bounded(InputStream input, int maximum) throws IOException {
        try (input; var output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (output.size() + count > maximum) { throw new IOException("bounded original producer output exceeded"); }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}
