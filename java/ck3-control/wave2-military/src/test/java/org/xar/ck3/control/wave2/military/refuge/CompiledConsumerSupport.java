package org.xar.ck3.control.wave2.military.refuge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;

/** Support for the two existing capture entries; deliberately has no independent launcher. */
public final class CompiledConsumerSupport {
    private CompiledConsumerSupport() { }
    private static final int OUTPUT_MAX = 16_384;
    public static void run(String[] arguments, Class<?> producer, Class<?> capture,
            String inputSchema, String outputSchema, Function<byte[], byte[]> transfer, String script) throws Exception {
        if (arguments.length != 10 || !arguments[3].equals("--compiled-consumers")) {
            throw new IllegalArgumentException("repo python fresh-output --compiled-consumers main-jar main-sha golden golden-sha test-classes test-tree-sha required");
        }
        Path repository = path(arguments[0]), output = path(arguments[2]), mainJar = path(arguments[4]);
        Path golden = path(arguments[6]), tests = path(arguments[8]);
        Path outputRoot = path(requiredProperty("xar.consumerProbe.outputRoot"));
        Path scratchRoot = path(requiredProperty("xar.consumerProbe.scratchRoot"));
        if (!output.getParent().equals(outputRoot) || !Files.isDirectory(scratchRoot)
                || !path(requiredProperty("java.io.tmpdir")).equals(scratchRoot)
                || !"1".equals(System.getenv("PYTHONDONTWRITEBYTECODE"))) {
            throw new IllegalArgumentException("explicit output/scratch profile and bytecode-disabled Python required");
        }
        for (String variable : List.of("TEMP", "TMP", "TMPDIR")) {
            String value = System.getenv(variable);
            if (value == null || !path(value).equals(scratchRoot)) {
                throw new IllegalArgumentException("Python/JVM scratch profile differs: " + variable);
            }
        }
        if (Files.exists(output) || !Files.isDirectory(repository) || !Files.isDirectory(output.getParent())) {
            throw new IllegalArgumentException("existing repository and parent plus CREATE_NEW output required");
        }
        Path loadedMain = Path.of(producer.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        Path loadedCapture = Path.of(capture.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        Path loadedSupport = Path.of(CompiledConsumerSupport.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        if (!loadedMain.equals(mainJar) || !loadedCapture.equals(tests) || !loadedSupport.equals(tests)) {
            throw new IllegalStateException("actual compiled producer/capture/support origin differs from qualified artifacts");
        }
        String mainSha = hash(mainJar, 16_777_216), goldenSha = hash(golden, 71_680), testSha = treeHash(tests);
        if (!mainSha.equals(arguments[5]) || !goldenSha.equals(arguments[7]) || !testSha.equals(arguments[9])) {
            throw new IllegalStateException("compiled artifact, complete test tree or original golden SHA differs");
        }
        ObjectNode report = StrictJson.object(); report.put("schema", "xar.compiled-military-consumer-probe.v1");
        report.put("observed_at_utc", Instant.now().toString()); report.put("qualified_main_jar", mainJar.toString());
        report.put("explicit_output_root", outputRoot.toString()); report.put("explicit_scratch_root", scratchRoot.toString());
        report.put("qualified_main_jar_sha256", mainSha); report.put("qualified_test_classes", tests.toString());
        report.put("qualified_test_tree_sha256", testSha); report.put("original_golden_sha256", goldenSha);
        report.put("native_action_authorized", false); report.put("production_route_switched", false);
        MessageDigest trace = digest(); int[] sequence = {0}; ObjectNode[] summary = {null};
        List<String> diagnostics = new ArrayList<>();
        Process child = new ProcessBuilder(List.of(arguments[1], "-c", script, repository.toString(), golden.toString(), goldenSha))
                .directory(repository.toFile()).redirectErrorStream(true).start();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(child.getInputStream(), StandardCharsets.UTF_8));
             BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(child.getOutputStream(), StandardCharsets.UTF_8))) {
            CompletableFuture<Void> pump = CompletableFuture.runAsync(() -> {
                try {
                    String line;
                    while ((line = boundedLine(reader)) != null) {
                        if (!line.startsWith("{")) {
                            if (diagnostics.stream().mapToInt(String::length).sum() + line.length() > 4096) {
                                throw new IllegalArgumentException("bounded capture diagnostics exceeded");
                            }
                            diagnostics.add(line); continue;
                        }
                        JsonNode parsed = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8), 131_072);
                        StrictJson.require(parsed instanceof ObjectNode, "protocol object required");
                        ObjectNode message = (ObjectNode) parsed;
                        String kind = StrictJson.text(message.get("type"));
                        if (kind.equals("done")) {
                            StrictJson.object(message, Set.of("type", "summary"));
                            if (summary[0] != null) { throw new IllegalStateException("duplicate terminal report"); }
                            StrictJson.require(message.get("summary") instanceof ObjectNode, "terminal summary object required");
                            summary[0] = (ObjectNode) message.get("summary"); continue;
                        }
                        if (summary[0] != null || !kind.equals("request")) { throw new IllegalArgumentException("request after terminal or unknown protocol kind"); }
                        StrictJson.object(message, Set.of("type", "sequence", "consumer", "input_json"));
                        int current = (int) StrictJson.integer(message.get("sequence"), 1, 4096);
                        if (current != ++sequence[0]) { throw new IllegalArgumentException("request sequence gap/replay"); }
                        ObjectNode request = StrictJson.object(); request.put("schema", inputSchema);
                        request.put("consumer", StrictJson.text(message.get("consumer")));
                        // Parse the original wire token bytes before constructing any domain record.
                        request.set("input", StrictJson.parse(StrictJson.text(message.get("input_json")).getBytes(StandardCharsets.UTF_8)));
                        byte[] input = StrictJson.canonical(request, 131_072), wire = transfer.apply(input);
                        JsonNode result = StrictJson.parse(wire, 16_384);
                        StrictJson.require(outputSchema.equals(result.path("schema").textValue()), "typed producer response schema differs");
                        StrictJson.require(request.get("consumer").equals(result.get("consumer")), "consumer response binding differs");
                        trace.update((current + "\0" + request.get("consumer").textValue() + "\0" + sha(input) + "\0" + sha(wire) + "\n").getBytes(StandardCharsets.UTF_8));
                        ObjectNode reply = StrictJson.object(); reply.put("sequence", current); reply.put("wire_json", new String(wire, StandardCharsets.UTF_8));
                        writer.write(new String(StrictJson.canonical(reply), StandardCharsets.UTF_8)); writer.newLine(); writer.flush();
                    }
                } catch (IOException error) { throw new IllegalStateException("consumer transport failed", error); }
            });
            try { pump.get(180, TimeUnit.SECONDS); }
            catch (Exception error) { child.destroyForcibly(); throw new IllegalStateException("bounded original-consumer probe failed; outer Job owns descendants", error); }
        }
        if (!child.waitFor(10, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new IllegalStateException("consumer did not exit after terminal protocol"); }
        if (summary[0] == null) { throw new IllegalStateException("original-consumer terminal summary missing"); }
        report.set("consumer_result", summary[0]); report.put("java_exchange_count", sequence[0]);
        report.put("java_exchange_sha256", HexFormat.of().formatHex(trace.digest()));
        report.put("python_exit_code", child.exitValue()); report.put("bounded_diagnostics", String.join("\n", diagnostics));
        boolean unchanged = hash(mainJar, 16_777_216).equals(mainSha) && hash(golden, 71_680).equals(goldenSha) && treeHash(tests).equals(testSha);
        report.put("artifacts_unchanged", unchanged);
        boolean passed = child.exitValue() == 0 && sequence[0] > 0 && unchanged && summary[0].path("status").asText().equals("PASS");
        report.put("status", passed ? "PASS" : "RED");
        Files.write(output, StrictJson.canonical(report, OUTPUT_MAX), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        if (!passed) { throw new IllegalStateException("real original-consumer probe RED; exact bounded report retained"); }
    }
    private static String boundedLine(BufferedReader reader) throws IOException {
        StringBuilder result = new StringBuilder(); int current;
        while ((current = reader.read()) != -1) {
            if (current == '\n') { return result.toString(); }
            if (current != '\r') { result.append((char) current); }
            if (result.length() > 131_072) { throw new IllegalArgumentException("bounded protocol line exceeded"); }
        }
        return result.isEmpty() ? null : result.toString();
    }
    private static Path path(String value) { return Path.of(value).toAbsolutePath().normalize(); }
    private static String requiredProperty(String name) {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) { throw new IllegalArgumentException("explicit profile property missing: " + name); }
        return value;
    }
    private static MessageDigest digest() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    private static String sha(byte[] raw) { return HexFormat.of().formatHex(digest().digest(raw)); }
    private static String hash(Path path, long maximum) throws IOException {
        if (!Files.isRegularFile(path) || Files.size(path) > maximum) { throw new IllegalArgumentException("qualified file type/size rejected"); }
        return sha(Files.readAllBytes(path));
    }
    /** Entire bounded test tree is pinned, including actual default fixtures; paths are POSIX and relative. */
    private static String treeHash(Path root) throws IOException {
        MessageDigest hash = digest(); long total = 0;
        try (var walk = Files.walk(root)) {
            List<Path> paths = walk.filter(Files::isRegularFile)
                    .sorted(Comparator.comparing(path -> root.relativize(path).toString().replace('\\', '/'))).toList();
            if (paths.size() > 2048) { throw new IllegalArgumentException("qualified test tree count exceeded"); }
            for (Path path : paths) {
                if (Files.isSymbolicLink(path) || !path.toRealPath().startsWith(root.toRealPath())) {
                    throw new IllegalArgumentException("qualified test file escapes exact artifact tree");
                }
                total += Files.size(path); if (total > 16_777_216) { throw new IllegalArgumentException("qualified test tree bytes exceeded"); }
                hash.update((root.relativize(path).toString().replace('\\', '/') + "\0" + Files.size(path) + "\0" + hash(path, 16_777_216) + "\n").getBytes(StandardCharsets.UTF_8));
            }
        }
        return HexFormat.of().formatHex(hash.digest());
    }
}
