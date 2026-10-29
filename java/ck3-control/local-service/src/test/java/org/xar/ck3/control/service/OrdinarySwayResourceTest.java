package org.xar.ck3.control.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayServiceWire;
import static org.junit.jupiter.api.Assertions.*;

/** Real single-host adapter -> strict codec -> Java consumer; no listening server or native access. */
public final class OrdinarySwayResourceTest {
    @Test void rawTokensReachConsumerAndCanonicalBytesReturnWithoutBase64Conversion() throws Exception {
        try (InputStream stream = getClass().getResourceAsStream("/schemesway/producer-golden-v1.json")) {
            assertNotNull(stream, "g2-research resources must be present in the host test route");
            JsonNode request = StrictJson.parse(stream.readAllBytes(), 262144).path("plan_cases").get(0).get("input");
            ObjectNode envelope = StrictJson.object(); envelope.put("schema", OrdinarySwayServiceWire.REQUEST_SCHEMA);
            envelope.put("wrapper_snapshot_id", request.path("snapshot").path("snapshot_id").textValue());
            envelope.set("wrapper_revision", request.path("snapshot").get("revision"));
            envelope.put("formal_query_enabled", true); envelope.put("formal_action_enabled", true); envelope.put("lifecycle_reader_enabled", true);
            envelope.set("request", request);
            try (var response = new OrdinarySwayResource().stage(StrictJson.canonical(envelope))) {
                assertEquals(200, response.getStatus());
                assertEquals("java-ordinary-sway-service/v1", response.getHeaderString("X-Xar-Producer"));
                assertInstanceOf(byte[].class, response.getEntity());
                JsonNode result = StrictJson.parse((byte[]) response.getEntity());
                assertEquals("staged", result.path("status").textValue());
                assertEquals(900, result.path("decision").path("target_character_id").intValue());
                assertFalse(result.path("submit_allowed").booleanValue());
            }
        }
    }
    @Test void malformedRequestCannotBecomeHttpSuccessOrStage() {
        for (byte[] raw : new byte[][] {null, new byte[0], "{}".getBytes(StandardCharsets.UTF_8),
                "{\"schema\":true}".getBytes(StandardCharsets.UTF_8)}) {
            try (var response = new OrdinarySwayResource().stage(raw)) { assertEquals(400, response.getStatus()); }
        }
    }
}
