package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson;
import static org.junit.jupiter.api.Assertions.*;

/** Registered typed host boundary tests. Original Python 18 parents/43 subtests stay mandatory separately. */
final class MovementProjectionPortsTest {
    private static final Map<ProjectionOperation, RegisteredProjection> PORTS = MovementProjectionPorts.registrations()
            .stream().collect(Collectors.toUnmodifiableMap(RegisteredProjection::operation, Function.identity()));

    private static JsonNode golden(String leaf, boolean gzip) throws IOException {
        String resource = "/" + leaf + "/original-producer-golden.json" + (gzip ? ".gz" : "");
        try (var stream = MovementProjectionPortsTest.class.getResourceAsStream(resource)) {
            assertNotNull(stream, "original capture is required: " + resource);
            byte[] raw = stream.readNBytes((gzip ? 98_304 : 262_144) + 1);
            assertTrue(raw.length <= (gzip ? 98_304 : 262_144), "fixture byte bound");
            if (!gzip) { return StrictJson.parse(raw, 262_144); }
            try (var uncompressed = new GZIPInputStream(new ByteArrayInputStream(raw))) {
                return StrictJson.parse(uncompressed.readNBytes(262_145), 262_144);
            }
        }
    }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ProjectionResult execute(ProjectionOperation operation, byte[] payload) {
        var identity = new ProjectionCall.Identity("movement-port-regression", operation);
        return PORTS.get(operation).execute(new ProjectionCall(identity, ProjectionJson.object(payload, 65_536)));
    }
    private static byte[] success(ProjectionOperation operation, byte[] payload) {
        var result = assertInstanceOf(ProjectionResult.Succeeded.class, execute(operation, payload));
        assertEquals(operation, result.identity().operation());
        return result.result().bytes();
    }
    private static void rejection(ProjectionOperation operation, byte[] payload) {
        var result = assertInstanceOf(ProjectionResult.Rejected.class, execute(operation, payload));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, result.error().code());
    }

    @Test void allPortsHaveTheCanonicalRoleBoundsAndNoAliases() {
        assertEquals(5, PORTS.size());
        PORTS.values().forEach(port -> {
            assertEquals(65_536, port.inputMaximumBytes()); assertEquals(65_536, port.outputMaximumBytes());
        });
    }

    @Test void allOriginalCountyContractVectorsCrossTheRegisteredPort() throws IOException {
        JsonNode capture = golden("countyentry", false);
        assertEquals(18, capture.get("original_tests").intValue());
        assertEquals(43, capture.get("original_subtests").intValue());
        assertEquals(0, capture.get("original_skipped").intValue());
        int vectors = 0;
        for (JsonNode sample : capture.get("contract_cases")) {
            vectors++;
            if (!sample.get("present").booleanValue()) {
                assertTrue(sample.get("expected").isNull(), "old wire omission does not invoke present-only normalizer");
                continue;
            }
            ObjectNode payload = StrictJson.object(); payload.set("value", sample.get("input").get("county_entry_inputs_v1"));
            payload.set("current_soldiers", sample.get("input").get("current_soldiers"));
            assertEquals(sample.get("expected"), StrictJson.parse(success(ProjectionOperation.MILITARY_COUNTY_ENTRY_NORMALIZE, bytes(payload))));
        }
        assertEquals(8, vectors);
    }

    @Test void allOriginalPrestoreAndMovementVectorsCrossTheRegisteredPorts() throws IOException {
        JsonNode capture = golden("prestore", true);
        int prestoreVectors = 0, movementVectors = 0;
        for (JsonNode sample : capture.get("cases")) {
            prestoreVectors++;
            ObjectNode expected = sample.get("expected_top").deepCopy();
            expected.set("county_entry_risk_v1", capture.get("county_risks").get(sample.get("county_risk_index").intValue()));
            assertEquals(expected, StrictJson.parse(success(ProjectionOperation.MILITARY_PRESTORE_PROJECT, bytes(sample.get("input")))));
        }
        for (JsonNode sample : capture.get("movements")) {
            movementVectors++;
            ObjectNode payload = StrictJson.object(); payload.set("value", sample.get("input"));
            assertEquals(sample.get("expected"), StrictJson.parse(success(ProjectionOperation.MILITARY_CURRENT_MOVEMENT_NORMALIZE, bytes(payload))));
        }
        assertEquals(15, prestoreVectors); assertEquals(8, movementVectors);
        assertArrayEquals(utf8("null"), success(ProjectionOperation.MILITARY_CURRENT_MOVEMENT_NORMALIZE, utf8("{\"value\":null}")));
        for (JsonNode sample : capture.get("rejections")) {
            rejection(ProjectionOperation.MILITARY_CURRENT_MOVEMENT_NORMALIZE,
                    utf8("{\"value\":" + sample.get("raw_json").textValue() + "}"));
        }
    }

    @Test void allOriginalDisembarkTokensAndRejectionsCrossTheRegisteredPorts() throws IOException {
        JsonNode capture = golden("disembark", false);
        int vectors = 0, invalid = 0;
        for (JsonNode sample : capture.get("samples")) {
            vectors++;
            // EvidenceJson preserves float provenance and arbitrary integers; StrictJson.canonical is deliberately absent.
            byte[] payload = EvidenceJson.encode(EvidenceJson.parse(utf8(sample.get("input").toString())));
            byte[] result = success(ProjectionOperation.MILITARY_DISEMBARK_PROJECT, payload);
            assertEquals(EvidenceJson.parse(utf8(sample.get("expected_projection").toString())), EvidenceJson.parse(result));
            JsonNode raw = sample.get("input").get("raw");
            if (!raw.isNull()) {
                byte[] normalized = success(ProjectionOperation.MILITARY_DISEMBARK_NORMALIZE, utf8("{\"value\":" + raw + "}"));
                assertEquals(EvidenceJson.parse(utf8(sample.get("expected_normalized").toString())), EvidenceJson.parse(normalized));
            }
        }
        for (JsonNode sample : capture.get("rejections")) {
            invalid++;
            rejection(ProjectionOperation.MILITARY_DISEMBARK_NORMALIZE,
                    utf8("{\"value\":" + sample.get("raw_json").textValue() + "}"));
        }
        assertEquals(19, vectors); assertEquals(25, invalid);
    }

    @Test void exactWrappersRejectWrongFieldsMissingFieldsAndEqualButWrongTokenTypes() {
        for (String payload : new String[]{"{}", "{\"value\":null,\"extra\":0}", "{\"value\":null,\"current_soldiers\":0}"}) {
            rejection(ProjectionOperation.MILITARY_CURRENT_MOVEMENT_NORMALIZE, utf8(payload));
        }
        for (String token : new String[]{"true", "1.0", "\"1\"", "null"}) {
            rejection(ProjectionOperation.MILITARY_COUNTY_ENTRY_NORMALIZE,
                    utf8("{\"value\":{},\"current_soldiers\":" + token + "}"));
        }
        rejection(ProjectionOperation.MILITARY_DISEMBARK_PROJECT, utf8("{\"raw\":null}"));
        rejection(ProjectionOperation.MILITARY_PRESTORE_PROJECT, utf8("{}"));
    }
}
