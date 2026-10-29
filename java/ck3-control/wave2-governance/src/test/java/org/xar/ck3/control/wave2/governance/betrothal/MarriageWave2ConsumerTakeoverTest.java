package org.xar.ck3.control.wave2.governance.betrothal;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffCodec;

/** Producer goldens enter the actual registered typed operation, then the existing consumer codecs. */
class MarriageWave2ConsumerTakeoverTest {
    private static JsonNode golden(String resource) throws Exception {
        try (var input = MarriageWave2ConsumerTakeoverTest.class.getResourceAsStream(resource)) {
            assertNotNull(input, "actual original producer resource is mandatory; never skip missing evidence");
            return MarriageProjectionJson.value(input.readAllBytes(), 262_144);
        }
    }
    private static byte[] bytes(JsonNode node) { return MarriageProjectionJson.bytes(node, 525_312); }
    private static <I, O> JsonNode call(ProjectionPort<I, O> port, JsonNode request) {
        byte[] raw = port.encode(port.project(port.decode(bytes(request))));
        assertTrue(raw.length <= port.outputMaximumBytes());
        return MarriageProjectionJson.value(raw, port.outputMaximumBytes());
    }
    private static ObjectNode patch(JsonNode base, JsonNode changes) {
        ObjectNode result = base.deepCopy();
        for (JsonNode change : changes) {
            JsonNode parent = result, path = change.get("path");
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode key = path.get(index); parent = key.isIntegralNumber() ? parent.get(key.intValue()) : parent.get(key.textValue());
            }
            JsonNode key = path.get(path.size() - 1);
            if (parent instanceof ObjectNode object) {
                if (change.path("remove").asBoolean(false)) { object.remove(key.textValue()); }
                else { object.set(key.textValue(), change.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (change.path("remove").asBoolean(false)) { array.remove(key.intValue()); }
                else { array.set(key.intValue(), change.get("value").deepCopy()); }
            } else { fail("invalid actual producer patch"); }
        }
        return result;
    }
    @Test void originalBuildResultsRoundTripIntoTheExistingResourceConsumer() throws Exception {
        JsonNode golden = golden("/betrothal/python-golden-v1.json");
        assertEquals(10, golden.path("original_tests_run").intValue());
        for (JsonNode vector : golden.path("build_cases")) {
            JsonNode actual = call(new MarriageWave2ProjectionCatalog.BuildPort(), patch(golden.get("base_build_request"), vector.get("patches")));
            assertEquals(vector.get("expected_resource"), actual, vector.path("name").asText());
            BetrothalModel.ResourceProposal consumer = BetrothalCodec.decodeResource(bytes(actual));
            assertEquals(actual, BetrothalCodec.readJson(BetrothalCodec.encodeResource(consumer)));
            assertEquals(Boolean.FALSE, consumer.resourceReservationPerformed());
        }
    }
    @Test void originalAdapterAcceptAndRejectCasesPassThroughTheRegisteredPort() throws Exception {
        JsonNode golden = golden("/betrothal/python-golden-v1.json");
        var port = new MarriageWave2ProjectionCatalog.AdaptPort();
        for (JsonNode vector : golden.path("adapt_cases")) {
            ObjectNode request = patch(golden.get("base_adapt_request"), vector.get("patches"));
            if (vector.path("expected").path("accepted").asBoolean()) {
                assertEquals(vector.path("expected").get("proposal"), call(port, request), vector.path("name").asText());
            } else {
                assertThrows(IllegalArgumentException.class, () -> call(port, request), vector.path("name").asText());
            }
        }
    }
    private static ObjectNode handoff(String stage, JsonNode request) {
        ObjectNode root = StrictJson.object(); root.put("schema", MarriageWave2ProjectionCatalog.EpisodeHandoffPort.SCHEMA);
        root.put("stage", stage); root.set("request", request.deepCopy()); return root;
    }
    @Test void originalHandoffResultIsRevalidatedBeforeExistingWriterConsumption() throws Exception {
        JsonNode golden = golden("/marriagehandoff/original-producer-golden.json");
        JsonNode request = golden.get("base_request");
        var port = new MarriageWave2ProjectionCatalog.EpisodeHandoffPort();
        JsonNode prepared = call(port, handoff("prepare", request));
        assertEquals("prepared", prepared.path("stage").asText());
        assertTrue(prepared.path("result").path("write_required").asBoolean());
        ObjectNode revalidate = handoff("revalidate", request); revalidate.set("current_ledger", request.get("ledger").deepCopy());
        JsonNode validated = call(port, revalidate);
        assertEquals(prepared.path("result").get("ledger"), validated.get("ledger"));
        assertNotNull(MarriageHandoffCodec.decodeLedger(bytes(validated.get("ledger"))));
        assertFalse(prepared.path("result").path("receipt").path("ck3_command_submitted").asBoolean());
        ObjectNode changed = revalidate.deepCopy(); ((ObjectNode) changed.get("current_ledger")).put("concurrent_writer_evidence", true);
        assertThrows(ProjectionDomainRejection.class, () -> call(port, changed));
        assertEquals(request.get("ledger"), revalidate.get("current_ledger"), "pure revalidation never mutates caller evidence");
    }
    @Test void wrapperRejectsMissingExtraWrongStageAndMalformedIntegerTokens() throws Exception {
        JsonNode request = golden("/marriagehandoff/original-producer-golden.json").get("base_request");
        var port = new MarriageWave2ProjectionCatalog.EpisodeHandoffPort();
        ObjectNode extra = handoff("prepare", request); extra.put("qualified", true);
        assertThrows(IllegalArgumentException.class, () -> port.decode(bytes(extra)));
        ObjectNode missing = handoff("revalidate", request);
        assertThrows(IllegalArgumentException.class, () -> port.decode(bytes(missing)));
        assertThrows(IllegalArgumentException.class, () -> port.decode(bytes(handoff("ack", request))));
        assertThrows(IllegalArgumentException.class, () -> port.decode(new byte[port.inputMaximumBytes() + 1]));
    }
    @Test void originalAdapterBusinessGateUsesExplicitDomainRejection() throws Exception {
        ObjectNode request = golden("/betrothal/python-golden-v1.json").get("base_adapt_request").deepCopy();
        ((ObjectNode) request.path("plan").path("current_betrothal_choice").path("resource_proposal")).put("selected", false).put("formal_action_ready", false);
        var port = new MarriageWave2ProjectionCatalog.AdaptPort();
        var input = port.decode(bytes(request));
        var rejected = assertThrows(ProjectionDomainRejection.class, () -> port.project(input));
        assertEquals("selected same-frame current-betrothal resource proposal required", rejected.getMessage());
    }
    @Test void decimalEvidenceSurvivesTheActualProducerPortAndConsumerRoundTrip() {
        byte[] raw = "{\"opaque\":1.0,\"identity\":18446744073709551615}".getBytes(StandardCharsets.UTF_8);
        BetrothalModel.WireValue typed = BetrothalCodec.decodeEvidence(raw);
        byte[] encoded = BetrothalCodec.encodeEvidence(typed);
        assertTrue(BetrothalCodec.readJson(encoded).get("opaque").isFloatingPointNumber());
        assertEquals(typed, BetrothalCodec.decodeEvidence(encoded));
    }
}
