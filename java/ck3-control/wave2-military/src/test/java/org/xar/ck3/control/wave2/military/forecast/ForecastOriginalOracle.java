package org.xar.ck3.control.wave2.military.forecast;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicReference;

/** Test-only original producer bridge. It adds no Python implementation or generated script file. */
public final class ForecastOriginalOracle {
    private ForecastOriginalOracle() { }
    private record SourcePin(String name, String sha256) { }
    private static final List<SourcePin> ORIGINALS = List.of(
            new SourcePin("general_battle_forecast.py", "ff63be2dd75c0b1c8701479d2ee58ee152e8f835bb07e032ac92f3fdc0b430f3"),
            new SourcePin("combat_input.py", "8b78e136f302432bf7fbeb05a631563ae6438b5904687bdfde046d634e7dbfe3"),
            new SourcePin("combat_core.py", "15a9efce451e1830def6a7d93c87d0d00b7bb4e852fd75895780d289108a11b6"),
            new SourcePin("research_envelope.py", "fad22164c2dd8745aad220cad2409677366d2f52b4a8614a5c1bfa952414584f"),
            new SourcePin("battle_v2_constructor_advantage.py", "2e6eb0992b5bc529e5c3ae47b74b9391164e582f1af69a033b8f54f21846493a"));
    private static Path configuredPath(String name, boolean directory) throws IOException {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) throw new IllegalStateException("required original-producer property missing: " + name);
        Path supplied = Path.of(value);
        if (!supplied.isAbsolute()) throw new IllegalStateException("absolute original-producer path required: " + name);
        Path actual = supplied.toRealPath();
        if (directory ? !Files.isDirectory(actual) : !Files.isRegularFile(actual)) throw new IllegalStateException("unavailable original-producer path: " + name);
        return actual;
    }
    public static Path repositoryRoot() throws IOException { return configuredPath("xar.repository.root", true); }
    public static JsonNode fixture(String relativePath) throws IOException {
        Path root = repositoryRoot(), actual = root.resolve(relativePath).normalize().toRealPath();
        if (!actual.startsWith(root) || !Files.isRegularFile(actual)) throw new IllegalStateException("fixture escaped original repository");
        long bytes = Files.size(actual); if (bytes <= 0 || bytes > 8 * 1024 * 1024) throw new IllegalStateException("fixture exceeds bounded combat input size");
        return CombatJson.parse(Files.readAllBytes(actual));
    }
    private static void verifyOriginals(Path root) throws IOException {
        Path simulation = root.resolve("ck3_autonomous_player/src/xar_autoplayer/simulation");
        for (SourcePin pin : ORIGINALS) {
            Path actual = simulation.resolve(pin.name()).toRealPath();
            if (!actual.startsWith(root) || !Files.isRegularFile(actual) || Files.size(actual) > 128 * 1024) throw new IllegalStateException("original source unavailable: " + pin.name());
            if (!sha256(Files.readAllBytes(actual)).equals(pin.sha256())) throw new IllegalStateException("original producer source drift: " + pin.name());
        }
    }
    private static String sha256(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    public static JsonNode call(String pythonSource, JsonNode input) throws IOException, InterruptedException {
        return call(pythonSource, input, 1024 * 1024);
    }
    public static JsonNode call(String pythonSource, JsonNode input, int maximumOutputBytes) throws IOException, InterruptedException {
        if (maximumOutputBytes <= 0 || maximumOutputBytes > 8 * 1024 * 1024) throw new IllegalArgumentException("original call output budget must be positive and at most 8MiB");
        if (pythonSource == null || pythonSource.isBlank() || pythonSource.length() > 64 * 1024) throw new IllegalArgumentException("bounded original call required");
        Path root = repositoryRoot(), python = configuredPath("xar.python", false); verifyOriginals(root);
        String bootstrap = """
                import sys
                from pathlib import Path
                sys.dont_write_bytecode=True
                root=Path(sys.argv[1])
                sys.path.insert(0,str(root))
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
                """;
        var builder = new ProcessBuilder(python.toString(), "-B", "-I", "-c", bootstrap + pythonSource, root.toString()).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        var overflow = new AtomicReference<String>();
        var stdoutTask = new FutureTask<byte[]>(() -> bounded(process, process.getInputStream(), maximumOutputBytes, "stdout", overflow));
        var stderrTask = new FutureTask<byte[]>(() -> bounded(process, process.getErrorStream(), 8192, "stderr", overflow));
        Thread.ofVirtual().start(stdoutTask); Thread.ofVirtual().start(stderrTask);
        try {
            byte[] request = CombatJson.canonical(input); if (request.length > 8 * 1024 * 1024) throw new IllegalArgumentException("original call input exceeds bound");
            try (var stdin = process.getOutputStream()) { stdin.write(request); }
            if (!process.waitFor(45, TimeUnit.SECONDS)) throw new IllegalStateException("original combat producer timed out");
            byte[] stdout = completed(stdoutTask), stderr = completed(stderrTask);
            if (process.exitValue() != 0) throw new IllegalStateException("original combat producer exit=" + process.exitValue() + ": " + new String(stderr, StandardCharsets.UTF_8));
            if (stdout.length > maximumOutputBytes || stderr.length > 8192) throw new IllegalStateException("original combat producer output exceeds bound");
            verifyOriginals(root); return CombatJson.parse(stdout);
        } catch (IOException | IllegalStateException failure) {
            if (overflow.get() != null) throw new IllegalStateException("original combat producer " + overflow.get() + " exceeds explicit output bound", failure);
            throw failure;
        } finally {
            if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); }
        }
    }
    private static byte[] bounded(Process process, InputStream stream, int maximumBytes, String name,
            AtomicReference<String> overflow) throws IOException {
        byte[] bytes = stream.readNBytes(maximumBytes + 1);
        if (bytes.length > maximumBytes) {
            overflow.compareAndSet(null, name);
            process.destroyForcibly();
        }
        return bytes;
    }
    private static byte[] completed(FutureTask<byte[]> task) throws InterruptedException {
        try { return task.get(5, TimeUnit.SECONDS); }
        catch (ExecutionException | TimeoutException error) { throw new IllegalStateException("original combat producer stream unavailable", error); }
    }
}
