package org.xar.ck3.control.wave2.military.actualcontact;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyinventory.ArmyInventoryValidation;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowCodec;
import org.xar.ck3.control.wave2.military.routewindowstep.RouteWindowStepCodec;

/** Compiled main bytes -> all unchanged original consumers; never a Job launcher. */
public final class ProbeCompiledContactConsumers {
    private static final int RAW_LIMIT = 1_048_576;
    private static final int VECTOR_GZIP_LIMIT = 24_576;
    private static final int PACKET_GZIP_LIMIT = 32_768;
    private static final int FIXTURE_LIMIT = 114_688;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private ProbeCompiledContactConsumers() { }

    /** root python new-receipt fresh-fixtures main-jar main-SHA test-classes
     * source-pins source-pins-SHA native-FIRST native-FIRST-SHA artifacts artifacts-SHA
     * admitted-machine-profile profile-SHA.
     * The shared owner fills actual artifact refs after compilation; no source-ready
     * manifest may fabricate those hashes or claim that this program has executed.
     */
    public static void main(String[] arguments) throws IOException, InterruptedException, URISyntaxException, NoSuchAlgorithmException {
        if (arguments.length != 15) { throw new IllegalArgumentException("15 qualified compiled-contact consumer arguments required"); }
        Path root = path(arguments[0]); Path output = path(arguments[2]); Path fixtureRoot = path(arguments[3]);
        Path mainJar = path(arguments[4]); Path testClasses = path(arguments[6]); Path pins = path(arguments[7]);
        Path nativeFirst = path(arguments[9]); Path artifacts = path(arguments[11]); Path profilePath = path(arguments[13]);
        requireHash(profilePath, arguments[14], 8192);
        JsonNode profile = JSON.readTree(Files.readAllBytes(profilePath));
        StrictJson.object(profile, Set.of("schema", "machine_id", "observed_at_utc", "review_at_utc", "output_root", "fixture_parent", "retained_cap_bytes"));
        if (!StrictJson.text(profile.get("schema")).equals("xar.contact-consumer-machine-profile/v1")
                || !Instant.now().isBefore(Instant.parse(StrictJson.text(profile.get("review_at_utc"))))
                || StrictJson.integer(profile.get("retained_cap_bytes"), 1, FIXTURE_LIMIT) != FIXTURE_LIMIT) {
            throw new IllegalArgumentException("current admitted machine profile and complete bounded fixture reservation required");
        }
        Path allowedLogs = path(StrictJson.text(profile.get("output_root")));
        Path allowedScratch = path(StrictJson.text(profile.get("fixture_parent")));
        if (!output.startsWith(allowedLogs) || !fixtureRoot.startsWith(allowedScratch)
                || fixtureRoot.equals(allowedScratch) || Files.exists(output) || Files.exists(fixtureRoot)) {
            throw new IllegalArgumentException("fresh admitted machine receipt/fixture paths required");
        }
        requireHash(mainJar, arguments[5], 16_777_216); requireHash(pins, arguments[8], 32_768);
        requireHash(nativeFirst, arguments[10], 65_536); requireHash(artifacts, arguments[12], 32_768);
        for (Class<?> type : List.of(ContactConsumerPort.class, ArmyInventoryValidation.class,
                RouteWindowCodec.class, RouteWindowStepCodec.class, ActualContactCodec.class)) {
            if (!origin(type).equals(mainJar)) { throw new IllegalStateException("producer class loaded from unqualified origin: " + type.getName()); }
        }
        for (Class<?> type : List.of(ProbeCompiledContactConsumers.class, CaptureContactConsumerVectors.class)) {
            if (!origin(type).equals(testClasses)) { throw new IllegalStateException("consumer adapter class origin mismatch"); }
        }
        JsonNode artifactManifest = JSON.readTree(Files.readAllBytes(artifacts));
        if (!artifactManifest.path("schema").asText().equals("xar.contact-consumer-artifacts/v1")) {
            throw new IllegalArgumentException("qualified artifact manifest schema required");
        }
        Set<Path> qualifiedFiles = verifyArtifactRefs(artifactManifest);
        Set<Path> requiredOrigins = new HashSet<>();
        for (Class<?> type : List.of(StrictJson.class, JsonNode.class, JsonFactory.class, ObjectMapper.class,
                com.fasterxml.jackson.annotation.JsonProperty.class)) { requiredOrigins.add(origin(type)); }
        requiredOrigins.add(mainJar);
        requiredOrigins.add(testClasses.resolve(ProbeCompiledContactConsumers.class.getName().replace('.', '/') + ".class"));
        requiredOrigins.add(testClasses.resolve(CaptureContactConsumerVectors.class.getName().replace('.', '/') + ".class"));
        if (!qualifiedFiles.containsAll(requiredOrigins)) { throw new IllegalArgumentException("all loaded serializer/producer/adapter artifacts must have exact qualified file refs"); }
        String mainSha = hash(mainJar, 16_777_216); String pinsSha = hash(pins, 32_768);
        String artifactsSha = hash(artifacts, 32_768); String nativeSha = hash(nativeFirst, 65_536);
        if (!profile.get("machine_id").equals(JSON.readTree(Files.readAllBytes(pins)).get("machine_id"))) {
            throw new IllegalArgumentException("machine profile and source qualification belong to different machines");
        }
        Files.createDirectory(fixtureRoot);
        Path sourceVectors = fixtureRoot.resolve("original-consumer-vectors.json.gz");
        Path packetPath = fixtureRoot.resolve("actual-java-consumer-packet.json.gz");
        Path sourceReport = fixtureRoot.resolve("original-consumer-report.json");
        Path replayReport = fixtureRoot.resolve("java-consumer-report.json");
        CaptureContactConsumerVectors.run(root, arguments[1], "collect", sourceVectors, packetPath,
                sourceReport, fixtureRoot.resolve("collect"), pins, nativeFirst);
        byte[] sourceBytes = boundedRead(sourceVectors, VECTOR_GZIP_LIMIT);
        JsonNode vectors = JSON.readTree(expand(sourceBytes));
        if (!vectors.path("schema").asText().equals("xar.original-contact-consumer-vectors/v1")
                || !vectors.path("cases").isArray() || vectors.path("cases").isEmpty()) {
            throw new IllegalStateException("complete original consumer vectors required");
        }
        ObjectNode packet = JSON.createObjectNode(); packet.put("schema", "xar.compiled-contact-consumer-packet/v1");
        packet.put("main_jar_sha256", mainSha); packet.put("source_pins_sha256", pinsSha);
        packet.put("original_vectors_sha256", sha(sourceBytes));
        var cases = packet.putArray("cases"); Set<String> seen = new HashSet<>(); Set<String> operations = new HashSet<>();
        for (JsonNode vector : vectors.get("cases")) {
            StrictJson.object(vector, Set.of("operation", "input_json", "accepted", "expected", "legacy_error"));
            String operation = StrictJson.text(vector.get("operation"));
            if (!vector.get("input_json").isTextual()) { throw new IllegalArgumentException("original input JSON string required"); }
            String input = vector.get("input_json").textValue();
            if (!seen.add(operation + "|" + input)) { throw new IllegalStateException("duplicate original consumer vector"); }
            operations.add(operation);
            if (!vector.get("accepted").isBoolean()) { throw new IllegalArgumentException("actual acceptance boolean required"); }
            boolean accepted = vector.get("accepted").booleanValue(); String wire = null; String javaError = null;
            try {
                wire = new String(ContactConsumerPort.apply(new ContactConsumerPort.Request(probeOperation(operation),
                        input.getBytes(StandardCharsets.UTF_8))).outputJson(), StandardCharsets.UTF_8);
                if (!accepted || !JSON.readTree(wire).equals(vector.get("expected"))) {
                    throw new IllegalStateException("compiled Java output differs from actual original producer at consumer seam: " + operation);
                }
            } catch (ContractViolationException error) {
                if (accepted) { throw new IllegalStateException("Java rejected a qualified original consumer request: " + operation, error); }
                javaError = error.getMessage();
            }
            ObjectNode row = cases.addObject(); row.put("operation", operation); row.put("input_json", input);
            row.put("accepted", accepted); row.set("legacy_error", vector.get("legacy_error"));
            if (wire == null) { row.putNull("output_json"); } else { row.put("output_json", wire); }
            if (javaError == null) { row.putNull("java_error"); } else { row.put("java_error", javaError); }
        }
        if (!operations.equals(Set.of("inventory", "route_window", "route_step", "actual_scope", "actual_query"))) {
            throw new IllegalStateException("all contact producer routes must actually reach original consumers");
        }
        byte[] packetBytes = compress(JSON.writeValueAsBytes(packet));
        if (packetBytes.length > PACKET_GZIP_LIMIT) { throw new IllegalArgumentException("actual Java consumer packet exceeds admitted cap"); }
        Files.write(packetPath, packetBytes, StandardOpenOption.CREATE_NEW);
        CaptureContactConsumerVectors.run(root, arguments[1], "probe", sourceVectors, packetPath,
                replayReport, fixtureRoot.resolve("probe"), pins, nativeFirst);
        if (!qualifiedFiles.equals(verifyArtifactRefs(artifactManifest))
                || !hash(mainJar, 16_777_216).equals(mainSha) || !hash(pins, 32_768).equals(pinsSha)
                || !hash(nativeFirst, 65_536).equals(nativeSha) || !hash(artifacts, 32_768).equals(artifactsSha)
                || !hash(profilePath, 8192).equals(arguments[14]) || !Instant.now().isBefore(Instant.parse(profile.get("review_at_utc").textValue()))
                || !hash(packetPath, PACKET_GZIP_LIMIT).equals(sha(packetBytes)) || !hash(sourceVectors, VECTOR_GZIP_LIMIT).equals(sha(sourceBytes))) {
            throw new IllegalStateException("qualified artifact/source/golden/native input/actual packet drift");
        }
        long fixtureBytes;
        try (var files = Files.walk(fixtureRoot)) {
            List<Path> paths = files.toList(); if (paths.size() > 128) { throw new IOException("bounded fixture entry count exceeded"); }
            fixtureBytes = 0;
            for (Path file : paths) {
                if (Files.isSymbolicLink(file)) { throw new IOException("unexpected fixture link"); }
                if (Files.isRegularFile(file)) { fixtureBytes += Files.size(file); }
            }
        }
        if (fixtureBytes > FIXTURE_LIMIT) { throw new IOException("contact fixture retained byte cap exceeded"); }
        JsonNode replay = JSON.readTree(boundedRead(replayReport, 8192));
        if (!replay.path("actual_java_outputs_consumed").asBoolean(false) || replay.path("used_java_requests").asInt(0) <= 0) {
            throw new IllegalStateException("original consumers did not consume compiled Java bytes");
        }
        ObjectNode receipt = JSON.createObjectNode(); receipt.put("schema", "xar.compiled-contact-consumer-probe/v1");
        receipt.put("observed_at_utc", Instant.now().toString()); receipt.put("status", "PASS");
        receipt.put("machine_id", JSON.readTree(Files.readAllBytes(pins)).path("machine_id").asText());
        receipt.put("qualified_main_jar", mainJar.toString()); receipt.put("qualified_main_jar_sha256", mainSha);
        receipt.put("qualified_test_classes", testClasses.toString()); receipt.put("source_pins_sha256", pinsSha);
        receipt.put("artifact_manifest_sha256", artifactsSha); receipt.put("native_first_sha256", nativeSha);
        receipt.put("machine_profile_sha256", arguments[14]);
        receipt.put("actual_java_packet_sha256", sha(packetBytes)); receipt.put("original_vectors_sha256", sha(sourceBytes));
        receipt.put("unique_requests", cases.size()); receipt.put("fixture_bytes", fixtureBytes);
        receipt.put("fixture_peak_cap_bytes", FIXTURE_LIMIT); receipt.put("game_rpc_count", 0); receipt.put("live_consumer_switched", false);
        receipt.set("original_tests", replay.get("original_tests")); receipt.set("extra_checks", replay.get("extra_checks"));
        byte[] receiptBytes = JSON.writeValueAsBytes(receipt);
        if (receiptBytes.length > 8192) { throw new IOException("bounded contact receipt exceeded"); }
        Files.write(output, receiptBytes, StandardOpenOption.CREATE_NEW);
        System.out.println("contact compiled consumer probe PASS requests=" + cases.size() + " retained=" + fixtureBytes);
    }

