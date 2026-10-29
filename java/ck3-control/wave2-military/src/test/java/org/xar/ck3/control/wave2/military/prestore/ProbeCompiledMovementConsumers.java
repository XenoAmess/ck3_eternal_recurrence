package org.xar.ck3.control.wave2.military.prestore;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPOutputStream;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryGoldenCapture;
import org.xar.ck3.control.wave2.military.disembark.CaptureDisembarkGolden;
import org.xar.ck3.control.wave2.military.disembark.DisembarkCodec;

/** Explicit compiled producer to original-consumer probe, following ProbeCompiledCounterConsumers. */
public final class ProbeCompiledMovementConsumers {
    private static final ObjectMapper JSON = new ObjectMapper();
    public record FilePin(Path path, long bytes, String sha256) {
        public FilePin {
            path = path.toAbsolutePath().normalize();
            StrictJson.require(bytes >= 0 && bytes <= 16_777_216 && sha256.matches("[0-9a-f]{64}"), "finite exact file pin required");
            String name = path.getFileName().toString().toLowerCase(java.util.Locale.ROOT);
            StrictJson.require(!name.equals("driver.json") && !name.endsWith(".ck3"), "real Driver/SAVE input prohibited");
        }
        public void verify() throws IOException {
            StrictJson.require(Files.isRegularFile(path) && Files.size(path) == bytes, "pinned path/length changed: " + path);
            StrictJson.require(MovementConsumerTransport.sha256(Files.readAllBytes(path)).equals(sha256), "pinned SHA changed: " + path);
        }
    }
    public record Inputs(Path repository, Path python, String machineId, Instant reviewAt,
                         FilePin mainJar, List<FilePin> runtimeJars, Path testClasses, List<FilePin> testClassFiles,
                         List<FilePin> sources, List<FilePin> nativeInputs, FilePin countyGolden,
                         FilePin prestoreGolden, FilePin disembarkGolden, FilePin wholeConsumer,
                         FilePin nativeWire, Path outputRoot) {
        public Inputs {
            runtimeJars = List.copyOf(runtimeJars); testClassFiles = List.copyOf(testClassFiles);
            sources = List.copyOf(sources); nativeInputs = List.copyOf(nativeInputs);
            StrictJson.require(!machineId.isBlank() && !sources.isEmpty() && !testClassFiles.isEmpty()
                    && nativeInputs.size() == 8 && runtimeJars.size() >= 3, "complete compiled/source/native fixture closure required");
        }
        public List<FilePin> pins() {
            List<FilePin> pins = new ArrayList<>(sources); pins.addAll(runtimeJars); pins.addAll(testClassFiles);
            pins.addAll(nativeInputs); pins.add(mainJar); pins.add(countyGolden); pins.add(prestoreGolden);
            pins.add(disembarkGolden); pins.add(wholeConsumer); pins.add(nativeWire); return List.copyOf(pins);
        }
    }
    private ProbeCompiledMovementConsumers() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) throw new IllegalArgumentException("one sealed compiled-input manifest required");
        Path manifest = Path.of(arguments[0]).toAbsolutePath().normalize();
        byte[] manifestBytes = Files.readAllBytes(manifest);
        Inputs inputs = decode(manifestBytes);
        String manifestSha = MovementConsumerTransport.sha256(manifestBytes);
        verify(inputs); verifyOrigins(inputs);
        Path output = inputs.outputRoot().toAbsolutePath().normalize();
        Path scratch = Path.of(System.getProperty("java.io.tmpdir")).toRealPath();
        if (!output.startsWith(scratch) || output.equals(scratch) || Files.exists(output)) {
            throw new IllegalArgumentException("fresh D-only probe output root required");
        }
        Files.createDirectory(output);
        Path receipt = output.resolve("CONSUMER-RECEIPT.json"), transcript = output.resolve("actual-java-returns.jsonl.gz");
        ObjectNode record = JSON.createObjectNode();
        record.put("schema", "xar.compiled-movement-consumer-probe/v1");
        record.put("machine_id", inputs.machineId()); record.put("observed_at_utc", Instant.now().toString());
        record.put("input_manifest_sha256", manifestSha); record.put("status", "RED");
        record.put("qualified_main_jar", inputs.mainJar().path().toString());
        record.put("qualified_main_jar_sha256", inputs.mainJar().sha256());
        record.put("qualified_test_classes", inputs.testClasses().toString());
        record.put("original_county_golden_sha256", inputs.countyGolden().sha256());
        record.put("original_prestore_golden_sha256", inputs.prestoreGolden().sha256());
        record.put("original_disembark_golden_sha256", inputs.disembarkGolden().sha256());
        record.put("production_deployment", false); record.put("game_used", false); record.put("sdk_body_read", false);
        Throwable failure = null;
        try {
            ObjectNode init = JSON.createObjectNode(); init.put("machine_id", inputs.machineId());
            init.put("county_program", existingProgram(CountyEntryGoldenCapture.class));
            init.put("prestore_program", CapturePrestoreGolden.originalProgram());
            init.put("disembark_program", existingProgram(CaptureDisembarkGolden.class));
            init.put("county_golden", inputs.countyGolden().path().toString());
            init.put("prestore_golden", inputs.prestoreGolden().path().toString());
            init.put("disembark_golden", inputs.disembarkGolden().path().toString());
            byte[] completion;
            int[] sequence = {1};
            try (var bounded = new BoundedOutput(Files.newOutputStream(transcript, StandardOpenOption.CREATE_NEW), 16_384);
                    var gzip = new GZIPOutputStream(bounded)) {
                completion = CapturePrestoreGolden.runCompiledConsumer(inputs.repository(), inputs.python().toString(),
                        output.resolve("fixture"), inputs.wholeConsumer().path(), inputs.nativeWire().path(),
                        JSON.writeValueAsBytes(init), request -> {
                            try {
                                var typed = MovementConsumerTransport.decode(request, sequence[0]++);
                                byte[] actual = MovementConsumerTransport.encode(MovementConsumerTransport.evaluate(typed));
                                ObjectNode row = JSON.createObjectNode();
                                row.put("original_request_json", new String(request, StandardCharsets.UTF_8));
                                row.put("actual_java_return_json", new String(actual, StandardCharsets.UTF_8));
                                gzip.write(JSON.writeValueAsBytes(row)); gzip.write('\n');
                                return actual;
                            } catch (IOException error) { throw new java.io.UncheckedIOException(error); }
                        });
                gzip.write(completion); gzip.write('\n');
            }
            JsonNode summary = StrictJson.parse(completion, 16_384);
            StrictJson.trueValue(summary.get("completed"));
            requireInteger(summary, "original_parent_tests", 18); requireInteger(summary, "original_subtests", 43);
            requireInteger(summary, "original_skipped", 0); requireInteger(summary, "original_whole_consumer_tests", 1);
            requireInteger(summary, "registered_whole_passes", 14);
            StrictJson.require(inputs.machineId().equals(StrictJson.text(summary.get("machine_id"))), "consumer machine binding drift");
            for (var operation : MovementConsumerTransport.Operation.values()) {
                StrictJson.integer(summary.path("java_calls").get(operation.name()), 1, 4_096);
            }
            StrictJson.integer(summary.get("negative_token_calls"), 1, 4_096);
            verify(inputs); verifyOrigins(inputs);
            StrictJson.require(MovementConsumerTransport.sha256(Files.readAllBytes(manifest)).equals(manifestSha), "sealed manifest drift");
            ObjectNode compactSummary = ((ObjectNode) summary).deepCopy();
            JsonNode compactOutputs = compactSummary.remove("compact_original_outputs");
            compactSummary.put("original_output_records_in_return_transcript", true);
            compactSummary.put("original_output_record_count", compactOutputs.size());
            compactSummary.put("original_output_records_sha256", MovementConsumerTransport.sha256(JSON.writeValueAsBytes(compactOutputs)));
            record.set("actual_original_consumer", compactSummary); record.put("status", "PASS");
            record.put("source_input_artifact_postcheck", "MATCH");
        } catch (Throwable error) {
            failure = error; record.put("error", error.getClass().getName() + ": " + String.valueOf(error.getMessage()));
        } finally {
            if (Files.isRegularFile(transcript)) {
                record.put("actual_java_returns_gzip_bytes", Files.size(transcript));
                record.put("actual_java_returns_gzip_sha256", MovementConsumerTransport.sha256(Files.readAllBytes(transcript)));
            }
            byte[] bytes = JSON.writeValueAsBytes(record);
            if (bytes.length > 4_096) throw new IOException("consumer receipt exceeds 4 KiB");
            Files.write(receipt, bytes, StandardOpenOption.CREATE_NEW);
        }
        if (failure != null) throw new IllegalStateException("compiled original consumer probe failed; retained RED receipt", failure);
    }

    private static void requireInteger(JsonNode node, String field, long expected) {
        StrictJson.integer(node.get(field), expected, expected);
    }
    /** Narrow test-fixture boundary; class origin and exact compiled class bytes are independently pinned. */
    private static String existingProgram(Class<?> originalCapture) throws ReflectiveOperationException {
        var field = originalCapture.getDeclaredField("PROGRAM");
        if (!field.trySetAccessible()) throw new IllegalStateException("existing compiled capture recipe inaccessible");
        Object value = field.get(null);
        if (!(value instanceof String text)) throw new IllegalStateException("existing compiled capture recipe type changed");
        return text;
    }
    private static void verify(Inputs inputs) throws IOException {
        StrictJson.require(Instant.now().isBefore(inputs.reviewAt()), "finite compiled-consumer review expired");
        Set<Path> nativeExpected = new HashSet<>();
        for (String scene : List.of("disembark_rule_positive", "disembark_rule_zero", "disembark_rule_negative",
                "disembark_rule_unavailable", "disembark_target_medium_zero", "disembark_unit_kind_bypass", "disembark_arrival_not_selected")) {
            nativeExpected.add(inputs.nativeWire().path().getParent().resolve(scene + ".native-context.json"));
        }
        nativeExpected.add(inputs.nativeWire().path().getParent().resolve("PRODUCER-RECEIPT.json"));
        Set<Path> nativeActual = new HashSet<>(); inputs.nativeInputs().forEach(pin -> nativeActual.add(pin.path()));
        StrictJson.require(nativeActual.equals(nativeExpected), "whole fixture sidecars/producer receipt are not the exact read closure");
        for (FilePin pin : inputs.pins()) pin.verify();
        verifyGoldenLineage(inputs, inputs.countyGolden(), "source_pins", false);
        verifyGoldenLineage(inputs, inputs.prestoreGolden(), "source_refs", true);
        verifyGoldenLineage(inputs, inputs.disembarkGolden(), "source_refs", false);
    }
    private static void verifyGoldenLineage(Inputs inputs, FilePin golden, String field, boolean compressed) throws IOException {
        byte[] raw = Files.readAllBytes(golden.path());
        if (compressed) {
            try (var stream = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(raw))) { raw = stream.readNBytes(262_145); }
        }
        JsonNode node = StrictJson.parse(raw, 262_144).get(field);
        StrictJson.require(node != null && node.isArray() && !node.isEmpty(), "golden original source lineage missing");
        java.util.Map<Path, FilePin> sources = new java.util.HashMap<>();
        inputs.sources().forEach(pin -> sources.put(pin.path(), pin));
        for (JsonNode binding : node) {
            Path path = inputs.repository().resolve(StrictJson.text(binding.get("path"))).toAbsolutePath().normalize();
            FilePin pinned = sources.get(path);
            StrictJson.require(pinned != null && pinned.sha256().equals(StrictJson.text(binding.get("sha256"))), "original golden source does not match sealed current source: " + path);
            if (binding.has("bytes")) StrictJson.integer(binding.get("bytes"), pinned.bytes(), pinned.bytes());
        }
    }
    private static Path origin(Class<?> type) throws URISyntaxException {
        return Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
    }
    private static void verifyOrigins(Inputs inputs) throws URISyntaxException {
        for (Class<?> type : List.of(PrestoreCodec.class, CurrentMovementCodec.class, CountyEntryCodec.class, DisembarkCodec.class)) {
            StrictJson.require(origin(type).equals(inputs.mainJar().path()), "actual main class origin differs: " + type.getName());
        }
        for (Class<?> type : List.of(ProbeCompiledMovementConsumers.class, MovementConsumerTransport.class,
                CapturePrestoreGolden.class, CountyEntryGoldenCapture.class, CaptureDisembarkGolden.class)) {
            StrictJson.require(origin(type).equals(inputs.testClasses()), "actual compiled test origin differs: " + type.getName());
        }
        Set<Path> runtime = new HashSet<>(); inputs.runtimeJars().forEach(pin -> runtime.add(pin.path()));
        for (Class<?> type : List.of(StrictJson.class, JsonNode.class, JsonFactory.class)) {
            StrictJson.require(runtime.contains(origin(type)), "actual dependency class origin is not pinned: " + type.getName());
        }
        Set<Path> expected = new HashSet<>(); inputs.testClassFiles().forEach(pin -> expected.add(pin.path()));
        Set<Path> actual = new HashSet<>();
        try (var files = Files.walk(inputs.testClasses())) {
            files.filter(Files::isRegularFile).filter(path -> {
                String name = path.getFileName().toString();
                return name.endsWith(".class") && (name.startsWith("ProbeCompiledMovementConsumers")
                        || name.startsWith("MovementConsumerTransport") || name.startsWith("CapturePrestoreGolden")
                        || name.startsWith("CountyEntryGoldenCapture") || name.startsWith("CaptureDisembarkGolden"));
            }).forEach(path -> actual.add(path.toAbsolutePath().normalize()));
        } catch (IOException error) { throw new IllegalStateException("compiled test closure unreadable", error); }
        StrictJson.require(!actual.isEmpty() && actual.equals(expected), "actual compiled test class closure differs from pins");
    }

    public static Inputs decode(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw, 65_536), Set.of("schema", "status", "repository", "python",
                "machine_id", "review_at_utc", "main_jar", "runtime_jars", "test_classes", "test_class_files",
                "source_refs", "native_inputs", "county_golden", "prestore_golden", "disembark_golden",
                "whole_consumer", "native_wire", "output_root"));
        StrictJson.require(StrictJson.text(node.get("schema")).equals("xar.compiled-movement-consumer-inputs/v1")
                && StrictJson.text(node.get("status")).equals("QUALIFIED_COMPILED_INPUTS"), "uncompiled/unpinned inputs cannot execute");
        return new Inputs(path(node, "repository"), path(node, "python"), StrictJson.text(node.get("machine_id")),
                Instant.parse(StrictJson.utc(StrictJson.text(node.get("review_at_utc")))), pin(node.get("main_jar")),
                pins(node.get("runtime_jars")), path(node, "test_classes"), pins(node.get("test_class_files")),
                pins(node.get("source_refs")), pins(node.get("native_inputs")), pin(node.get("county_golden")),
                pin(node.get("prestore_golden")), pin(node.get("disembark_golden")), pin(node.get("whole_consumer")),
                pin(node.get("native_wire")), path(node, "output_root"));
    }
    private static Path path(JsonNode node, String field) {
        Path value = Path.of(StrictJson.text(node.get(field)));
        StrictJson.require(value.isAbsolute(), "absolute input/output path required"); return value.normalize();
    }
    private static FilePin pin(JsonNode node) {
        StrictJson.object(node, Set.of("path", "bytes", "sha256"));
        return new FilePin(path(node, "path"), StrictJson.integer(node.get("bytes"), 0, 16_777_216), StrictJson.text(node.get("sha256")));
    }
    private static List<FilePin> pins(JsonNode node) {
        StrictJson.require(node != null && node.isArray() && node.size() <= 128, "finite source/artifact refs required");
        List<FilePin> result = new ArrayList<>(); node.forEach(value -> result.add(pin(value))); return List.copyOf(result);
    }
    private static final class BoundedOutput extends FilterOutputStream {
        private final long maximum; private long written;
        private BoundedOutput(OutputStream output, long maximum) { super(output); this.maximum = maximum; }
        @Override public void write(int value) throws IOException {
            if (++written > maximum) throw new IOException("compressed return transcript exceeds 16 KiB"); out.write(value);
        }
        @Override public void write(byte[] value, int offset, int length) throws IOException {
            if (written + length > maximum) throw new IOException("compressed return transcript exceeds 16 KiB");
            out.write(value, offset, length); written += length;
        }
    }
}
