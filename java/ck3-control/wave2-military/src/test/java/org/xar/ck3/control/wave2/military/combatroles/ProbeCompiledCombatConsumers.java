package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit compiled Java bytes -> original strict/pure/Service/Driver/registered MCP consumers. */
public final class ProbeCompiledCombatConsumers {
    private static final String SCHEMA = "xar.compiled-combat-probe-input/v1";
    private ProbeCompiledCombatConsumers() { }

    public record Qualification(Path taskRoot, Path logsRoot, Path scratchRoot, Path repository, Path python, CombatWholeWire.FileReference mainJar,
            Path testClasses, List<CombatWholeWire.FileReference> testClassFiles,
            CombatWholeWire.FileReference golden, CombatWholeWire.FileReference originalWire,
            CombatWholeWire.FileReference nativeProducerReceipt, Path originalWireReference,
            Path nativeReceiptReference, Path freshOutput) {
        public Qualification {
            testClassFiles = List.copyOf(testClassFiles);
            if (testClassFiles.isEmpty()) throw new IllegalArgumentException("actual qualified compiled test files required");
        }
    }

    public static void main(String[] args) throws IOException, URISyntaxException, InterruptedException {
        if (args.length != 1) throw new IllegalArgumentException("one actual artifact-bound qualification JSON required");
        Qualification q = decode(CombatWholeWire.parseJson(readBounded(Path.of(args[0]), 65536), 65536));
        verifyOrigins(q);
        byte[] mainBytes = CombatWholeWire.readPinned(q.mainJar(), q.taskRoot());
        byte[] goldenCompressed = CombatWholeWire.readPinned(q.golden(), q.taskRoot());
        byte[] originalRaw = CombatWholeWire.readPinned(q.originalWire(), q.taskRoot());
        CombatWholeWire.readPinned(q.nativeProducerReceipt(), q.taskRoot());
        CaptureCombatRolesGolden.verifyNativeProducer(q.nativeProducerReceipt().path(), q.originalWire());
        verifyClassFiles(q);
        CombatWholeWire.Parsed whole = CombatWholeWire.parse(originalRaw);
        JsonNode golden;
        try (var gzip = new GZIPInputStream(new java.io.ByteArrayInputStream(goldenCompressed))) {
            golden = StrictJson.parse(gzip.readNBytes(CombatRolesCodec.MAX_BYTES + 1), CombatRolesCodec.MAX_BYTES);
        }
        if (!"xar.combat-roles-original-producer-golden.v1".equals(golden.path("schema").textValue())
                || !golden.path("actual_live_qualification").isBoolean() || golden.path("actual_live_qualification").booleanValue()
                || !golden.path("cases").isArray() || golden.path("cases").size() != 14) {
            throw new IllegalArgumentException("genuine original producer golden required");
        }
        if (!golden.path("original_wire").path("sha256").textValue().equals(q.originalWire().sha256())) {
            throw new IllegalArgumentException("golden and compiled probe must reference the same native original bytes");
        }
        if (!golden.path("original_service_compound_tests").isIntegralNumber()
                || !golden.path("original_service_compound_tests").bigIntegerValue().equals(java.math.BigInteger.ONE)
                || !golden.path("original_service_compound_skipped").isIntegralNumber()
                || golden.path("original_service_compound_skipped").bigIntegerValue().signum() != 0
                || !q.nativeProducerReceipt().sha256().equals(golden.path("native_producer_receipt").path("sha256").textValue())) {
            throw new IllegalArgumentException("actual original Service compound/native source receipt binding required");
        }
        ObjectNode packet = StrictJson.object();
        packet.put("schema", "xar.compiled-combat-consumer-packet/v1");
        packet.put("qualified_main_jar", q.mainJar().path().toString());
        packet.put("qualified_main_jar_sha256", q.mainJar().sha256());
        packet.put("qualified_test_classes", q.testClasses().toString());
        packet.put("original_golden_sha256", q.golden().sha256());
        packet.put("original_wire_sha256", q.originalWire().sha256());
        ArrayNode cases = packet.putArray("cases");
        ObjectNode snapshot = snapshot(golden.get("source_provenance"));
        for (CombatWholeWire.Scene scene : whole.scenes()) {
            JsonNode reference = scene(golden, scene.name());
            ObjectNode nativeRow = scene.originalWholeRow();
            byte[] originalLeaf = StrictJson.canonical(nativeRow.get(CombatRolesCodec.MEMBER), CombatRolesCodec.MAX_BYTES);
            CombatRoles.Inputs model = CombatRolesCodec.decode(originalLeaf);
            byte[] encoded = CombatRolesCodec.encodeBytes(model);
            same(reference.get("expected_normalized"), StrictJson.parse(encoded, CombatRolesCodec.MAX_BYTES));
            byte[] projection = StrictJson.canonical(CombatRolesCodec.encodeProjection(
                    CombatRolesPolicy.project(model, CombatRolesCodec.provenanceFromSnapshot(snapshot))), CombatRolesCodec.MAX_BYTES);
            same(reference.get("expected_projection"), StrictJson.parse(projection, CombatRolesCodec.MAX_BYTES));
            // This is a derived Java consumer carrier, explicitly not another native observation.
            nativeRow.set(CombatRolesCodec.MEMBER, StrictJson.parse(encoded, CombatRolesCodec.MAX_BYTES));
            ArrayNode selected = StrictJson.object().putArray("rows"); selected.add(nativeRow);
            byte[] family = StrictJson.canonical(CombatRolesCodec.projectSelectedRows(selected, snapshot), CombatRolesCodec.MAX_BYTES);
            same(reference.get("expected_service_family"), StrictJson.parse(family, CombatRolesCodec.MAX_BYTES));
            ObjectNode row = cases.addObject(); row.put("name", scene.name());
            row.put("normalized_input_json", new String(encoded, StandardCharsets.UTF_8));
            row.put("projection_json", new String(projection, StandardCharsets.UTF_8));
            row.put("service_family_json", new String(family, StandardCharsets.UTF_8));
        }
        ArrayNode negatives = packet.putArray("raw_token_rejections");
        String good = cases.get(0).path("normalized_input_json").textValue();
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "null")) {
            String altered = good.replace("\"schema_version\":1", "\"schema_version\":" + token);
            if (altered.equals(good)) throw new IllegalStateException("raw rejection vector did not modify a token");
            try {
                CombatRolesCodec.decode(altered.getBytes(StandardCharsets.UTF_8));
                throw new IllegalStateException("compiled strict domain accepted raw substitute " + token);
            } catch (org.xar.ck3.control.contracts.ContractViolationException expected) {
                negatives.addObject().put("raw_request_json", altered).put("expected_error", "contract_rejection");
            }
        }
        Path packetPath = q.freshOutput().resolveSibling(q.freshOutput().getFileName() + ".java-wire-packet.json");
        byte[] packetBytes = packet.toString().getBytes(StandardCharsets.UTF_8);
        if (packetBytes.length > CombatRolesCodec.MAX_BYTES || Files.exists(q.freshOutput()) || Files.exists(packetPath)) {
            throw new IllegalArgumentException("finite create-new consumer outputs required");
        }
        Files.write(packetPath, packetBytes, StandardOpenOption.CREATE_NEW);
        CaptureCombatRolesGolden.main(new String[] {q.repository().toString(), q.python().toString(),
                q.taskRoot().toString(), q.originalWireReference().toString(), q.nativeReceiptReference().toString(),
                q.freshOutput().toString(), packetPath.toString()});
        if (!java.util.Arrays.equals(mainBytes, CombatWholeWire.readPinned(q.mainJar(), q.taskRoot()))
                || !java.util.Arrays.equals(goldenCompressed, CombatWholeWire.readPinned(q.golden(), q.taskRoot()))
                || !java.util.Arrays.equals(originalRaw, CombatWholeWire.readPinned(q.originalWire(), q.taskRoot()))
                || !CombatWholeWire.sha256(packetBytes).equals(CombatWholeWire.sha256(readBounded(packetPath, CombatRolesCodec.MAX_BYTES)))) {
            throw new IllegalStateException("compiled source/reference/native/actual wire packet drifted during probe");
        }
        CombatWholeWire.readPinned(q.nativeProducerReceipt(), q.taskRoot());
        verifyClassFiles(q);
    }

    static Qualification decode(JsonNode value) throws IOException {
        ObjectNode root = object(value);
        Set<String> keys = new HashSet<>(); root.fieldNames().forEachRemaining(keys::add);
        if (!keys.equals(Set.of("schema", "task_root", "logs_root", "scratch_root", "repository", "python", "main_jar", "test_classes",
                "test_class_files", "golden", "original_wire", "native_producer_receipt",
                "original_wire_reference", "native_receipt_reference", "fresh_output"))
                || !SCHEMA.equals(root.path("schema").textValue())) {
            throw new IllegalArgumentException("exact actual compiled probe qualification fields required");
        }
        List<CombatWholeWire.FileReference> classes = new ArrayList<>();
        if (!root.get("test_class_files").isArray()) throw new IllegalArgumentException("compiled class references required");
        for (JsonNode ref : root.get("test_class_files")) classes.add(ref(ref));
        return new Qualification(path(root.get("task_root")), path(root.get("logs_root")), path(root.get("scratch_root")),
                path(root.get("repository")), path(root.get("python")), ref(root.get("main_jar")),
                path(root.get("test_classes")), classes, ref(root.get("golden")), ref(root.get("original_wire")),
                ref(root.get("native_producer_receipt")), path(root.get("original_wire_reference")),
                path(root.get("native_receipt_reference")), path(root.get("fresh_output")));
    }
    private static void verifyOrigins(Qualification q) throws URISyntaxException, IOException {
        if (!origin(CombatRolesCodec.class).equals(q.mainJar().path())
                || !origin(ProbeCompiledCombatConsumers.class).equals(q.testClasses())
                || !origin(CaptureCombatRolesGolden.class).equals(q.testClasses())
                || !origin(CombatWholeWire.class).equals(q.testClasses())) {
            throw new IllegalStateException("compiled domain/capture/parser loaded from an unqualified location");
        }
        if (!q.logsRoot().startsWith(q.taskRoot()) || !q.scratchRoot().startsWith(q.taskRoot())
                || q.logsRoot().equals(q.taskRoot()) || q.scratchRoot().equals(q.taskRoot())
                || !q.mainJar().path().toString().endsWith(".jar") || !q.freshOutput().startsWith(q.logsRoot())
                || Files.exists(q.freshOutput())) throw new IllegalArgumentException("qualified jar and fresh task output required");
        CombatWholeWire.FileReference rawRef = CombatWholeWire.reference(readBounded(q.originalWireReference(), 8192));
        CombatWholeWire.FileReference receiptRef = CombatWholeWire.reference(readBounded(q.nativeReceiptReference(), 8192));
        if (!rawRef.equals(q.originalWire()) || !receiptRef.equals(q.nativeProducerReceipt())) {
            throw new IllegalArgumentException("compiled probe and capture exact original references disagree");
        }
    }
    private static void verifyClassFiles(Qualification q) throws IOException {
        Set<String> relative = new HashSet<>();
        for (CombatWholeWire.FileReference ref : q.testClassFiles()) {
            if (!ref.path().startsWith(q.testClasses()) || !ref.path().toString().endsWith(".class")) {
                throw new IllegalArgumentException("qualified compiled class escapes actual test classes");
            }
            relative.add(q.testClasses().relativize(ref.path()).toString().replace('\\', '/'));
            CombatWholeWire.readPinned(ref, q.taskRoot());
        }
        for (String name : List.of("CombatWholeWire", "CaptureCombatRolesGolden", "ProbeCompiledCombatConsumers")) {
            if (!relative.contains("org/xar/ck3/control/wave2/military/combatroles/" + name + ".class")) {
                throw new IllegalArgumentException("required compiled probe class omitted from qualified manifest");
            }
        }
        Path packageRoot = q.testClasses().resolve("org/xar/ck3/control/wave2/military/combatroles");
        try (var files = Files.list(packageRoot)) {
            for (Path file : files.filter(p -> Files.isRegularFile(p, java.nio.file.LinkOption.NOFOLLOW_LINKS)).toList()) {
                String name = file.getFileName().toString();
                if (name.endsWith(".class") && (name.startsWith("CombatWholeWire$")
                        || name.startsWith("CaptureCombatRolesGolden$") || name.startsWith("ProbeCompiledCombatConsumers$"))
                        && !relative.contains(q.testClasses().relativize(file).toString().replace('\\', '/'))) {
                    throw new IllegalArgumentException("nested compiled probe class omitted from actual manifest");
                }
            }
        }
    }
    private static Path origin(Class<?> type) throws URISyntaxException { return Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize(); }
    private static CombatWholeWire.FileReference ref(JsonNode value) throws IOException {
        return CombatWholeWire.reference(value.toString().getBytes(StandardCharsets.UTF_8));
    }
    private static Path path(JsonNode value) {
        if (value == null || !value.isTextual()) throw new IllegalArgumentException("actual path string required");
        Path result = Path.of(value.textValue()); if (!result.isAbsolute() || !result.normalize().equals(result)) throw new IllegalArgumentException("normalized absolute path required"); return result;
    }
    private static ObjectNode object(JsonNode value) { if (!(value instanceof ObjectNode node)) throw new IllegalArgumentException("object required"); return node; }
    private static byte[] readBounded(Path path, int maximum) throws IOException {
        try (var stream = Files.newInputStream(path)) { byte[] raw = stream.readNBytes(maximum + 1); if (raw.length > maximum) throw new IllegalArgumentException("bounded actual artifact required"); return raw; }
    }
    private static ObjectNode snapshot(JsonNode provenance) {
        ObjectNode result = StrictJson.object();
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw")) result.set(key, provenance.get(key).deepCopy());
        ObjectNode hello = result.putObject("diagnostics").putObject("hello");
        hello.set("game_version", provenance.get("game_version").deepCopy());
        hello.set("executable_sha256", provenance.get("executable_sha256").deepCopy()); return result;
    }
    private static JsonNode scene(JsonNode golden, String name) {
        for (JsonNode row : golden.get("cases")) if (name.equals(row.path("name").textValue())) return row;
        throw new IllegalArgumentException("original scene absent from captured golden");
    }
    private static void same(JsonNode expected, JsonNode actual) {
        if (!java.util.Arrays.equals(StrictJson.canonical(expected, CombatRolesCodec.MAX_BYTES),
                StrictJson.canonical(actual, CombatRolesCodec.MAX_BYTES))) {
            throw new IllegalStateException("compiled Java output differs from original producer/consumer JSON domain");
        }
    }
}
