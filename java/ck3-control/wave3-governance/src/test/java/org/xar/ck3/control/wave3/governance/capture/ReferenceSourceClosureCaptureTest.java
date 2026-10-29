package org.xar.ck3.control.wave3.governance.capture;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ReferenceSourceClosureCaptureTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String BOOTSTRAP = "tools/.venv/Lib/site-packages/win32/lib/pywin32_bootstrap.py";
    @TempDir Path temporary;
    private int observations;

    @Test void metadataProducerBindsActualSourcesAndRoundTripsWithoutAnOracleResult() throws Exception {
        Path repository = fixture();
        Path output = temporary.resolve("closure.json.gz");
        var ref = ReferenceSourceClosureCapture.writeNew(repository, "software-fixture-machine", output);
        var closure = ReferenceSourceClosureCapture.verify(repository, output, ref.sha256());
        assertEquals(8, closure.files().size());
        assertEquals(1, closure.files().stream().filter(row -> row.role()
                == ReferenceSourceClosureCapture.Role.INTERPRETER_BOOTSTRAP).count());
        assertTrue(closure.files().stream().anyMatch(row -> row.path().equals(repository.resolve(BOOTSTRAP).toString())));
        assertThrows(IOException.class, () -> ReferenceSourceClosureCapture.writeNew(repository, "software-fixture-machine", output));
    }

    @Test void missingBootstrapAndWrongSourceRoleRejectBeforeAnOracleStarts() throws Exception {
        Path repository = fixture();
        ObjectNode base = serialized(repository);
        ArrayNode rows = (ArrayNode) base.get("files");
        for (int index = rows.size() - 1; index >= 0; index--) {
            if (rows.get(index).path("role").asText().equals("INTERPRETER_BOOTSTRAP")) rows.remove(index);
        }
        Path missing = compressed("missing-bootstrap.json.gz", base);
        assertThrows(IOException.class, () -> ReferenceSourceClosureCapture.verify(repository, missing, hash(missing)));
        ObjectNode wrong = serialized(repository);
        ((ObjectNode) wrong.path("files").get(0)).put("role", "REFERENCE");
        Path wrongRole = compressed("wrong-role.json.gz", wrong);
        assertThrows(IOException.class, () -> ReferenceSourceClosureCapture.verify(repository, wrongRole, hash(wrongRole)));
    }

    @Test void integerSourceLengthsRejectBooleanDecimalAndStringTokens() throws Exception {
        Path repository = fixture();
        for (String token : List.of("true", "1.0", "\"1\"")) {
            String raw = JSON.writeValueAsString(serialized(repository));
            String wrong = raw.replaceFirst("\"bytes\":\\d+", "\"bytes\":" + token);
            assertTrue(!raw.equals(wrong));
            Path output = compressedRaw("wrong-size-" + token.length() + "-" + token.hashCode() + ".json.gz", wrong.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(IOException.class, () -> ReferenceSourceClosureCapture.verify(repository, output, hash(output)));
        }
    }

    @Test void actualBootstrapDriftAndAdditionalProductionSourceInvalidateTheOriginalClosure() throws Exception {
        Path repository = fixture();
        Path output = temporary.resolve("original.json.gz");
        var ref = ReferenceSourceClosureCapture.writeNew(repository, "software-fixture-machine", output);
        Path production = repository.resolve("ck3_autonomous_player/src/xar_autoplayer");
        Path added = production.resolve("new_actual_source.py");
        Files.writeString(added, "value = 2\n");
        assertThrows(IOException.class, () -> ReferenceSourceClosureCapture.verify(repository, output, ref.sha256()));
        Files.delete(added);
        Files.writeString(repository.resolve(BOOTSTRAP), "changed = True\n");
        assertThrows(IOException.class, () -> ReferenceSourceClosureCapture.verify(repository, output, ref.sha256()));
    }

    private Path fixture() throws IOException {
        Path repository = Files.createDirectory(temporary.resolve("repository")).toRealPath();
        for (String relative : List.of("ck3_autonomous_player/src/xar_autoplayer/reference_fixture.py",
                "ck3_autonomous_player/tests/unit/test_family_guardian_negative_cadence_v1.py",
                "ck3_autonomous_player/tests/unit/test_service_family_guardian_negative_cadence_v1.py",
                "ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json",
                "ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py",
                "ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py",
                "tools/ck3_live_run_id.py", BOOTSTRAP)) {
            Path file = repository.resolve(relative);
            Files.createDirectories(file.getParent());
            Files.writeString(file, relative.endsWith(".json") ? "{}\n" : "fixture = True\n");
        }
        return repository;
    }
    private ObjectNode serialized(Path repository) throws IOException {
        Path output = temporary.resolve("observed-" + observations++ + ".json.gz");
        ReferenceSourceClosureCapture.writeNew(repository, "software-fixture-machine", output);
        try (GZIPInputStream gzip = new GZIPInputStream(Files.newInputStream(output))) {
            return (ObjectNode) JSON.readTree(gzip);
        }
    }
    private Path compressed(String name, ObjectNode value) throws IOException {
        return compressedRaw(name, JSON.writeValueAsBytes(value));
    }
    private Path compressedRaw(String name, byte[] value) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(buffer)) { gzip.write(value); }
        Path output = temporary.resolve(name);
        Files.write(output, buffer.toByteArray());
        return output;
    }
    private static String hash(Path path) throws IOException {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
