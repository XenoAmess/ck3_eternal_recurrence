package org.xar.ck3.control.wave2.finance.projection;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.ServiceLoader;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

final class RawCashProjectionPortTest {
    private static final int DOCUMENT_MAX = 65_536;
    private record Vector(String kind, ObjectNode arguments, JsonNode expected) { }

    @Test void actualSpiHasOneRawCashPortWithTwoDocumentWrapperAndOriginalResultBudgets() {
        var profiles = dispatcher().profiles().stream()
                .filter(profile -> profile.operation() == ProjectionOperation.RAW_CASH_NORMALIZE).toList();
        assertEquals(1, profiles.size(), "the real SPI catalog must register this port exactly once");
        assertEquals(132_096, profiles.getFirst().inputMaximumBytes());
        assertEquals(DOCUMENT_MAX, profiles.getFirst().outputMaximumBytes());
    }

    @Test void everyRetainedOriginalNormalizeVectorReachesTheRealSpiDispatcher() throws Exception {
        int successful = 0, invalid = 0;
        for (Vector vector : normalizeVectors()) {
            ProjectionResult result = dispatch(wire(vector.arguments()));
            if (vector.kind().equals("invalid_contract")) {
                ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, result);
                assertTrue(Set.of(ProjectionError.Code.INVALID_PAYLOAD, ProjectionError.Code.DOMAIN_REJECTED)
                        .contains(rejected.error().code()), "an actual negative vector must reach a registered decoder or domain");
                invalid++;
            } else {
                ProjectionResult.Succeeded actual = assertInstanceOf(ProjectionResult.Succeeded.class, result);
                assertEquals(vector.expected(), StrictJson.parse(actual.result().bytes()));
                assertArrayEquals(RawCashCodec.normalize(
                        SdkProjectionJson.encode(vector.arguments().get("value")),
                        SdkProjectionJson.encode(vector.arguments().get("snapshot"))).toJson(), actual.result().bytes());
                assertEquals(StrictJson.parse(actual.result().bytes()),
                        StrictJson.parse(ProjectionWire.encodeResult(actual)).get("result"));
                successful++;
            }
        }
        assertEquals(50, successful, "all actual original successful normalizations are mandatory");
        assertEquals(84, invalid, "all actual original invalid normalizations are mandatory");
    }

    @Test void checkedRequestDefensivelyCopiesBothTreesAndRetainsJsonNull() throws Exception {
        ObjectNode original = firstSuccessfulArguments();
        ObjectNode value = object(original.get("value"));
        ObjectNode snapshot = object(original.get("snapshot"));
        var request = new RawCashNormalizeProjectionPort.Request(value, snapshot);
        JsonNode expectedValue = value.deepCopy(), expectedSnapshot = snapshot.deepCopy();
        value.removeAll(); snapshot.removeAll();
        object(request.value()).removeAll(); request.snapshot().removeAll();
        assertEquals(expectedValue, request.value());
        assertEquals(expectedSnapshot, request.snapshot());
        var port = new RawCashNormalizeProjectionPort();
        var explicitNull = port.decode("{\"value\":null,\"snapshot\":{}}".getBytes(StandardCharsets.UTF_8));
        assertTrue(explicitNull.value().isNull());
        assertThrows(IllegalArgumentException.class, () -> port.project(explicitNull));
        assertThrows(IllegalArgumentException.class, () -> port.decode("{\"snapshot\":{}}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void exactWrapperRejectsMissingExtraNullAndWrongSnapshotShapes() throws Exception {
        for (String raw : List.of(
                "{}", "{\"value\":{}}", "{\"snapshot\":{}}",
                "{\"value\":{},\"snapshot\":null}", "{\"value\":{},\"snapshot\":[]}",
                "{\"value\":{},\"snapshot\":{},\"extra\":0}")) {
            assertRejected(ProjectionError.Code.INVALID_PAYLOAD, raw.getBytes(StandardCharsets.UTF_8));
        }
        for (String raw : List.of("{\"value\":null,\"snapshot\":{}}", "{\"value\":[],\"snapshot\":{}}")) {
            assertRejected(ProjectionError.Code.DOMAIN_REJECTED, raw.getBytes(StandardCharsets.UTF_8));
        }
        ObjectNode missing = firstSuccessfulArguments();
        object(missing.get("value")).remove("schema");
        assertRejected(ProjectionError.Code.DOMAIN_REJECTED, wire(missing));
    }

    @Test void sdkFloatExtensionAndNullStayDistinctFromAbsentWhileFloatIdentityIsRejected() throws Exception {
        ObjectNode arguments = firstSuccessfulArguments();
        ObjectNode value = object(arguments.get("value"));
        value.put("raw_cash_port_float_extension", 1.0);
        value.putNull("raw_cash_port_nullable_extension");
        object(arguments.get("snapshot")).put("raw_cash_port_snapshot_float_extension", 2.0);
        JsonNode output = StrictJson.parse(succeeded(wire(arguments)).result().bytes());
        assertTrue(output.get("raw_cash_port_float_extension").isFloatingPointNumber());
        assertTrue(output.has("raw_cash_port_nullable_extension") && output.get("raw_cash_port_nullable_extension").isNull());
        value.remove("raw_cash_port_nullable_extension");
        assertFalse(StrictJson.parse(succeeded(wire(arguments)).result().bytes()).has("raw_cash_port_nullable_extension"));
        value.put("snapshot_revision", value.get("snapshot_revision").bigIntegerValue().doubleValue());
        byte[] floating = wire(arguments);
        assertTrue(StrictJson.parse(floating, RawCashNormalizeProjectionPort.INPUT_MAX_BYTES)
                .get("value").get("snapshot_revision").isFloatingPointNumber());
        assertRejected(ProjectionError.Code.DOMAIN_REJECTED, floating);
        arguments = firstSuccessfulArguments();
        ObjectNode snapshot = object(arguments.get("snapshot"));
        snapshot.put("native_revision", snapshot.get("native_revision").bigIntegerValue().doubleValue());
        assertRejected(ProjectionError.Code.DOMAIN_REJECTED, wire(arguments));
    }

    @Test void bothOriginalDocumentsCanReachTheirOwnLimitInsideTheLargerWrapper() throws Exception {
        ObjectNode arguments = firstSuccessfulArguments();
        // Optional loan absence keeps this boundary case's output equal in size to its actual current document.
        object(arguments.get("value")).remove(RawCashCodec.LOAN_KEY);
        pad(object(arguments.get("value")), DOCUMENT_MAX);
        pad(object(arguments.get("snapshot")), DOCUMENT_MAX);
        assertEquals(DOCUMENT_MAX, SdkProjectionJson.encode(arguments.get("value")).length);
        assertEquals(DOCUMENT_MAX, SdkProjectionJson.encode(arguments.get("snapshot")).length);
        byte[] raw = wire(arguments);
        assertTrue(raw.length > DOCUMENT_MAX && raw.length <= RawCashNormalizeProjectionPort.INPUT_MAX_BYTES);
        ProjectionResult.Succeeded result = succeeded(raw);
        assertEquals(DOCUMENT_MAX, result.result().size());
        assertEquals(arguments.get("value"), StrictJson.parse(result.result().bytes()));
        byte[] exactWrapper = paddedWrapper(raw, RawCashNormalizeProjectionPort.INPUT_MAX_BYTES);
        assertEquals(RawCashNormalizeProjectionPort.INPUT_MAX_BYTES, exactWrapper.length);
        assertArrayEquals(result.result().bytes(), succeeded(exactWrapper).result().bytes());
    }

    @Test void aSingleOversizedDocumentIsStillRefusedEvenWhenItsWrapperFits() throws Exception {
        for (String field : List.of("value", "snapshot")) {
            ObjectNode arguments = firstSuccessfulArguments();
            pad(object(arguments.get(field)), DOCUMENT_MAX + 1);
            byte[] raw = wire(arguments);
            assertTrue(raw.length <= RawCashNormalizeProjectionPort.INPUT_MAX_BYTES);
            assertRejected(ProjectionError.Code.DOMAIN_REJECTED, raw);
        }
    }

    @Test void wrapperTotalLimitIsEnforcedByTheActualDispatcherBeforeDomainWork() throws Exception {
        byte[] original = wire(firstSuccessfulArguments());
        assertTrue(original.length <= RawCashNormalizeProjectionPort.INPUT_MAX_BYTES);
        byte[] oversized = paddedWrapper(original, RawCashNormalizeProjectionPort.INPUT_MAX_BYTES + 1);
        assertRejected(ProjectionError.Code.PAYLOAD_TOO_LARGE, oversized);
    }

    @Test void generatedOutputOverflowIsAnInternalFailureAtTheRealRawCashPort() throws Exception {
        ObjectNode arguments = firstGrowingLoanArguments();
        pad(object(arguments.get("value")), DOCUMENT_MAX);
        byte[] current = SdkProjectionJson.encode(arguments.get("value"));
        byte[] snapshot = SdkProjectionJson.encode(arguments.get("snapshot"));
        var error = assertThrows(IllegalStateException.class, () -> RawCashCodec.normalize(current, snapshot));
        assertInstanceOf(ContractViolationException.class, error.getCause());
        assertRejected(ProjectionError.Code.PROJECTION_FAILED, wire(arguments));
    }

    @Test void financingDoesNotConvertGeneratedOutputOverflowIntoARefusedObservation() throws Exception {
        ObjectNode arguments = firstGrowingLoanArguments();
        ObjectNode cash = object(arguments.get("value")), snapshot = object(arguments.get("snapshot"));
        ObjectNode source = StrictJson.object();
        source.put("schema", "xar.ck3.planning-source-frame/v1"); source.put("status", "complete");
        for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")) {
            source.set(key, snapshot.get(key));
        }
        source.set("actor_character_id", snapshot.get("played_character").get("character_id"));
        source.set("bridge_pid", snapshot.get("diagnostics").get("bridge_pid"));
        source.set("connection_generation", snapshot.get("diagnostics").get("connection_generation"));
        for (String key : List.of("snapshot_id", "revision", "native_revision")) {
            cash.set("queried_" + key, snapshot.get(key));
        }
        ObjectNode request = StrictJson.object();
        request.set("snapshot", snapshot); request.set("cash_resources", cash); request.set("cash_source_frame", source);
        int overhead = SdkProjectionJson.encode(request).length - SdkProjectionJson.encode(cash).length;
        pad(cash, DOCUMENT_MAX - overhead);
        byte[] raw = SdkProjectionJson.encode(request);
        assertEquals(DOCUMENT_MAX, raw.length);
        var error = assertThrows(IllegalStateException.class, () -> LoanFinancingCodec.decodeAndProject(raw));
        assertInstanceOf(ContractViolationException.class, error.getCause());
        ProjectionCall call = new ProjectionCall(
                new ProjectionCall.Identity("loan-generated-output-test", ProjectionOperation.HOLY_LOAN_PROJECT),
                ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
        var rejected = assertInstanceOf(ProjectionResult.Rejected.class, dispatcher().dispatch(ProjectionWire.encodeCall(call)));
        assertEquals(ProjectionError.Code.PROJECTION_FAILED, rejected.error().code());
    }

    private static ObjectNode firstGrowingLoanArguments() throws Exception {
        for (Vector vector : normalizeVectors()) {
            if (vector.kind().equals("result") && vector.arguments().get("value").has(RawCashCodec.LOAN_KEY)
                    && SdkProjectionJson.encode(vector.expected()).length
                    > SdkProjectionJson.encode(vector.arguments().get("value")).length) {
                return vector.arguments().deepCopy();
            }
        }
        throw new IllegalStateException("an actual retained growing loan normalization vector is required");
    }

    private static void pad(ObjectNode document, int target) {
        document.put("raw_cash_port_boundary_padding_a", "");
        document.put("raw_cash_port_boundary_padding_b", "");
        int base = SdkProjectionJson.encode(document).length;
        assertTrue(base < target);
        int remaining = target - base, first = Math.min(32_768, remaining);
        assertTrue(remaining - first <= 32_768, "retain the original per-string codepoint limit");
        document.put("raw_cash_port_boundary_padding_a", "x".repeat(first));
        document.put("raw_cash_port_boundary_padding_b", "x".repeat(remaining - first));
        assertEquals(target, SdkProjectionJson.encode(document, RawCashNormalizeProjectionPort.INPUT_MAX_BYTES).length);
    }
    private static byte[] paddedWrapper(byte[] original, int target) {
        assertEquals((byte) '{', original[0]); assertTrue(target >= original.length);
        byte[] raw = new byte[target]; raw[0] = '{';
        int padding = target - original.length;
        // Internal whitespace remains part of the captured payload span; trailing whitespace would not.
        java.util.Arrays.fill(raw, 1, padding + 1, (byte) ' ');
        System.arraycopy(original, 1, raw, padding + 1, original.length - 1);
        return raw;
    }
    private static byte[] wire(JsonNode wrapper) {
        return SdkProjectionJson.encode(wrapper, RawCashNormalizeProjectionPort.INPUT_MAX_BYTES);
    }
    private static ProjectionDispatcher dispatcher() {
        return ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
    }
    private static ProjectionResult dispatch(byte[] raw) {
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("rawcash-port-test", ProjectionOperation.RAW_CASH_NORMALIZE),
                ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
        return dispatcher().dispatch(ProjectionWire.encodeCall(call));
    }
    private static ProjectionResult.Succeeded succeeded(byte[] raw) {
        return assertInstanceOf(ProjectionResult.Succeeded.class, dispatch(raw));
    }
    private static void assertRejected(ProjectionError.Code code, byte[] raw) {
        assertEquals(code, assertInstanceOf(ProjectionResult.Rejected.class, dispatch(raw)).error().code());
    }
    private static ObjectNode object(JsonNode value) {
        return assertInstanceOf(ObjectNode.class, value, "actual object field is required");
    }
    private static ObjectNode firstSuccessfulArguments() throws Exception {
        for (Vector vector : normalizeVectors()) {
            if (vector.kind().equals("result")) { return vector.arguments().deepCopy(); }
        }
        throw new IllegalStateException("an actual original successful normalize vector is required");
    }
    private static List<Vector> normalizeVectors() throws Exception {
        InputStream source = RawCashProjectionPortTest.class.getResourceAsStream("/holyloan/original-v1.jsonl.gz");
        assertNotNull(source, "retained original golden is mandatory; missing evidence is never skipped");
        byte[] compressed;
        try (InputStream input = source) { compressed = input.readNBytes(65_537); }
        assertEquals(20_361, compressed.length, "the retained original02 corpus must be used unchanged");
        assertEquals("4d0b61ac6ce05b16b78b3ff4bf51891b9780ba348edff7d8c8c6da09780c3539",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
        try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            byte[] raw = gzip.readNBytes(8 * 1024 * 1024 + 1);
            assertTrue(raw.length <= 8 * 1024 * 1024, "bounded retained corpus");
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            String[] lines = text.split("\n", -1);
            assertEquals("", lines[lines.length - 1]);
            assertTrue(lines.length >= 5 && (lines.length - 2) % 3 == 0);
            JsonNode header = StrictJson.parse(lines[0].getBytes(StandardCharsets.UTF_8));
            assertEquals("xar.holyloan-rawcash-original-golden.v1", header.path("schema").textValue());
            assertFalse(StrictJson.text(header.get("machine_id")).isBlank());
            StrictJson.text(header.get("observed_at_utc"));
            assertTrue(header.path("source_sha256").isObject() && header.path("source_sha256").size() >= 15);
            assertEquals(0, header.path("skips").intValue());
            int count = (lines.length - 2) / 3;
            assertTrue(count <= 1000);
            assertEquals(count, header.path("vector_count").intValue());
            List<Vector> vectors = new ArrayList<>();
            for (int index = 1; index < lines.length - 1; index += 3) {
                JsonNode metadata = StrictJson.parse(lines[index].getBytes(StandardCharsets.UTF_8));
                assertEquals((index - 1) / 3 + 1, metadata.path("ordinal").intValue());
                String kind = StrictJson.text(metadata.get("expected_kind"));
                assertTrue(Set.of("result", "invalid_contract").contains(kind));
                JsonNode request = StrictJson.parse(lines[index + 1].getBytes(StandardCharsets.UTF_8));
                if ("normalize".equals(request.path("operation").textValue())) {
                    vectors.add(new Vector(kind, object(request.get("arguments")),
                            StrictJson.parse(lines[index + 2].getBytes(StandardCharsets.UTF_8))));
                }
            }
            assertEquals(134, vectors.size(), "all retained normalize vectors are required");
            return List.copyOf(vectors);
        }
    }
}
