package org.xar.ck3.rrf;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.acceptance.CompatibilityModEmitter;
import org.xar.ck3.rrf.acceptance.CompatibilityModEmitter.Request;
import org.xar.ck3.rrf.acceptance.CompatibilityModEmitter.Source;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FilePin;

final class CompatibilityModEmitterTest {
    @TempDir Path temporary;

    @BeforeEach void canonicalTemporaryRoot() throws IOException {
        // Hosted Windows TEMP may use an alias; requests require canonical paths.
        temporary = temporary.toRealPath();
    }

    @Test void actualProducerReachesPublicPrepareSavedHostAndRealAllocatorFingerprint() throws Exception {
        Request request = request();
        Path output = temporary.resolve("emitted");
        var manifest = CompatibilityModEmitter.emit(Json.read(Json.write(request), Request.class), output);
        assertEquals(List.of("slots", "dynastic"), manifest.caseInputs().compatibilityMods().stream().map(mod -> mod.key()).toList());
        assertFalse(manifest.gameStarted()); assertEquals("NOT_ASSESSED", manifest.businessAcceptance());
        assertEquals(manifest, Json.read(Files.readAllBytes(output.resolve("compatibility-mods.json")), CompatibilityModEmitter.Manifest.class));
        Path repository = Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        Path local = repository.resolve("tools/.venv/Scripts/python.exe");
        String python = Files.isRegularFile(local) ? local.toString() : "python";
        ProcessBuilder builder = new ProcessBuilder(python, "-B", "-X", "utf8", "-m", "unittest",
                "test_compatibility_mod_profiles.PublicCompatibilityAllocationTests.test_producer_to_public_prepare_saved_host_and_actual_allocation_fingerprint")
                .directory(repository.resolve("tools").toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_COMPATIBILITY_PRODUCER_MANIFEST", output.resolve("compatibility-mods.json").toString());
        String result = execute(builder);
        assertTrue(result.contains("OK"), result);
    }

    @Test void strictRequestRejectsNullWrongTypesUnknownFieldsAndRepeatedKeys() throws IOException {
        Request request = request();
        String source = new String(Json.write(request), StandardCharsets.UTF_8);
        for (String wrong : List.of("null", "true", "1.0", "\"1\""))
            assertThrows(IOException.class, () -> Json.read(source.replace("\"schema_version\" : 1", "\"schema_version\" : " + wrong).getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IOException.class, () -> Json.read(source.replace("\"mods\"", "\"unknown\"").getBytes(StandardCharsets.UTF_8), Request.class));
        assertThrows(IllegalArgumentException.class, () -> new Request(1, "scope-test-machine", List.of(request.mods().getFirst(), request.mods().getFirst())));
        assertThrows(IllegalArgumentException.class, () -> new Source("../escape", temporary.toString(), pin(temporary.resolve("slots-release.json"))));
    }

    @Test void sourceManifestContentFileSetAndCanonicalPathsAreVerifiedBeforeEmission() throws IOException {
        Request request = request();
        Source source = request.mods().getFirst();
        Path root = Path.of(source.directory());
        Files.writeString(root.resolve("undeclared.txt"), "extra");
        assertThrows(IllegalArgumentException.class, () -> CompatibilityModEmitter.emit(request, temporary.resolve("extra-output")));
        assertFalse(Files.exists(temporary.resolve("extra-output")));
        Files.delete(root.resolve("undeclared.txt"));
        Path manifest = Path.of(source.sourceManifest().path());
        Files.writeString(manifest, " ", java.nio.file.StandardOpenOption.APPEND);
        assertThrows(IllegalArgumentException.class, () -> CompatibilityModEmitter.emit(request, temporary.resolve("changed-output")));
        assertFalse(Files.exists(temporary.resolve("changed-output")));
    }

    private Request request() throws IOException {
        java.util.ArrayList<Source> sources = new java.util.ArrayList<>();
        for (String key : List.of("slots", "dynastic")) {
            Path root = temporary.resolve(key); Files.createDirectories(root.resolve("common/on_action"));
            Files.writeString(root.resolve("descriptor.mod"), "name=\"" + key + "\"\n");
            Files.writeString(root.resolve("common/on_action/start.txt"), "on_game_start_after_lobby = { }\n");
            Path manifest = temporary.resolve(key + "-release.json");
            Files.write(manifest, Json.write(Map.of("files", List.of(
                    entry(root, "common/on_action/start.txt", key.equals("slots") ? "bytes" : "size"),
                    entry(root, "descriptor.mod", key.equals("slots") ? "bytes" : "size")))));
            sources.add(new Source(key, root.toString(), pin(manifest)));
        }
        return new Request(1, "scope-test-machine", sources);
    }
    private static Map<String, Object> entry(Path root, String relative, String sizeField) throws IOException {
        FilePin pin = pin(root.resolve(relative));
        return Map.of("path", relative, sizeField, pin.bytes(), "sha256", pin.sha256());
    }
    private static FilePin pin(Path path) throws IOException {
        byte[] bytes = Files.readAllBytes(path);
        return new FilePin(path.toAbsolutePath().normalize().toString(), bytes.length, ReleaseBuilder.sha256(bytes));
    }
    private static String execute(ProcessBuilder builder) throws IOException, InterruptedException {
        Process process = builder.start();
        FutureTask<byte[]> output = new FutureTask<>(() -> {
            byte[] bytes = process.getInputStream().readNBytes(65_537);
            if (bytes.length > 65_536) { process.destroyForcibly(); throw new IOException("compatibility consumer exceeded output bound"); }
            return bytes;
        });
        Thread reader = Thread.ofVirtual().start(output);
        try {
            assertTrue(process.waitFor(45, TimeUnit.SECONDS), "bounded compatibility consumer timed out");
            byte[] bytes;
            try { bytes = output.get(5, TimeUnit.SECONDS); }
            catch (ExecutionException | TimeoutException error) { throw new IOException("compatibility consumer output failed", error); }
            String result = new String(bytes, StandardCharsets.UTF_8);
            assertEquals(0, process.exitValue(), result);
            return result;
        } finally {
            if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); }
            process.getInputStream().close(); reader.interrupt(); reader.join(5_000);
            assertFalse(process.isAlive()); assertFalse(reader.isAlive());
        }
    }
}