    private static Set<Path> verifyArtifactRefs(JsonNode manifest) throws IOException, NoSuchAlgorithmException {
        if (!manifest.path("files").isArray()) { throw new IllegalArgumentException("artifact refs required"); }
        Set<Path> result = new HashSet<>();
        for (JsonNode reference : manifest.get("files")) {
            StrictJson.object(reference, Set.of("path", "bytes", "sha256")); Path file = path(StrictJson.text(reference.get("path")));
            long bytes = StrictJson.integer(reference.get("bytes"), 1, 16_777_216);
            if (!result.add(file) || Files.size(file) != bytes) { throw new IllegalArgumentException("duplicate or changed qualified artifact ref"); }
            requireHash(file, StrictJson.text(reference.get("sha256")), 16_777_216);
        }
        return Set.copyOf(result);
    }
    /** These packet tags belong only to this test probe, never to the host operation registry. */
    private static ContactConsumerPort.Operation probeOperation(String tag) {
        return switch (tag) {
            case "inventory" -> ContactConsumerPort.Operation.INVENTORY;
            case "route_window" -> ContactConsumerPort.Operation.ROUTE_WINDOW;
            case "route_step" -> ContactConsumerPort.Operation.ROUTE_STEP;
            case "actual_scope" -> ContactConsumerPort.Operation.ACTUAL_SCOPE;
            case "actual_query" -> ContactConsumerPort.Operation.ACTUAL_QUERY;
            default -> throw new IllegalArgumentException("unknown test-probe packet tag");
        };
    }
    private static Path origin(Class<?> type) throws URISyntaxException { return path(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toString()); }
    private static Path path(String value) { return Path.of(value).toAbsolutePath().normalize(); }
    private static byte[] boundedRead(Path path, int maximum) throws IOException {
        if (!Files.isRegularFile(path) || Files.isSymbolicLink(path) || Files.size(path) > maximum) { throw new IOException("bounded regular input required: " + path); }
        return Files.readAllBytes(path);
    }
    private static String hash(Path path, int maximum) throws IOException, NoSuchAlgorithmException { return sha(boundedRead(path, maximum)); }
    private static String sha(byte[] bytes) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
    private static void requireHash(Path path, String expected, int maximum) throws IOException, NoSuchAlgorithmException {
        if (!expected.matches("[0-9a-f]{64}") || !hash(path, maximum).equals(expected)) { throw new IOException("qualified input SHA differs: " + path); }
    }
    private static byte[] expand(byte[] bytes) throws IOException {
        try (var input = new GZIPInputStream(new ByteArrayInputStream(bytes))) {
            byte[] raw = input.readNBytes(RAW_LIMIT + 1); if (raw.length > RAW_LIMIT) { throw new IOException("expanded vector limit"); } return raw;
        }
    }
    private static byte[] compress(byte[] raw) throws IOException {
        if (raw.length > RAW_LIMIT) { throw new IOException("raw packet limit"); }
        var bytes = new ByteArrayOutputStream(); try (var output = new GZIPOutputStream(bytes)) { output.write(raw); } return bytes.toByteArray();
    }
}
