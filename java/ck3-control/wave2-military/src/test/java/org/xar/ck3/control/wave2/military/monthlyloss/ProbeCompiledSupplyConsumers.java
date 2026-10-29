package org.xar.ck3.control.wave2.military.monthlyloss;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyProjection;
import org.xar.ck3.control.wave2.military.losssequence.LossSequencePolicy;
import org.xar.ck3.control.wave2.military.supplyschedule.NativeNextDailySupplySchedule;
import org.xar.ck3.control.wave2.military.zerostockclock.ZeroStockProjection;

/** One qualified Java JVM invokes the unchanged original consumers, never a Game or SDK. */
public final class ProbeCompiledSupplyConsumers {
    private static final int LOG_MAX = 8192;
    private static final int PACKET_MAX = 262_144;
    private static final Set<String> LEAVES = Set.of("monthlyloss", "losssequence", "fleetsupply", "supplyschedule", "zerostockclock");
    private static final Set<String> GZIP16_LEAVES = Set.of("monthlyloss", "fleetsupply", "zerostockclock");
    private record Pin(Path path, long bytes, String sha256) { }
    private record Trace(int calls, JsonNode report) { }
    private record Diagnostic(byte[] prefix, boolean exceeded) { }
    private ProbeCompiledSupplyConsumers() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 13) throw new IllegalArgumentException("repository Python manifest manifestSHA newOutput newFixture mainJar mainSHA testClasses probeClassSHA oracleClassSHA machineId approvedOutputRoot required");
        Path repository = repository(args[0]);
        Path manifest = path(args[2]); Path output = path(args[4]); Path fixture = path(args[5]);
        Path mainJar = path(args[6]); Path testClasses = path(args[8]);
        Path allocated = path(args[12]).toRealPath();
        if (!output.getParent().equals(allocated) || !fixture.getParent().equals(allocated)
                || Files.exists(output) || Files.exists(fixture)) throw new IllegalArgumentException("fresh allocated D outputs required");
        for (Class<?> type : List.of(SupplyConsumerBindings.class, MonthlyLossPolicy.class, LossSequencePolicy.class,
                FleetSupplyProjection.class, NativeNextDailySupplySchedule.class, ZeroStockProjection.class)) {
            if (!origin(type).equals(mainJar)) throw new IllegalStateException("unqualified main class origin: " + type.getName());
        }
        if (!origin(ProbeCompiledSupplyConsumers.class).equals(testClasses) || !origin(SupplyConsumerOracle.class).equals(testClasses)) {
            throw new IllegalStateException("unqualified test class origin");
        }
        Pin jarPin = pin(mainJar, 32 * 1024 * 1024); check(jarPin, args[7]);
        Pin manifestPin = pin(manifest, 16 * 1024); check(manifestPin, args[3]);
        Path probeClass = testClasses.resolve("org/xar/ck3/control/wave2/military/monthlyloss/ProbeCompiledSupplyConsumers.class");
        Pin probePin = pin(probeClass, 128 * 1024); check(probePin, args[9]);
        Pin oraclePin = pin(testClasses.resolve("org/xar/ck3/control/wave2/military/monthlyloss/SupplyConsumerOracle.class"), 128 * 1024);
        check(oraclePin, args[10]);
        Map<Path, Pin> sources = new LinkedHashMap<>(); Map<Path, Pin> goldens = new LinkedHashMap<>();
        ObjectNode qualification = StrictJson.object(StrictJson.parse(Files.readAllBytes(manifest), 16 * 1024), Set.of("schema", "goldens"));
        StrictJson.require("xar.supply-five-qualified-goldens/v1".equals(StrictJson.text(qualification.get("schema"))), "golden manifest schema differs");
        JsonNode rows = qualification.get("goldens"); StrictJson.require(rows.isArray() && rows.size() == 5, "all five qualified goldens required");
        java.util.HashSet<String> leaves = new java.util.HashSet<>();
        for (JsonNode row : rows) {
            ObjectNode value = StrictJson.object(row, Set.of("leaf", "path", "bytes", "sha256"));
            String leaf = StrictJson.text(value.get("leaf"));
            StrictJson.require(LEAVES.contains(leaf) && leaves.add(leaf), "missing/duplicate/unknown leaf");
            int gzipMaximum = leaf.equals("losssequence") ? 24 * 1024 : GZIP16_LEAVES.contains(leaf) ? 16 * 1024 : 0;
            int rawMaximum = leaf.equals("losssequence") ? 160 * 1024 : 128 * 1024;
            Path file = path(StrictJson.text(value.get("path"))); Pin actual = pin(file, gzipMaximum == 0 ? rawMaximum : gzipMaximum);
            StrictJson.require(actual.bytes() == StrictJson.integer(value.get("bytes"), 1, 128 * 1024), "golden byte count differs");
            check(actual, StrictJson.text(value.get("sha256"))); goldens.put(file, actual);
            JsonNode golden = StrictJson.parse(readGolden(Files.readAllBytes(file), gzipMaximum, rawMaximum), rawMaximum);
            StrictJson.require(golden.isObject(), "golden must be object");
            if (leaf.equals("monthlyloss") || leaf.equals("losssequence")) {
                StrictJson.require(golden.path("original_tests_executed").isBoolean() && golden.path("original_tests_executed").booleanValue()
                        && StrictJson.integer(golden.get("original_tests"), 1, 10_000) > 0
                        && StrictJson.integer(golden.get("original_skipped"), 0, 0) == 0, "fresh complete original suites required");
            }
            retainSources(repository, golden, sources);
        }
        // Full consumer test sources are guarded even when absent from an older producer fixture's inventory.
        for (String test : List.of("test_conditional_monthly_loss_budgets.py", "test_conditional_loss_sequence_replay.py",
                "test_army_chunk_loss_writeback_projection.py", "test_army_loss_allocation_projection.py", "test_post_refill_land_rate_service_join.py",
                "test_selected_refill_monthly_assembly_service.py", "test_selected_refill_monthly_fleet_service.py",
                "test_current_callback_soldier_effects_service_12004.py", "test_army_zero_stock_clock_12004.py",
                "test_r05_first_zero_budget_capture.py", "test_r05_zero_preparation_decision.py")) {
            Path file = repository.resolve("ck3_autonomous_player/tests/unit/" + test); sources.putIfAbsent(file, pin(file, 256 * 1024));
        }
        recheck(sources); Files.createDirectories(fixture);
        ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-c", SupplyConsumerOracle.program(), repository.toString());
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        builder.environment().put("TEMP", fixture.toString()); builder.environment().put("TMP", fixture.toString());
        builder.environment().put("TMPDIR", fixture.toString()); builder.environment().put("XAR_REPO_ROOT", repository.toString());
        Process child = builder.start(); Diagnostic diagnostic; Trace trace = null; Exception transportFailure = null;
        try (var workers = Executors.newFixedThreadPool(2)) {
            var transport = workers.submit(() -> exchange(child));
            var errors = workers.submit(() -> diagnostic(child.getErrorStream()));
            try {
                if (!child.waitFor(120, TimeUnit.SECONDS)) throw new IOException("original consumer probe timed out");
                trace = transport.get(5, TimeUnit.SECONDS);
            } catch (IOException | InterruptedException | ExecutionException | TimeoutException failure) {
                transportFailure = failure;
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                child.waitFor(5, TimeUnit.SECONDS);
            }
            diagnostic = errors.get(5, TimeUnit.SECONDS);
        }
        Path diagnostics = output.resolveSibling(output.getFileName() + ".stderr.log");
        Files.write(diagnostics, diagnostic.prefix(), StandardOpenOption.CREATE_NEW);
        if (diagnostic.exceeded()) throw new IOException("original consumer diagnostics exceeded 8192 bytes; prefix retained");
        if (transportFailure != null) throw new IOException("actual original consumer transport failed; bounded diagnostics retained", transportFailure);
        if (child.exitValue() != 0) throw new IOException("original consumer suite exit " + child.exitValue() + "; bounded diagnostics retained");
        if (trace == null) throw new IOException("actual consumer trace missing");
        recheck(sources); recheck(goldens); verify(jarPin); verify(manifestPin); verify(probePin); verify(oraclePin);
        JsonNode loaded = trace.report().get("loaded_source_sha256");
        JsonNode beforeLoaded = trace.report().get("loaded_source_before_sha256");
        StrictJson.require(loaded != null && loaded.isObject(), "actual loaded source identities required");
        StrictJson.require(beforeLoaded != null && beforeLoaded.isObject(), "pre-execution loaded source identities required");
        var beforeNames = beforeLoaded.fieldNames();
        while (beforeNames.hasNext()) {
            String name = beforeNames.next(); StrictJson.require(beforeLoaded.get(name).equals(loaded.get(name)), "loaded original source drifted");
        }
        var names = loaded.fieldNames();
        while (names.hasNext()) {
            String name = names.next(); Path file = childPath(repository, name);
            check(pin(file, 2 * 1024 * 1024), StrictJson.text(loaded.get(name)));
            // Pre/post guards above bind every retained producer and declared consumer; loaded imports are separately inventoried.
        }
        ObjectNode result = StrictJson.object(); result.put("schema", "xar.compiled-supply-consumer-probe/v1");
        result.put("machine_id", args[11]); result.put("observed_at_utc", Instant.now().toString());
        result.put("status", "PASS"); result.put("main_jar_sha256", jarPin.sha256()); result.put("probe_class_sha256", probePin.sha256());
        result.put("oracle_class_sha256", oraclePin.sha256()); result.put("approved_output_root", allocated.toString());
        result.put("golden_manifest_sha256", manifestPin.sha256()); result.put("actual_java_calls", trace.calls());
        result.put("source_unchanged", true); result.put("goldens_unchanged", true); result.set("actual_original_consumers", trace.report());
        result.put("scope", "offline Java bytes to original Service/assembly/sequence/dispatch only; native/SDK/Game/writer NOTRUN");
        Files.write(output, StrictJson.canonical(result, 64 * 1024), StandardOpenOption.CREATE_NEW);
    }

    private static Trace exchange(Process child) throws IOException {
        int calls = 0; JsonNode report = null;
        try (InputStream input = child.getInputStream(); OutputStream reply = child.getOutputStream()) {
            byte[] line;
            while ((line = line(input, PACKET_MAX)) != null) {
                JsonNode packet = StrictJson.parse(line, PACKET_MAX);
                String schema = StrictJson.text(packet.get("schema"));
                if (schema.equals("xar.supply-probe-complete/v1")) {
                    if (report != null) throw new IOException("duplicate terminal consumer report");
                    StrictJson.object(packet, Set.of("schema", "original_tests", "java_consumer_tests", "skipped", "consumer_calls",
                            "loaded_source_before_sha256", "loaded_source_sha256", "scope"));
                    long count = StrictJson.integer(packet.get("original_tests"), 1, 10_000);
                    StrictJson.integer(packet.get("java_consumer_tests"), count, count); StrictJson.integer(packet.get("skipped"), 0, 0);
                    Set<String> operations = new java.util.HashSet<>();
                    for (var operation : SupplyConsumerBindings.Operation.values()) operations.add(operation.name());
                    ObjectNode performed = StrictJson.object(packet.get("consumer_calls"), operations);
                    for (String operation : operations) StrictJson.integer(performed.get(operation), 1, 100_000);
                    report = packet; continue;
                }
                if (report != null) throw new IOException("consumer call after terminal report");
                ObjectNode call = StrictJson.object(packet, Set.of("schema", "sequence", "request_json"));
                if (!schema.equals("xar.supply-probe-call/v1")) throw new IOException("unknown child packet");
                long sequence = StrictJson.integer(call.get("sequence"), calls + 1L, calls + 1L); calls++;
                ObjectNode response = StrictJson.object(); response.put("sequence", sequence);
                byte[] originalTokens = StrictJson.text(call.get("request_json")).getBytes(StandardCharsets.UTF_8);
                try {
                    byte[] actual = SupplyConsumerBindings.exchange(originalTokens);
                    response.put("status", "complete"); response.put("result_json", new String(actual, StandardCharsets.UTF_8));
                } catch (IllegalArgumentException rejected) {
                    String reason = rejected.getMessage(); if (reason == null) reason = "contract rejected";
                    response.put("status", "rejected"); response.put("error", reason.substring(0, Math.min(reason.length(), 512)));
                }
                reply.write(StrictJson.canonical(response, PACKET_MAX)); reply.write('\n'); reply.flush();
            }
        }
        if (report == null || calls == 0) throw new IOException("consumer execution did not reach terminal report");
        return new Trace(calls, report);
    }
    static byte[] readGolden(byte[] bytes, boolean gzip) throws IOException {
        return readGolden(bytes, gzip ? 24 * 1024 : 0, gzip ? 160 * 1024 : 128 * 1024);
    }
    static byte[] readGolden(byte[] bytes, int gzipMaximum, int rawMaximum) throws IOException {
        byte[] raw;
        if (gzipMaximum > 0) {
            if (bytes.length == 0 || bytes.length > gzipMaximum) throw new IOException("compressed golden outside bound");
            try (GZIPInputStream input = new GZIPInputStream(new ByteArrayInputStream(bytes))) { raw = bounded(input, rawMaximum); }
        } else {
            if (bytes.length == 0 || bytes.length > rawMaximum) throw new IOException("golden outside bound"); raw = bytes.clone();
        }
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(raw));
        return raw;
    }
    private static byte[] line(InputStream input, int maximum) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream(); int value;
        while ((value = input.read()) != -1) {
            if (value == '\n') return out.toByteArray();
            if (out.size() == maximum) throw new IOException("JSONL call exceeds bound"); out.write(value);
        }
        if (out.size() != 0) throw new IOException("unterminated JSONL call"); return null;
    }
    private static byte[] bounded(InputStream input, int maximum) throws IOException {
        byte[] bytes = input.readNBytes(maximum + 1); if (bytes.length > maximum) throw new IOException("bounded stream exceeded " + maximum); return bytes;
    }
    private static Diagnostic diagnostic(InputStream input) throws IOException {
        ByteArrayOutputStream prefix = new ByteArrayOutputStream(); byte[] buffer = new byte[4096]; boolean exceeded = false; int count;
        while ((count = input.read(buffer)) != -1) {
            int retained = Math.min(count, LOG_MAX - prefix.size()); prefix.write(buffer, 0, retained);
            if (retained != count) exceeded = true;
        }
        return new Diagnostic(prefix.toByteArray(), exceeded);
    }
    private static void retainSources(Path root, JsonNode golden, Map<Path, Pin> sources) throws Exception {
        for (String array : List.of("source_refs", "source_pins")) {
            JsonNode values = golden.get(array); if (values == null) continue;
            StrictJson.require(values.isArray(), "source refs must be ordered array");
            for (JsonNode value : values) retain(root, StrictJson.text(value.get("path")), StrictJson.text(value.get("sha256")), value.get("bytes"), sources);
        }
        JsonNode hashes = golden.get("source_sha256");
        if (hashes != null) {
            StrictJson.require(hashes.isObject(), "source hash inventory must be object"); var fields = hashes.fieldNames();
            while (fields.hasNext()) { String name = fields.next(); retain(root, name, StrictJson.text(hashes.get(name)), null, sources); }
        }
    }
    private static void retain(Path root, String name, String sha, JsonNode size, Map<Path, Pin> sources) throws Exception {
        Path file = childPath(root, name); Pin actual = pin(file, 2 * 1024 * 1024); check(actual, sha);
        if (size != null) StrictJson.require(actual.bytes() == StrictJson.integer(size, 0, 2 * 1024 * 1024), "retained source length differs");
        Pin previous = sources.putIfAbsent(file, actual); if (previous != null && !previous.equals(actual)) throw new IOException("mixed source inventories");
    }
    private static Path childPath(Path root, String name) {
        Path file = root.resolve(name).toAbsolutePath().normalize(); StrictJson.require(file.startsWith(root), "source reference escapes repository"); return file;
    }
    private static Path repository(String value) {
        String configured = value.isBlank() ? System.getProperty("xar.repo", System.getenv("XAR_REPO_ROOT")) : value;
        if (configured == null || configured.isBlank()) throw new IllegalArgumentException("explicit qualified repository required");
        Path root = path(configured); StrictJson.require(Files.isDirectory(root.resolve("ck3_autonomous_player/src")), "qualified repository source missing"); return root;
    }
    private static Path path(String value) { return Path.of(value).toAbsolutePath().normalize(); }
    private static Path origin(Class<?> type) throws URISyntaxException { return path(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toString()); }
    private static Pin pin(Path path, int maximum) throws IOException, NoSuchAlgorithmException {
        if (!Files.isRegularFile(path) || Files.size(path) > maximum) throw new IOException("qualified input path/size rejected: " + path);
        byte[] bytes = Files.readAllBytes(path);
        return new Pin(path, bytes.length, java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static void check(Pin actual, String expected) { StrictJson.require(actual.sha256().equals(expected), "qualified SHA differs: " + actual.path()); }
    private static void verify(Pin expected) throws Exception {
        Pin actual = pin(expected.path(), 32 * 1024 * 1024); if (!actual.equals(expected)) throw new IOException("input drifted: " + expected.path());
    }
    private static void recheck(Map<Path, Pin> pins) throws Exception { for (Pin pin : pins.values()) verify(pin); }
}
